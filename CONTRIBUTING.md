# Writing entries

This repo is written mostly by AI agents and read mostly by AI agents. That
makes quality control different from a normal docs repo: a confidently wrong
entry will be trusted and acted on. Changes from anyone but the owner go through
a pull request the owner reviews, but a reviewer cannot re-run your SolidWorks
session. The rules below exist to make what you write safe to trust anyway.

**If you are about to add or change an entry, read this file first and follow
the checklist at the bottom.**

---

## The one rule everything else follows from

**An entry states what is known, marked by how it is known.**

This repo's value is not that it contains code. It is that it distinguishes
code that has been observed working from code that merely looks right. Blur
that and the repo becomes worse than nothing, because it will be trusted.

## Rule 1 — Never invent an API call

If you cannot point to documentation or to code that ran, do not write the call.

Write down what is missing instead, as a limitation, and say what a person
would do by hand. [sketches/06](entries/sketches/06-what-the-sketch-api-cannot-do.md)
is the model for this: every limit is named, the manual workaround is spelled
out, and the count is stated up front.

A macro that silently does the wrong thing is worse than one that stops.

**Specifically forbidden:** plausible-looking member names, argument orders
guessed from a similar call, enum constants you have not seen, and "this should
work" code.

## Rule 2 — `status` is a claim about evidence, and it is load-bearing

| Value | Means |
|---|---|
| `verified` | It was run against SolidWorks and the result was observed. `verified_on` names the version. |
| `partly-verified` | Some of it was run. The entry says which part, in the body. |
| `unverified` | Well-formed against the documented API. Nobody has watched it run. |

`verified` requires **evidence in the entry**: the version, and what was
observed. "All 12 curves refreshed, `ForceRebuild3` returned True, the surface
rebuilt with no reference re-picked" is evidence. "This works" is not.

Do not upgrade a status because the code looks fine. Do not upgrade it because
a test passed that did not involve SolidWorks. Only running it counts.

**Downgrading is always allowed and never needs permission.** If you find
something that contradicts an entry, change the status and say what you found.

The status is the entry's whole claim, and there is one. The code an entry
shows may be in several languages; `verified_on` says what was run, so a
`verified` earned in Python reads as such. A C# recipe (below) has its own
`recipe_status`, because it is separate code that was or was not run.
`verified` also needs an observation the tools can see: `majors` named in
`verified_on`, or a passing `full` evidence record.

## Rule 3 — Code must be real

Copy it from something that ran, or generate it with the tool that generates
it. Do not paraphrase code from memory and do not tidy it on the way in.

No elisions that hide a needed line. `' ... entities here ...` is fine for a
section you describe elsewhere; dropping the `ClearSelection2` from a selection
sequence is not, because someone will copy it.

If the entry's code is longer than about 150 lines, put the full file in
[`code/`](code/) and quote the important part in the entry.

## Rule 4 — One entry answers one question

The `answers:` field is a question a future agent would actually type. Write it
first. If you cannot phrase one, you have a section of another entry, not an
entry.

Do not split a single mechanism across two entries, and do not bundle two
mechanisms into one.

## Rule 5 — Search before you write

Read [`manifest.json`](manifest.json) and grep the keywords. If an entry covers
the mechanism already, **extend it**. A second entry on the same call is worse
than no entry, because the reader gets two answers and has to choose.

If your finding contradicts an existing entry, that is not a new entry either.
Fix the old one and record what changed.

## Rule 6 — Record failures, not just successes

An entry saying "this call does not work on this interface, here is the error
number" saves as much time as one saying how to do it. Error 438 on
`InsertCurveFile` and error 429 from the wrong ProgID are two of the most useful
facts in this repo, and both are failures.

Open questions belong in the entry too, explicitly marked, with what it would
take to settle them. See the 3D arc question in
[sketches/02](entries/sketches/02-3d-sketch-as-vba.md).

## Rule 7 — Always state the units and the interface

Every entry that crosses the millimetre-to-metre boundary says which side it is
on. Every API member is attributed to the interface it lives on. Both of these
have cost real time when omitted.

## Rule 8 — Say which version, and do not generalise past it

"Verified on SolidWorks 2026" is a fact. "Works on SolidWorks" is a guess
dressed as a fact. Majors: 32 is 2024, 33 is 2025, 34 is 2026. `majors` lists
the revision majors the whole claim was run on, and only those: a part of the
claim seen "also on 2024" does not make 2024 a major of the entry.

