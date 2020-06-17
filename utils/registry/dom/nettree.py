"Net Tree"

from ipaddress import ip_network, IPv6Network
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional

NET = IPv6Network
V6_NET = ip_network("::/0")
V4_NET = ip_network("::ffff:0.0.0.0/96")


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
        return "inetnum" if V4_NET.supernet_of(self.network) \
            else "inet6num"

    @property
    def object_name(self) -> str:
        """object name"""
        if V4_NET.supernet_of(self.network):
            n = self.network.network_address.exploded.replace(":", "")[-8:]
            return ip_network((
                bytes.fromhex(n),
                self.network.prefixlen - 96,
            )).with_prefixlen.replace("/", "_")

        return self.network.with_prefixlen.replace("/", "_")


@dataclass
class NetList:
    "Network List"
    index: int
    parent: Optional[int]
    level: int
    net: Optional[NetRecord]
    nets: List[NET]

    def in_net(self, i: NET) -> Tuple[bool, NET]:
        "find a network within a list of networks"
        found = False
        net = None
        for n in self.nets:
            if n.supernet_of(i):
                found = True
                net = n
                break

        return found, net


class NetTree:
    "Network Tree"
    def __init__(self, nets: Optional[List[NET]] = None):
        self.tree = {}  # type: Dict[NET, NetList]
        if nets is not None:
            self.make_tree(nets)

    def __getitem__(self, key):
        return self.tree[key]

    def find_tree(self, ip: NET) -> Tuple[bool, int]:
        """Find net in tree"""
        net = V6_NET
        current = self.tree[net]

        while True:
            found, net = current.in_net(ip)
            if not found:
                return True, current.level + 1

            if ip == net:
                return True, current.level + 2

            current = self.tree[net]
            continue

        return False, 0

    def make_tree(self, nets: List[NetRecord]):
        """build a network tree index"""
        root = V6_NET
        self.tree = {root: NetList(0, None, -1, None, [])}
        for index, net in enumerate(sorted(
                sorted(nets, key=lambda x: x.network),
                key=lambda x: x.network.prefixlen)):

            current = self.tree[root]

            while True:
                found, n = current.in_net(net.network)

                if found:
                    current = self.tree[n]
                    continue

                if current.level >= 0:
                    current.nets.append(net.network)

                self.tree[net.network] = NetList(
                    index, current.index, current.level + 1, net, [])
                break

    def write_csv(self, fn: str = ".netindex"):
        "write tree to csv"
        with open(fn, "w") as f:
            f.writelines({line+"\n" for line in self._lines()})

    def __str__(self) -> str:
        return "\n".join(self._lines())

    def _lines(self) -> List[str]:
        for v in self.tree.values():
            yield (
                "|".join([str(i) for i in (
                    v.index,
                    v.parent,
                    v.level,
                    v.net.network.network_address.exploded,
                    v.net.network.prefixlen,
                    v.net.object_type,
                    v.net.object_name,
                    v.net.policy,
                    v.net.status,
                    ",".join(v.net.mnters),
                    )])
            )
