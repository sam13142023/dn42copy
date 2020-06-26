"""RSPL Whois Search
====================

Usage: rpsl whois [text]

"""

import sys
from ipaddress import ip_network
from typing import List, Dict, Optional

from dn42.rpsl import RPSL, Config
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
        ip = ip_network(text)
    except ValueError:
        pass

    if ip is not None:
        print(f"Searching network {text}...")
        return 0

    for dom in rpsl.find(text, schema):
        print(dom)

    return 0
