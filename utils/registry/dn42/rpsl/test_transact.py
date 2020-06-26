"Test TransactDOM"

import unittest
import inspect

from .transact import TransactDOM


def clean(s: str) -> str:
    "Clean input for use"
    return inspect.cleandoc(s) + "\n"


dn42_mnt_file = clean("""
    .BEGIN DN42-MNT
    schema:             SCHEMA-SCHEMA
    ref:                dn42.schema
    key:                schema   required  single    primary schema > [name]
    key:                ref      required  single    > [schema]
    key:                key      required  multiple  > [key-name]
                        {required|optional|recommend|deprecate}
                        {single|multiple} {primary|} {schema|}
                        lookup=str '>' [spec]...
    key:                mnt-by   required  multiple    lookup=dn42.mntner > [mntner]
    key:                remarks  optional  multiple  > [text]...
    key:                source   required  single      lookup=dn42.registry
    mnt-by:             DN42-MNT
    source:             DN42
    ...
    schema:             INETNUM-SCHEMA
    ref:                dn42.inetnum
    key:                inetnum     required  single    schema
    key:                cidr        required  single    primary
    key:                netname     required  single
    key:                nserver     optional  multiple  > [domain-name]
    key:                country     optional  multiple
    key:                descr       optional  single
    key:                status      optional  single    > {ALLOCATED|ASSIGNED} {PI|PA|}
    key:                policy      optional  single    > {open|closed|ask|reserved}
    key:                admin-c     optional  multiple  lookup=dn42.person,dn42.role
    key:                tech-c      optional  multiple  lookup=dn42.person,dn42.role
    key:                zone-c      optional  multiple  lookup=dn42.person,dn42.role
    key:                mnt-by      optional  multiple  lookup=dn42.mntner
    key:                remarks     optional  multiple
    key:                source      required  single    lookup=dn42.registry
    mnt-by:             DN42-MNT
    source:             DN42
    ...
    schema:             ROLE-SCHEMA
    ref:                dn42.role
    key:                role            required   single    schema
    key:                nic-hdl         required   single    primary
    key:                mnt-by          required   multiple  lookup=dn42.mntner
    key:                org             optional   multiple  lookup=dn42.organisation
    key:                admin-c         optional   multiple  lookup=dn42.person
    key:                tech-c          optional   multiple  lookup=dn42.person
    key:                abuse-c         optional   multiple  lookup=dn42.person
    key:                abuse-mailbox   optional   multiple
    key:                descr           optional   single
    key:                remarks         optional   multiple
    key:                source          required   single    lookup=dn42.registry
    mnt-by:             DN42-MNT
    source:             DN42
    ...
    schema:             PERSON-SCHEMA
    ref:                dn42.person
    key:                person          required   single    schema
    key:                nic-hdl         required   single    primary
    key:                mnt-by          required   multiple  lookup=dn42.mntner
    key:                org             optional   multiple  lookup=dn42.organisation
    key:                nick            optional   multiple
    key:                pgp-fingerprint optional   multiple
    key:                www             optional   multiple
    key:                e-mail          optional   multiple
    key:                contact         optional   multiple
    key:                abuse-mailbox   optional   multiple
    key:                phone           optional   multiple
    key:                fax-no          optional   multiple
    key:                address         optional   multiple
    key:                remarks         optional   multiple
    key:                source          required   single    lookup=dn42.registry
    mnt-by:             DN42-MNT
    source:             DN42
    ...
    schema:             MNTNER-SCHEMA
    ref:                dn42.mntner
    key:                mntner         required  single    primary schema
    key:                descr          optional  single
    key:                mnt-by         required  multiple  lookup=dn42.mntner
    key:                admin-c        optional  multiple  lookup=dn42.person,dn42.role
    key:                tech-c         optional  multiple  lookup=dn42.person,dn42.role
    key:                auth           optional  multiple  > [method] [value]...
    key:                org            optional  multiple  lookup=dn42.organisation
    key:                abuse-mailbox  optional  single
    key:                remarks        optional  multiple
    key:                source         required  single    lookup=dn42.registry
    mnt-by:             DN42-MNT
    source:             DN42
    ...
    schema:             REGISTRY-SCHEMA
    ref:                dn42.registry
    key:                registry   required  single    primary schema
    key:                url        required  multiple
    key:                descr      optional  multiple
    key:                mnt-by     required  multiple  lookup=dn42.mntner
    key:                admin-c    optional  multiple  lookup=dn42.person,dn42.role
    key:                tech-c     optional  multiple  lookup=dn42.person,dn42.role
    key:                source     required  single    lookup=dn42.registry
    mnt-by:             DN42-MNT
    source:             DN42
    ...
    mntner:             DN42-MNT
    descr:              mntner for owning objects in the name of whole dn42.
    mnt-by:             DN42-MNT
    source:             DN42
    ...
    inetnum:            0.0.0.0 - 255.255.255.255
    cidr:               0.0.0.0/0
    netname:            NET-BLK0-DN42
    policy:             open
    descr:              * The entire IPv4 address space
    mnt-by:             DN42-MNT
    status:             ALLOCATED
    source:             DN42
    ...
    registry:           DN42
    url:                https://git.dn42.us/dn42/registry
    mnt-by:             DN42-MNT
    source:             DN42
    .END
    """)  # noqa E501

xuu_mnt_file = clean("""
    .BEGIN XUU-MNT
    .DELETE person XUU-DN42
    inetnum:            172.21.64.0 - 172.21.64.7
    cidr:               172.21.64.0/29
    netname:            XUU-TEST-NET
    descr:              Xuu TestNet
    country:            US
    admin-c:            SOURIS-DN42
    tech-c:             SOURIS-DN42
    mnt-by:             XUU-MNT
    nserver:            lavana.sjc.xuu.dn42
    nserver:            kapha.mtr.xuu.dn42
    nserver:            rishi.bre.xuu.dn42
    status:             ALLOCATED
    remarks:            This is a transfernet.
    source:             DN42
    ...
    role:               Souris Organization Role
    abuse-mailbox:      abuse@sour.is
    admin-c:            XUU-DN42
    tech-c:             XUU-DN42
    nic-hdl:            SOURIS-DN42
    mnt-by:             XUU-MNT
    source:             DN42
    ...
    person:             Xuu
    remarks:            test
    contact:            xmpp:xuu@xmpp.dn42
    contact:            mail:xuu@dn42.us
    pgp-fingerprint:    20AE2F310A74EA7CEC3AE69F8B3B0604F164E04F
    nic-hdl:            XUU-DN42
    mnt-by:             XUU-MNT
    source:             DN42
    .
    mntner:             XUU-MNT
    descr:              Xuu Maintenance Object
    admin-c:            SOURIS-DN42
    tech-c:             SOURIS-DN42
    mnt-by:             XUU-MNT
    source:             DN42
    .END
    """)  # noqa E501


class TestTransactDOM(unittest.TestCase):
    "test TransactDOM"

    def test_transact_parse(self):
        "test tranact parsing"
        ts = TransactDOM(text=dn42_mnt_file.splitlines())

        assert ts.mntner == "DN42-MNT"
        assert len(ts.files) == 9

        ts = TransactDOM(text=xuu_mnt_file.splitlines())

        assert ts.mntner == "XUU-MNT"
        assert len(ts.files) == 4
        assert len(ts.delete) == 1
        assert ts.delete[0] == ("person", "XUU-DN42")
