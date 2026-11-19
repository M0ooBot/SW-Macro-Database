---
id: G9
title: Rebuilding per change is both slow and wrong
always: false
members: []
languages: [all]
---

Update twelve curves with the rebuild live and you get a real but transient
error partway through, because mid-refresh some curves carry the old geometry
and some the new, so a surface over them genuinely does not close. Suppress,
change everything, restore, rebuild once.

**Restore the flag in a `finally`.** A document left suppressed looks fine and
silently stops updating, which is about the worst state to hand back to
someone. See [curves/08](../entries/curves/08-rebuild-once-at-the-end.md).
