---
id: G27
title: `sqr ( 0 )` is refused, and `IIF` does not guard it
always: false
members: []
languages: [all]
---

`"x"= sqr ( 0 )` returned `-1`, and so did `IIF ( 1 > 1 , sqr ( 0 ) , 0 )`,
where the square root is on the branch that is never taken. So a formula like
`sqr ( ( a / b ) ^ 2 - 1 )` is refused whenever `a` equals `b`, however it is
wrapped. `0 ^ 0.5` evaluated to 0. Write square roots as `( ... ) ^ 0.5`. See
[equations/01](../entries/equations/01-global-variables-from-code.md).
