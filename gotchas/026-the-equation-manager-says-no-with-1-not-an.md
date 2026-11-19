---
id: G26
title: The Equation Manager says no with -1, not an exception
always: true
members: [IEquationMgr.Add3, Add2, IEquationMgr.SetEquationAndConfigurationOption]
languages: [all]
---

Three calls returned `-1` on SolidWorks 2026 and did nothing:

- `IEquationMgr.Add3` on a part with one configuration, as its help warns. Use
  `Add2(-1, text, True)`.
- `IEquationMgr.SetEquationAndConfigurationOption` changing a global. An
  indexed property put of `Equation(i)` works; from Python it needs
  `Invoke` ([connect/02](../entries/connect/02-attach-from-python.md)).
- `Add2` of a malformed equation, of one naming a global that does not exist,
  and of a dimension link added before the dimension exists. `Status` read `-1`
  after the first two (it was not read after the third); no dialog, nothing
  raised.

Check every return. See [equations/01](../entries/equations/01-global-variables-from-code.md).
