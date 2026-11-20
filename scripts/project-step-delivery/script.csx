var source = ctx.Params.GetFile("model");
var outputFolder = ctx.Params.GetFolder("deliverables");
var outputName = ctx.Params.GetString("fileName");
Kit.Prefs.With(swUserPreferenceIntegerValue_e.swStepAP, ctx.Params.GetInt("stepProtocol"), () =>
{
    var destination = Path.Combine(outputFolder, outputName);
    ctx.Log($"Exporting {source} to {destination}");
    Kit.Docs.Export(source, destination);
});
