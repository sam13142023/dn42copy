"""RSPL Scan
============

"""

import os
import sys
import argparse
from typing import List, Dict

from dom.filedom import FileDOM
from dom.schema import SchemaDOM
from dom.transact import TransactDOM

parser = argparse.ArgumentParser()
parser.add_argument("--add-index", action='store_true')
parser.add_argument("--scan-dir", type=str, default=None)
parser.add_argument("--scan-file", type=str, default=None)


def index_files(path: str):
    """generate list of dom files"""
    for root, _, files in os.walk(path):
        if root == path:
            continue
        if root.endswith(".rpsl"):
            continue

        for f in files:
            dom = FileDOM.from_file(os.path.join(root, f))
            yield dom


def run(args: List[str], env: Dict[str, str]) -> int:
    """run scan script"""
    opts = parser.parse_args(args)

    path = env.get("RPSL_DIR")
    if path is None:
        print("RPSL directory not found. do `rpsl init` or set RPSL_DIR",
              file=sys.stderr)
        return 1

    index_file = os.path.join(path, ".rpsl/index")
    schema_file = os.path.join(path, ".rpsl/schema")

    if not os.path.exists(index_file) or not os.path.exists(schema_file):
        print("RPSL index files not found. do `rpsl index`?")
        return 1

    lookups = {}  # type: Dict[str, FileDOM]
    schemas = {}  # type: Dict[str, SchemaDOM]

    with open(index_file) as fd:
        print("Reading index... ", end="", file=sys.stderr, flush=True)
        for line in fd.readlines():
            sp = line.strip().split(sep="|")
            lookups[(sp[0], sp[1])] = (sp[2], "")
        print("done.", file=sys.stderr, flush=True)

    schema_set = TransactDOM.from_file(schema_file)

    for schema in schema_set.schemas:
        schemas[schema.ref] = schema

    def file_gen():
        if opts.scan_dir is not None:
            path = os.path.join(env.get("WORKING_DIR"), opts.scan_dir)
        elif opts.scan_file is not None:
            path = os.path.join(env.get("WORKING_DIR"), opts.scan_file)
            return TransactDOM.from_file(path).files

        return index_files(path)

    if opts.add_index:
        print("Add scanned items to lookup index...", file=sys.stderr)
        for dom in file_gen():
            key, value = dom.index
            lookups[key] = value

    for dom in file_gen():
        s = schemas.get(dom.rel)
        if s is None:
            print(f"{dom.src} schema not found for {dom.rel}")

        status = s.check_file(dom, lookups=lookups)
        status.print()
    print(status)
    return 0 if status else 1
