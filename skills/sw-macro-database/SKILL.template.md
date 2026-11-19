---
name: sw-macro-database
description: Proven SolidWorks automation knowledge (COM/API recipes, gotchas, an API ledger), each marked verified or unverified against a real SolidWorks. Use before writing, running or debugging any SolidWorks automation, and when a SolidWorks API call fails or behaves oddly.
---

# SolidWorks macro database (v{{VERSION}})

This skill answers one question: **has this SolidWorks automation problem already
been solved, and is the solution trustworthy?** Check here before writing any
SolidWorks code, so a fresh session does not rediscover what is already known.

## Looking something up

With SW-Agent's tools available, use them: `db_search` finds entries,
`db_entry` reads one (its C# recipe when it has one), `api_status` says whether
an API member is proven, and `gotchas_for` returns the gotchas for the members
you are about to call. SW-Agent's own skill says how.

Without them, everything is in this folder:

1. `python3 lookup.py "what you want to do"` ranks the entries; add
   `--gotchas "topic"` to search the gotchas, `--always` for the always-list,
   `--json` for machine-readable output. It needs Python 3.9 or later whose
   SQLite has FTS5 (python.org and Ubuntu builds do). Without Python, scan the
   index below, or `manifest.json` for keywords and API members.
2. If an entry matches, read it in full (`entries/…`). Entries are
   self-contained; longer code lives under `code/`, linked from the entry.
3. To check whether one API member is proven, look it up in `api-ledger.json`
   (or read `API-LEDGER.md`, generated from it).
4. Before writing any SolidWorks automation, read the always-list below, then
   `GOTCHAS.md`: most of it is failure modes that are silent.
5. For a common task, check the prebuilt scripts below before writing code.

## How to read status

Every entry has one `status`, a claim about the entry as a whole:

| Value | What you may do with it |
|---|---|
| `verified` | Use it. It ran against the SolidWorks named in `verified_on`. |
| `partly-verified` | Use it, and check the entry for which part is proven. |
| `unverified` | A good starting point. Test it before relying on it, and say it is untested. |
| `superseded` | Do not use. Follow `superseded_by` to what replaced it. |

`verified_on` says what was run, and on what: a `verified` earned in Python is
a Python run. `majors` lists the SolidWorks revision majors it ran on (32 =
2024, 33 = 2025, 34 = 2026); on another major the evidence is weaker, so say so.
An entry with a C# recipe (`recipe` in the manifest, a `.csx` beside the entry)
gives the recipe its own status: that is the status of the code SW-Agent runs.
Evidence records (`evidence/`) say what each newer verification observed.

Do not trust an entry more than its `status` says just because the code reads
well. That distinction is this collection's whole value.

**Never invent an API call.** If the database does not cover something and you
cannot point to documentation, say what is missing instead of guessing member
names, argument orders or enum values.

## Always-list

The gotchas to keep in mind in any SolidWorks automation, whatever the
language. The rest are in `GOTCHAS.md`, by number, as `GOTCHAS §N` cites them.

{{ALWAYS}}

## If the answer is not here

Say so plainly rather than improvising something that looks like an entry. If
you then solve it against a real SolidWorks, or prove an `unverified` entry or
script works, use the `sw-macro-contribute` skill to write it back.

## Prebuilt scripts

Parameterised C# scripts for common tasks, in the release package's top-level
`scripts/` folder, next to `skills/`; SW-Agent lists them with `scripts_list`.
Each links to the entry that explains its method. Status works as for entries:
an `unverified` script has not run in this form yet.

{{SCRIPTS}}

## Index

{{INDEX}}
