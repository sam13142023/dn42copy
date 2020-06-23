"""RSPL Build Indexes
=====================

Usage: rspl index

"""


import os
import sys

from typing import Dict, Generator, List, Set, Tuple

from dom.filedom import FileDOM
from dom.schema import SchemaDOM
from dom.nettree import NetTree, NetRecord
from dom.transact import TransactDOM
from dom.rspl import RPSLConfig


def run(args: List[str], env: Dict[str, str]) -> int:
    "rspl index"

    _ = args

    path = env.get("WORKING_DIR")

    if not os.path.isdir(os.path.join(path, "schema")):
        print("schema directory not found in path", file=sys.stderr)
        sys.exit(1)

    print(r"Reading Files...", end="\r", flush=True, file=sys.stderr)
    idx = index_files(path)
    lookup, schemas, files, nets = build_index(idx)

    print(
        f"Reading Files: done! files: {len(files)}" +
        f" schemas: {len(schemas)}" +
        f" networks: {len(nets)}",
        file=sys.stderr)

    print("Writing .rpsl/index", file=sys.stderr)
    with open(".rpsl/index", 'w') as out:
        print("Writing .rpsl/links", file=sys.stderr)
        with open(".rpsl/links", 'w') as link_out:
            for dom in files:
                s = schemas.get(dom.rel)
                if s is None:
                    print(
                        f"{dom.src} schema not found for {dom.rel}",
                        file=sys.stderr)
                    continue

                primary, mntner = dom.get(s.primary), ",".join(dom.mntner)
                _ = mntner
                src = remove_prefix(dom.src, path+os.sep)
                print(dom.rel, primary, src,  # mntner,
                      sep="|", file=out)

                for (link, rel, d) in generate_links(dom, s.links, lookup):
                    print(f"{dom.rel}|{dom.name}|{link}|{rel}|{d}",
                          file=link_out)

    print("Generate .rpsl/nettree", file=sys.stderr)
    tree = NetTree(nets)

    print("Writing .rpsl/nettree", file=sys.stderr)
    tree.write_csv(".rpsl/nettree")

    print("Writing .rpsl/schema", file=sys.stderr)
    s = TransactDOM()
    s.mntner = "DN42-MNT"
    s.files = schemas.values()
    with open(".rpsl/schema", "w") as out:
        print(s, file=out)

    print("done.", file=sys.stderr)

    return 0


class NotRPSLPath(Exception):
    "error raised if unable to determine RPSL root"


def index_files(path: str) -> Generator[FileDOM, None, None]:
    """generate list of dom files"""
    path = os.path.abspath(path)
    rpsl = os.path.join(path, ".rpsl/config")
    while not os.path.exists(rpsl):
        if path == "/":
            break
        path = os.path.dirname(path)
        rpsl = os.path.join(path, ".rpsl/config")

    if not os.path.exists(rpsl):
        raise NotRPSLPath()

    yield FileDOM.from_file(rpsl)

    for root, _, files in os.walk(path):
        if root == path:
            continue
        if root.endswith(".rpsl"):
            continue

        for f in files:
            dom = FileDOM.from_file(os.path.join(root, f))
            yield dom


def build_index(
        idx: Generator[FileDOM, None, None]
    ) -> Tuple[
        Set[Tuple[str, str]],
        Dict[str, SchemaDOM],
        List[FileDOM],
        List[NetRecord]]:
    "build index for files"
    rspl = RPSLConfig.default()
    lookup = set()  # type: Set[Tuple[str, str]]
    schemas = {}  # type: Dict[str, SchemaDOM]
    files = []  # type: List[FileDOM]
    nets = []  # type: List[NetRecord]

    print(r"Reading Files...", end="\r", flush=True, file=sys.stderr)

    net_types = rspl.network_parents

    for (i, dom) in enumerate(idx):
        if not dom.valid:
            print("E", end="", flush=True)
            continue

        key, _ = dom.index
        lookup.add(key)
        files.append(dom)

        if dom.schema == "namespace":
            rspl = RPSLConfig.from_dom(dom)
            net_types = rspl.network_parents

        if dom.schema == rspl.schema:
            schema = SchemaDOM(dom)
            schemas[schema.ref] = schema

        if dom.schema in net_types:
            nets.append(NetRecord(
                dom.get("cidr").as_net6,
                dom.mntner,
                dom.get("policy", default="closed"),
                dom.get("status", default="ASSIGNED"),
            ))

        if i % 120 == 0:
            print(
                f"Reading Files: files: {len(files)}" +
                f" schemas: {len(schemas)} " +
                f" networks: {len(nets)}",
                end="\r", flush=True, file=sys.stderr)

    return (lookup, schemas, files, nets)


def generate_links(
        dom: FileDOM,
        links: Dict[str, List[str]],
        lookup: Set[Tuple[str, str]]
        ) -> Generator[Tuple[str, str, str], None, None]:
    "print file links out to file"
    for (link, refs) in links.items():
        d = dom.get(link)
        if d is None:
            return

        found = False
        for ref in refs:
            if (ref, d.value) in lookup:
                found = True
                yield (link, ref, d)

        if not found:
            print(f"{dom.name} missing link {link} {d.value}")


def remove_prefix(text, prefix):
    "remove the prefix"
    if text.startswith(prefix):
        return text[len(prefix):]
    return text
