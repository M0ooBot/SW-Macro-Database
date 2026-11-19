// recipe-effects: read-only
// recipe-param: depth number required Extrusion depth in mm.
// recipe-param: name string optional Feature name; default "Boss".
var depth = ctx.Params.GetNumber("depth");
var name = ctx.Params.ContainsKey("name") ? (string)ctx.Params["name"] : "Boss";
foreach (var target in ctx.Params.GetFiles("targets"))
    ctx.Log(target + name + depth);
