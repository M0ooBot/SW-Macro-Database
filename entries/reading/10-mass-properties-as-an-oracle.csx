// recipe-effects: read-only

var measurements = new List<MassPropertiesInfo>();
foreach (var target in ctx.Params.GetFiles("targets"))
{
    ctx.Cancel.ThrowIfCancellationRequested();
    measurements.Add(Kit.Read.MassProperties(SwPath.FromString(target)));
}
ctx.SetResult(measurements);
