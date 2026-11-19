---
id: G7
title: `Marshal.GetActiveObject` does not exist on modern .NET
always: false
members: [GetActiveObject]
languages: [csharp]
---

It was dropped after .NET Framework. On .NET 8 you P/Invoke `GetActiveObject`
from `oleaut32.dll` yourself, or walk the Running Object Table via
`GetRunningObjectTable` and `CreateBindCtx` from `ole32.dll`. Both are in
[`code/csharp/ComActivation.cs`](../code/csharp/ComActivation.cs).
