// recipe-effects: read-only
// recipe-param: path string required Full path of the already loaded part document.
// recipe-param: configuration string required Expected configuration referenced by the assembly occurrence.

var path = ctx.Params.GetString("path");
var configuration = ctx.Params.GetString("configuration");
var model = ctx.Sw.GetOpenDocumentByName(path) as ModelDoc2
    ?? throw new InvalidOperationException($"Part is not loaded: {path}");
if (model is not PartDoc part)
    throw new InvalidOperationException($"Expected a part: {path}");

var activeConfiguration = model.ConfigurationManager.ActiveConfiguration.Name;
if (!StringComparer.OrdinalIgnoreCase.Equals(activeConfiguration, configuration))
    throw new InvalidOperationException($"Active part configuration '{activeConfiguration}' differs from assembly reference '{configuration}'.");

var bodies = part.GetBodies2((int)swBodyType_e.swSolidBody, false) as object[] ?? Array.Empty<object>();
using var mesh = new MemoryStream();
using var writer = new BinaryWriter(mesh);
writer.Write(new byte[84]);
var triangleCount = 0;
var degenerateCount = 0;
var volumeMm3 = 0.0;
foreach (Body2 body in bodies)
{
    ctx.Cancel.ThrowIfCancellationRequested();
    var tessellation = body.GetTessellation(null) as Tessellation
        ?? throw new InvalidOperationException("SolidWorks did not create a tessellation.");
    tessellation.MatchType = (int)swTesselationMatchType_e.swTesselationMatchFacetTopology;
    tessellation.CurveChordTolerance = 0.00002;
    tessellation.SurfacePlaneTolerance = 0.00002;
    tessellation.CurveChordAngleTolerance = Math.PI / 36;
    tessellation.SurfacePlaneAngleTolerance = Math.PI / 36;
    tessellation.NeedVertexNormal = true;
    if (!tessellation.Tessellate())
        throw new InvalidOperationException("SolidWorks failed to tessellate a solid body.");

    var vertexCount = tessellation.GetVertexCount();
    var points = new float[vertexCount][];
    var normals = new double[vertexCount][];
    var facetCount = tessellation.GetFacetCount();
    var bodyTriangleCount = triangleCount;
    var bodyVolume = 0.0;
    for (var facet = 0; facet < facetCount; facet++)
    {
        ctx.Cancel.ThrowIfCancellationRequested();
        var fins = (int[])tessellation.GetFacetFins(facet);
        if (fins.Length != 3)
            throw new InvalidOperationException($"Expected three fins for facet {facet}; got {fins.Length}.");

        var first = (int[])tessellation.GetFinVertices(fins[0]);
        var second = (int[])tessellation.GetFinVertices(fins[1]);
        var third = (int[])tessellation.GetFinVertices(fins[2]);
        int a = first[0], b = first[1], c = -1;
        foreach (int vertex in second.Concat(third))
        {
            if (vertex == a || vertex == b)
                continue;
            if (c != -1 && c != vertex)
                throw new InvalidOperationException($"Facet {facet} references more than three vertices.");
            c = vertex;
        }
        if (c == -1 || a == b)
        {
            degenerateCount++;
            continue;
        }

        foreach (int vertex in new[] { a, b, c })
        {
            if (points[vertex] != null)
                continue;
            var coordinates = (double[])tessellation.GetVertexPoint(vertex);
            points[vertex] = coordinates.Select(value => (float)(value * 1000.0)).ToArray();
            if (points[vertex].Any(value => !float.IsFinite(value)))
                throw new InvalidOperationException($"Nonfinite vertex {vertex}.");
            normals[vertex] = (double[])tessellation.GetVertexNormal(vertex);
        }

        var p = points[a];
        var q = points[b];
        var r = points[c];
        double ux = (double)q[0] - p[0], uy = (double)q[1] - p[1], uz = (double)q[2] - p[2];
        double vx = (double)r[0] - p[0], vy = (double)r[1] - p[1], vz = (double)r[2] - p[2];
        double nx = uy * vz - uz * vy, ny = uz * vx - ux * vz, nz = ux * vy - uy * vx;
        var length = Math.Sqrt(nx * nx + ny * ny + nz * nz);
        if (length == 0)
        {
            degenerateCount++;
            continue;
        }

        // Use SolidWorks' surface normals to orient the facet before computing its STL normal.
        double dot = 0;
        foreach (int vertex in new[] { a, b, c })
            dot += nx * normals[vertex][0] + ny * normals[vertex][1] + nz * normals[vertex][2];
        if (!double.IsFinite(dot) || dot == 0)
            throw new InvalidOperationException($"Cannot orient facet {facet} using its surface normals.");
        if (dot < 0)
        {
            (q, r) = (r, q);
            nx = -nx;
            ny = -ny;
            nz = -nz;
        }
        writer.Write((float)(nx / length));
        writer.Write((float)(ny / length));
        writer.Write((float)(nz / length));
        foreach (var point in new[] { p, q, r })
            foreach (float coordinate in point)
                writer.Write(coordinate);
        writer.Write((ushort)0);
        triangleCount++;
        bodyVolume += (p[0] * nx + p[1] * ny + p[2] * nz) / 6;
    }
    if (triangleCount == bodyTriangleCount || !double.IsFinite(bodyVolume) || bodyVolume <= 0)
        throw new InvalidOperationException($"Invalid solid mesh: {triangleCount - bodyTriangleCount} triangles, volume {bodyVolume} mm³.");
    volumeMm3 += bodyVolume;
}

mesh.Position = 80;
writer.Write((uint)triangleCount);
writer.Flush();
using var compressed = new MemoryStream();
using (var gzip = new System.IO.Compression.GZipStream(compressed, System.IO.Compression.CompressionLevel.Optimal, true))
{
    mesh.Position = 0;
    mesh.CopyTo(gzip);
}
ctx.SetResult(new
{
    path = model.GetPathName(),
    configuration = activeConfiguration,
    units = "mm",
    bodyCount = bodies.Length,
    triangleCount,
    degenerateCount,
    volumeMm3,
    gzipStlBase64 = triangleCount == 0 ? null : Convert.ToBase64String(compressed.ToArray())
});
