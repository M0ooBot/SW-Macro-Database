---
schema: 2
id: reading-17-read-exact-b-spline-geometry
title: Read a face's exact B-spline surface and an edge's B-spline curve back over COM
answers: "How do I read a face's exact B-spline surface and an edge's B-spline curve (degrees, knots, control points, weights) back from SolidWorks over COM?"
keywords: [GetBSurfParams3, Parameterization2, VP0, IBSurfParamData, GetControlPoints, ControlPointRowCount, ControlPointColumnCount, UKnots, VKnots, GetBCurveParams5, ISplineParamData, GetKnotPoints, GetCurveParams3, ICurveParamData, B-spline, NURBS, poles, control points, knots, exact geometry, read surface back, read curve back, compare with STEP, Open CASCADE, 0x800706BE, remote procedure call failed, empty array, 1-based]
api: [ISurface.Parameterization2, ISurface.GetBSurfParams3, IBSurfParamData.UOrder, IBSurfParamData.VOrder, IBSurfParamData.ControlPointRowCount, IBSurfParamData.ControlPointColumnCount, IBSurfParamData.ControlPointDimension, IBSurfParamData.UPeriodicity, IBSurfParamData.VPeriodicity, IBSurfParamData.UKnots, IBSurfParamData.VKnots, IBSurfParamData.GetControlPoints, ICurve.GetEndParams, ICurve.GetBCurveParams5, ISplineParamData.Dimension, ISplineParamData.Order, ISplineParamData.Periodic, ISplineParamData.ControlPointsCount, ISplineParamData.KnotPointsCount, ISplineParamData.GetControlPoints, ISplineParamData.GetKnotPoints, IEdge.GetCurveParams3, ICurveParamData.UMinValue, ICurveParamData.UMaxValue, ICurveParamData.Sense, ICurveParamData.StartPoint, ICurveParamData.EndPoint, ISurface.Evaluate]
language: [python]
status: verified
verified_on: SolidWorks 2026 (34.1.1), Python over pywin32, late-bound
majors: [34]
evidence: [2026-11-28-reading-17-read-exact-b-spline-geometry-python-34]
recipe_status: null
recipe_evidence: []
superseded_by: null
---

# Read a face's exact B-spline surface and an edge's B-spline curve back over COM

## What this is for

To check what SolidWorks actually built against what was meant, or to hand the
geometry to another kernel, you need a face's surface and an edge's curve as
SolidWorks holds them: degrees, knot vectors, control points and weights, not a
tessellation or sampled points. `ISurface` and `ICurve` hand these out through
param-data objects. The curve side is straightforward. The surface side has
three traps the help does not prepare you for: one ended SolidWorks inside the
call, and the other two lose control points without an error.

Attach as in [connect/02](../connect/02-attach-from-python.md); `call` below is
the one from there ([`code/python/swcom.py`](../../code/python/swcom.py)).

## The call

The reader that ran is in
[`code/python/bspline_readback.py`](../../code/python/bspline_readback.py): its
geometry part, copied unchanged, with the COM helpers it uses (`Com`, which
times each member; `pywin32_com`, whose `out(kind)` makes a by-reference
`VARIANT`; `outs`, which takes the out values from a returned tuple or from the
`VARIANT`s; `mm`, the one place metres become millimetres). The important parts:

**The surface** of a face (`IFace2.GetSurface`, then this):

```python
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
```

- `ISurface.Parameterization2` takes no arguments and returns an
  `ISurfaceParameterizationData` (type library). It is only passed on, as
  `GetBSurfParams3`'s `VP0`; none of its members were read.
- `ISurface.GetBSurfParams3(WantCubic, WantNonRational, VP0, Tolerance, out
  Sense)` returns an `IBSurfParamData`. `False, False` asks for the surface as
  it is, with no conversion. `Tolerance` is in **metres** (the help: the allowed
  deviation, in metres; default 0.01).
- On `IBSurfParamData`: `UOrder` / `VOrder` are orders (degree + 1); `UKnots` /
  `VKnots` are the full knot vectors, end knots repeated (`n + order` values);
  `ControlPointDimension` is 3, or 4 with a weight when the surface is rational
  (the help; only 3 was seen); `GetControlPoints(Row, Column)` gives **one**
  control point per call, in **metres**.
- **Pole counts come from the knots**: `n_u = len(UKnots) - UOrder`,
  `n_v = len(VKnots) - VOrder`. Then `Row` runs `1..n_u` and indexes u,
  `Column` runs `1..n_v` and indexes v. On SolidWorks 2026
  `ControlPointColumnCount` held `n_u` and `ControlPointRowCount` held `n_v`
  ([GOTCHAS §119](../../GOTCHAS.md)), so the code only checks that the two counts
  are the same pair, and fails on any call that is not exactly one point.
- Knots and parameters are SolidWorks' own, unscaled (0 to 1 on every surface and
  curve read here). Weights, when there are any, are unscaled too.

**The curve** of an edge (`IEdge.GetCurve`, then `ICurve.GetEndParams` for
`IsClosed`, then this):

