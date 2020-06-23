"""RSPL Status
==============
"""


from typing import List, Dict


def run(args: List[str], env: Dict[str, str]) -> int:
    "do run"
    print("RUN STATUS", args, env)
    return 0
