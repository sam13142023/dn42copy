"""rpsl a tool for managing RPSL databases
==========================================

Usage: rpsl [command] [options]
       rpsl help [command]

"""


import os
import sys
from typing import Tuple, List, Optional

import importlib
import pkgutil


def remove_prefix(text, prefix):
    "remove the prefix"
    if text.startswith(prefix):
        return text[len(prefix):]
    return text


discovered_plugins = {
    remove_prefix(name, "rpsl_"): importlib.import_module(name)
    for finder, name, ispkg
    in pkgutil.iter_modules()
    if name.startswith("rpsl_")
}


def do_help(cmd: Optional[str] = None):
    "Print Help and exit"

    print(__doc__, file=sys.stderr)

    if cmd is None:
        print("Available commands:", file=sys.stderr)
        for pkg in discovered_plugins.keys():
            print(f" - {pkg}", file=sys.stderr)
        return 0

    if cmd not in discovered_plugins:
        print(f"Command not found: {cmd}", file=sys.stderr)
        return 1

    print(discovered_plugins[cmd].__doc__, file=sys.stderr)
    return 0


def find_rpsl(path: str) -> str:
    "Find the root directory for RPSL"
    path = os.path.abspath(path)
    rpsl = os.path.join(path, ".rpsl")
    while not os.path.exists(rpsl):
        if path == "/":
            break
        path = os.path.dirname(path)
        rpsl = os.path.join(path, ".rpsl")

    if not os.path.exists(rpsl):
        return None

    return path


def run() -> int:
    "run application"
    working_dir = os.getcwd()
    working_dir = os.environ.get("WORKING_DIR", working_dir)
    prog_dir = os.path.dirname(os.path.realpath(__file__))

    cmd, args = shift(shift(sys.argv)[1])

    if cmd is None or cmd == 'help':
        cmd, _ = shift(args)
        return do_help(cmd)

    if cmd not in discovered_plugins:
        print(f"Unsupported Command: {cmd}")
        return 1

    pkg = discovered_plugins[cmd]

    if 'run' not in dir(pkg):
        print(f"Command {cmd} is not compatible with rspl.", file=sys.stderr)
        return 1

    return pkg.run(args, {
        "WORKING_DIR": working_dir,
        "BIN_DIR": prog_dir,
        "RPSL_DIR": find_rpsl(working_dir),
        })


def shift(args: List[str]) -> Tuple[str, List[str]]:
    "shift off first arg + rest"
    if len(args) == 0:
        return None, []

    if len(args) == 1:
        return args[0], []

    return args[0], args[1:]


if __name__ == '__main__':
    code = run()
    sys.exit(code)
