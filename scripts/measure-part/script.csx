var part = SwPath.FromString(ctx.Params.GetFile("part"));
var boundingBox = Kit.Read.BoundingBox(part);
var massProperties = Kit.Read.MassProperties(part);
ctx.SetResult(new { boundingBox, massProperties });
