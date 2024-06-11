"""Tests whether boolean arguments are correctly parsed from the command line."""

from slurmexec import *

set_slurm_debug()

@slurm_job
def test_bool_arg(myflag: bool = False):
    print(f"{type(myflag) = },   {myflag = }")

if __name__ == "__main__":
    slurm_exec(test_bool_arg)
