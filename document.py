#!/usr/bin/env python3

import os
import sys
from ast import literal_eval

import sp_cvars

import marko
from marko.md_renderer import MarkdownRenderer


DOC_HEADER_PATTERNS: list[str] = []


def update_readme(cvars: list[sp_cvars.Cvar], input: str) -> str:
    if len(cvars) == 0:
        return input

    md = marko.Markdown(renderer=MarkdownRenderer)
    doc = md.parse(input)
    it = iter(doc.children)
    i = 0
    target = None
    while True:
        try:
            child = next(it)
            i += 1
            if not isinstance(child, marko.block.Heading):
                continue
            text = md.renderer.render_children(child)
            if any((text.lower() == p.lower() for p in DOC_HEADER_PATTERNS)):
                target = child  # Find target header
                next_child = next(it)
                # TODO: other types
                if not any(isinstance(next_child, a) for a in (marko.block.List,)):
                    print(f"Skip {type(next_child)}")
                    continue
                # Remove old content
                for _ in range(len(next_child.children)):  # type: ignore
                    next_child.children.pop()  # type: ignore
                break
        except StopIteration:
            break
    if target is None:
        return input

    rawtext = ""
    trueish = lambda a: (a.isnumeric() and a != "0") or a.lower() == "true"
    for cvar in cvars:
        skip = False
        for j, (name, val) in enumerate(cvar.items()):
            print(name, val)
            if skip:  # Skip values we don't have
                skip = False
                continue
            skip = False

            val = val.lstrip('"').rstrip('"')
            if j == 0:
                rawtext += f"* {val}\n"
            else:
                if name in ("Has min", "Has max"):
                    skip = not trueish(val)
                    continue  # Skip the implicit "has mins/maxs" values
                if name == "Bit flags" and val == "0":  # Skip no bit flags
                    continue
                rawtext += f"  * {name}: `{val}`\n"
    p = marko.block.Paragraph([])
    p.children.append(marko.inline.RawText(rawtext))  # type: ignore
    doc.children.insert(i, p)  # type: ignore
    return md.render(doc)


if __name__ == "__main__":
    ENCODING = "utf-8"
    DRY_RUN = False
    try:  # TODO: argparse
        PATH_CODE = sys.argv[1]
        PATH_DOC = sys.argv[2]
        DOC_HEADER_PATTERNS = [a.strip() for a in sys.argv[3].split(",")]
        if len(sys.argv) > 4:
            DRY_RUN = sys.argv[4] != "0"
    except IndexError:
        print(
            f'Usage: {sys.argv[0]} "<code file>" "<doc file>" "<comma-delimited list of doc header patterns>"'
        )
        print(f"Example: python {sys.argv[0]} plugin.sp README.md cvars")
        sys.exit(1)
    assert len(DOC_HEADER_PATTERNS) > 0
    for p in DOC_HEADER_PATTERNS:
        assert len(p) > 0

    CVARS = sp_cvars.parse_cvars(PATH_CODE)
    with open(PATH_DOC, mode="r", encoding=ENCODING) as f:
        DOC_INPUT = f.read()
    DOC_OUTPUT = update_readme(CVARS, DOC_INPUT)

    if DRY_RUN:
        print(DOC_OUTPUT)
    elif DOC_INPUT != DOC_OUTPUT:
        with open(PATH_DOC, mode="w", encoding=ENCODING) as f:
            f.write(DOC_OUTPUT)
