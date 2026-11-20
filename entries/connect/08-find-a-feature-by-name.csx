// recipe-effects: read-only
// recipe-param: titleSubstring string required A case-insensitive substring of an open document's title.
// recipe-param: featureName string required The exact, case-sensitive feature name.

var document = Kit.Docs.FindOpenDocument(ctx.Params.GetString("titleSubstring"))
    ?? throw new InvalidOperationException("No open target matches the requested title.");
var feature = Kit.Features.FindByName(document, ctx.Params.GetString("featureName"));
ctx.SetResult(new { found = feature != null, name = feature?.Name, type = feature?.GetTypeName2() });
