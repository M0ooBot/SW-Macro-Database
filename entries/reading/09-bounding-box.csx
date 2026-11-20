// recipe-effects: read-only

var measurements = new List<BoundingBoxInfo>();
foreach (var target in ctx.Params.GetFiles("targets"))
{
    ctx.Cancel.ThrowIfCancellationRequested();
    measurements.Add(Kit.Read.BoundingBox(SwPath.FromString(target)));
}
ctx.SetResult(measurements);
