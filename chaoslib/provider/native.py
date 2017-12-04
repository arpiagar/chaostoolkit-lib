# -*- coding: utf-8 -*-
import importlib
import inspect
import os
import os.path
import traceback
from typing import Any

from logzero import logger

from chaoslib.exceptions import FailedActivity, InvalidActivity
from chaoslib.types import Activity, Secrets


__all__ = ["run_python_activity", "validate_python_activity"]


def run_python_activity(activity: Activity, secrets: Secrets) -> Any:
    """
    Run a Python activity.

    A python activity is a function from any importable module. The result
    of that function is returned as the activity's output.

    This should be considered as a private function.
    """
    provider = activity["provider"]
    mod_path = provider["module"]
    func_name = provider["func"]
    mod = importlib.import_module(mod_path)
    func = getattr(mod, func_name)
    arguments = provider.get("arguments", {}).copy()

    if "secrets" in provider:
        arguments["secrets"] = secrets.get(provider["secrets"]).copy()

    try:
        return func(**arguments)
    except Exception as x:
        raise FailedActivity(
            traceback.format_exception_only(
                type(x), x)[0].strip()).with_traceback(
                    sys.exc_info()[2])


def validate_python_activity(activity: Activity):
    """
    Validate a Python activity.

    A Python activity requires:

    * a `"module"` key which is an absolute Python dotted path for a Python
      module this process can import
    * a `func"` key which is the name of a function in that module

    The `"arguments"` activity key must match the function's signature.

    In all failing cases, raises :exc:`InvalidActivity`.

    This should be considered as a private function.
    """
    name = activity["name"]
    provider = activity["provider"]
    mod_name = provider.get("module")
    if not mod_name:
        raise InvalidActivity("a Python activity must have a module path")

    func = provider.get("func")
    if not func:
        raise InvalidActivity("a Python activity must have a function name")

    try:
        mod = importlib.import_module(mod_name)
    except ImportError:
        raise InvalidActivity("could not find Python module '{mod}' "
                              "in activity '{name}'".format(
                                  mod=mod_name, name=name))

    found_func = False
    arguments = provider.get("arguments", {})
    needs_secrets = "secrets" in activity
    candidates = set(
        inspect.getmembers(mod, inspect.isfunction)).union(
            inspect.getmembers(mod, inspect.isbuiltin))
    for (name, cb) in candidates:
        if name == func:
            found_func = True

            # let's try to bind the activity's arguments with the function
            # signature see if they match
            sig = inspect.signature(cb)
            try:
                # secrets are provided through a `secrets` parameter to an
                # activity that needs them. However, they are declared out of
                # band of the `arguments` mapping. Here, we simply ensure the
                # signature of the activity is valid by injecting a fake
                # `secrets` argument into the mapping.
                args = arguments.copy()
                if needs_secrets:
                    args["secrets"] = None

                sig.bind(**args)
            except TypeError as x:
                # I dislike this sort of lookup but not sure we can
                # differentiate them otherwise
                msg = str(x)
                if "missing" in msg:
                    arg = msg.rsplit(":", 1)[1].strip()
                    raise InvalidActivity(
                        "required argument {arg} is missing from "
                        "activity '{name}'".format(arg=arg, name=name))
                elif "unexpected" in msg:
                    arg = msg.rsplit(" ", 1)[1].strip()
                    raise InvalidActivity(
                        "argument {arg} is not part of the "
                        "function signature in activity '{name}'".format(
                            arg=arg, name=name))
                else:
                    # another error? let's fail fast
                    raise
            break

    if not found_func:
        raise InvalidActivity(
            "'{mod}' does not expose '{func}' in activity '{name}'".format(
                mod=mod_name, func=func, name=name))
