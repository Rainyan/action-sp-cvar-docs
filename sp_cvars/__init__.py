#!/usr/bin/env python3

import os
import re
import sys
from enum import StrEnum


class CvarName(StrEnum):
    NAME = "Name"
    DEFAULT = "Default value"
    DESCRIPTION = "Description"
    FLAGS = "Bit flags"
    HAS_MIN = "Has min"
    MIN = "Min"
    HAS_MAX = "Has max"
    MAX = "Max"


class Cvar:
    def __init__(self, input) -> None:
        self._i: int = 0

        input = input.replace("\\\n", " ")  # C line continuations

        parms: list[str] = []
        add_parm = lambda a, b: a.append(b if b == "_" else f'"{b}"')

        in_str = False
        prev_c = None
        buffer = ""
        for i, c in enumerate(input):
            if len(c.strip()) == 0 and len(buffer.strip()) == 0:
                prev_c = None
                continue
            if c == '"' and prev_c != "\\":
                in_str = not in_str
                if not in_str:
                    add_parm(parms, buffer.strip())
                    buffer = ""
            elif c == "," and not in_str:
                if len(buffer) > 0:
                    add_parm(parms, buffer.strip())
                    buffer = ""
                else:
                    prev_c = c
                    continue
            else:
                buffer += c
            if i + 1 == len(input):
                add_parm(parms, buffer.strip())
                break
            prev_c = c
        parms = ["" if p == "_" else p.strip() for p in parms]

        self._name: str = "".join(parms[0:1])
        self._default_value: str = "".join(parms[1:2])
        self._description: str = "".join(parms[2:3])
        self._flags: str = "".join(parms[3:4])
        self._has_min: str = "".join(parms[4:5])
        self._min: str = "".join(parms[5:6])
        self._has_max: str = "".join(parms[6:7])
        self._max: str = "".join(parms[7:8])

        if len(self._flags) == 0:
            self._flags = '"0"'
        if len(self._has_min) == 0:
            self._has_min = '"false"'
        if len(self._min) == 0:
            self._min = '"0.0"'
        if len(self._has_max) == 0:
            self._has_max = '"false"'
        if len(self._max) == 0:
            self._max = '"0.0"'

    def __iter__(self):
        return self

    def __repr__(self) -> str:
        return repr(vars(self))

    @staticmethod
    def keys():
        return [
            CvarName.NAME,
            CvarName.DEFAULT,
            CvarName.DESCRIPTION,
            CvarName.FLAGS,
            CvarName.HAS_MIN,
            CvarName.MIN,
            CvarName.HAS_MAX,
            CvarName.MAX,
        ]

    def values(self):
        return [
            self.name,
            self.default_value,
            self.description,
            self.flags,
            self.has_min,
            self.min,
            self.has_max,
            self.max,
        ]

    def items(self):
        return [(a, b) for a, b in zip(self.keys(), self.values())]

    def __next__(self):
        i = self._i
        self._i += 1
        try:
            return self.values()[i]
        except IndexError:
            self._i = 0
            raise StopIteration

    @property
    def name(self) -> str:
        return self._name

    @property
    def default_value(self) -> str:
        return self._default_value

    @property
    def description(self) -> str:
        return self._description

    @property
    def flags(self) -> str:
        return self._flags

    @property
    def has_min(self) -> str:
        return self._has_min

    @property
    def min(self) -> str:
        return self._min

    @property
    def has_max(self) -> str:
        return self._has_max

    @property
    def max(self) -> str:
        return self._max


def parse_cvars(filepath: os.PathLike | str) -> list[Cvar]:
    with open(filepath, mode="r", encoding="utf-8") as f:
        code = f.read()
    name = "CreateConVar"
    return [Cvar(a) for a in re.findall(rf"{name}\((.*?)\);", code, flags=re.DOTALL)]


if __name__ == "__main__":
    print(parse_cvars(sys.argv[1]))
