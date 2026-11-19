"""The header of an entry's C# recipe sidecar (entries/<category>/NN-slug.csx).

A recipe is the code SW-Agent runs for an entry: a script body with `ctx` and
`Kit`. It starts with header lines, one per line, before any code:

    // recipe-effects: read-only
    // recipe-param: depth number required Extrusion depth in mm.
    // recipe-param: name string optional Feature name; default "Boss".

- `recipe-effects`: exactly one, one of EFFECTS.
- `recipe-param`: zero or more: a camelCase name (not `targets` or `output`, which
  the host synthesises), a type, `required` or `optional`, then the description.

The body may read `ctx.Params` only for declared names and the two role names.
That is a regular-expression check; compiling the recipe is the real one.
Python 3 stdlib only.
"""

from __future__ import annotations

import re

EFFECTS = {"read-only", "edits-open-document", "modifies-models", "writes-new-files"}
PARAM_TYPES = {"string", "bool", "int", "number", "file", "files", "folder"}
ROLE_NAMES = {"targets", "output"}
CAMEL = re.compile(r"^[a-z][A-Za-z0-9]*$")

HEADER = re.compile(r"^// recipe-([A-Za-z0-9-]+):[ \t]*(.*?)\s*$")
PARAMS_READ = [
    re.compile(r'ctx\.Params\s*\[\s*"([^"]*)"\s*\]'),
    re.compile(r'ctx\.Params\s*\.\s*Get\w*\s*(?:<[^>()]*>)?\s*\(\s*"([^"]*)"'),
]


def parse(text: str):
    """(header, problems). header is {"effects": str | None, "params": [...]}."""
    problems: list[str] = []
    effects: list[str] = []
    params: list[dict] = []
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    i = 0
    while i < len(lines) and lines[i].startswith("// recipe-"):
        n, line = i + 1, lines[i]
        i += 1
        m = HEADER.match(line)
        if not m:
            problems.append(f"line {n}: a header line is '// recipe-<key>: <value>'")
            continue
        key, value = m.group(1), m.group(2)
        if key == "effects":
            if value not in EFFECTS:
                problems.append(f"line {n}: recipe-effects {value!r} is not one of {sorted(EFFECTS)}")
            effects.append(value)
        elif key == "param":
            parts = value.split(None, 3)
            if len(parts) < 4:
                problems.append(f"line {n}: recipe-param is '<name> <type> required|optional <description>'")
                continue
            name, ptype, req, desc = parts
            if not CAMEL.match(name):
                problems.append(f"line {n}: param name {name!r} must be camelCase")
            elif name in ROLE_NAMES:
                problems.append(f"line {n}: param name {name!r} is a role name the host supplies; do not declare it")
            elif any(p["name"] == name for p in params):
                problems.append(f"line {n}: param {name!r} declared twice")
            if ptype not in PARAM_TYPES:
                problems.append(f"line {n}: param type {ptype!r} is not one of {sorted(PARAM_TYPES)}")
            if req not in ("required", "optional"):
                problems.append(f"line {n}: write 'required' or 'optional', not {req!r}")
            params.append({"name": name, "type": ptype, "required": req == "required", "description": desc})
        else:
            problems.append(f"line {n}: unknown header key 'recipe-{key}'")
    if len(effects) != 1:
        problems.append(f"the header needs exactly one '// recipe-effects:' line (found {len(effects)})")
    for n, line in enumerate(lines[i:], i + 1):
        if line.lstrip().startswith("// recipe-"):
            problems.append(f"line {n}: header lines go first, before any code")
    header = {"effects": effects[0] if len(effects) == 1 else None, "params": params}
    return header, problems


def check(text: str):
    """parse(), plus: the body reads ctx.Params only for declared names and the role names."""
    header, problems = parse(text)
    declared = {p["name"] for p in header["params"]} | ROLE_NAMES
    body = "\n".join(l for l in text.replace("\r\n", "\n").split("\n") if not l.startswith("// recipe-"))
    for rx in PARAMS_READ:
        for m in rx.finditer(body):
            if m.group(1) not in declared:
                problems.append(f"reads ctx.Params {m.group(1)!r}, which the header does not declare")
    return header, problems
