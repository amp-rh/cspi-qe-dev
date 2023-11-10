import sys
from cspi_qe_dev.ref_sandbox.core import RefSandbox
from pathlib import Path


def get_ref_sandbox_from_path(p: Path | str):
    p = Path(p)
    p = p.parent if p.is_file() else p
    return RefSandbox(ref_dir=p)


def build_and_run_interactively_from_path(p: Path | str, shell=True):
    sb = RefSandbox(p)
    sb.build()
    sb.run(shell)


def ref_sandbox():
    p = Path(".")
    shell=False if "run" in sys.argv else True
    build_and_run_interactively_from_path(p, shell=shell)
