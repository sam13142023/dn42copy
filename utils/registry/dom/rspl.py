"RPSL"

import os
import os.path
from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple, TypeVar

from .filedom import FileDOM
from .nettree import NetTree
from .schema import SchemaDOM


C = TypeVar('C', bound='RPSLConfig')


@dataclass
class RPSLConfig:
    "RSPLConfig"
    namespace: str
    root: str
    schema: str
    owners: str
    default_owner: str
    source: str
    network_owner: Set[Tuple[str, str]] = field(default_factory=set)
    primary_key: Set[Tuple[str, str]] = field(default_factory=set)

    @property
    def network_parents(self) -> Set[str]:
        "return network parents"
        return set(self.network_owner.values())

    @property
    def schema_dir(self) -> str:
        "get schema directory"
        return os.path.join(self.root, self.schema)

    @property
    def owner_dir(self) -> str:
        "get owner directory"
        return os.path.join(self.root, self.owners)

    @property
    def config_file(self) -> str:
        "get config file"
        return os.path.join(self.root, ".rpsl/config")

    @staticmethod
    def default() -> C:
        "create default"
        root = os.getcwd()
        return RPSLConfig("dn42", root, "schema", "mntner", "DN42-MNT", "DN42",
                          {}, {})

    @staticmethod
    def from_dom(dom: FileDOM) -> C:
        "create from dom"
        ns = dom.get("namespace", default="dn42").value
        schema = dom.get("schema", default="schema").value
        owners = dom.get("owners", default="mntner").value
        source = dom.get("source", default="DN42").value
        default_owner = dom.get("default-owner", default=dom.mntner).value

        root = os.path.dirname(dom.src)

        network_owner = {}  # type: Dict[str, str]
        for (parent, child) in [
                i.fields for i in dom.get_all("network-owner")]:
            network_owner[child] = parent

        primary_key = {}  # type: Dict[str, str]
        for (parent, child) in [
                i.fields for i in dom.get_all("primary-key")]:
            primary_key[child] = parent

        return RPSLConfig(namespace=ns,
                          root=root,
                          schema=schema,
                          owners=owners,
                          source=source,
                          default_owner=default_owner,
                          network_owner=network_owner,
                          primary_key=primary_key,
                          )

    def __str__(self):
        dom = FileDOM(ns=self.namespace)
        dom.put("namespace", self.namespace)
        dom.put("schema", self.schema)
        dom.put("owners", self.owners)
        dom.put("default-owner", self.default_owner)
        for (k, v) in self.primary_key:
            dom.put("primary-key", f"{k} {v}", append=True)
        for (k, v) in self.network_owner:
            dom.put("network-owner", f"{v} {k}", append=True)
        dom.put("mnt-by", self.default_owner)
        dom.put("source", self.source)

        return dom.__str__()


R = TypeVar('R', bound="RPSL")


@dataclass
class RSPL:
    "RSPL"
    config: RPSLConfig
    files: List[FileDOM]
    nettree: NetTree
    schema: Dict[str, SchemaDOM]

    @staticmethod
    def from_index(path: str) -> R:
        "Create RSPL from indexs"

    @staticmethod
    def from_files(path: str, schema_only: bool = False) -> R:
        "Create RSPL from files"
