import pytest

from atomate2.abinit.flows.dfpt_base import DfptFlowMaker
from atomate2.abinit.flows.dfpt_core import PhononMaker


def test_dfpt_flow_requires_a_perturbation_maker():
    with pytest.raises(ValueError, match="At least one of dde_maker, phonon_maker"):
        DfptFlowMaker()


def test_phonon_maker_runs_base_validation():
    PhononMaker()  # defaults are valid
    PhononMaker(with_dde=False)  # DDK and DDE disabled together
    with pytest.raises(ValueError, match="DDK calculations are required"):
        PhononMaker(ddk_maker=None)
    with pytest.raises(ValueError, match="one of ngqpt, qpt_list"):
        PhononMaker(ngqpt=[2, 2, 2], qpt_list=[[0, 0, 0]])
