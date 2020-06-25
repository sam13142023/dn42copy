#!/usr/bin/env python3
"""Scans Registry at given path for issues"""

import os
import sys
from typing import Dict

from dom.filedom import FileDOM
from dom.schema import SchemaDOM


def index_files(path: str):
    """generate list of dom files"""
    for root, _, files in os.walk(path):
        if root == path:
            continue

        for f in files:
            if f[0] == ".":
                continue

            dom = FileDOM.from_file(os.path.join(root, f))

            yield dom


def run(path: str = "."):
    """run main script"""
    idx = index_files(path)

    lookups = {}  # type: Dict[str, FileDOM]
    schemas = {}  # type: Dict[str, SchemaDOM]
    files = []

    print(r"Reading Files...", end="\r", flush=True, file=sys.stderr)

    for (i, dom) in enumerate(idx):
        if not dom.valid:
            print("E", end="", flush=True)
            continue

        key, value = dom.index
        lookups[key] = value
        files.append(dom)

        if dom.schema == "schema":
            schema = SchemaDOM(dom)
            schemas[schema.ref] = schema

        if i % 120 == 0:
            print(
                f"Reading Files: files: {len(files)} schemas: {len(schemas)}",
                end="\r", flush=True, file=sys.stderr)

    print(
        f"Reading Files: done! files: {len(files)}, schemas: {len(schemas)}",
        file=sys.stderr)

    for dom in files:
        s = schemas.get(dom.rel)
        if s is None:
            print(f"{dom.src} schema not found for {dom.rel}")
            continue

        status = s.check_file(dom, lookups)
        status.print()


if __name__ == "__main__":
    run(sys.argv[1] if len(sys.argv) > 1 else os.getcwd())
