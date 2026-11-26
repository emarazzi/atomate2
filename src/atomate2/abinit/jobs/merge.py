"""Shared job maker for the ABINIT merge utilities (mrgddb, mrgdv, ...).

The merge utilities only differ by their input set generator, runner and task
document. :obj:`.MergeMaker` implements the common job logic, so that adding
another utility (e.g. mrggkk or mrgscr, not used in atomate2 yet) only
requires a small subclass, as done in :obj:`.MrgddbMaker` and
:obj:`.MrgdvMaker`.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

import numpy as np
from jobflow import Maker, Response

from atomate2.abinit.jobs.base import setup_job
from atomate2.abinit.schemas.outfiles import AbinitStoredFile

if TYPE_CHECKING:
    from collections.abc import Callable

    from atomate2.abinit.sets.merge import MergeInputGenerator
    from atomate2.abinit.utils.history import JobHistory

logger = logging.getLogger(__name__)

__all__ = ["MERGE_DATA_OBJECTS", "MergeMaker"]

# Large objects (merged files) stored in the atomate2 data store
MERGE_DATA_OBJECTS = [AbinitStoredFile]


@dataclass
class MergeMaker(Maker):
    """
    Base maker for jobs running an ABINIT merge utility.

    Subclasses must define the dataclass fields ``name`` (the job name) and
    ``input_set_generator`` (a :obj:`.MergeInputGenerator`), and a ``make``
    method, decorated with the job decorator of the utility, that calls
    :meth:`_make` with the utility's input writer, runner and task document
    class. The fields are not declared here to keep the subclasses free to set
    their defaults.
    """

    if TYPE_CHECKING:
        # For type checkers only: defined as dataclass fields by the subclasses
        name: str
        input_set_generator: MergeInputGenerator

    @property
    def calc_type(self) -> str:
        """Get the type of calculation for this maker."""
        return self.input_set_generator.calc_type

    def _make(
        self,
        prev_outputs: list[str] | list[list[str]],
        history: JobHistory | None,
        write_input_set: Callable,
        run: Callable,
        task_doc_cls: type[Any],
    ) -> Response:
        """
        Write the input, run the merge utility and parse its outputs.

        Parameters
        ----------
        prev_outputs : list[str] or list[list[str]]
            Directories of the calculations whose outputs are merged. Can be a
            nested list, which is flattened. Required, and must contain at
            least one directory.
        history : JobHistory or None
            A JobHistory object containing the history of previous jobs.
        write_input_set : Callable
            Function writing the input set (e.g. write_mrgddb_input_set).
        run : Callable
            Function running the utility (e.g. run_mrgddb).
        task_doc_cls : type
            Task document class with a ``from_directory`` method.

        Returns
        -------
        Response
            A jobflow Response with the task document as output.

        Raises
        ------
        ValueError
            If prev_outputs is None or empty.
        """
        if not prev_outputs:
            raise ValueError(
                f"prev_outputs is required: no files to merge for {self.calc_type}."
            )
        # Flatten nested list of previous output directories
        flat_prev_outputs: list[str] = [str(p) for p in np.hstack(prev_outputs)]

        config = setup_job(
            structure=None,
            prev_outputs=flat_prev_outputs,
            restart_from=None,
            history=history,
            wall_time=None,
        )
        write_input_set(
            input_set_generator=self.input_set_generator,
            prev_outputs=flat_prev_outputs,
            directory=config.workdir,
        )
        run(start_time=config.start_time)

        task_doc = task_doc_cls.from_directory(Path.cwd())
        task_doc.task_label = self.name
        return Response(output=task_doc)
