import os

import abipy.flowtk.psrepos
import pytest
from abipy.abio.inputs import AbinitInput

from atomate2.abinit.sets.base import AbinitInputSet
from atomate2.abinit.sets.core import StaticSetGenerator


def test_init_static_generator():
    StaticSetGenerator()


def test_static_generator_get_abinit_input(si_structure, abinit_test_dir):
    ssg = StaticSetGenerator()
    si_pseudo = os.path.join(abipy.flowtk.psrepos.REPOS_ROOT, "14si.fhi")
    abinit_input = ssg.get_abinit_input(structure=si_structure, pseudos=si_pseudo)
    assert isinstance(abinit_input, AbinitInput)
    with pytest.raises(RuntimeError, match=r"Structure is mandatory.*"):
        ssg.get_abinit_input()

    with pytest.raises(
        RuntimeError,
        match=r"Previous outputs not allowed.*",
    ):
        ssg.get_abinit_input(structure=si_structure, prev_outputs="prev_fake_dir")


def test_static_generator_get_input_set(si_structure):
    ssg = StaticSetGenerator()
    input_set = ssg.get_input_set(structure=si_structure)
    assert isinstance(input_set, AbinitInputSet)


# def test_static_generator_restart(si_structure):
#     ssg1 = StaticSetGenerator(ecut=8.5, nband=13, smearing=None)
#     ssg2 = StaticSetGenerator(nband=8, smearing=None)
#     ssg3 = StaticSetGenerator()
#
#     with ScratchDir(".") as tmpdir:
#         input_set1 = ssg1.get_input_set(
#             structure=si_structure, smearing="marzari5:0.5 eV"
#         )
#         assert isinstance(input_set1, AbinitInputSet)
#         assert input_set1.abinit_input["occopt"] == 5
#         input_set1.write_input("first_run")
#         dirlist = os.listdir("first_run")
#         assert len(dirlist) == 6
#         assert "abinit_input_set_generator.json" in dirlist
#         assert "abinit_input.json" in dirlist
#         with open("first_run/run.abi") as file:
#             runabi1_str = file.read()
#         assert "ecut 8.5" in runabi1_str
#         assert "nband 13" in runabi1_str
#         assert "occopt 5" in runabi1_str
#         matched_tsmear_lines = [
#             line for line in runabi1_str.split("\n") if "tsmear" in line
#         ]
#         assert len(matched_tsmear_lines) == 1
#         _, tsmear, tsmear_unit = matched_tsmear_lines[0].split()
#         assert float(tsmear) == pytest.approx(0.0183746610878275)
#         assert tsmear_unit == "Ha"
#         outdenpath = os.path.join(
#             tmpdir, "first_run", OUTDIR_NAME, f"{OUTDATAFILE_PREFIX}_DEN"
#         )
#         Path(outdenpath).touch()
#
#         input_set2 = ssg2.get_input_set(
#             structure=si_structure,
#             charge=1.0,
#             restart_from=os.path.join(tmpdir, "first_run"),
#         )
#         input_set2.write_input("second_run")
#         indenpath = os.path.join(
#             tmpdir, "second_run", INDIR_NAME, f"{INDATAFILE_PREFIX}_DEN"
#         )
#         assert os.path.islink(indenpath)
#         assert os.readlink(indenpath) == outdenpath
#         with open("second_run/run.abi") as file:
#             runabi2_str = file.read()
#         assert "ecut 8.5" in runabi2_str
#         assert "nband 8" in runabi2_str
#         assert "occopt" not in runabi2_str
#         assert "tsmear" not in runabi2_str
#         assert "charge 1.0" in runabi2_str
#         assert "irdden 1" in runabi2_str
#
#         outwfkpath = os.path.join(
#             tmpdir, "first_run", OUTDIR_NAME, f"{OUTDATAFILE_PREFIX}_WFK"
#         )
#         Path(outwfkpath).touch()
#         input_set3 = ssg3.get_input_set(
#             structure=si_structure, restart_from=os.path.join(tmpdir, "first_run")
#         )
#         input_set3.write_input("second_run_bis")
#         indenpath = os.path.join(
#             tmpdir, "second_run_bis", INDIR_NAME, f"{INDATAFILE_PREFIX}_DEN"
#         )
#         inwfkpath = os.path.join(
#             tmpdir, "second_run_bis", INDIR_NAME, f"{INDATAFILE_PREFIX}_WFK"
#         )
#         assert os.path.islink(inwfkpath)
#         assert os.readlink(inwfkpath) == outwfkpath
#         with open("second_run_bis/run.abi") as file:
#             runabi3_str = file.read()
#         assert "ecut 8.5" in runabi3_str
#         assert "nband 13" in runabi3_str
#         assert "occopt 5" in runabi3_str
#         matched_tsmear_lines = [
#             line for line in runabi3_str.split("\n") if "tsmear" in line
#         ]
#         assert len(matched_tsmear_lines) == 1
#         _, tsmear, tsmear_unit = matched_tsmear_lines[0].split()
#         assert float(tsmear) == pytest.approx(0.0183746610878275)
#         assert tsmear_unit == "Ha"
#         outdenpath = os.path.join(
#             tmpdir, "first_run", OUTDIR_NAME, f"{OUTDATAFILE_PREFIX}_DEN"
#         )


