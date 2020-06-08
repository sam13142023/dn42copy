#!/usr/bin/env python3
"""Test FileDOM"""
import unittest
import inspect
from pprint import pprint

from .filedom import FileDOM


class TestFileDOM(unittest.TestCase):
    """Test FileDOM"""

    def test_parse(self):
        """Test Parsing"""
        s = """
            person:             Xuu
            remarks:            test
            +
                                Multi-Line
            contact:            xmpp:xuu@xmpp.dn42
            contact:            mail:xuu@dn42.us
            pgp-fingerprint:    20AE2F310A74EA7CEC3AE69F8B3B0604F164E04F
            nic-hdl:            XUU-DN42
            mnt-by:             XUU-MNT
            source:             DN42
            """
        s = inspect.cleandoc(s)+"\n"

        dom = FileDOM()
        dom.parse(s.splitlines())

        self.assertTrue(dom.valid)
        self.assertEqual(dom.schema, "person")
        self.assertEqual(dom.get("person"), "Xuu")
        self.assertEqual(dom.get("contact"), "xmpp:xuu@xmpp.dn42")
        self.assertEqual(dom.get("contact", index=1), "mail:xuu@dn42.us")
        self.assertIsNone(dom.get("xxx"))
        self.assertEqual(dom.get("xxx", default="default"), "default")
        self.assertEqual(str(dom), s)

    def test_put_values(self):
        """Test putting values"""
        s = """
            person:             Xuu
            remarks:            test
            contact:            xmpp:xuu@xmpp.dn42
            contact:            mail:xuu@dn42.us
            pgp-fingerprint:    20AE2F310A74EA7CEC3AE69F8B3B0604F164E04F
            nic-hdl:            XUU-DN42
            mnt-by:             XUU-MNT
            source:             DN42
            """
        s = inspect.cleandoc(s)+"\n"

        dom = FileDOM()
        dom.parse(s.splitlines())

        dom.put("source", "SOURIS")
        self.assertEqual(dom.get("source"), "SOURIS")

        dom.put("contact", "mail:me@sour.is", append=True)
        self.assertEqual(str(dom.get("contact")), "xmpp:xuu@xmpp.dn42")
        self.assertEqual(dom.get("contact", index=1), "mail:xuu@dn42.us")
        self.assertEqual(dom.get("contact", index=2), "mail:me@sour.is")

    def test_parse_ip6address(self):
        """Test network ip address parsing"""
        s = """
            inet6num:           fd00:0000:0000:0000:0000:0000:0000:0000 - fdff:ffff:ffff:ffff:ffff:ffff:ffff:ffff
            cidr:               fd00::/8
            netname:            ROOT-DN42-ULA
            descr:              DN42 ULA Address Space
            status:             ALLOCATED
            policy:             open
            org:                ORG-DN42
            mnt-by:             DN42-MNT
            source:             DN42
            """  # noqa: E501

        s = inspect.cleandoc(s)+"\n"

        dom = FileDOM()
        dom.parse(s.splitlines())

        cidr = dom.get("cidr").as_net()
        self.assertEqual(cidr.compressed, "fd00::/8")
        self.assertEqual(
            cidr.exploded, "fd00:0000:0000:0000:0000:0000:0000:0000/8")

        end = cidr.broadcast_address.exploded
        start = cidr.network_address.exploded

        self.assertEqual(dom.get("inet6num"), f"{start} - {end}")

    def test_parse_ip4address(self):
        """Test network ip address parsing"""
        s = """
            inetnum:            172.20.0.0 - 172.23.255.255
            cidr:               172.20.0.0/14
            netname:            ROOT-DN42
            """

        s = inspect.cleandoc(s)+"\n"

        dom = FileDOM()
        dom.parse(s.splitlines())

        cidr = dom.get("cidr").as_net()
        self.assertEqual(cidr.compressed, "172.20.0.0/14")
        self.assertEqual(
            cidr.exploded, "172.20.0.0/14")

        end = cidr.broadcast_address.exploded
        start = cidr.network_address.exploded

        self.assertEqual(dom.get("inetnum"), f"{start} - {end}")

    @unittest.skip
    def test_bad_parse(self):
        """bad parse stuff"""
        s = """
            person:             Xuu
                                EXTRA
            :
            source:             DN42
            """
        s = inspect.cleandoc(s)+"\n"

        dom = FileDOM()
        dom.parse(s.splitlines())
        pprint(dom.dom)
        self.assertEqual(str(dom), s)


if __name__ == '__main__':
    unittest.main()
