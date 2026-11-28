"""Reading a face's exact B-spline surface and an edge's B-spline curve back over COM.

Excerpts of the reader that ran on SolidWorks 2026 (34.1.1) on 2026-11-28, from Windows Python
3.13 with pywin32 (late-bound), described in entries/reading/17-read-exact-b-spline-geometry.md.
Every line below this docstring is copied unchanged from that reader, in its order; its other
imports are left out with the code that used them. Also left out: finding the part's faces and
edges, opening the part read-only and closing it, and writing the results, which are covered by
the entries reading/17 links to. Comments in the code that name "S1", "S2" or "the tip" refer to
the spike the reader was written for: S1 built the part, S2 is this reader.

swcom is code/python/swcom.py (its call, _dispatch and _null_dispatch).
"""

from __future__ import annotations

import time


MM_PER_M = 1000.0
# GetBSurfParams3's Tolerance (metres): SolidWorks' help, as its search index quotes it, gives the
# allowed deviation of an approximated B-spline from the surface, default 0.01, and its C# example
# calls GetBSurfParams3(false, false, swSurfParam, 0.01, out sense) with swSurfParam from
# ISurface.Parameterization2. With no cubic or non-rational conversion asked for it should not be
# used; the comparison with the STEP shows whether the surface came back approximated. (S2's first
# run passed Nothing for VP0 and 1e-10 here, and SolidWorks died inside the call.)
SURFACE_TOLERANCE_M = 0.01
CURVE_SAMPLES = 21  # SolidWorks' own ICurve.Evaluate2 per edge, across the edge's range
SURFACE_SAMPLES = 7  # SolidWorks' own ISurface.Evaluate, a 7 x 7 grid across the knot range
DISP_E_MEMBERNOTFOUND = -2147352573


class ReadFailed(Exception):
    """A step that the rest of the read cannot go on without."""


def mm(values):
    """Metres to millimetres: the one place the reader converts lengths."""
    return [float(v) * MM_PER_M for v in values]


def floats(values):
    return [float(v) for v in (values or ())]


def number(value):
    """A by-reference out as a float, or None when it did not come back."""
    return None if value is None else float(value)


# -- COM --------------------------------------------------------------------------------------


class Com:
    """The few COM helpers the reader uses, timed per member. The real one wraps pywin32 and the
    Converter's swcom; tests pass a fake with the same methods."""

    def __init__(self, call, wrap, out, null_dispatch):
        self._call, self.wrap, self.out, self.null_dispatch = call, wrap, out, null_dispatch
        self.timings = {}

    def call(self, obj, name, *args):
        start = time.perf_counter()
        try:
            return self._call(obj, name, *args)
        finally:
            row = self.timings.setdefault(name, {"count": 0, "seconds": 0.0})
            row["count"] += 1
            row["seconds"] += time.perf_counter() - start


def pywin32_com(swcom):
    """Com over pywin32's late binding, through swcom.call (zero-argument members as property
    gets, uncalled methods for those returning nothing or an array: GOTCHAS 5 and 55)."""
    import pythoncom
    from win32com.client import VARIANT

    kinds = {"bool": (pythoncom.VT_BOOL, False), "double": (pythoncom.VT_R8, 0.0),
             "long": (pythoncom.VT_I4, 0), "variant": (pythoncom.VT_VARIANT, None)}

    def out(kind):
        vt, value = kinds[kind]
        return VARIANT(pythoncom.VT_BYREF | vt, value)

    def call(obj, name, *args):
        try:
            return swcom.call(obj, name, *args)
        except pythoncom.com_error as exc:
            # GOTCHAS 39: late binding can ask for a property get where a method with arguments
            # is meant; invoking the same member as a method worked there.
            if not args or exc.hresult != DISP_E_MEMBERNOTFOUND or not hasattr(obj, "_oleobj_"):
                raise
            raw = obj._oleobj_
            returned = raw.Invoke(raw.GetIDsOfNames(name), 0, pythoncom.DISPATCH_METHOD, True, *args)
            return lift(returned, swcom._dispatch)  # as the normal path hands results back

    def wrap(item):
        return item if item is None or hasattr(item, "_oleobj_") else swcom._dispatch(item)

    return Com(call, wrap, out, swcom._null_dispatch)


def lift(value, dispatch):
    """A raw Invoke result made like swcom.call's: COM objects (raw PyIDispatch) wrapped for late
    binding, inside tuples too (a return value followed by by-reference outs)."""
    if isinstance(value, tuple):
        return tuple(lift(v, dispatch) for v in value)
    if type(value).__name__ == "PyIDispatch":
        return dispatch(value)
    return value


def outs(returned, holders):
    """(return value, out values). pywin32 may hand by-reference outs back in a tuple after the
    return value, or leave them in the VARIANTs passed in (assemblies-02 reads both)."""
    if isinstance(returned, tuple):
        values = list(returned[1:])
        values += [h.value for h in holders[len(values):]]
        return returned[0], values
    return returned, [h.value for h in holders]


