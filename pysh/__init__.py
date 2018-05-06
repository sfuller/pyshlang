import sys

from pysh.interactive import Interactive


def main() -> None:
    instance = Interactive()
    sys.exit(instance.main())
