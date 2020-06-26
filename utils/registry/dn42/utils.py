"DN42 Utils"
import os.path
from typing import List, Tuple


def remove_prefix(text, prefix):
    "remove the prefix"
    if text.startswith(prefix):
        return text[len(prefix):]
    return text


def shift(args: List[str]) -> Tuple[str, List[str]]:
    "shift off first arg + rest"
    if len(args) == 0:
        return None, []

    if len(args) == 1:
        return args[0], []

    return args[0], args[1:]


def find_rpsl(path: str) -> str:
    "Find the root directory for RPSL"
    path = os.path.abspath(path)
    rpsl = os.path.join(path, ".rpsl")
    while not os.path.exists(rpsl):
        if path == "/":
            break
        path = os.path.dirname(path)
        rpsl = os.path.join(path, ".rpsl")

    if not os.path.exists(rpsl):
        return None

    return path


def exists(*args: str) -> bool:
    "check if files exist"
    for i in args:
        if not os.path.exists(i):
            return False
    return True
