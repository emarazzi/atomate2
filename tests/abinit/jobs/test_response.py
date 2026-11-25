from unittest.mock import MagicMock

import pytest

from atomate2.abinit.jobs.response import DdeMaker, generate_perts


@pytest.mark.parametrize("ddk_output", [None, []])
def test_generate_perts_dde_requires_ddk(ddk_output):
    with pytest.raises(ValueError, match="DDK output is required to run DDE"):
        generate_perts.original(
            gsinput=MagicMock(),
            scf_output="scf_dir",
            ddk_output=ddk_output,
            dde_maker=DdeMaker(),
        )


@pytest.mark.parametrize("maker_name", ["MrgddbMaker", "MrgdvMaker"])
@pytest.mark.parametrize("prev_outputs", [None, []])
def test_merge_makers_require_prev_outputs(maker_name, prev_outputs):
    from atomate2.abinit.jobs.mrgddb import MrgddbMaker
    from atomate2.abinit.jobs.mrgdv import MrgdvMaker

    maker = {"MrgddbMaker": MrgddbMaker, "MrgdvMaker": MrgdvMaker}[maker_name]()
    with pytest.raises(ValueError, match="prev_outputs is required"):
        maker.make.original(maker, prev_outputs=prev_outputs)
