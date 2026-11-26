"""MRGDDB jobs merging the DDB files of ABINIT DFPT calculations."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from jobflow import job

from atomate2.abinit.files import write_mrgddb_input_set
from atomate2.abinit.jobs.merge import MERGE_DATA_OBJECTS, MergeMaker
from atomate2.abinit.run import run_mrgddb
from atomate2.abinit.schemas.mrgddb import MrgddbTaskDoc
from atomate2.abinit.sets.mrgddb import MrgddbInputGenerator

if TYPE_CHECKING:
    from collections.abc import Callable

    import jobflow

    from atomate2.abinit.utils.history import JobHistory

logger = logging.getLogger(__name__)

__all__ = ["MrgddbMaker", "mrgddb_job"]


def mrgddb_job(method: Callable) -> job:
    """
    Decorate the ``make`` method of MRGDDB job makers.

    This is a thin wrapper around :obj:`~jobflow.core.job.job` that stores the
    merged files in the atomate2 data store and sets the output schema to
    :obj:`.MrgddbTaskDoc`.

    Parameters
    ----------
    method : callable
        A MrgddbMaker.make method. This should not be specified directly and
        is implied by the decorator.

    Returns
    -------
    callable
        A decorated version of the make function that will generate MRGDDB jobs.
    """
    return job(method, data=MERGE_DATA_OBJECTS, output_schema=MrgddbTaskDoc)


@dataclass
class MrgddbMaker(MergeMaker):
    """
    Maker to create jobs merging DDB files with MRGDDB.

    MRGDDB (MeRGe Derivative DataBase) merges the DDB files of several DFPT
    calculations into a single DDB file, typically before running ANADDB.
    See :obj:`.MergeMaker`.

    Parameters
    ----------
    name : str
        The job name. Default is "Merge DDB".
    input_set_generator : MrgddbInputGenerator
        Generator for MRGDDB input files. Defaults to MrgddbInputGenerator.
    """

    name: str = "Merge DDB"
    input_set_generator: MrgddbInputGenerator = field(
        default_factory=MrgddbInputGenerator
    )

    @mrgddb_job
    def make(
        self,
        prev_outputs: list[str] | list[list[str]],
        history: JobHistory | None = None,
    ) -> jobflow.Response:
        """
        Create a MRGDDB job.

        Parameters
        ----------
        prev_outputs : list[str] or list[list[str]]
            Directories of the calculations whose derivative database (DDB) files
            are merged. Can be a nested list, which is flattened. Required, and
            must contain at least one directory.
        history : JobHistory or None
            A JobHistory object containing the history of previous jobs.

        Returns
        -------
        Response
            A jobflow Response containing a MrgddbTaskDoc.
        """
        return self._make(
            prev_outputs,
            history,
            write_input_set=write_mrgddb_input_set,
            run=run_mrgddb,
            task_doc_cls=MrgddbTaskDoc,
        )
