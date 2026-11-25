"""Module defining the MRGDDB input set and generator."""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from abipy.abio.input_tags import DDE, DTE, PH_Q_PERT

from atomate2.abinit.sets.merge import MergeInputGenerator, MergeInputSet
from atomate2.abinit.utils.common import MRGDDB_INPUT_FILE_NAME

__all__ = ["MrgddbInputGenerator", "MrgddbInputSet"]


class MrgddbInputSet(MergeInputSet):
    """
    Input set for MRGDDB, which merges derivative database (DDB) files.

    See :obj:`.MergeInputSet`.
    """

    input_file_name: ClassVar[str] = MRGDDB_INPUT_FILE_NAME
    in_file_prefix: ClassVar[str] = "in_DDB"


@dataclass
class MrgddbInputGenerator(MergeInputGenerator):
    """
    Generator of MRGDDB input sets.

    MRGDDB merges the DDB files of several perturbation calculations (DDE, DTE,
    phonons). Unlike mrgdv, it reads a description line after the output file
    name. See :obj:`.MergeInputGenerator`.

    Attributes
    ----------
    calc_type : str
        A short description of the calculation type. Default is "mrgddb".
    prev_outputs_deps : tuple
        Defines the files that need to be linked from previous calculations,
        as "run levels:extensions" strings (see
        :obj:`.AbinitMixinInputGenerator`).
        Default is (f"{DDE}:DDB", f"{DTE}:DDB", f"{PH_Q_PERT}:DDB").
    """

    calc_type: str = "mrgddb"
    prev_outputs_deps: tuple = (f"{DDE}:DDB", f"{DTE}:DDB", f"{PH_Q_PERT}:DDB")

    input_set_class: ClassVar[type[MergeInputSet]] = MrgddbInputSet
    output_name: ClassVar[str] = "out_DDB"
    description: ClassVar[str | None] = "DDBs merged on {date}"
