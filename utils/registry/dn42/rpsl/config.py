
"RSPL Config"

import os
import os.path
from dataclasses import dataclass
from typing import Dict, Set, Tuple, Optional, TypeVar

from .filedom import FileDOM


C = TypeVar('C', bound='Config')


@dataclass
class Config:
    "RSPL Config"
    path: str
    _dom: FileDOM

    @property
    def namespace(self) -> str:
        "Get namespace"
        return self._dom.get("namespace", default="dn42").value

    @property
    def schema(self) -> str:
        "Get schema type name"
        return self._dom.get("schema", default="schema").value

    @property
    def owners(self) -> str:
        "Get owner type name"
        return self._dom.get("owner", default="mntner").value

    @property
    def source(self) -> str:
        "Get source"
        return self._dom.get("source", default="DN42").value

    @property
    def default_owner(self) -> str:
        "Get default onwer"
        return self._dom.get("default-owner", default=self._dom.mntner).value

    @property
    def network_owners(self) -> Dict[str, str]:
        "Get network owners"
        network_owner = {}  # type: Dict[str, str]
        for (parent, child) in [
                i.fields for i in self._dom.get_all("network-owner")]:
            network_owner[child] = parent
        return network_owner

    @property
    def primary_keys(self) -> Dict[str, str]:
        "Get primary keys"
        primary_keys = {}  # type: Dict[str, str]
        for (parent, key) in [
                i.fields for i in self._dom.get_all("primary-key")]:
            primary_keys[parent] = key
        return primary_keys

    @property
    def network_parents(self) -> Set[str]:
        "return network parents"
        return set(self.network_owners.values())

    @property
    def schema_dir(self) -> str:
        "get schema directory"
        return os.path.join(self.path, self.schema)

    @property
    def owner_dir(self) -> str:
        "get owner directory"
        return os.path.join(self.path, self.owners)

    @property
    def config_file(self) -> str:
        "get config file"
        return os.path.join(self.path, ".rpsl/config")

    @property
    def index_file(self) -> str:
        "get index file"
        return os.path.join(self.path, ".rpsl/index")

    @property
    def links_file(self) -> str:
        "get links file"
        return os.path.join(self.path, ".rpsl/links")

    @property
    def schema_file(self) -> str:
        "get schema file"
        return os.path.join(self.path, ".rpsl/schema")

    @property
    def nettree_file(self) -> str:
        "get nettree file"
        return os.path.join(self.path, ".rpsl/nettree")

    @classmethod
    def from_path(cls, path: str) -> C:
        "create from path"
        src = os.path.join(path, ".rpsl/config")
        return cls(FileDOM.from_file(src))

    @classmethod
    def build(cls,  # pylint: disable=too-many-arguments
              path: str,
              namespace: str = "dn42",
              schema: str = "schema",
              owners: str = "mntner",
              default_owner: str = "DN42-MNT",
              primary_keys: Optional[Set[Tuple[str, str]]] = None,
              network_owners: Optional[Set[Tuple[str, str]]] = None,
              source: str = "DN42") -> FileDOM:
        "Build config from parameters"
        FileDOM.namespace = namespace
        dom = FileDOM()
        dom.src = os.path.join(path, "config")
        dom.put("namespace", namespace)
        dom.put("schema", schema)
        dom.put("owners", owners)
        dom.put("default-owner", default_owner)
        for (k, v) in primary_keys:
            dom.put("primary-key", f"{k} {v}", append=True)
        for (k, v) in network_owners:
            dom.put("network-owner", f"{v} {k}", append=True)
        dom.put("mnt-by", default_owner)
        dom.put("source", source)

        return cls(dom)

    def __init__(self, dom: FileDOM):
        self._dom = dom
        self.path = os.path.dirname(os.path.dirname(dom.src))
        # TODO: bit of a smelly side effect. Need something better.
        FileDOM.namespace = self.namespace
        FileDOM.primary_keys = self.primary_keys

    def __str__(self):
        return self._dom.__str__()
