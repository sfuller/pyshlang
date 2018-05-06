import os
import sys
from typing import List, Tuple


class InvokeInfo(object):
    def __init__(self, arguments: List[str], env: List[Tuple[str, str]], stdin: str, pwd: str) -> None:
        self.arguments = arguments
        self.env = env
        self.stdin = stdin
        self.pwd = pwd


def ls(info: InvokeInfo) -> int:
    entries = os.listdir(info.pwd)
    print('\n'.join(entries))
    return 0


def exit(info: InvokeInfo) -> int:
    rv = 0
    if len(info.arguments) > 0:
        try:
            rv = int(info.arguments[0])
        except ValueError:
            pass
    sys.exit(rv)


def echo(info: InvokeInfo) -> int:
    print(' '.join(info.arguments))
    return 0


def true(info: InvokeInfo) -> int:
    return 0


def false(info: InvokeInfo) -> int:
    return 1
