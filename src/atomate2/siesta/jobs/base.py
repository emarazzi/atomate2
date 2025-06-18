"""Defines the base SIESTA Maker."""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

from jobflow import Maker, Response, job
from monty.serialization import dumpfn

from atomate2.siesta.files import (
    cleanup_siesta_outputs,
    copy_siesta_outputs,
    write_siesta_input_set,
)
from atomate2.siesta.run import run_siesta
from atomate2.siesta.sets.base import SiestaInputGenerator  # TODO

if TYPE_CHECKING:
    from pymatgen.core import Molecule, Structure

logger = logging.getLogger(__name__)

# Input files.
# Exclude those that are also outputs
_INPUT_FILES = [
    "siesta.fdf",  # "geometry.in",
    # "parameters.fdf", #"control.in",
]

# Output files.
_OUTPUT_FILES = ["siesta.out", "*.DM"]

# Files to zip: inputs, outputs and additionally generated files
_FILES_TO_ZIP = _INPUT_FILES + _OUTPUT_FILES


@dataclass
class BaseSiestaMaker(Maker):
    """
    Base Siesta job maker.

    Parameters
    ----------
    name : str
        The job name.
    input_set_generator : .SiestaInputGenerator
        A generator used to make the input set.
    write_input_set_kwargs : dict[str, Any]
        Keyword arguments that will get passed to :obj:`.write_siesta_input_set`.
    copy_siesta_kwargs : dict[str, Any]
        Keyword arguments that will get passed to :obj:`.copy_siesta_outputs`.
    run_siesta_kwargs : dict[str, Any]
        Keyword arguments that will get passed to :obj:`.run_aims`.
    task_document_kwargs : dict[str, Any]
        Keyword arguments that will get passed to :obj:`.TaskDoc.from_directory`.
    stop_children_kwargs : dict[str, Any]
        Keyword arguments that will get passed to :obj:`.should_stop_children`.
    write_additional_data : dict[str, Any]
        Additional data to write to the current directory. Given as a dict of
        {filename: data}. Note that if using FireWorks, dictionary keys cannot contain
        the "." character which is typically used to denote file extensions. To avoid
        this, use the ":" character, which will automatically be converted to ".". E.g.
        ``{"my_file:txt": "contents of the file"}``.
    store_output_data: bool
        Whether the job output (TaskDoc) should be stored in the JobStore through
        the response.
    """

    name: str = "base"
    input_set_generator: SiestaInputGenerator = field(
        default_factory=SiestaInputGenerator
    )
    # input_set_generator: SiestaInputGenerator = field(default_factory=SiestaInputGenerator(Structure))
    # input_set_generator: SiestaInputGenerator | None = None  # Allow None
    write_input_set_kwargs: dict[str, Any] = field(default_factory=dict)
    copy_siesta_kwargs: dict[str, Any] = field(default_factory=dict)
    run_siesta_kwargs: dict[str, Any] = field(default_factory=dict)
    task_document_kwargs: dict[str, Any] = field(default_factory=dict)
    stop_children_kwargs: dict[str, Any] = field(default_factory=dict)
    write_additional_data: dict[str, Any] = field(default_factory=dict)
    store_output_data: bool = True

    # def __post_init__(self):
    #    if self.input_set_generator is None:
    #        raise ValueError("SiestaInputGenerator requires a 'structure' argument to be provided separately.")

    @job
    def make(
        self,
        structure: Structure | Molecule,
        prev_dir: str | Path | None = None,
    ) -> Response:
        """Run an SIESTA calculation.

        Parameters
        ----------
        structure : Structure or Molecule
            A pymatgen Structure object to create the calculation for.
        prev_dir : str or Path or None
            A previous SIESTA calculation directory to copy output files from.
        """
        # if self.input_set_generator is None:
        #    self.input_set_generator = SiestaInputGenerator(structure)  # Initialize here
        #    print(f"Initialized SiestaInputGenerator: {self.input_set_generator}")

        # copy previous inputs if needed (governed by self.copy_aims_kwargs)
        if prev_dir is not None:
            copy_siesta_outputs(prev_dir, **self.copy_siesta_kwargs)

        # write SIESTA input files
        self.write_input_set_kwargs["prev_dir"] = prev_dir

        print("WRITING SIESTA INPUT SET")
        write_siesta_input_set(
            structure, self.input_set_generator, **self.write_input_set_kwargs
        )
        # self.input_set_generator.write()
        # write any additional data
        # usefull for LUA stuff or images maybe
        for filename, data in self.write_additional_data.items():
            dumpfn(data, filename.replace(":", "."))

        # run FHI-aims
        print("RUNNING SIESTA")
        run_siesta(**self.run_siesta_kwargs)

        # parse FHI-aims outputs
        # print("READING SIESTA TASK DOCS")
        # task_doc = SiestaTaskDoc.from_directory(Path.cwd(), **self.task_document_kwargs)
        # task_doc.task_label = self.name

        # print("decide whether child jobs should proceed".upper())
        # decide whether child jobs should proceed
        # stop_children = should_stop_children(task_doc, **self.stop_children_kwargs)

        # cleanup files to save disk space
        cleanup_siesta_outputs(directory=Path.cwd())

        # gzip folder
        # gzip_output_folder(
        #    directory=Path.cwd(),
        #    setting=SETTINGS.SIESTA_ZIP_FILES,
        #    files_list=_FILES_TO_ZIP,
        # )

        return Response(
            # stop_children=stop_children,
            # output=task_doc if self.store_output_data else None,
            output=os.getcwd()
        )
