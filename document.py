#!/usr/bin/env python3

import os
import sys
from ast import literal_eval

from bs4 import BeautifulSoup as Soup
from bs4.element import NavigableString, Tag

import sp_cvars

import marko
from markdownify import markdownify as md  # type: ignore


DOC_HEADER_PATTERNS: list[str] = []


def find_cvar_header(tag):
    global DOC_HEADER_PATTERNS
    is_header = lambda t: t.name in (f"h{n}" for n in range(1, 6 + 1))
    if not is_header(tag):
        return False
    if not any((p.lower() in tag.string.lower() for p in DOC_HEADER_PATTERNS)):
        return False
    for a in tag.next_siblings:
        if isinstance(a, NavigableString) and len(a.string.strip()) != 0:
            return False
        if not isinstance(a, Tag):
            continue
        if is_header(a):
            break
        if a.string is None:
            a.decompose()  # Header already has content; remove old
            break
        if len(a.string.strip()) != 0:
            return False
        break
    return True


def update_readme(cvars: list[sp_cvars.Cvar], input: str) -> str:
    if len(cvars) == 0:
        return input
    soup = Soup(marko.convert(input), features="html.parser")
    headers = soup.find_all(find_cvar_header)
    if len(headers) == 0:
        return input
    header = headers[0]
    ul_top = soup.new_tag("ul")
    trueish = lambda a: (a.isnumeric() and a != "0") or a.lower() == "true"
    for cvar in cvars:
        li_cvar = soup.new_tag("li")
        ul_cvar = soup.new_tag("ul")
        skip = False
        for i, (name, val) in enumerate(cvar.items()):
            if skip:  # Skip values we don't have
                skip = False
                continue
            skip = False

            val = val.lstrip('"').rstrip('"')
            if i == 0:
                li_cvar.string = f"<i>{val}</i>"
            else:
                if name in ("Has min", "Has max"):
                    skip = not trueish(val)
                    continue  # Skip the implicit "has mins/maxs" values
                if name == "Bit flags" and val == "0":  # Skip no bit flags
                    continue
                li_val = soup.new_tag("li")
                li_val.string = f"{name}: <code>{val}</code>"
                ul_cvar.append(li_val)
        li_cvar.append(ul_cvar)
        ul_top.append(li_cvar)
    header.insert_after(ul_top)
    return str(md(str(soup)))


if __name__ == "__main__":
    ENCODING = "utf-8"
    PATH_CODE = sys.argv[1]
    PATH_DOC = sys.argv[2]
    DOC_HEADER_PATTERNS = [a.strip() for a in sys.argv[3].split(",")]
    assert len(DOC_HEADER_PATTERNS) > 0
    for p in DOC_HEADER_PATTERNS:
        assert len(p) > 0

    CVARS = sp_cvars.parse_cvars(PATH_CODE)
    with open(PATH_DOC, mode="r", encoding=ENCODING) as f:
        DOC_INPUT = f.read()
    DOC_OUTPUT = update_readme(CVARS, DOC_INPUT)

    DRY_RUN = False
    if DRY_RUN:
        print(DOC_OUTPUT)
    elif DOC_INPUT != DOC_OUTPUT:
        with open(PATH_DOC, mode="w", encoding=ENCODING) as f:
            f.write(DOC_OUTPUT)
