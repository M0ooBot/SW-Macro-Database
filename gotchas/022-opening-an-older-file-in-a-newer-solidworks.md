---
id: G22
title: Opening an older file in a newer SolidWorks makes closing it dangerous
always: true
members: [ISldWorks.CloseDoc, QuitDoc, CloseAllDocuments]
languages: [all]
---

The version upgrade alone marks the document modified, so closing prompts
*"Save changes to ...?"* — under a **"SOLIDWORKS CAM Warning"** title, which
gives no clue what is at stake. Answering **yes rewrites the file in the new
format**, in place. For a read-only pass over someone's library that is data
loss with a friendly dialog in front of it.

`CloseAllDocuments` raises this prompt. `ISldWorks.CloseDoc(title)` discards
silently, which is what a batch wants, except that on SolidWorks 2026 with the
CAM add-in loaded, `CloseDoc` and `QuitDoc` on a changed assembly saved by 2024
both raised the add-in's Yes/No box (§100).
