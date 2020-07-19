"Metafile"
from dataclasses import dataclass
from typing import Sequence, Generator

from .rspl import RPSL
from .file import Value


@dataclass
class MetaFile:
    "file"
    obj_type: str
    obj_name: str


class MetaDOM:
    "metafile dom"
    def __init__(self, lis: Sequence[MetaFile], rpsl: RPSL):
        self.lis = lis
        self.rpsl = rpsl

    def get(self, name: str) -> Generator[Value, None, None]:
        "get values"
