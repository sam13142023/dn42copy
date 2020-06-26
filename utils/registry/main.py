"""rpsl a tool for managing RPSL databases
==========================================

Usage: rpsl [command] [options]
       rpsl help [command]

"""


import os
import sys
from typing import Optional

import importlib
import pkgutil

from dn42.utils import find_rpsl, remove_prefix, shift

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


def run() -> int:
    "run application command"
    _, args = shift(sys.argv)  # drop exec name
    cmd, args = shift(args)

    working_dir = os.getcwd()
    working_dir = os.environ.get("WORKING_DIR", working_dir)

    prog_dir = os.path.dirname(os.path.realpath(__file__))

    rpsl_dir = os.environ.get("RPSL_DIR", working_dir)
    rpsl_dir = find_rpsl(rpsl_dir)

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
        "RPSL_DIR": rpsl_dir,
        })


if __name__ == '__main__':
    code = run()
    sys.exit(code)
