"Testing NetTree"
import unittest
from ipaddress import ip_network

from .nettree import NetTree, NetRecord

records = [
    NetRecord(
        ip_network("::/0"),
        ["DN42-MNT"],
        "closed",
        "ALLOCATED"),
    NetRecord(
        ip_network("::ffff:0.0.0.0/96"),
        ["DN42-MNT"],
        "closed",
        "ALLOCATED"),
    NetRecord(
        ip_network("::ffff:172.21.64.0/125"),
        ["XUU-MNT"],
        "closed",
        "ALLOCATED"),
    NetRecord(
        ip_network("fdea:a15a:77b9::/48"),
        ["XUU-MNT"],
        "closed",
        "ALLOCATED"),
]

text = [
    "0|0|0|0000:0000:0000:0000:0000:0000:0000:0000|0|inet6num|::_0|closed|ALLOCATED|DN42-MNT",  # noqa: E501
    "1|0|1|fdea:a15a:77b9:0000:0000:0000:0000:0000|48|inet6num|fdea:a15a:77b9::_48|closed|ALLOCATED|XUU-MNT",  # noqa: E501
    "2|0|1|0000:0000:0000:0000:0000:ffff:0000:0000|96|inetnum|0.0.0.0_0|closed|ALLOCATED|DN42-MNT",  # noqa: E501
    "3|2|2|0000:0000:0000:0000:0000:ffff:ac15:4000|125|inetnum|172.21.64.0_29|closed|ALLOCATED|XUU-MNT"  # noqa: E501
]


class TestNetTree(unittest.TestCase):
    "testing NetTree"
    def test_nettree(self):
        "test NetTree"
        tree = NetTree(records)
        for (left, right) in zip(str(tree).splitlines(), text):
            self.assertEqual(left, right)

    def test_find(self):
        "test NetTree"
        tree = NetTree(records)
        tt = [
            ("fdea:a15a:77b9:ffff::/64", (True, 2)),
            ("fdea:a15a:77ba:ffff::/64", (True, 1)),
            ("::ffff:172.21.64.0/126", (True, 3)),
            ("::ffff:172.21.64.4/126", (True, 3)),
            ("::ffff:172.21.64.8/126", (True, 2)),

        ]

        for (net, expect) in tt:
            self.assertEqual(
                tree.find_tree(ip_network(net)),
                expect,
                msg="network "+net)
