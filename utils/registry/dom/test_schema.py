"""Test SchemaDOM"""

import inspect
import unittest

from .schema import SchemaDOM
from .filedom import FileDOM


def clean(s: str) -> str:
    "Clean input for use"
    return inspect.cleandoc(s) + "\n"


test_files = [
    ("SCHEMA-SCHEMA", clean(
        r"""
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
        remarks:            # option descriptions
                            Attribute names must match /[a-zA-Z]([a-zA-Z0-9_\-]*[a-zA-Z0-9])?/.
        +
                            required
                            :    object required to have at least one
                            optional
                            :    object not required to have at least one
        +
                            single
                            :    only one of this type allowed
                            multiple
                            :    more than one of this type allowed
        +
                            primary
                            :    use field as lookup key for lookup
                            * only one allowed per schema
                            * does not allow newlines
        +
                            schema
                            :    use field name as the name of the schema
                            * only one allowed per schema
                            * does not allow newlines
        +
                            lookup
                            :    schema match to use for related record
        """  # noqa: E501
    )),
    ("INETNUM-SCHEMA", clean(
        r"""
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
        """  # noqa: E501
    )),
    ("ROLE-SCHEMA", clean(
        r"""
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
        """  # noqa: E501
    )),
    ("PERSON-SCHEMA", clean(
        r"""
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
        """  # noqa: E501
    )),
    ("MNTNER-SCHEMA", clean(
        r"""
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
        """  # noqa: E501
    )),
    ("REGISTRY-SCHEMA", clean(
        r"""
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
        """  # noqa: E501
    )),
    ("172.21.64.0_29", clean(
        r"""
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
        """
    )),
    ("SOURIS-DN42", clean(
        r"""
        role:               Souris Organization Role
        abuse-mailbox:      abuse@sour.is
        admin-c:            XUU-DN42
        tech-c:             XUU-DN42
        nic-hdl:            SOURIS-DN42
        mnt-by:             XUU-MNT
        source:             DN42
        """
    )),
    ("XUU-DN42", clean(
        r"""
        person:             Xuu
        remarks:            test
        contact:            xmpp:xuu@xmpp.dn42
        contact:            mail:xuu@dn42.us
        pgp-fingerprint:    20AE2F310A74EA7CEC3AE69F8B3B0604F164E04F
        nic-hdl:            XUU-DN42
        mnt-by:             XUU-MNT
        source:             DN42
        """
    )),
    ("XUU-MNT", clean(
        r"""
        mntner:             XUU-MNT
        descr:              Xuu Maintenance Object
        admin-c:            SOURIS-DN42
        tech-c:             SOURIS-DN42
        mnt-by:             XUU-MNT
        source:             DN42
        """
    )),
    ("DN42-MNT", clean(
        r"""
        mntner:             DN42-MNT
        descr:              mntner for owning objects in the name of whole dn42.
        mnt-by:             DN42-MNT
        source:             DN42
        """  # noqa: E501
    )),
    ("DN42", clean(
        r"""
        registry:           DN42
        url:                https://git.dn42.us/dn42/registry
        mnt-by:             DN42-MNT
        source:             DN42
        """
    )),
    ]


class TestSchema(unittest.TestCase):
    """Test SchemaDOM
    """

    def test_schema_parse(self):
        """Test schema parsing
        """
        d = FileDOM(src="schema/SCHEMA-SCHEMA")
        d.parse(test_files[0][1].splitlines())

        self.assertEqual(str(d), test_files[0][1])
        self.assertTrue(d.valid)

        s = SchemaDOM()
        s.parse(d)

        self.assertTrue(s.valid)

        state = s.check_file(d)

        self.assertTrue(state)
        state.print()

    def test_schema_all(self):
        """Test schema failures
        """

        schemas = {}
        for (fname, text) in {
                row for row in test_files if row[0].endswith("-SCHEMA")}:
            dom = FileDOM(src=fname)
            dom.parse(text.splitlines())

            schema = SchemaDOM()
            schema.parse(dom)

            schemas[schema.ref] = schema

        files = []
        idx = {}

        for (fname, text) in test_files:
            dom = FileDOM(src=fname)
            dom.parse(text.splitlines())

            files.append(dom)

            name = dom.src.split("/")[-1].replace("_", "/")
            idx[(f"dn42.{dom.schema}", name)] = (dom.src, ",".join(dom.mntner))

        for dom in files:
            s = schemas["dn42." + dom.schema]
            state = s.check_file(dom, idx)

            self.assertTrue(state)
            state.print()
