#!/usr/bin/env python3

"""Automatic Markdown documentation for SourceMod plugin ConVars."""

import argparse
import os
import re
import sys
from typing import Optional

import marko
from marko.md_renderer import MarkdownRenderer

import sp_cvars


VERSION = "0.1.0"


def purge_readme(
    md: marko.Markdown, input: str, header_patterns
) -> Optional[marko.block.Document]:
    doc = md.parse(input)  # type: ignore
    it = iter(doc.children)
    i = 0
    target = None
    while True:
        try:
            child = next(it)
            i += 1
            if not isinstance(child, marko.block.Heading):
                continue
            text = md.renderer.render_children(child)  # type: ignore
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
    return doc if target is not None else None


def update_readme(
    md: marko.Markdown,
    codes_cvars: dict[str, list[sp_cvars.Cvar]],
    doc: marko.block.Document,
    header_patterns,
    format_filename: str,
    format_cvarname: str,
    format_cvarprop: str,
) -> str:
    for i, child in enumerate(doc.children, start=1):
        if not isinstance(child, marko.block.Heading):
            continue
        text = md.renderer.render_children(child)  # type: ignore
        if header_patterns.fullmatch(text):
            target = child  # Find target header
            break
    else:
        return md.render(doc)

    trueish = lambda a: (a.isnumeric() and a != "0") or a.lower() == "true"

    rawtext = ""
    for filename, cvars in codes_cvars.items():
        if len(cvars) == 0:  # Skip cvars docs for code files with no cvars
            continue
        if len(codes_cvars) > 1:
            rawtext += format_filename.replace("!a!", filename)
        for cvar in cvars:
            skip = False
            for j, (name, val) in enumerate(cvar.items()):
                if skip:  # Skip values we don't have
                    skip = False
                    continue
                skip = False

                val = val.lstrip('"').rstrip('"')
                if j == 0:
                    rawtext += format_cvarname.replace("!a!", val)
                else:
                    if name in (
                        sp_cvars.CvarName.HAS_MIN,
                        sp_cvars.CvarName.HAS_MAX,
                    ):
                        skip = not trueish(val)  # Skip when no min/max set
                        continue  # Skip the implicit "has min/max" values
                    if name == sp_cvars.CvarName.FLAGS and val == "0":
                        continue  # Skip no bit flags
                    rawtext += format_cvarprop.replace("!a!", name).replace("!b!", val)
    rawtext.replace("\\n", "\n")

    p = marko.block.Paragraph([])
    p.children.append(marko.inline.RawText(rawtext))  # type: ignore
    doc.children.insert(i, p)  # type: ignore
    return md.render(doc)


def main() -> None:
    parser = argparse.ArgumentParser(
        prog=sys.argv[0],
        description=__doc__,
        epilog=f"Version {VERSION}",
    )
    parser.add_argument(
        "cwd",
        help="Current working directory.",
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
        help="If set, print the output to stdout instead of writing to file.",
    )
    parser.add_argument(
        "--encoding",
        help="Encoding to use for file read/write operations.",
        default="utf-8",
    )
    parser.add_argument(
        "--format-filename",
        help="Formatting for the code file name, with placeholder !a!. This is skipped if parsing one single code file.",
        default="### !a!\n",
    )
    parser.add_argument(
        "--format-cvarname",
        help="Formatting for the cvar name, with placeholder !a!.",
        default="* !a!\n",
    )
    parser.add_argument(
        "--format-cvarprop",
        help="Formatting for the cvar property, with placeholder !a! (property name), and !b! (property default value).",
        default="  * !a!: `!b!`\n",
    )
    args = parser.parse_args()

    print(rf"{args.format_filename=}")
    print(rf"{args.format_cvarname=}")
    print(rf"{args.format_cvarprop=}")

    working_dir = (
        os.path.dirname(os.path.realpath(__file__)) if args.cwd == "" else args.cwd
    )
    assert os.path.isdir(working_dir)

    path_codes: list[os.PathLike | str] = []
    pattern_code = re.compile(args.code_patterns)
    for root, _, files in os.walk(working_dir):
        for file in files:
            if pattern_code.match(file):
                p = os.path.join(root, file)
                assert os.path.isfile(p)
                path_codes.append(p)
    assert len(path_codes) > 0

    path_doc = None
    pattern_doc = re.compile(args.doc_patterns)
    for root, _, files in os.walk(working_dir):
        for file in files:
            if pattern_doc.match(file):
                path_doc = os.path.join(root, file)
                break
    assert path_doc is not None
    assert os.path.isfile(path_doc)

    with open(path_doc, mode="r", encoding=args.encoding) as f:
        doc_input = f.read()

    md = marko.Markdown(renderer=MarkdownRenderer)
    pattern_headers = re.compile(args.header_patterns)
    if (doc := purge_readme(md, doc_input, pattern_headers)) is None:
        return
    codes_cvars = {os.path.basename(a): sp_cvars.parse_cvars(a) for a in path_codes}

    doc_output = update_readme(
        md,
        codes_cvars,
        doc,
        pattern_headers,
        args.format_filename,
        args.format_cvarname,
        args.format_cvarprop,
    )
    if args.dry_run:
        print(doc_output)
        return
    if doc_input != doc_output:
        with open(path_doc, mode="w", encoding=args.encoding) as f:
            f.write(doc_output)


if __name__ == "__main__":
    main()
