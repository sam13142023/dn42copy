"""RSPL Scan
============

"""

import os
import sys
from typing import List, Dict

from dom.filedom import FileDOM
from dom.schema import SchemaDOM
from dom.transact import TransactDOM


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

    path = env.get("RPSL_DIR")
    if path is None:
        print("RPSL index has not been generated.", file=sys.stderr)
        return 1

    index_file = os.path.join(path, ".rpsl/index")

    lookups = {}  # type: Dict[str, FileDOM]
    schemas = {}  # type: Dict[str, SchemaDOM]

    with open(index_file) as fd:
        print("Reading index... ", end="", file=sys.stderr, flush=True)
        for line in fd.readlines():
            sp = line.strip().split(sep="|")
            lookups[(sp[0], sp[1])] = (sp[2], "")
        print("done.", file=sys.stderr, flush=True)

    schema_file = os.path.join(path, ".rpsl/schema")
    schema_set = TransactDOM.from_file(schema_file)

    for schema in schema_set.schemas:
        schemas[schema.ref] = schema

    files = index_files(path)
    # for dom in files:
    #     key, value = dom.index
    #     lookups[key] = value

    for dom in files:
        s = schemas.get(dom.rel)
        if s is None:
            print(f"{dom.src} schema not found for {dom.rel}")

        status = s.check_file(dom, lookups=lookups)
        status.print()
    print(status)
    return 0 if status else 1
