"spec"
from dataclasses import dataclass
from typing import Dict, List, Enum

class Rule:
    pass


@dataclass
class LabelRule(Rule):
    name: str

    def parse(self, fields: Sequence[str]) -> Optional[Tuple[str, str]]:

@dataclass
class Spec:
    keys: Dict[str, SpecRule]

    @classmethod
    def from_dom(cls, dom: file.FileDOM):
        for key in
