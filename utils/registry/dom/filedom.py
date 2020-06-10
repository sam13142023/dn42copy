"""FileDOM parse and formating"""

import re
from dataclasses import dataclass
from typing import Sequence, NamedTuple, List, Dict, Optional, Union
import ipaddress

import log


@dataclass
class Value:
    """Dom Value"""
    value: str

    def __eq__(self, other: str) -> bool:
        return self.value == other

    def __str__(self) -> str:
        return self.value

    def lines(self) -> List[str]:
        """return value split into lines"""
        return self.value.splitlines()

    def fields(self) -> List[str]:
        """return value split into fields"""
        return self.value.split()

    def as_ip(self) -> Union[ipaddress.IPv4Address, ipaddress.IPv6Address]:
        """return value as an ip address"""
        return ipaddress.ip_address(self.value)

    def as_net(self) -> Union[ipaddress.IPv4Network, ipaddress.IPv6Network]:
        """return value as an ip network"""
        return ipaddress.ip_network(self.value)

    def as_key(self) -> str:
        """Format as key name"""
        return self.value.replace("/", "_").replace(" ", "")


class Row(NamedTuple):
    """DOM Row"""
    key: str
    value: Value
    lineno: int
    src: str = None

    def loc(self) -> str:
        """format as location"""
        s = f"{self.src} Line {self.lineno} "
        s += "" if self.key == "" else f"Key [{self.key}]:"
        return s


class FileDOM:
    """Parses a reg file"""

    def __init__(self, src: Optional[str] = None):
        self.valid = False
        self.dom = []  # type: List[Row]
        self.keys = {}  # type: Dict[str, int]
        self.multi = {}  # type: Dict[str, int]
        self.mntner = []  # type: List[str]
        self.schema = None  # type: Optional[str]
        self.src = src

    def parse(self, input_str: Sequence[str], src: Optional[str] = None):
        """Parse an input string generator"""
        dom = []
        keys = {}
        multi = {}
        mntner = []
        last_multi = None
        self.valid = True
        self.src = self.src if src is None else src

        for lineno, i in enumerate(input_str, 1):
            # print(lineno, i)
            if re.match(r'[ \t]', i):
                if len(dom) == 0:
                    log.error(f"File {src} does not parse properly")
                    self.valid = False
                    return

                dom[-1][1] += "\n" + i.strip()

                if dom[-1][0] not in multi:
                    multi[dom[-1][0]] = []

                if last_multi is None:
                    multi[dom[-1][0]].append(lineno)
                    last_multi = dom[-1][0]

            else:
                if i[0] == '+':
                    dom[-1][1] += "\n"

                    if dom[-1][0] not in multi:
                        multi[dom[-1][0]] = []

                    if last_multi is None:
                        multi[dom[-1][0]].append(lineno)
                        last_multi = dom[-1][0]

                i = i.split(":")
                if len(i) < 2:
                    continue

                dom.append([i[0].strip(), ':'.join(
                    i[1:]).strip(), lineno - 1])

                if i[0].strip() not in keys:
                    keys[i[0].strip()] = []

                keys[i[0].strip()].append(len(dom) - 1)

                last_multi = None

            if dom[-1][0] == 'mnt-by':
                mntner.append(dom[-1][1])

        self.dom = [Row(k, Value(v), n) for k, v, n in dom]
        self.keys = keys
        self.multi = multi
        self.mntner = mntner
        self.schema = self.dom[0].key

    def __str__(self):
        length = 19
        for i in self.dom:
            if len(i.key) > length:
                length = len(i.key) + 2
        s = ""
        for i in self.dom:
            sp = i.value.lines()

            s += i.key + ":" + " " * (length - len(i.key)) + sp[0] + "\n"
            for m in sp[1:]:
                if m == "":
                    s += "+\n"
                    continue
                s += " " * (length + 1) + m + "\n"

        return s

    def get(self, key, index=0, default=None):
        """Get a key value"""
        if key not in self.keys:
            return default
        if index >= len(self.keys[key]) or index <= -len(self.keys[key]):
            return default

        return self.dom[self.keys[key][index]].value

    def put(self, key, value, index=0, append=False):
        """Put a value"""
        if key not in self.keys:
            self.keys[key] = []

        i = (self.keys[key][index:index+1] or (None,))[0]
        if i is None or append:
            i = len(self.dom)
            self.dom.append(Row(key, Value(value), i))
        elif i is not None:
            self.dom[i] = Row(key, Value(value), i)

        if index not in self.keys[key]:
            self.keys[key].append(i)


def read_file(fn: str) -> FileDOM:
    """Parses FileDOM from file"""
    with open(fn, mode='r', encoding='utf-8') as f:
        return FileDOM().parse(f.readlines())
