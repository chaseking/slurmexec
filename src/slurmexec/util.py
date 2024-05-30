import os
import argparse
import inspect

def get_env_var(*varnames):
    """
    Get one or more environment variables.

    Raises:
        ValueError: If no variable names are specified

    Returns:
        any or list: Returns a single variable if only one name was specfied, else a tuple.
    """
    if len(varnames) == 0:
        raise ValueError("At least one environment variable name must be provided.")
    v = tuple(os.environ.get(name) for name in varnames)
    return v[0] if len(varnames) == 1 else v

def load_func_argparser(func, ignore=None):
    """
    Instantiates an ArgumentParser with arguments for each argument in func, except those in ignore.

    Args:
        func (callable): Function with which to parse args.
        ignore (iterable[str], optional): Function parameter names to ignore. Defaults to None.

    Returns:
        argparse.ArgumentParser: Arg parser
    """
    parser = argparse.ArgumentParser()
    signature = inspect.signature(func)
    _get_or_none = lambda x: None if x is inspect._empty else x

    for name, param in signature.parameters.items():
        if ignore is not None and name in ignore:
            continue

        dtype = _get_or_none(param.annotation)
        default = _get_or_none(param.default)
        parser.add_argument(f"--{name}", type=dtype, default=default, help=(f"(default: {default})" if default is not None else None))
    
    return parser