---
id: G114
title: `ShowConfiguration2` can raise and still switch
always: false
members: [ShowConfiguration2, ForceRebuild3]
languages: [all]
---

On an assembly with an in-context part, `ShowConfiguration2` and the
`ForceRebuild3` after it raised "The server threw an exception" (−2147417851) on
some switches while the configuration did change. Catch it and read
`ActiveConfiguration.Name`. §109 saw the same exception from `SetSuppression2`. SolidWorks 2024 SP5 (32.5.0). See
[assemblies/07](../entries/assemblies/07-configurations-that-hold-different-positions.md#showconfiguration2-and-forcerebuild3-can-raise-and-still-succeed).
