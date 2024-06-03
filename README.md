# SlurmExec
Lightweight Python library to easily deploy and execute Slurm tasks. Fast and easy; no dependencies needed.

## Features
- Define a job function in Python and call `slurm_exec` in the python file `__main__`
- Dynamically-created slurm scripts avoid the headache of writing and manually keeping track of messy slurm job files
- Control function arguments from command line

## Install
Option 1 (preferred): Directly:
```
pip install git+https://github.com/chaseking/slurmexec.git
```
**Note:** If you use this method you will need to run `pip install --upgrade git+https://github.com/chaseking/slurmexec.git` to install updates made to this package. Eventually I will make this available on PyPI.

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
    # Conditional imports to avoid memory
    # crashing (OOM) Slurm login node
    import biglibrary

@slurm_job
def hello(message: str = "World"):
    print(f"Hello {message}!")
    
    biglibrary.expensive_function()
    
    print(f"Finished slurm job {get_slurm_id()}")

if __name__ == "__main__":
    slurm_exec(
        func = hello,
        slurm_args = {
            "--gres": "gpu:1",
        }
        pre_run_commands = [
            "conda activate myenv"
        ]
    )
```

```bash
# Executed on a slurm login node
python myfile.py --message 'big beautiful world'
```