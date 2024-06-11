"""Tests whether boolean arguments are correctly parsed from the command line."""

from slurmexec import *

set_slurm_debug()

@slurm_job
def test_bool_arg(num: int = 123, myflag: bool = False, myotherflag: bool = True):
    print(f"{type(myflag) = },   {myflag = }")
    print(f"{type(myotherflag) = },   {myotherflag = }")

if __name__ == "__main__":
    slurm_exec(test_bool_arg)
