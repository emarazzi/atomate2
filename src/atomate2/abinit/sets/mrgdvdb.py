"""Module defining the MRGDV input set and generator."""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from abipy.abio.input_tags import DDE, DTE, PH_Q_PERT

from atomate2.abinit.sets.merge import MergeInputGenerator, MergeInputSet
from atomate2.abinit.utils.common import MRGDV_INPUT_FILE_NAME

__all__ = ["MrgdvInputGenerator", "MrgdvInputSet"]


class MrgdvInputSet(MergeInputSet):
    """
    Input set for MRGDV, which merges first-order potential (POT) files.

    See :obj:`.MergeInputSet`.
    """

    input_file_name: ClassVar[str] = MRGDV_INPUT_FILE_NAME
    in_file_prefix: ClassVar[str] = "in_POT"


@dataclass
class MrgdvInputGenerator(MergeInputGenerator):
    """
    Generator of MRGDV input sets.

    MRGDV merges the first-order potential (POT) files of several perturbation
    calculations (DDE, DTE, phonons) into a DVDB file. Unlike mrgddb, it does
    not read a description line: its stdin is the output file name, the number
    of files and the file names. See :obj:`.MergeInputGenerator`.

    Attributes
    ----------
    calc_type : str
        A short description of the calculation type. Default is "mrgdv".
    prev_outputs_deps : tuple
        Defines the files that need to be linked from previous calculations,
        as "run levels:extensions" strings (see
        :obj:`.AbinitMixinInputGenerator`).
        Default is (f"{DDE}:POT", f"{DTE}:POT", f"{PH_Q_PERT}:POT").
    """

    calc_type: str = "mrgdv"
    prev_outputs_deps: tuple = (f"{DDE}:POT", f"{DTE}:POT", f"{PH_Q_PERT}:POT")

    input_set_class: ClassVar[type[MergeInputSet]] = MrgdvInputSet
    output_name: ClassVar[str] = "out_dvdb"
    description: ClassVar[str | None] = None
