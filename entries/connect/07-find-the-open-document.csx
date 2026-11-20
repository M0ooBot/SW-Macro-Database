// recipe-effects: read-only
// recipe-param: titleSubstring string required A case-insensitive substring of an open document's title.

var document = Kit.Docs.FindOpenDocument(ctx.Params.GetString("titleSubstring"));
ctx.SetResult(new { found = document != null, title = document?.GetTitle() });
