"""RSPL Scan
============

Usage: rspl scan [options]

Options:
--scan-dir=<dir>       Scan given directory
--scan-file=<file>     Scan given file
--add-index            Add scanned items to lookup table

"""

import os
import sys
import argparse
from typing import List, Dict

from dn42.rpsl import RPSL, Config, TransactDOM, index_files

parser = argparse.ArgumentParser()
parser.add_argument("--add-index", action='store_true')
parser.add_argument("--scan-dir", type=str, default=None)
parser.add_argument("--scan-file", type=str, default=None)


def run(args: List[str], env: Dict[str, str]) -> int:
    """run scan script"""
    opts = parser.parse_args(args)

    path = env.get("RPSL_DIR")
    if path is None:
        print("RPSL directory not found. do `rpsl init` or set RPSL_DIR",
              file=sys.stderr)
        return 1

    config = Config.from_path(path)
    if not os.path.exists(config.index_file) or \
            not os.path.exists(config.schema_file):
        print("RPSL index files not found. do `rpsl index`?", file=sys.stderr)
        return 1

    rpsl = RPSL(config)
    files = _file_gen(path, opts, wd=env.get("WORKING_DIR"), config=config)

    if opts.add_index:
        files, g = [], files
        print("Add scanned items to lookup index...", file=sys.stderr)
        for dom in g:
            files.append(dom)
            rpsl.append_index(dom)

    print("Scanning files...", file=sys.stderr)
    status = rpsl.scan_files(files)
    status.print_msgs()
    print(status)
    return 0 if status else 1


def _file_gen(path, opts: argparse.Namespace, wd: str, config: Config):
    if opts.scan_dir is not None:
        path = os.path.join(wd, opts.scan_dir)
    elif opts.scan_file is not None:
        path = os.path.join(wd, opts.scan_file)
        return TransactDOM.from_file(path).files

    return index_files(path, config.namespace, config.primary_keys)
