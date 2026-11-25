"""MRGDV jobs merging the POT files of ABINIT DFPT calculations."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from jobflow import job

from atomate2.abinit.files import write_mrgdv_input_set
from atomate2.abinit.jobs.merge import MERGE_DATA_OBJECTS, MergeMaker
from atomate2.abinit.run import run_mrgdv
from atomate2.abinit.schemas.mrgdvdb import MrgdvdbTaskDoc
from atomate2.abinit.sets.mrgdvdb import MrgdvInputGenerator

if TYPE_CHECKING:
    from collections.abc import Callable

    import jobflow

    from atomate2.abinit.utils.history import JobHistory

logger = logging.getLogger(__name__)

__all__ = ["MrgdvMaker", "mrgdv_job"]


def mrgdv_job(method: Callable) -> job:
    """
    Decorate the ``make`` method of MRGDV job makers.

    This is a thin wrapper around :obj:`~jobflow.core.job.job` that stores the
    merged files in the atomate2 data store and sets the output schema to
    :obj:`.MrgdvdbTaskDoc`.

    Parameters
    ----------
    method : callable
        A MrgdvMaker.make method. This should not be specified directly and
        is implied by the decorator.

    Returns
    -------
    callable
        A decorated version of the make function that will generate MRGDV jobs.
    """
    return job(method, data=MERGE_DATA_OBJECTS, output_schema=MrgdvdbTaskDoc)


@dataclass
class MrgdvMaker(MergeMaker):
    """
    Maker to create jobs merging POT files with MRGDV.

    MRGDV merges the first-order potential (POT) files of several DFPT
    calculations into a single DVDB file.
    See :obj:`.MergeMaker`.

    Parameters
    ----------
    name : str
        The job name. Default is "Merge DVDB".
    input_set_generator : MrgdvInputGenerator
        Generator for MRGDV input files. Defaults to MrgdvInputGenerator.
    """

    name: str = "Merge DVDB"
    input_set_generator: MrgdvInputGenerator = field(
        default_factory=MrgdvInputGenerator
    )

    @mrgdv_job
    def make(
        self,
        prev_outputs: list[str] | list[list[str]],
        history: JobHistory | None = None,
    ) -> jobflow.Response:
        """
        Create a MRGDV job.

        Parameters
        ----------
        prev_outputs : list[str] or list[list[str]]
            Directories of the calculations whose first-order potential (POT) files
            are merged. Can be a nested list, which is flattened. Required, and
            must contain at least one directory.
        history : JobHistory or None
            A JobHistory object containing the history of previous jobs.

        Returns
        -------
        Response
            A jobflow Response containing a MrgdvdbTaskDoc.
        """
        return self._make(
            prev_outputs,
            history,
            write_input_set=write_mrgdv_input_set,
            run=run_mrgdv,
            task_doc_cls=MrgdvdbTaskDoc,
        )
