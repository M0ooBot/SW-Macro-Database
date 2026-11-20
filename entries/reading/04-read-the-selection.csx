// recipe-effects: read-only
// recipe-param: titleSubstring string required A substring identifying the visible part.
// recipe-param: planeName string required Exact name of the reference plane.
// recipe-param: mark int required Nonnegative selection mark.

var document = Kit.Docs.FindOpenDocument(ctx.Params.GetString("titleSubstring"))
    ?? throw new InvalidOperationException("The part must be visible and within the verified scope.");
var plane = Kit.Features.FindByName(document, ctx.Params.GetString("planeName"))
    ?? throw new InvalidOperationException("The named reference plane was not found.");
var mark = ctx.Params.GetInt("mark");
var count = 0;
var selectedType = swSelectType_e.swSelNOTHING;
Kit.Select.WithFeature(document, plane, mark, () =>
{
    var selection = (SelectionMgr)document.SelectionManager;
    count = selection.GetSelectedObjectCount2(mark);
    if (count == 1)
        selectedType = (swSelectType_e)selection.GetSelectedObjectType3(1, mark);
});
ctx.SetResult(new { count, selectedType = selectedType.ToString() });
