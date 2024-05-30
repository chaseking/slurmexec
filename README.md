# SlurmExec
Lightweight Python library to easily deploy and execute Slurm tasks. Fast and easy; no dependencies needed.

## Install
Option 1 (preferred): Directly:
```
pip install git+https://github.com/chaseking/slurmexec.git
```

Option 2: Clone and install
```
git clone git@github.com:chaseking/slurmexec.git
cd slurmexec
pip install -e .
```

## Example
```python
from slurmexec import *

# set_slurm_debug()  # to run locally

if is_this_a_slurm_job():
    import biglibrary

@slurm_job
def hello(message: str = "World"):
    print(f"Hello {message}!")
    
    biglibrary.expensive_function()
    
    print(f"Finished slurm job {get_slurm_id()}")

if __name__ == "__main__":
    slurm_exec(
        func = hello,
        pre_run_commands = [
            "conda activate myenv"
        ]
    )
```

```bash
# Executed on a slurm login node
python myfile.py --message 'big beautiful world'
```