```python
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
```

- `ICurve.GetBCurveParams5(WantCubicIn, WantNRational, ForceNonPeriodic,
  IsClosed)` returns an `ISplineParamData`. `IsClosed` was passed from
  `ICurve.GetEndParams(out Start, out End, out IsClosed, out IsPeriodic)`.
- `ISplineParamData.GetControlPoints(out ControlPoints)` and
  `GetKnotPoints(out KnotPoints)` return `True` and fill their out: the control
  points as one flat array, `Dimension` numbers a point (3, or 4 with the weight),
  in **metres**; the knots as the full vector, `ControlPointsCount + Order`
  values. `Periodic` is an integer here (0), not a boolean.

**The edge on its curve**, from the start of `read_edge`:

```python
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
        # ...the curve's own identity, type tests and end parameters, then the spline above
```

`IEdge.GetCurveParams3` returns an `ICurveParamData`: `UMinValue` /
`UMaxValue` are the edge's range on its curve's parameter, `Sense` its direction
along it, `StartPoint` / `EndPoint` its ends in **metres**, `CurveType` the
curve's type (3005, the same as `ICurve.Identity`, on both edges here).

To check a readback, `read_face` and `read_edge` also ask SolidWorks to
evaluate: `ISurface.Evaluate(u, v, 0, 0)` returned 6 numbers whose first three
are the point in metres (the other three were not identified), and
`ICurve.Evaluate2(t, 0)` 4 numbers, the first three the point.

## Why it is not obvious

- **`VP0` must come from `Parameterization2`.** The type library types it as a
  plain `IDispatch` and nothing stops you passing Nothing. Passing Nothing (with
  `Tolerance` 1e-10) was followed by SolidWorks ending inside the call after
  19.2 s: `0x800706BE`, "The remote procedure call failed".
  [GOTCHAS §118](../../GOTCHAS.md) has the confounds.
- **`IBSurfParamData.GetControlPoints` is 1-based and never raises.** `(0, 0)`
  returned an empty array, and so did every index past the bounds below.
- **Its bounds are not the ones its counts suggest.** A reader looping `Row` over
  `ControlPointRowCount` and `Column` over `ControlPointColumnCount`, as the
  help words it, got 16 points from a surface of 4 × 98 poles and 9,604 from one of
  179 × 98, and nothing to say the rest were missing. [GOTCHAS §119](../../GOTCHAS.md).
- **A straight edge can be a B-spline.** The two-pole trailing edge read
  `IsLine` `False`, `IsBcurve` `True`, `Identity` 3005: a degree-1 B-spline
  with knots `[0, 0, 1, 1]`. Branching on `IsLine` to choose a reader would not
  have reached `LineParams`.
- **It is slow through late binding**: one point per call, about 1.6 ms a call.
  The 179 × 98-pole face took 17,542 `GetControlPoints` calls and 28 s.

## What it does not do

- **Rational and periodic geometry was not exercised.** Every surface and curve
  read was non-rational (dimension 3) and non-periodic; the dimension-4 (weights)
  branches of this code have not run, `ForceNonPeriodic` was only `False`, and
  `WantCubic` / `WantNonRational` were only `False`.
- **What `Tolerance` does when no conversion is asked is not known.** With 0.01 m
  the surfaces came back exact (identical knots and poles to SolidWorks' own STEP
  of the part), so it did not visibly approximate. Settling it needs the same face
  read at two very different tolerances and compared.
- **Only lofted skin faces were read** (`ISurface.Identity` 4006 on both). Planar
  and other analytic faces were not passed to `GetBSurfParams3`.
- **Whether `VP0` Nothing on its own ends SolidWorks is not settled**
  ([GOTCHAS §118](../../GOTCHAS.md)). Rerunning it means risking the session, so
  it was not repeated.
- **Only SolidWorks 2026 (34.1.1).** The swapped counts in particular may differ
  on 2024 or 2025; nothing here was run there.
- **The `Sense` out of `GetBSurfParams3` was not interpreted.** It read `True` on
  both faces while `IFace2.FaceInSurfaceSense` read `False` on both; what the
  out means was not worked out, and the comparison below did not need it.
