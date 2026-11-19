// recipe-effects: modifies-models
// recipe-param: depth number required Extrusion depth in mm.
var depth = ctx.Params.GetNumber("depth");
var width = ctx.Params["width"];
var height = ctx.Params.Get<double>("height");
var output = ctx.Params.GetFolder("output");
