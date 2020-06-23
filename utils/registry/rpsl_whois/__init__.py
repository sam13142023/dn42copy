"""RSPL Whois Search
====================

Usage: rpsl whois [text]

"""

import os.path
from ipaddress import ip_network
from typing import List, Dict, Tuple

from dom.filedom import FileDOM


def run(args: List[str], env: Dict[str, str]) -> int:
    "do whois search"
    path = env.get("RPSL_DIR")

    if len(args) == 0:
        print("Usage: rpsl whois [text]")

    schema = None
    text, args = shift(args)

    if len(args) > 0:
        schema = text
        text, args = shift(args)

    ip = None
    try:
        ip = ip_network(text)
    except ValueError:
        pass

    lookups, find = load_lookup(path)

    if ip is not None:
        print(f"Searching network {text}...")
        return 0

    keys = [(schema, text)]
    if schema is None:
        keys = find.get(text, [])

    for i in keys:
        fn = os.path.join(path, lookups[i][2])
        print(FileDOM.from_file(fn))

    return 0


def load_lookup(path: str) -> Tuple[Dict[Tuple[str, str], FileDOM],
                                    Dict[str, List[Tuple[str, str]]]]:
    "Load lookup data"
    index_file = os.path.join(path, ".rpsl/index")

    lookups = {}  # type: Dict[Tuple[str, str], FileDOM]
    find = {}  # type: Dict[str, List[Tuple[str, str]]]

    with open(index_file) as fd:
        for line in fd.readlines():
            sp = line.strip().split(sep="|")
            lookups[(sp[0], sp[1])] = (sp[0], sp[1], sp[2])
            find[sp[1]] = find.get(sp[1], [])
            find[sp[1]].append((sp[0], sp[1]))

    return lookups, find


def shift(args: List[str]) -> Tuple[str, List[str]]:
    "shift off first arg + rest"
    if len(args) == 0:
        return None, []

    if len(args) == 1:
        return args[0], []

    return args[0], args[1:]