- **Faster reads were not tried.** The type library also lists
  `IBSurfParamData.IGetControlPoints(Row, Column, Count)`, which may hand out
  several points at once; it was not called. Early binding (C#) was not timed.
- Whether `pywin32_com`'s `DISPATCH_METHOD` retry ([GOTCHAS §39](../../GOTCHAS.md))
  was ever needed in these runs was not recorded.

## Evidence

SolidWorks 2026 (revision 34.1.1), 2026-11-28, Windows Python 3.13 with pywin32,
late-bound through `call`. Each run read the same part, a solid loft of a wing
tip (one solid, four faces: two planar ends and two lofted skin faces). Runs 2 to
4 opened the saved file read-only themselves. Run 1 instead read a copy already
open in SolidWorks with unsaved changes (it had been opened read-only for viewing
and its view changed): `IsOpenedReadOnly` `True`, `GetSaveFlag` `True` before the
read. The reader read the
two edges of the planar tip face and the skin face beside each.

| Run | Surface read | What happened |
|---|---|---|
| 1 | `GetBSurfParams3(False, False, Nothing, 1e-10, out)` | Both edge curves read. Then SolidWorks ended inside `GetBSurfParams3` after 19.2 s, `0x800706BE` (confounds in §118). |
| 2 | `VP0` from `Parameterization2`, `Tolerance` 0.01 | Returned in about 0.01 s. `GetControlPoints(0, 0)` returned an empty array, not an error. |
| 3 | 1-based, `Row` 1..`ControlPointRowCount`, `Column` 1..`ControlPointColumnCount` | 16 points from the face with counts 98 rows × 4 columns, 9,604 (98 × 98) from 98 × 179; the other calls returned empty arrays silently, and the points read could not be laid out on the knots. |
| 4 | The code above: pole counts from the knots, `Row` = u, `Column` = v | Pass: 392 and 17,542 points, one per call. |

What run 4 read: edge 0 a degree-1 curve of 2 poles and 4 knots, edge 1 a cubic of
505 poles and 509 knots, both non-periodic, range 0 to 1, `GetCurveParams3`'s
`StartPoint` equal to `Evaluate2` at `UMinValue`; face 0 bicubic, `UKnots` 8 and
`VKnots` 102 values, so 4 × 98 poles, with `ControlPointColumnCount` 4 and
`ControlPointRowCount` 98; face 1 bicubic, 183 and 102 knots, 179 × 98 poles, with
`ControlPointColumnCount` 179 and `ControlPointRowCount` 98. The part's save flag
was clear before and after the read, and the reader closed only the copy it had
opened.

How it was checked, in Open CASCADE on the readback (millimetres):

- Each curve and surface rebuilt from the readback matched SolidWorks' own
  `ICurve.Evaluate2` (21 points an edge) and `ISurface.Evaluate` (a 7 × 7 grid a
  face) to 2.4e-13 mm or better. The surfaces matched only with `Row` as u: taking
  `Column` as u was off by 436 mm and 622 mm.
- Against the same part's STEP, exported by SolidWorks: both curves and both
  surfaces had the same degrees, pole counts, knots (largest difference 0.0) and
  poles (0.0 mm), both non-rational, and agreed to 0.0 mm at matched parameters
  (1,000 samples a curve, 1,024 a surface).

Timings in run 4: `GetBSurfParams3` 0.012 s a face; reading the 4 × 98 face 0.8 s
and the 179 × 98 face 28 s, nearly all of it the 17,542 `GetControlPoints` calls;
each edge about 0.15 s, including its 21 evaluations.

Sources: the signatures from SolidWorks 2026's `sldworks.tlb`, read as a file
(`GetBSurfParams3([in] BOOL WantCubic, [in] BOOL WantNonRational, [in] IDispatch
VP0, [in] double Tolerance, [out] BOOL* Sense)` → `IBSurfParamData*`;
`Parameterization2()` → `ISurfaceParameterizationData*`;
`GetBCurveParams5(BOOL WantCubicIn, BOOL WantNRational, BOOL ForceNonPeriodic,
BOOL IsClosed)` → `ISplineParamData*`; `IBSurfParamData.GetControlPoints([in] long
Row, [in] long Column)` → `VARIANT`). The SolidWorks API help, whose pages render
by JavaScript, was not read directly: what this entry says it says is SolidWorks
API help as quoted by its search index. That quotes, for `GetBSurfParams3`,
"Before calling this method, call ISurface:Parameterization2 to populate VP0",
`Tolerance` as "the allowed deviation, in metres; default 0.01", and a C# example calling `GetBSurfParams3(false, false,
swSurfParam, 0.01, out sense)`; for `IBSurfParamData.GetControlPoints(Row,
Column)`, "1 <= index of row <= ControlPointRowCount" and likewise for columns,
one control point per call, dimension 3 (4 with a weight when rational), and
"The U direction of surface is in the row direction". `Row` did index u; its
bound was `ControlPointColumnCount`, not `ControlPointRowCount`.

## See also

- [connect/02 — Attach from Python](../connect/02-attach-from-python.md): `call`,
  and why zero-argument members are reached by attribute access
- [reading/15 — Measure a part that has no dimensions](../reading/15-measure-a-part-that-has-no-dimensions.md):
  faces, `PlaneParams` and the analytic surfaces
- [surfacing/03 — How a loft fills between profiles](../surfacing/03-how-a-loft-fills-between-profiles.md):
  measuring a loft against the surface that was meant
- [files/04 — Export a body to STEP](../files/04-export-a-body-to-step.md): the
  STEP this readback was compared with
- [curves/05 — Read curve points back](../curves/05-read-curve-points-back.md): a
  curve feature's points, rather than an edge's B-spline
- [GOTCHAS.md](../../GOTCHAS.md) §118 (`VP0`), §119 (`GetControlPoints`), §5 and
  §55 (zero-argument members), §39 (`DISPATCH_METHOD`)
