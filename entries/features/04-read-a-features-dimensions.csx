// recipe-effects: modifies-models
// recipe-param: dimension string required Fully qualified name of the driving dimension.
// recipe-param: metres number required Positive finite dimension value in metres.

Kit.Docs.EditClosedPart(ctx.Params.GetFiles("targets")[0], part =>
{
    using (Kit.Batch(part))
    {
        Kit.Features.SetDrivingDimension(part, ctx.Params.GetString("dimension"), ctx.Params.GetNumber("metres"));
    }
    Kit.Docs.Save(part);
});
