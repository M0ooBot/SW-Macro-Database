// recipe-effects: writes-new-files
// recipe-param: fileName string required STEP filename including extension, with no folder components.

Kit.Prefs.With(swUserPreferenceIntegerValue_e.swStepAP, 214, () =>
{
    Kit.Docs.Export(ctx.Params.GetFiles("targets")[0], Path.Combine(ctx.Params.GetFolder("output"), ctx.Params.GetString("fileName")));
});
