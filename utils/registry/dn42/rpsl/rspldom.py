"RPSL"

import os.path
from typing import Dict, List, Tuple, TypeVar, Optional, Generator

from .filedom import FileDOM
from .nettree import NetTree
from .schema import SchemaDOM, State
from .transact import TransactDOM
from .config import Config

R = TypeVar('R', bound="RPSL")


class RPSL:
    "RSPL"

    def __init__(self, config: Config):
        self._config = config
        self._files = {}  # type: Dict[Tuple[str, str], str]
        self._lookup = {}  # type: Dict[str, List[Tuple[str, str]]]
        self._links = {}  \
            # type: Dict[Tuple[str, str], List[Tuple[str, str, str]]]
        self._nettree = None  # type: NetTree
        self._schema = {}  # type: Dict[str, SchemaDOM]
        self._load_index()

    def _load_index(self):
        with open(self._config.index_file) as fd:
            for line in fd.readlines():
                sp = line.strip().split(sep="|")
                self._files[(sp[0], sp[1])] = sp[2]
                self._lookup[sp[1]] = self._lookup.get(sp[1], [])
                self._lookup[sp[1]].append((sp[0], sp[1]))

        with open(self._config.links_file) as fd:
            for line in fd.readlines():
                sp = line.strip().split(sep="|")
                key = (sp[0], sp[1])
                arr = self._links.get(key, [])
                arr.append((sp[2], sp[3], sp[4]))
                self._links[key] = arr

        self._nettree = NetTree.read_csv(self._config.nettree_file)

        files = TransactDOM.from_file(self._config.schema_file)
        for schema in files.schemas:
            self._schema[schema.ref] = schema

    def append_index(self, dom: FileDOM):
        "append files to index"
        key, value = dom.index
        self._lookup[key] = value

    def scan_files(self, files: List[FileDOM]) -> State:
        "scan files for schema errors"
        state = State()
        for dom in files:
            s = self._schema.get(dom.rel)
            if s is None:
                state.warning(dom.dom[0],
                              f"{dom.src} schema not found for {dom.rel}")
                continue

            state = s.check_file(dom, lookups=self._files, state=state)
        return state

    def find(self,
             text: str,
             schema: Optional[str] = None) -> Generator[FileDOM, None, None]:
        "Find files that match text and schema"
        keys = [(schema, text)]
        if schema is None:
            keys = self._lookup.get(text, [])

        related = set()

        for i in keys:
            yield self.load_file(self._files[i])
            for link in self.links(i):
                key = (link[1], link[2])
                related.add(key)

        for i in related:
            if i in keys:
                continue
            yield self.load_file(self._files[i])

    def load_file(self, fn: str) -> FileDOM:
        "load file"
        fn = os.path.join(self._config.path, fn)
        fo = FileDOM.from_file(fn)
        fo.namespace = self._config.namespace
        fo.primary_keys = self._config.primary_keys

        return fo

    def links(self, key: Tuple[str, str]) -> List[Tuple[str, str]]:
        "get links"
        return self._links.get(key, [])
