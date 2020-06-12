#!/usr/bin/env python3
"""Builds registry index to be used by scan-index.py"""

import os
import sys

from ipaddress import ip_network, IPv6Network
from dataclasses import dataclass
from typing import TypeVar, Dict, Generator, List, Tuple

from dom.filedom import FileDOM, read_file
from dom.schema import SchemaDOM


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


NET = IPv6Network
NET_LIST = TypeVar('NET_LIST', int, List[NET])
NET_TREE = Dict[NET, NET_LIST]
V6_NET = ip_network("::/0")
V4_NET = ip_network("::0.0.0.0/96")


@dataclass
class NetRecord:
    "Network Record"
    network: NET
    mnters: List[str]
    policy: str
    status: str

    @property
    def object_type(self) -> str:
        """object type"""
        return "inetnum" if V4_NET.network.supernet_of(self.network) \
            else "inet6num"

    @property
    def object_name(self) -> str:
        """object name"""
        return self.network.with_prefixlen.replace("/", "_")


def in_net(i: NET, nets: List[NET]) -> Tuple[bool, NET]:
    "find a network within a list of networks"
    found = False
    net = None
    for n in nets:
        if n.supernet_of(i):
            found = True
            net = n
            break

    return found, net


def find_tree(ip: NET, nets: NET_TREE):
    """Find net in tree"""
    net = V6_NET
    current = nets[net]
    while True:
        found, net = in_net(ip, current[1])
        if not found:
            return True, current[0] + 1

        if ip.network == net.network:
            return True, current[0] + 2

        current = nets[net]
        continue


def make_tree(nets: List[NET]) -> Dict[NET, NET_LIST]:
    """build a network tree index"""
    root = V6_NET
    tree = {root: [-1, []]}
    for i in sorted(
            sorted(nets, key=lambda x: x.exploded),
            key=lambda x: x.prefixlen):
        current = tree[root]

        while True:
            found, n = in_net(i, current[1])

            if found:
                current = tree[n]
                continue

            if current[0] >= 0:
                current[1].append(i)

            tree[i] = [current[0] + 1, []]
            break

    return tree


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
    print("Writing .linkindex", file=sys.stderr)
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
                      sep="\t",
                      file=out)

                for (link, refs) in s.links.items():
                    d = dom.get(link)
                    if d is not None:
                        print(
                            f"{dom.name}\t{link}\t{d}\t{','.join(refs)}",
                            file=link_out)

    print("Generate .netindex", file=sys.stderr)
    tree = make_tree({n.network for n in nets})

    netindex = []
    for net in nets:
        v = tree[net.network]
        netindex.append((v[0],
                         net.network.network_address.exploded,
                         net.network.broadcast_address.exploded,
                         net.policy, net.status, ",".join(net.mnters)))

    print("Writing .netindex", file=sys.stderr)
    with open(".netindex", "w") as out:
        for row in sorted(netindex, key=lambda x: x[0]):
            print("\t".join([str(i) for i in row]), file=out)

    print("done.", file=sys.stderr)


if __name__ == "__main__":
    run(sys.argv[1] if len(sys.argv) > 1 else os.getcwd())