def items(com, obj, name, *args):
    """A member that returns an array of COM objects, each wrapped to call members on."""
    return [com.wrap(x) for x in (com.call(obj, name, *args) or ())]


# -- the spline readers -----------------------------------------------------------------------


def spline_curve_record(dimension, order, periodic, count, knot_count, control_points, knots):
    """ISplineParamData's numbers as written: poles in mm, weights apart (dimension 4)."""
    flat = floats(control_points)
    record = {"dimension": int(dimension), "order": int(order), "degree": int(order) - 1,
              "periodic": int(periodic), "control_points_count": int(count), "knot_points_count": int(knot_count),
              "knots": floats(knots), "raw_control_points_length": len(flat)}
    dim = int(dimension)
    if dim not in (3, 4) or len(flat) != dim * int(count):
        raise ReadFailed(f"GetBCurveParams5 gave {len(flat)} control point numbers for {count} points of "
                         f"dimension {dim}")
    rows = [flat[i:i + dim] for i in range(0, len(flat), dim)]
    record["poles"] = [mm(r[:3]) for r in rows]
    record["weights"] = [r[3] for r in rows] if dim == 4 else None
    record["full_knots"] = len(record["knots"]) == int(count) + int(order)
    return record


def read_curve_spline(com, curve, is_closed):
    request = {"WantCubicIn": False, "WantNRational": False, "ForceNonPeriodic": False, "IsClosed": bool(is_closed)}
    data = com.call(curve, "GetBCurveParams5", *request.values())
    if data is None:
        raise ReadFailed("GetBCurveParams5 returned nothing")
    holder = com.out("variant")
    ok_points, (points,) = outs(com.call(data, "GetControlPoints", holder), [holder])
    holder = com.out("variant")
    ok_knots, (knots,) = outs(com.call(data, "GetKnotPoints", holder), [holder])
    record = spline_curve_record(com.call(data, "Dimension"), com.call(data, "Order"), com.call(data, "Periodic"),
                                 com.call(data, "ControlPointsCount"), com.call(data, "KnotPointsCount"),
                                 points, knots)
    record.update({"request": request, "get_control_points_returned": bool(ok_points),
                   "get_knot_points_returned": bool(ok_knots)})
    return record


def surface_points(n_u, n_v, dimension, fetch):
    """IBSurfParamData's control points, one GetControlPoints(Row, Column) call each, 1-based.

    The help says Row runs to ControlPointRowCount and Column to ControlPointColumnCount, and that u
    is the row direction. SolidWorks 2026 (34.1.1) answered the other way round: on a surface whose
    knots give 179 u poles and 98 v poles (ControlPointColumnCount 179, ControlPointRowCount 98) it
    returned a point only for Row <= 179 and Column <= 98, and an EMPTY array, not an error,
    outside that. So the pole counts are taken from the knot vectors, Row indexes u and Column
    indexes v, and any call that does not give exactly one point fails the read. Points come back
    u outer, v inner."""
    flat = []
    for i in range(1, n_u + 1):
        for j in range(1, n_v + 1):
            point = floats(fetch(i, j))
            if len(point) != dimension:
                raise ReadFailed(f"GetControlPoints({i}, {j}) gave {len(point)} numbers, not one point of "
                                 f"{dimension}")
            flat += point
    return flat, "Row = u pole 1..n_u (outer), Column = v pole 1..n_v (inner), one point per call"


