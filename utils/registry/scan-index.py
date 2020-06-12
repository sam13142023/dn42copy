#!/usr/bin/env python3
"""Scans Registry at given path for issues using an pregenerated index"""

import os
import sys
from typing import Dict

from dom.filedom import FileDOM, read_file
from dom.schema import SchemaDOM


def index_files(path: str):
    """generate list of dom files"""
    for root, _, files in os.walk(path):
        if root == path:
            continue

        for f in files:
            if f[0] == ".":
                continue

            dom = read_file(os.path.join(root, f))
            yield dom


def run(path: str = ".", index: str = ".index"):
    """run main script"""

    lookups = {}  # type: Dict[str, FileDOM]
    schemas = {}  # type: Dict[str, SchemaDOM]

    schema_set = set()
    with open(index) as fd:
        for line in fd.readlines():
            sp = line.split()
            lookups[(sp[0], sp[1])] = (sp[2], sp[3])

            if sp[0] == "dn42.schema":
                schema_set.add(sp[2])

    for s in schema_set:
        dom = read_file(s)
        schema = SchemaDOM()
        schema.parse(dom)

        schemas[schema.ref] = schema

    files = index_files(path)
    for dom in files:
        key, value = dom.index
        lookups[key] = value

    for dom in files:
        s = schemas.get(dom.rel)
        if s is None:
            print(f"{dom.src} schema not found for {dom.rel}")

        status = s.check_file(dom, lookups=lookups)
        status.print()
        print(status)


if __name__ == "__main__":
    run(sys.argv[1] if len(sys.argv) >= 2 else os.getcwd())
