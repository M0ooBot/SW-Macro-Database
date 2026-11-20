// recipe-effects: modifies-models
// recipe-param: feature string required Exact name of the existing top-level feature.
// recipe-param: folder string required Unoccupied name for the new feature-tree folder.

Kit.Docs.EditClosedPart(ctx.Params.GetFiles("targets")[0], part =>
{
    using (Kit.Batch(part))
    {
        Kit.Features.GroupInFolder(part, ctx.Params.GetString("feature"), ctx.Params.GetString("folder"));
    }
    Kit.Docs.Save(part);
});
