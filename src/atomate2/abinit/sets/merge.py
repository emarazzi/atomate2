"""Shared input set and generator for the ABINIT merge utilities.

ABINIT ships several utilities that merge the outputs of many perturbation
calculations into a single file, reading a short input from stdin: mrgddb
(DDB files), mrgdv (first-order potentials), and also mrggkk and mrgscr, which
are not used in atomate2 yet. The classes here implement the common logic;
each utility only defines the few attributes that differ (see
:obj:`.MrgddbInputGenerator` and :obj:`.MrgdvInputGenerator`).
"""

from __future__ import annotations

import copy
import logging
import os
import time
from dataclasses import dataclass
from typing import TYPE_CHECKING, ClassVar

from pymatgen.io.core import InputSet

from atomate2.abinit.sets.base import AbinitMixinInputGenerator, set_workdir
from atomate2.abinit.utils.common import OUTDIR_NAME

if TYPE_CHECKING:
    from collections.abc import Iterable
    from pathlib import Path

__all__ = ["MergeInputGenerator", "MergeInputSet"]

logger = logging.getLogger(__name__)


class MergeInputSet(InputSet):
    """
    Input set for an ABINIT merge utility (mrgddb, mrgdv, ...).

    The utility reads its input from stdin, written to ``input_file_name``.
    The files to merge are referenced in that input by absolute path, so
    ``input_files`` is only used to validate that they exist.

    Subclasses define the class attributes below.

    Attributes
    ----------
    input_file_name : str
        Name of the file passed as stdin to the utility (e.g. "mrgddb.in").
    in_file_prefix : str
        Expected prefix of the input file names of the files to merge
        (e.g. "in_DDB"), used by :meth:`validate`.
    """

    input_file_name: ClassVar[str]
    in_file_prefix: ClassVar[str]

    def __init__(
        self,
        merge_input: str,
        input_files: Iterable[tuple[str, str]] | None = None,
    ) -> None:
        """
        Initialize a MergeInputSet.

        Parameters
        ----------
        merge_input : str
            The stdin input string of the merge utility.
        input_files : Iterable[tuple[str, str]] or None
            List of (output_filepath, input_filename) tuples for the files to
            merge. Default is None.
        """
        self.input_files = input_files
        super().__init__(inputs={self.input_file_name: merge_input})

    def write_input(
        self,
        directory: str | Path,
        make_dir: bool = True,
        overwrite: bool = True,
        zip_inputs: bool = False,
    ) -> None:
        """
        Write the input file and create the standard ABINIT directories.

        Parameters
        ----------
        directory : str or Path
            The directory to write the input files to.
        make_dir : bool
            Whether to create the directory if it does not exist. Default is True.
        overwrite : bool
            Whether to overwrite existing files. Default is True.
        zip_inputs : bool
            Whether to zip the input files. Default is False.
        """
        super().write_input(
            directory=directory,
            make_dir=make_dir,
            overwrite=overwrite,
            zip_inputs=zip_inputs,
        )
        _indir, _outdir, _tmpdir = set_workdir(workdir=directory)

    def validate(self) -> bool:
        """
        Validate the input set.

        Returns
        -------
        bool
            True if there is at least one file to merge, and all of them exist
            and have the expected input file name, False otherwise.
        """
        if not self.input_files:
            return False
        return all(
            os.path.isfile(out_filepath) and in_file.startswith(self.in_file_prefix)
            for out_filepath, in_file in self.input_files
        )

    @property
    def merge_input(self) -> str:
        """Get the stdin input string of the merge utility."""
        return self[self.input_file_name]

    def deepcopy(self) -> MergeInputSet:
        """Create a deep copy of the input set."""
        return copy.deepcopy(self)


@dataclass
class MergeInputGenerator(AbinitMixinInputGenerator):
    """
    Generator for the input sets of ABINIT merge utilities.

    The generated stdin input has the format expected by mrgddb/mrgdv::

        <absolute path of the merged output file>
        <description>              (only if ``description`` is not None)
        <number of files to merge>
        <path of file 1>
        ...

    Subclasses define the class attributes below, together with the dataclass
    fields ``calc_type`` and ``prev_outputs_deps``.

    Attributes
    ----------
    input_set_class : type[MergeInputSet]
        The input set class to generate.
    output_name : str
        Name of the merged output file in the outdata directory
        (e.g. "out_DDB").
    description : str or None
        Description line, formatted with ``date``. None if the utility does
        not read a description line (e.g. mrgdv).
    """

    # Narrowed from AbinitMixinInputGenerator: always a tuple for merge utilities
    prev_outputs_deps: tuple

    input_set_class: ClassVar[type[MergeInputSet]]
    output_name: ClassVar[str]
    description: ClassVar[str | None] = None

    def get_input_set(
        self,
        prev_outputs: str | tuple | list | Path | None = None,
        workdir: str | Path | None = ".",
    ) -> MergeInputSet:
        """
        Generate the input set, collecting the files to merge from prev_outputs.

        Parameters
        ----------
        prev_outputs : str or Path or list or tuple or None
            Directory or list of directories of the calculations whose
            outputs are merged. Required.
        workdir : str or Path or None
            Working directory for the calculation. Default is ".".

        Returns
        -------
        MergeInputSet
            The input set, ready to be written and executed.

        Raises
        ------
        RuntimeError
            If no previous outputs are provided, or if previous outputs are
            not allowed for this generator.
        """
        prev_outputs = self.check_format_prev_dirs(prev_outputs)
        if not prev_outputs:
            raise RuntimeError(
                f"No previous_outputs. Required for {type(self).__name__}."
            )
        if not self.prev_outputs_deps:
            raise RuntimeError(
                f"Previous outputs not allowed for {type(self).__name__}."
            )

        _irdvars, files = self.resolve_deps(prev_outputs, self.prev_outputs_deps)
        return self.input_set_class(
            merge_input=self.get_merge_input(files, workdir=workdir),
            input_files=files,
        )

    def get_merge_input(
        self, files: list[tuple[str, str]], workdir: str | Path | None = "."
    ) -> str:
        """
        Generate the stdin input string of the merge utility.

        Parameters
        ----------
        files : list[tuple[str, str]]
            List of (output_filepath, input_filename) tuples for the files to
            merge, as returned by ``resolve_deps``.
        workdir : str or Path or None
            Working directory for the calculation. Default is ".".

        Returns
        -------
        str
            The stdin input string.
        """
        lines = [os.path.join(os.path.abspath(workdir), OUTDIR_NAME, self.output_name)]
        if self.description is not None:
            lines.append(self.description.format(date=time.asctime()))
        lines.append(str(len(files)))
        lines.extend(str(file_path) for file_path, _ in files)
        return "\n".join(lines)