def _make_prev_dir(src, dest, out_files):
    """Copy abinit_input.json (and run.abo) of a test calc and touch outdata files."""
    import gzip
    import shutil

    (dest / "outdata").mkdir(parents=True)
    for fname, subdir in (("abinit_input.json", "inputs"), ("run.abo", "outputs")):
        gz_file = src / subdir / f"{fname}.gz"
        if gz_file.exists():
            with gzip.open(gz_file, "rb") as fin, open(dest / fname, "wb") as fout:
                shutil.copyfileobj(fin, fout)
    for out_file in out_files:
        (dest / "outdata" / out_file).touch()
    return dest


def test_wfq_generator_restart(abinit_test_dir, tmp_path):
    from atomate2.abinit.sets.core import NscfWfqSetGenerator

    ref_dir = abinit_test_dir / "flows/dfpt_core/PhononMaker/Si_phonon_bandstructure"
    scf_dir = _make_prev_dir(
        ref_dir / "Scf_calculation/1", tmp_path / "scf", ["out_WFK", "out_DEN"]
    )
    wfq_dir = _make_prev_dir(
        ref_dir / "WFQ_nscf_Calculation_-_1/1", tmp_path / "wfq", ["out_WFQ"]
    )
    gen = NscfWfqSetGenerator(factory_kwargs={"qpt": [0.25, 0.0, 0.0]})

    def linked(input_set):
        return {dest: src for src, dest in input_set.input_files}

    # First run: SCF WFK as starting wavefunctions, SCF DEN
    first = gen.get_input_set(prev_outputs=[str(scf_dir)])
    assert linked(first) == {
        "in_WFK": str(scf_dir / "outdata/out_WFK"),
        "in_DEN": str(scf_dir / "outdata/out_DEN"),
    }

    # Restart: the previous out_WFQ replaces the SCF WFK as in_WFK
    restart = gen.get_input_set(
        prev_outputs=[str(scf_dir)], restart_from=[str(wfq_dir)]
    )
    assert linked(restart) == {
        "in_WFK": str(wfq_dir / "outdata/out_WFQ"),
        "in_DEN": str(scf_dir / "outdata/out_DEN"),
    }
    assert restart.abinit_input["irdwfk"] == 1
    assert "irdwfq" not in restart.abinit_input
    assert restart.abinit_input["nqpt"] == 1

    # Restart without prev_outputs (no SCF density) fails explicitly
    with pytest.raises(ValueError, match="requires prev_outputs"):
        gen.get_input_set(restart_from=[str(wfq_dir)])

    # Restart without a WFQ file fails explicitly
    (wfq_dir / "outdata/out_WFQ").unlink()
    with pytest.raises(Exception, match="Cannot find WFQ file"):
        gen.get_input_set(prev_outputs=[str(scf_dir)], restart_from=[str(wfq_dir)])
