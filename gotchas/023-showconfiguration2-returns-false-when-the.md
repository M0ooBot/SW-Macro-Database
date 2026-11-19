---
id: G23
title: `ShowConfiguration2` returns False when the configuration is already active
always: false
members: [ShowConfiguration2, DeleteConfiguration2, DeleteDesignTable, GetConfigurationNames]
languages: [all]
---

Activating a configuration that happens to be the active one returns **False**
having done nothing wrong. In a loop over every configuration in a part, that is
exactly one false failure per part: whichever configuration the file was last
saved in.

Read the name back instead of trusting the return:

```vb
swModel.ShowConfiguration2 cfg
If swModel.ConfigurationManager.ActiveConfiguration.Name <> cfg Then
```

Same shape as §8. A SolidWorks call's return value tells you less than the state
does.

In an assembly, `ShowConfiguration2` also **marks the assembly modified** (its
`GetSaveFlag` False → True before any rebuild) and no part, and it makes every
component handle held from before stale (§108). SolidWorks 2026 (34.1.1) and
2024 SP5. See
[assemblies/13](../entries/assemblies/13-assembly-configurations-from-code.md).

Two more from the same area, both silent:

- **A design table owns its configurations.** With the table still in place,
  `DeleteConfiguration2` either fails or the configuration comes back on the
  next edit. `DeleteDesignTable` first.
- **Configurations delete in a cascade.** A derived configuration goes when its
  parent does, so a pass over a name list captured up front tries to delete
  names that are already gone. Re-read `GetConfigurationNames` each pass, and
  assert on what is left before saving.

See [files/02](../entries/files/02-explode-configurations.md).
