"""Functions for manipulating ABINIT files."""

from __future__ import annotations

import contextlib
import logging
import os
from itertools import chain
from pathlib import Path
from typing import TYPE_CHECKING

from abipy.flowtk.utils import abi_extensions
from jobflow.core.job import job
from monty.serialization import loadfn

from atomate2 import SETTINGS
from atomate2.abinit.utils.common import INDIR_NAME
from atomate2.common.files import delete_files, gzip_files
from atomate2.utils.file_client import FileClient, auto_fileclient
from atomate2.utils.path import strip_hostname

if TYPE_CHECKING:
    from collections.abc import Iterable

    from abipy.abio.inputs import AbinitInput
    from pymatgen.core.structure import Structure

    from atomate2.abinit.sets.anaddb import AnaddbInputGenerator
    from atomate2.abinit.sets.base import AbinitInputGenerator
    from atomate2.abinit.sets.merge import MergeInputGenerator

__all__ = [
    "del_gzip_files",
    "fname2ext",
    "load_abinit_input",
    "out_to_in",
    "write_abinit_input_set",
    "write_anaddb_input_set",
    "write_merge_input_set",
    "write_mrgddb_input_set",
    "write_mrgdv_input_set",
]

logger = logging.getLogger(__name__)

ALL_ABIEXTS = abi_extensions()


def fname2ext(filepath: Path | str) -> str | None:
    """
    Get the ABINIT extension of a given filename.

    Parameters
    ----------
    filepath : Path or str
        Path to the file.

    Returns
    -------
    str or None
        The ABINIT extension if found, None otherwise.

    Notes
    -----
    For perturbations, the density file is named out_DENxx instead of
    out_1DENxx, so the extension is normalized to 1DEN.
    """
    filename = os.path.basename(filepath)
    if "_" not in filename:
        return None
    ext = filename.split("_")[-1].replace(".nc", "")
    if "1WF" in ext:
        ext = "1WF"
    if "DEN" in ext and ext[-1].isdigit():
        ext = "1DEN"
    if ext not in ALL_ABIEXTS:
        return None
    return ext


@auto_fileclient
def out_to_in(
    out_files: Iterable[tuple[str, str]],
    src_host: str | None = None,
    indir: Path | str = INDIR_NAME,
    file_client: FileClient | None = None,
    link_files: bool = True,
) -> None:
    """
    Copy or link ABINIT output files to the ABINIT input directory.

    Parameters
    ----------
    out_files : Iterable[tuple[str, str]]
        The list of (ABINIT output filepath, ABINIT input filename) tuples
        to be copied or linked.
    src_host : str or None
        The source hostname used to specify a remote filesystem. Can be given
        as either "username@remote_host" or just "remote_host" in which case
        the username will be inferred from the current user. If None, the
        local filesystem will be used as the source. Default is None.
    indir : Path or str
        The input directory for ABINIT input files. Default is INDIR_NAME.
    file_client : FileClient or None
        A file client to use for performing file operations. Default is None.
    link_files : bool
        Whether to link the files instead of copying them. Default is True.
    """
    dest_dir = file_client.abspath(indir, host=None)

    for out_filepath, in_file in out_files:
        src_file = file_client.abspath(out_filepath, host=src_host)
        dest_file = os.path.join(dest_dir, in_file)
        if link_files and src_host is None:
            file_client.link(src_file, dest_file)
        else:
            file_client.copy(src_file, dest_file, src_host=src_host)


def load_abinit_input(
    dirpath: Path | str, fname: str = "abinit_input.json"
) -> AbinitInput:
    """
    Load the AbinitInput object from a given directory.

    Parameters
    ----------
    dirpath : Path or str
        Directory to load the AbinitInput from.
    fname : str
        Name of the JSON file containing the AbinitInput.
        Default is "abinit_input.json".

    Returns
    -------
    AbinitInput
        The AbinitInput object.

    Raises
    ------
    NotImplementedError
        If the specified file does not exist in the directory.

    Notes
    -----
    Future implementation could use FileClient for remote filesystem support.
    """
    dirpath = strip_hostname(dirpath)
    abinit_input_file = os.path.join(dirpath, f"{fname}")
    if not os.path.exists(abinit_input_file):
        raise NotImplementedError(
            f"Cannot load AbinitInput from directory {dirpath} without {fname} file."
        )

    return loadfn(abinit_input_file)


def write_abinit_input_set(
    structure: Structure,
    input_set_generator: AbinitInputGenerator,
    prev_outputs: str | Path | list[str] | None = None,
    restart_from: str | Path | list[str] | None = None,
    directory: str | Path = ".",
) -> None:
    """
    Write the ABINIT inputs for a given structure using a given generator.

    Parameters
    ----------
    structure : Structure
        The structure for which the ABINIT inputs have to be written.
    input_set_generator : AbinitInputGenerator
        The input generator used to write the ABINIT inputs.
    prev_outputs : str or Path or list[str] or None
        The list of previous directories needed for the calculation.
        Default is None.
    restart_from : str or Path or list[str] or None
        The previous directory of the same calculation (in case of a restart).
        Should be provided as a list of one directory. Default is None.
    directory : str or Path
        Directory in which to write the ABINIT inputs. Default is ".".

    Raises
    ------
    RuntimeError
        If the generated AbinitInputSet is not valid.
    """
    ais = input_set_generator.get_input_set(
        structure=structure,
        restart_from=restart_from,
        prev_outputs=prev_outputs,
    )
    if not ais.validate():
        raise RuntimeError("AbinitInputSet is not valid.")

    ais.write_input(directory=directory, make_dir=True, overwrite=False)