def read_surface_spline(com, surface, tolerance_m=SURFACE_TOLERANCE_M):
    sense = com.out("bool")
    # VP0 must be the surface's own ISurfaceParameterizationData: "Before calling this method, call
    # ISurface:Parameterization2 to populate VP0" (the help). Never pass Nothing.
    parameterization = com.call(surface, "Parameterization2")
    if parameterization is None:
        raise ReadFailed("Parameterization2 returned nothing; GetBSurfParams3 not called")
    returned = com.call(surface, "GetBSurfParams3", False, False, parameterization, tolerance_m, sense)
    data, (sense_value,) = outs(returned, [sense])
    if data is None:
        raise ReadFailed("GetBSurfParams3 returned nothing")
    dim = int(com.call(data, "ControlPointDimension"))
    rows, columns = int(com.call(data, "ControlPointRowCount")), int(com.call(data, "ControlPointColumnCount"))
    record = {"request": {"WantCubic": False, "WantNonRational": False, "VP0": "Parameterization2()",
                          "Tolerance_m": tolerance_m},
              "sense": None if sense_value is None else bool(sense_value),
              "u_order": int(com.call(data, "UOrder")), "v_order": int(com.call(data, "VOrder")),
              "rows": rows, "columns": columns, "dimension": dim,
              "u_periodic": bool(com.call(data, "UPeriodicity")), "v_periodic": bool(com.call(data, "VPeriodicity")),
              "u_knots": floats(com.call(data, "UKnots")), "v_knots": floats(com.call(data, "VKnots"))}
    record["u_degree"], record["v_degree"] = record["u_order"] - 1, record["v_order"] - 1
    if dim not in (3, 4):
        raise ReadFailed(f"GetBSurfParams3 gave control points of dimension {dim}")
    # 1-based, one point per call (the help; S2's second run got an empty array for (0, 0)). Pole
    # counts from the knots: SolidWorks 2026 bounded Row by ControlPointColumnCount (see surface_points).
    n_u = len(record["u_knots"]) - record["u_order"]
    n_v = len(record["v_knots"]) - record["v_order"]
    if sorted((n_u, n_v)) != sorted((rows, columns)):
        raise ReadFailed(f"the knots give {n_u} x {n_v} poles but the counts are {rows} rows x {columns} columns")
    flat, layout = surface_points(n_u, n_v, dim, lambda i, j: com.call(data, "GetControlPoints", i, j))
    points = [flat[i:i + dim] for i in range(0, len(flat), dim)]
    record.update({"index_base": 1, "layout": layout, "poles_from_knots": [n_u, n_v],
                   "points": [mm(p[:3]) for p in points],
                   "weights": [p[3] for p in points] if dim == 4 else None})
    return record


def read_face(com, face, index, role):
    surface = com.call(face, "GetSurface")
    record = {"index": index, "role": role, "surface_identity": int(com.call(surface, "Identity")),
              "face_in_surface_sense": bool(com.call(face, "FaceInSurfaceSense")),
              "uv_bounds": floats(com.call(face, "GetUVBounds"))}
    spline = read_surface_spline(com, surface)
    record["surface"] = spline
    u0, u1 = spline["u_knots"][spline["u_order"] - 1], spline["u_knots"][-spline["u_order"]]
    v0, v1 = spline["v_knots"][spline["v_order"] - 1], spline["v_knots"][-spline["v_order"]]
    samples = []
    for i in range(SURFACE_SAMPLES):
        for j in range(SURFACE_SAMPLES):
            u = u0 + (u1 - u0) * i / (SURFACE_SAMPLES - 1)
            v = v0 + (v1 - v0) * j / (SURFACE_SAMPLES - 1)
            value = floats(com.call(surface, "Evaluate", u, v, 0, 0))
            samples.append({"u": u, "v": v, "point": mm(value[:3]), "raw_length": len(value)})
    record["evaluations"] = samples
    return record


def read_edge(com, edge, index):
    params = com.call(edge, "GetCurveParams3")
    curve = com.call(edge, "GetCurve")
    holders = [com.out("double"), com.out("double"), com.out("bool"), com.out("bool")]
    ok, (start, end, closed, periodic) = outs(com.call(curve, "GetEndParams", *holders), holders)
    record = {
        "index": index,
        "edge_params": {"u_min": float(com.call(params, "UMinValue")), "u_max": float(com.call(params, "UMaxValue")),
                        "sense": bool(com.call(params, "Sense")), "curve_type": int(com.call(params, "CurveType")),
                        "curve_tag": int(com.call(params, "CurveTag")),
                        "start_point": mm(floats(com.call(params, "StartPoint"))[:3]),
                        "end_point": mm(floats(com.call(params, "EndPoint"))[:3])},
        "curve_info": {"identity": int(com.call(curve, "Identity")), "is_bcurve": bool(com.call(curve, "IsBcurve")),
                       "is_line": bool(com.call(curve, "IsLine")),
                       "is_trimmed": bool(com.call(curve, "IsTrimmedCurve")),
                       "end_params": {"returned": bool(ok), "start": number(start), "end": number(end),
                                      "closed": None if closed is None else bool(closed),
                                      "periodic": None if periodic is None else bool(periodic)}},
    }
    if record["curve_info"]["is_line"]:
        line = floats(com.call(curve, "LineParams"))
        record["curve_info"]["line_params"] = {"point": mm(line[:3]), "direction": line[3:6], "raw_length": len(line)}
    try:
        record["curve"] = read_curve_spline(com, curve, closed)
    except Exception as exc:  # noqa: BLE001 - a line may have no spline; the rest of the edge still counts
        record["curve"] = None
        record["curve_error"] = f"{type(exc).__name__}: {exc}"
    t0, t1 = record["edge_params"]["u_min"], record["edge_params"]["u_max"]
    record["evaluations"] = []
    for k in range(CURVE_SAMPLES):
        t = t0 + (t1 - t0) * k / (CURVE_SAMPLES - 1)
        value = floats(com.call(curve, "Evaluate2", t, 0))
        record["evaluations"].append({"t": t, "point": mm(value[:3]), "raw_length": len(value)})
    return record