## Rule 9 — The entry must stand alone

A reader has only this repo. No "see the fuselage project for details", no
reference to a file that is not in `code/`. Naming where something came from is
fine and useful; depending on it is not.

## Rule 10 — Do not delete evidence

If an entry turns out to be wrong, correct it and say what was wrong. Deleting
the claim loses the information that someone once believed it, which is the
thing that stops it being rediscovered.

Retire an entry by setting `superseded_by` to the id of the entry that replaced
it, and linking to that entry in the body. Keep the file and its last `status`;
the manifest shows it as `superseded`.

## Rule 11 — New code is Python or a C# recipe

Going forward, the code in a new entry is **Python** (pywin32) or a **C# recipe**
(the entry's `.csx` sidecar, below). VBA or VBScript only in an entry about VBA
or VBScript themselves. Existing VBA, VBScript, TypeScript, shell and stand-alone
C# code stays where it is: it is verified knowledge, and translating it would
need new SolidWorks runs.

## Prebuilt scripts

`scripts/` holds parameterised C# scripts for common tasks. They ship in every
release and run inside SW-Agent, the local bridge that owns the SolidWorks
connection: it hands the script `ctx`, backs up what the script declares it
will modify, and re-checks the result. C# is the only runnable format: VBScript
is deprecated, Python needs installs, and VBA macros (`.swp`) are binary and
cannot be reviewed.

Each script is a folder `scripts/<id>/` with `script.json` (what it needs and
what it does) and `script.csx` (the code). Every rule above applies, plus:

- **Link an entry.** `entry` names the entry that explains the method. A script
  is the runnable form of knowledge that already lives in an entry.
- **`status` is about this exact script.** A port of verified code is
  `unverified` until the script itself has run and been observed. `verified`
  needs a passing `full` evidence record of the script, listed in `evidence`
  (an id list); the script's majors are those of its passing records.
- **Declare effects truthfully.** `read-only`, `edits-open-document` (edits
  documents that are open, in memory, and saves nothing: exactly one param with
  `role: targets`, none with `role: output`), `writes-new-files` (only inside
  the param with `role: output`) or `modifies-models` (only the files in the
  param with `role: targets`, which the host backs up first). Set
  `irreversible: true` when undoing is impossible, such as a file-version upgrade.
- **`openTargets`** (`true` or `false`): `true` says the script may be given
  documents the user has open, because it opens and closes only through
  `Kit.Docs`, which never closes what it did not open; such a script may not
  call `OpenDoc6`, `OpenDoc7`, `LoadFile4`, `CloseDoc` or `QuitDoc` itself.
  With `false` the host refuses open targets ("close X first").
- **Use only `ctx.Sw`.** Never attach to or start SolidWorks yourself.
- **Never close a document the script did not open.** Close only what you
  opened, by its own title. `CloseAllDocuments` is refused in every script.
- **Restore any user preference you change**, in `finally`. If you cannot read
  a preference first, do not change it.
- **Report every file** through `ctx.Wrote` / `ctx.Modified`, and failures
  through `ctx.Failed`. The host fails a run that touched a file it did not
  declare.
- **Honour `ctx.DryRun`** (write nothing, log what would happen) and
  **`ctx.Cancel`** (check between files).
- Synchronous code only: no asynchronous waits, no network, no processes, no
  `#r` directives.

`python3 tools/validate.py` checks `script.json`, the evidence and the forbidden
calls.

---

## Mechanics

### Frontmatter is mandatory and machine-parsed

```yaml
---
schema: 2
id: curves-02-insert-curve-from-file
title: Insert a curve from a file as a new feature
answers: "How do I import a .sldcrv file as a feature from code?"
keywords: [InsertCurveFile, error 438]
api: [IModelDoc2.InsertCurveFile]
language: [vbscript, python]
status: verified
verified_on: SolidWorks 2026
majors: [34]
evidence: []
recipe_status: null
recipe_evidence: []
superseded_by: null
---
```

Every key is always present, in this order, and no others. One `key: value` per
line: a value is text (quote it if it starts with a quote or a bracket), `null`,
`true`/`false`, or an inline list `[a, b]`. No comments after a value.

| Key | What it holds |
|---|---|
| `schema` | `2` |
| `id` | Unique, kebab-case, stable forever. Other entries link by path, and the manifest keys on it. |
| `title` | What the entry teaches, as a noun phrase. |
| `answers` | The question a future agent would type, ending in `?`. |
| `keywords` | What someone would search for, including error numbers. Not empty. |
| `api` | Members this entry teaches, as `Interface.Member`. May be empty for a file format or a convention. |
| `language` | The code the entry shows: `python`, `csharp-standalone`, `vba`, `vbscript`, `typescript`, `shell`, `powershell`; empty when it shows none. Not `csharp`: C# that SW-Agent runs is the recipe sidecar, and any other C# is `csharp-standalone`. |
| `status` | `verified`, `partly-verified` or `unverified` (Rule 2). |
| `verified_on` | What was run, on what, as text, or `null`. |
| `majors` | The revision majors the whole claim was run on, ascending, e.g. `[32, 34]`. Each must be named in `verified_on`, as a revision (`34.1.1`) or a year (2026). |
| `evidence` | Ids of evidence records (below) for this entry. |
| `recipe_status` | The C# recipe's status, or `null` when the entry has no recipe. |
| `recipe_evidence` | Ids of evidence records for the recipe. |
| `superseded_by` | The id of the entry that replaced this one, or `null` (Rule 10). |

### Evidence records

A verification made from now on gets a record, `evidence/<id>.json`, and its id
goes in the subject's `evidence` (an entry's, a recipe's `recipe_evidence`, or a
script's `evidence` in its `script.json`). Start from
[`evidence/_TEMPLATE.json`](evidence/_TEMPLATE.json):

| Field | What it holds |
|---|---|
| `id` | The file name without `.json`, kebab-case: date, subject, language, major. |
| `subject` | The entry id or script id the record is about. |
| `language` | The code that ran: an entry `language` value, or `csharp` for a recipe or script. |
| `swRevision`, `major` | `RevisionNumber` as read (`"32.5.0"`, or `null` if only the major is known) and its major. |
| `date` | `YYYY-MM-DD`. |
| `method` | `smoke` (SW-Agent's smoke run), `contribution`, `probe` or `manual`. |
| `result`, `scope` | `pass` or `fail`; `full` (the whole claim) or `partial`. |
| `observed` | What was seen: counts, return values, errors. No paths, user names or file names: this is published. |

A failed run is recorded too (Rule 6). A subject's effective majors are its
own `majors` plus those of its passing records.

### C# recipes

A recipe is an entry's C# in the form SW-Agent runs: a script body using `ctx`
and `Kit`, in a sidecar next to the entry, `NN-slug.csx`. The sidecar exists if
and only if `recipe_status` is set. It starts with its header, before any code:

```
// recipe-effects: read-only
// recipe-param: depth number required Extrusion depth in mm.
// recipe-param: name string optional Feature name; default "Boss".
```

`recipe-effects` is exactly one of `read-only`, `edits-open-document`,
`modifies-models` or `writes-new-files`. Each `recipe-param` gives a camelCase
name, a type (`string`, `bool`, `int`, `number`, `file`, `files`, `folder`),
`required` or `optional`, and a description. The code reads its inputs only
through `ctx.Params`: the declared names, plus `targets` and `output`, which the
host supplies and which are never declared. `recipe_status: verified` needs a
passing `full` record with `method: smoke` in `recipe_evidence`.

### After any change, regenerate the manifest

```
python3 tools/build_manifest.py
```

It rebuilds [`manifest.json`](manifest.json), `gotchas.json`, `GOTCHAS.md` and
`API-LEDGER.md` from the frontmatter, the gotcha files and `api-ledger.json`, and
fails if
an entry is missing a key or has an unknown one, has a duplicate `id`, lists a
major its `verified_on` does not name, claims `verified` with no observation,
or names an evidence record that does not exist or is about something else.
Commit the regenerated files.

### Gotchas are one file each

Each gotcha is `gotchas/NNN-slug.md`, numbered as `GOTCHAS §N` is cited, with a
small frontmatter (`id`, `title`, `always`, `members`, `languages`) and a
free-form body. [GOTCHAS.md](GOTCHAS.md) and `gotchas.json` are generated from
them by `python3 tools/build_manifest.py`: never edit those two by hand. A new
gotcha takes the next free number; a retired one stays, as a stub pointing to
its replacement, so no number is reused. Start from
[`gotchas/_TEMPLATE.md`](gotchas/_TEMPLATE.md), which says what each key holds.

### The API ledger is data

[API-LEDGER.md](API-LEDGER.md) is generated from `api-ledger.json`; edit the JSON
and run `python3 tools/build_manifest.py`. A row is one call form, in its section:

| Field | What it holds |
|---|---|
| `section`, `interface` | The section's title, and its interface when the title names exactly one (else `null`). |
| `members` | Every API member the Member cell names, `Interface.Member` where the cell (or, when the cell names none, the section) gives the interface. |
| `form` | The Member cell: the call form as written. |
| `purpose`, `on` | The Purpose cell; the On cell where the section has that column (in every row of it, or none). |
| `status` | `verified`, `partly-verified`, `unverified`, `fails` (observed not to work) or `absent` (observed not to exist). |
| `note` | The Status cell's own wording whenever it says more than the status (a version, a run, a condition), or `null`: the cell shows the note, else the plain status. Change it with the status. |
| `provenance` | The run the cell cites ("dev runs 2026-09-15"), described in the ledger's preamble. |
| `languages` | Bindings the row is limited to (`csharp`, `pywin32`, `late-bound`); empty when it does not say. |
| `majors`, `evidence` | Where it was observed, and evidence record ids. |

`verified` needs `majors`, `evidence`, or the note "no version recorded" (kept for
rows whose source said only "Verified"); `fails` and `absent` keep their wording in
`note`.

### Update the cross-references

- [INDEX.md](INDEX.md) — add the row to the right task table
- [`api-ledger.json`](api-ledger.json) — add any new API member, with its status (below)
- [`gotchas/`](gotchas/) — add anything that cost you an hour, as a new file (above)
- The **See also** section of every entry the new one relates to, both directions

An entry nothing links to will not be found.

### Start from the template

[`entries/_TEMPLATE.md`](entries/_TEMPLATE.md).

### Check before you push

```
python3 tools/validate.py
```

The same check runs on every pull request and must pass before a merge. It
re-runs the manifest checks, confirms the committed `manifest.json` is current,
validates every script, and builds the release package once.

### How changes get in

- **Anyone but the owner:** fork, branch, and open a pull request against
  `main`. The owner reviews it; `main` cannot be pushed to directly.
- **Can't open a pull request?** Open a *Verification report* issue with what
  you ran and what you observed. The owner turns it into the change.
- **The owner** may push straight to `main`; the checks still run afterwards.

Never add co-author or "generated by" trailers to commits.

### Releases

The owner tags a commit on `main` as `vX.Y.Z` (SemVer). A workflow validates it,
builds `sw-macro-database-X.Y.Z.zip` (the two skills and the scripts, with
`package.json` listing every file's SHA-256 and size, the scripts, and `minKit`
from `kit.version`, the oldest SW-Agent `Kit` the release needs)
and publishes a GitHub Release whose notes list, in order, a format change, any
changed scripts, and changed entries. Building the same commit twice gives the
same bytes. SW-Agent installs a release that changes no script by itself and
holds one that does for the user's review.

---

## Checklist before you commit

- [ ] Frontmatter complete (schema 2, every key), `id` unique, `answers` is a real question
- [ ] `status` matches the evidence actually in the body; `majors` only the versions the whole claim ran on
- [ ] `verified` entries name the version and say what was observed
- [ ] New code is Python or a C# recipe (Rule 11); a new verification has its evidence record
- [ ] Every API member attributed to its interface
- [ ] Units stated wherever the boundary is crossed
- [ ] No guessed calls; limits named instead
- [ ] Code copied or generated, not recalled; complete enough to run
- [ ] Searched the manifest; not a duplicate
- [ ] Entry stands alone, with no dependency on an external repo
- [ ] `manifest.json`, `gotchas.json`, `GOTCHAS.md` and `API-LEDGER.md` regenerated
- [ ] INDEX, API-LEDGER, gotchas and See-also links updated
- [ ] Scripts: effects declared truthfully, `openTargets` set, only `ctx.Sw`, nothing closed that the script did not open, preferences restored
- [ ] `python3 tools/validate.py` passes
