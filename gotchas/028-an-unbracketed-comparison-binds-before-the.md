---
id: G28
title: An unbracketed comparison binds before the arithmetic
always: false
members: []
languages: [all]
---

`IIF ( 3 >= 1 + 5 , 1 , 0 )` evaluated to **1**; `IIF ( 3 >= ( 1 + 5 ) , 1 , 0 )`
to 0. The first is what `( 3 >= 1 ) + 5` gives. Bracket both sides of every
comparison in an equation. Unary minus is also looser than `^`: `-2 ^ 2` is -4.
