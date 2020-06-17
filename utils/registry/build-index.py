#!/usr/bin/env python3
"""Builds registry index to be used by scan-index.py"""

import os
import sys

from typing import Dict, Generator, List

from dom.filedom import FileDOM, read_file
from dom.schema import SchemaDOM
from dom.nettree import NetTree, NetRecord
from dom.transact import TransactDOM

def index_files(path: str) -> Generator[FileDOM, None, None]:
    """generate list of dom files"""
    for root, _, files in os.walk(path):
        if root == path:
            continue

        for f in files:
            if f[0] == ".":
                continue

            dom = read_file(os.path.join(root, f))
            yield dom


def run(path: str = "."):
    """run main script"""
    if not os.path.isdir(os.path.join(path, "schema")):
        print("schema directory not found in path", file=sys.stderr)
        sys.exit(1)

    idx = index_files(path)

    lookup = {}  # type: Dict[str, FileDOM]
    schemas = {}  # type: Dict[str, SchemaDOM]
    files = []
    nets = []  # type: List[NetRecord]

    print(r"Reading Files...", end="\r", flush=True, file=sys.stderr)

    for (i, dom) in enumerate(idx):
        if not dom.valid:
            print("E", end="", flush=True)
            continue

        key, value = dom.index
        lookup[key] = value
        files.append(dom)

        if dom.schema == "schema":
            schema = SchemaDOM()
            schema.parse(dom)

            schemas[schema.ref] = schema

        if dom.schema in ["inetnum", "inet6num"]:
            nets.append(NetRecord(
                dom.get("cidr").as_net6,
                dom.mntner,
                dom.get("policy", default="closed"),
                dom.get("status", default="ASSIGNED"),
            ))

        if i % 120 == 0:
            print(
                f"Reading Files: files: {len(files)} schemas: {len(schemas)}",
                end="\r", flush=True, file=sys.stderr)

    print(
        f"Reading Files: done! files: {len(files)}, schemas: {len(schemas)}",
        file=sys.stderr)

    print("Writing .index", file=sys.stderr)
    print("Writing .links", file=sys.stderr)
    with open(".index", 'w') as out:
        with open(".links", 'w') as link_out:
            for dom in files:
                s = schemas.get(dom.rel)
                if s is None:
                    print(
                        f"{dom.src} schema not found for {dom.rel}",
                        file=sys.stderr)

                print(dom.rel,
                      dom.get(s.primary),
                      dom.src,
                      ",".join(dom.mntner),
                      sep="|",
                      file=out)

                for (link, refs) in s.links.items():
                    d = dom.get(link)
                    refs_join = ','.join(refs)
                    if d is not None:
                        print(
                            f"{dom.rel}|{dom.name}|{link}|{d}|{refs_join}",
                            file=link_out)

    print("Generate .nettree", file=sys.stderr)
    tree = NetTree(nets)

    print("Writing .nettree", file=sys.stderr)
    tree.write_csv(".nettree")

    print("Writing .schema", file=sys.stderr)
    s = TransactDOM()
    s.mntner = "DN42-MNT"
    s.files = schemas.values()
    with open(".schema", "w") as out:
        print(s, file=out)

    print("done.", file=sys.stderr)


if __name__ == "__main__":
    run(sys.argv[1] if len(sys.argv) > 1 else os.getcwd())
