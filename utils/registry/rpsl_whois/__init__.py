"""RSPL Whois Search
====================

Usage: rpsl whois [text]

"""

import sys
from itertools import chain
from typing import List, Dict, Optional, Set, Tuple

from dn42.rpsl import RPSL, Config, FileDOM, as_net6
from dn42.utils import shift, exists


def run(args: List[str], env: Dict[str, str]) -> int:
    "do whois search"
    if len(args) == 0:
        print("Usage: rpsl whois [text]")

    rpsl_dir = env.get("RPSL_DIR")
    if rpsl_dir is None:
        print("RPSL index files not found. do `rpsl index`?", file=sys.stderr)
        return 1

    config = Config.from_path(rpsl_dir)
    if not exists(config.index_file,
                  config.schema_file,
                  config.links_file):
        print("RPSL index files not found. do `rpsl index`?", file=sys.stderr)
        return 1

    rpsl = RPSL(config)

    schema = None  # type: Optional[str]
    text, args = shift(args)

    if len(args) > 0:
        schema = text
        text, args = shift(args)

    ip = None
    try:
        ip = as_net6(text)
    except ValueError:
        pass

    principle = []  # type: List[FileDOM]
    related_nets = []  # type: List[FileDOM]
    related_idx = set()  # type: Set[Tuple[str, str]]

    if ip is not None:
        print(f"# Searching network {text}...")
        nets = list(rpsl.find_network(text))
        last_net = nets[-1]
        dom = rpsl.load_file(str(last_net.net))
        principle.append(dom)
        related_idx.add(dom.index)
        ok, route = last_net.in_routes(ip)
        if ok:
            dom = rpsl.load_file(str(route))
            principle.append(dom)
            related_idx.add(dom.index)

        for net in nets[:-1]:
            dom = rpsl.load_file(str(net.net))
            related_nets.append(dom)
    else:
        for dom in rpsl.find(text, schema):
            principle.append(dom)
            related_idx.add(dom.index)

    print("# Found objects")
    for dom in principle:
        print(dom)

    if len(related_nets) > 0:
        print("# Related Networks")
        for dom in related_nets:
            print(dom)

    print("# Related objects")
    lis = set(chain.from_iterable(rpsl.related(i) for i in related_idx))
    for dom in rpsl.load_files(sorted(lis)):
        print(dom)
    return 0
