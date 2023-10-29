#!/usr/bin/env python3

"""Automatic Markdown documentation for SourceMod plugin ConVars."""

import argparse
import os
import re
import sys
from ast import literal_eval

import sp_cvars

import marko
from marko.md_renderer import MarkdownRenderer


VERSION = "0.1.0"


def update_readme(cvars: list[sp_cvars.Cvar], input: str, header_patterns) -> str:
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
            if header_patterns.fullmatch(text):
                target = child  # Find target header
                next_child = next(it)
                # TODO: other types
                if not any(
                    isinstance(next_child, a)
                    for a in (
                        marko.block.List,
                        marko.block.Paragraph,
                    )
                ):
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
            if skip:  # Skip values we don't have
                skip = False
                continue
            skip = False

            val = val.lstrip('"').rstrip('"')
            if j == 0:
                rawtext += f"* {val}\n"
            else:
                if name in (
                    sp_cvars.CvarName.HAS_MIN,
                    sp_cvars.CvarName.HAS_MAX,
                ):
                    skip = not trueish(val)
                    continue  # Skip the implicit "has min/max" values
                if name == sp_cvars.CvarName.FLAGS and val == "0":  # Skip no bit flags
                    continue
                rawtext += f"  * {name}: `{val}`\n"
    p = marko.block.Paragraph([])
    p.children.append(marko.inline.RawText(rawtext))  # type: ignore
    doc.children.insert(i, p)  # type: ignore
    return md.render(doc)


def main():
    parser = argparse.ArgumentParser(
        prog=sys.argv[0],
        description=__doc__,
        epilog=f"Version {VERSION}",
    )
    parser.add_argument(
        "-C",
        "--code_patterns",
        help="RegEx pattern for code files to match.",
        default=r"^.*\.(sp|inc|SP|INC)$",
    )
    parser.add_argument(
        "-D",
        "--doc_patterns",
        help="RegEx pattern for documentation files to match.",
        default=r"^.*\.(md|MD)$",
    )
    parser.add_argument(
        "-H",
        "--header_patterns",
        help="RegEx pattern for documentation headers to match for the location of the cvar docs placeholder.",
        default=r"([Cc]vars|[Cc]on[Vv]ars|[Cc]onsole [Vv]ariables)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="If set, print the output instead of writing to file.",
    )
    parser.add_argument(
        "--encoding",
        help="Encoding to use for file read/write operations.",
        default="utf-8",
    )
    args = parser.parse_args()

    path_code = None
    pattern_code = re.compile(args.code_patterns)
    for root, _, files in os.walk(os.path.dirname(os.path.realpath(__file__))):
        for file in files:
            if pattern_code.match(file):
                path_code = os.path.join(root, file)
                break
    assert path_code is not None
    assert os.path.isfile(path_code)

    path_doc = None
    pattern_doc = re.compile(args.doc_patterns)
    for root, subdirs, files in os.walk(os.path.dirname(os.path.realpath(__file__))):
        for file in files:
            if pattern_doc.match(file):
                path_doc = os.path.join(root, file)
    assert path_doc is not None
    assert os.path.isfile(path_doc)

    cvars = sp_cvars.parse_cvars(path_code)
    with open(path_doc, mode="r", encoding=args.encoding) as f:
        doc_input = f.read()
    doc_output = update_readme(cvars, doc_input, re.compile(args.header_patterns))

    if args.dry_run:
        print(f"Input differs from output: {doc_input != doc_output}")
        print(f"Length of output: {len(doc_output)}")
        print("= = = OUTPUT STARTS = = =")
        print(doc_output)
        print("= = = OUTPUT ENDS = = =")
        return

    if doc_input != doc_output:
        with open(path_doc, mode="w", encoding=args.encoding) as f:
            f.write(doc_output)


if __name__ == "__main__":
    main()
