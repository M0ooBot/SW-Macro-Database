// recipe-effects: modifies-models
// recipe-param: feature string required Exact name of the existing top-level feature.
// recipe-param: newName string required Unoccupied name for the renamed feature.

Kit.Docs.EditClosedPart(ctx.Params.GetFiles("targets")[0], part =>
{
    using (Kit.Batch(part))
    {
        Kit.Features.Rename(part, ctx.Params.GetString("feature"), ctx.Params.GetString("newName"));
    }
    Kit.Docs.Save(part);
});
