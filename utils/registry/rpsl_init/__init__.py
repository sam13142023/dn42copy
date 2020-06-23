"""RSPL Initialize data store
=============================

Usage: rspl init [options]

Options:
--namespace=<ns>       Namespace (default: current working dir name)
--schema=<schema>      Schema (default: schema)
--owners=<mntner>      Owner (default: mntner)
--default-owner=<mnt>  Default Owner (default: DN42-MNT)
--source=<src>         Source (default: DN42)
--force                Force creation of config
"""


import sys
import os.path
import argparse
from typing import List, Dict, Generator, Tuple, Set, TypeVar

from dom.rspl import RPSLConfig
from dom.filedom import FileDOM
from dom.schema import SchemaDOM

parser = argparse.ArgumentParser()
parser.add_argument("--namespace", type=str, default=None)
parser.add_argument("--schema", type=str, default="schema")
parser.add_argument("--owners", type=str, default="mntner")
parser.add_argument("--default-owner", type=str, default="DN42-MNT")
parser.add_argument("--source", type=str, default="DN42")
parser.add_argument("--force", action='store_true')


def run(args: List[str], env: Dict[str, str]) -> int:
    "rspl init"
    opts = parser.parse_args(args)
    if opts.namespace is None:
        opts.namespace = os.path.basename(env.get("WORKING_DIR"))

    rpsl_dir = env.get("RPSL_DIR")
    if rpsl_dir is not None and not opts.force:
        print(f"RPSL database already initialized! Found in: {rpsl_dir}")
        return 1

    rpsl_dir = env.get("WORKING_DIR")
    rpsl = RPSLConfig(root=rpsl_dir,
                      namespace=opts.namespace,
                      schema=opts.schema,
                      owners=opts.owners,
                      source=opts.source,
                      default_owner=opts.default_owner)

    if os.path.exists(rpsl.schema_dir):
        rpsl.network_owner, rpsl.primary_key = _parse_schema(rpsl.schema_dir)

    os.makedirs(os.path.dirname(rpsl.config_file), exist_ok=True)
    with open(rpsl.config_file, "w") as f:
        print(rpsl, file=f)

    print(f"Created: {rpsl.config_file}", file=sys.stderr)
    return 0


def _read_schemas(path: str) -> Generator[SchemaDOM, None, None]:
    for root, _, files in os.walk(path):
        for f in files:
            dom = FileDOM.from_file(os.path.join(root, f))
            schema = SchemaDOM(dom)
            yield schema


Group = TypeVar("Group", set, tuple)


def _parse_schema(path: str) -> Tuple[Group, Group]:
    schemas = _read_schemas(path)

    network_owner = set()  # type: Set[str, str]
    primary_key = set()  # type: Set[str, str]

    for s in schemas:
        for i in s.dom.get_all("network-owner"):
            network_owner.add((s.type, i.value))

        if s.primary != s.type:
            primary_key.add((s.type, s.primary))

    print(network_owner)
    return network_owner, primary_key
