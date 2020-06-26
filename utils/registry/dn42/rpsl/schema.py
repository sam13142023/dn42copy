"""Schema DOM"""
import re
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional, List, Tuple, Dict, Set, TypeVar

import log

from .filedom import FileDOM, Row

DOM = TypeVar("DOM", bound="FileDOM")
STATE = TypeVar("STATE", bound="State")


class Level(Enum):
    """State error level"""
    info = auto()
    warning = auto()
    error = auto()


@dataclass
class State:
    """State of schema check
    """
    state: bool = True
    msgs: List[Tuple[Level, Row, str]] = field(default_factory=list)

    def __eq__(self, other: bool) -> bool:
        return self.state == other

    def __bool__(self):
        return self.state

    def __str__(self) -> str:
        return "PASS" if self.state else "FAIL"

    def extend(self, state: STATE):
        "apply state to state"
        self.msgs.extend(state.msgs)
        self.state = state.state

    def print_msgs(self):
        """print out state info"""
        for (level, row, msg) in self.msgs:
            if level == Level.info:
                log.info(f"{row.loc} {msg}")
            elif level == Level.warning:
                log.warning(f"{row.loc} {msg}")
            elif level == Level.error:
                log.error(f"{row.loc} {msg}")

    def info(self, r: Row, s: str):
        """Add warning"""
        self.msgs.append((Level.info, r, s))

    def warning(self, r: Row, s: str):
        """Add warning"""
        self.msgs.append((Level.warning, r, s))

    def error(self, r: Row, s: str):
        """Add error"""
        self.state = False
        self.msgs.append((Level.error, r, s))


class SchemaDOM:
    """Schema DOM"""
    def __init__(self,
                 dom: FileDOM,
                 src: Optional[str] = None):
        self.valid = False
        self.name = None
        self.ref = None
        self.primary = None
        self.type = None
        self.src = src
        self._schema = {}  # type: Dict[str, Set[str]]
        self._spec = {}  # type: Dict[str, str]
        self._links = {}  # type: Dict[str, List[str]]
        self.dom = dom
        self.parse(dom)

    @property
    def links(self) -> Dict[str, List[str]]:
        "return schema links"
        return self._links

    @property
    def namespace(self) -> str:
        "get namespace"
        ns = "default"
        ref = self._dom.get("ref")
        if ref is not None:
            ns = ref.value.split(".")[0]
        return ns

    def parse(self, f: FileDOM):
        """Parse a FileDOM into a SchemaDOM"""
        self.src = self.src if f.src is None else f.src
        self._dom = f

        schema = {}
        for row in f.dom:
            if row.key == 'ref':
                self.ref = str(row.value)
            elif row.key == 'schema':
                self.name = str(row.value)

            if row.key != 'key':
                continue

            lines = row.value.fields
            key = lines.pop(0)

            schema[key] = set()
            for i in lines:
                if i == ">":
                    break
                schema[key].add(i)
                if i.startswith("lookup="):
                    self._links[key] = i.split("=", 2)[1].split(",")
            schema = self._process_schema(schema)

        self.valid = True
        self._schema = schema
        return schema

    def _process_schema(self, schema):
        for k, v in schema.items():
            if 'schema' in v:
                self.type = k

            if 'primary' in v:
                self.primary = k
                schema[k].add("oneline")
                if "multiline" in v:
                    schema[k].remove("multiline")
                schema[k].add("single")
                if "multiple" in v:
                    schema[k].remove("multiple")
                schema[k].add("required")
                if "optional" in v:
                    schema[k].remove("optional")
                if "recommend" in v:
                    schema[k].remove("recommend")
                if "deprecate" in v:
                    schema[k].remove("deprecate")

            if 'oneline' not in v:
                schema[k].add("multiline")
            if 'single' not in v:
                schema[k].add("multiple")

        return schema

    def check_file(self,
                   f: FileDOM,
                   lookups=None,
                   state: Optional[State] = None) -> State:
        """Check a FileDOM for correctness(tm)"""
        if state is None:
            state = State()

        file_state = State()
        if not f.valid:
            file_state.error(Row("", "", 0, f.src), "file does not parse")

        file_state = self._check_file_structure(file_state, f)
        file_state = self._check_file_values(file_state, f, lookups)
        file_state = inetnum_check(file_state, f)

        print("CHECK\t%-10s\t%-44s\t%s\tMNTNERS: %s" %
              (f.schema, f.src.split("/")[-1], file_state, ','.join(f.mntner)))

        state.extend(file_state)
        return state

    def _check_file_structure(self, state: State, f: FileDOM) -> State:
        for k, v in self._schema.items():
            row = Row(k, "", 0, f.src)
            if 'required' in v and k not in f.keys:
                state.error(row, "not found and is required")
            elif 'recommend' in v and k not in f.keys:
                state.info(row, "not found and is recommended")

            if 'schema' in v and f"{f.namespace}.{f.dom[0].key}" != self.ref:
                state.error(row, "not found and is required as the first line")

            if 'single' in v and k in f.keys and len(f.keys[k]) > 1:
                state.warning(row, "first defined here and has repeated keys")
                for i in f.keys[k][1:]:
                    state.error(row, f"repeated on {i} can only appear once")

            if 'oneline' in v and k in f.multi:
                for i in f.keys[k]:
                    state.error(row, "can not have multiple lines")

        return state

    def _check_file_values(self,
                           state: State,
                           f: FileDOM,
                           lookups: Optional[List[Tuple[str, str]]] = None
                           ) -> State:
        for row in f.dom:
            c = row.value.as_key

            src = "None" if f.src is None else f.src
            if row.key == self.primary and not src.endswith(c):
                state.error(row,
                            f"primary [{row.value}]" +
                            f" does not match filename [{src}].")

            if row.key.startswith("x-"):
                state.info(row, "is user defined")
                continue

            if row.key not in self._schema:
                state.error(row, "not in schema")
                continue

            if 'deprecate' in self._schema[row.key]:
                state.info(row, "was found and is deprecated")

            if lookups is not None:
                state = self._check_file_lookups(state, row, lookups)

        return state

    def _check_file_lookups(self,
                            state: State,
                            row: Row,
                            lookups: List[Tuple[str, str]] = None
                            ) -> State:
        if row.key not in self._links:
            return state

        refs = self._links[row.key]
        val = row.value.fields[0]
        found = False
        for ref in refs:
            if (ref, val) in lookups:
                found = True
        if not found:
            state.error(row,
                        f"{row.key} references object {val} " +
                        f"in {refs} but does not exist.")
        return state

    def __str__(self) -> str:
        return self._dom.__str__()

    @staticmethod
    def from_file(src: str) -> DOM:
        """Parses SchemaDOM from file"""
        with open(src, mode='r', encoding='utf-8') as f:
            dom = FileDOM(src=src, text=f.readlines())

            return SchemaDOM(dom=dom)


def inetnum_check(state: State, dom: FileDOM) -> State:
    """Sanity Check for checking the inet[6]num value"""
    if dom.schema == "inetnum" or dom.schema == "inet6num":
        cidr = dom.get("cidr").as_net
        Lnet = cidr.network_address.exploded
        Hnet = cidr.broadcast_address.exploded

        cidr_range = f"{Lnet}-{Hnet}"
        file_range = dom.get(dom.schema)
        file_range = re.sub(r"\s+", "", str(file_range), flags=re.UNICODE)

        if cidr_range != file_range:
            state.error(Row("", "", 0, dom.src),
                        f"inetnum range [{file_range}] " +
                        f"does not match: [{cidr_range}]")

    return state