def write_merge_input_set(
    input_set_generator: MergeInputGenerator,
    prev_outputs: str | Path | list[str] | None = None,
    directory: str | Path = ".",
) -> None:
    """
    Write the input of an ABINIT merge utility (mrgddb, mrgdv) using a generator.

    Parameters
    ----------
    input_set_generator : MergeInputGenerator
        The input generator used to write the inputs.
    prev_outputs : str or Path or list[str] or None
        The list of previous directories whose outputs are merged.
        Default is None.
    directory : str or Path
        Directory in which to write the inputs. Default is ".".

    Raises
    ------
    RuntimeError
        If the generated input set is not valid, e.g. if some of the files to
        merge do not exist.
    """
    merge_is = input_set_generator.get_input_set(
        prev_outputs=prev_outputs,
        workdir=directory,
    )
    if not merge_is.validate():
        raise RuntimeError(
            f"{type(merge_is).__name__} is not valid. "
            "Some previous outputs do not exist."
        )

    merge_is.write_input(directory=directory, make_dir=True, overwrite=False)


# Names used by the MRGDDB and MRGDV jobs (and patched by the test mocks)
write_mrgddb_input_set = write_merge_input_set
write_mrgdv_input_set = write_merge_input_set


def write_anaddb_input_set(
    structure: Structure,
    input_set_generator: AnaddbInputGenerator,
    prev_outputs: str | Path | list[str] | None = None,
    directory: str | Path = ".",
) -> None:
    """
    Write the ANADDB input using a given generator.

    Parameters
    ----------
    structure : Structure
        The structure for the ANADDB calculation.
    input_set_generator : AnaddbInputGenerator
        The input generator used to write the ANADDB inputs.
    prev_outputs : str or Path or list[str] or None
        The list of previous directories needed for the calculation.
        Default is None.
    directory : str or Path
        Directory in which to write the ANADDB inputs. Default is ".".

    Raises
    ------
    RuntimeError
        If the generated AnaddbInputSet is not valid or if some previous
        outputs do not exist.
    """
    anais = input_set_generator.get_input_set(
        structure=structure,
        prev_outputs=prev_outputs,
    )
    if not anais.validate():
        raise RuntimeError(
            "AnaddbInputSet is not valid. Some previous outputs do not exist."
        )

    anais.write_input(directory=directory, make_dir=True, overwrite=False)


# TODO: does not take the directories of the store_inputs
@job
def del_gzip_files(
    outputs: list,
    exclude_files_from_zip: list[str | Path] | None = None,
    delete: bool = True,
    exclude_files_from_del: list[str | Path] | None = None,
    include_files_to_del: list[str | Path] | None = None,
) -> None:
    r"""
    Delete and gzip files from a previous Job or Flow.

    Parameters
    ----------
    outputs : list
        Outputs of the Job or Flow that needs its files deleted/compressed.
    exclude_files_from_zip : list[str or Path] or None
        Filenames to exclude from compression. Supports glob file matching,
        e.g., "\*.dat". Default is None.
    delete : bool
        Whether to activate deletion of files. Default is True.
    exclude_files_from_del : list[str or Path] or None
        Filenames to exclude from deletion. Supports glob file matching,
        e.g., "\*.dat". Default is None.
    include_files_to_del : list[str or Path] or None
        Filenames to include for deletion as a list of str or Path objects
        given relative to directory. Glob file paths are supported,
        e.g., "\*.dat". If None, all files in the directory will be deleted.
        Default is None.

    Notes
    -----
    Compressed directories can no longer be used as ``prev_outputs`` or
    ``restart_from`` of a new job: files such as ``abinit_input.json``, the
    GSR or the DDB are then only available as ``.gz``, and the files in
    ``SETTINGS.ABINIT_FILES_TO_DEL`` (e.g. DEN and WFK) are deleted. To keep a
    directory reusable, exclude the needed files, e.g.
    ``exclude_files_from_zip=["abinit_input.json", "*GSR*", "*DDB*", "*DEN*",
    "*WFK*"]`` together with ``exclude_files_from_del=["*DEN*", "*WFK*"]``.
    """
    dirs_to_clean = []
    for o in outputs:
        with contextlib.suppress(TypeError, AttributeError):
            dirs_to_clean.append(o.dir_name)
        with contextlib.suppress(TypeError, AttributeError, KeyError):
            o_dirs = o["dirs"]
            if type(o_dirs) is dict:
                dirs_to_clean.extend(
                    list(chain(*o_dirs.values()))
                )  # flatten values of dict
            else:
                dirs_to_clean.extend(o_dirs)
        with contextlib.suppress(TypeError, AttributeError, KeyError):
            dirs_to_clean.append(o["dir_name"])  # to zip run_rf and generate_perts
        with contextlib.suppress(TypeError, AttributeError, KeyError):
            dirs_to_clean.extend(
                o.history_dirs
            )  # to clean dirs unconverged and restarted

    recursiv_dirs_to_clean = []
    for dz_ in dirs_to_clean:
        dz = strip_hostname(dz_)
        recursiv_dirs_to_clean.append(Path(dz))
        for root, _, _ in os.walk(dz):
            recursiv_dirs_to_clean.append(Path(root))
    # to take its own directory into account
    recursiv_dirs_to_clean.append(Path(os.getcwd()))

    if delete:
        if include_files_to_del is None:
            include_files_to_del = SETTINGS.ABINIT_FILES_TO_DEL
        for d in recursiv_dirs_to_clean:
            delete_files(
                directory=strip_hostname(d),
                include_files=include_files_to_del,
                exclude_files=exclude_files_from_del,
                allow_missing=True,
            )

    for d in recursiv_dirs_to_clean:
        gzip_files(
            directory=strip_hostname(d),
            exclude_files=exclude_files_from_zip,
            force=True,
        )
