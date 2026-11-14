"""Build a small gear train from nothing in SolidWorks and run, as written, every listing the
gear-train entries quote; record what each call returned.

    python gear_train_check.py --sldworks "C:\\path\\to\\SLDWORKS.exe" --scratch C:\\path\\to\\scratch
                               [--out <folder for the result files>] [--step-timeout 600]

Windows Python 3 with pywin32. It starts its own SolidWorks from the path given, refuses to run if
any other SolidWorks is already registered in the Running Object Table or if the one it started
has a document open that this script did not make, writes only under the scratch folder (and its
two result files under --out), closes what it opened, and exits that SolidWorks at the end. A
watchdog kills the SolidWorks it started if one step runs longer than --step-timeout seconds (a
modal dialog blocks every COM call), and writes what it has. A dialog watch logs every dialog box
that SolidWorks puts up; it never clicks anything.

The fixtures are plain cylinders (r 20 x 10 mm, with a reference axis "Gear Axis" made from the
Top and Right planes): a gear mate needs no teeth. Nothing here shows interference, and nothing
here calls ModifyDefinition on a gear mate or forces lightweight components (both can leave
SolidWorks 2024 waiting on something no script can answer); the entries keep those as prose.

Lengths cross COM in metres and angles in radians. Recorded lengths are in millimetres and turns in
degrees. Every path recorded is relative to the scratch folder.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import shutil
import subprocess
import sys
import threading
import time
import traceback

import pythoncom
import win32com.client.dynamic as dynamic
import win32gui
import win32process
from win32com.client import VARIANT

# -- constants, read from swconst.tlb (swMateType_e, swMateAlign_e, swDocumentTypes_e, ...) ---------

COINCIDENT, CONCENTRIC, DISTANCE, ANGLE, GEAR, LOCK = 0, 1, 5, 6, 10, 16
CLOSEST = 2
SW_DOC_PART, SW_DOC_ASSEMBLY = 1, 2
OPEN_SILENT = 1                       # swOpenDocOptions_Silent
SAVE_AS_CURRENT, SAVE_AS_SILENT = 0, 1
SUPPRESS, UNSUPPRESS, THIS_CONFIGURATION = 0, 1, 1
FOLDER_CONTAINING = 2                 # swFeatureTreeFolder_Containing
PLANE_DISTANCE = 8                    # swRefPlaneReferenceConstraint_Distance
PART_TEMPLATE, ASSEMBLY_TEMPLATE = 8, 9   # swUserPreferenceStringValue_e default templates

BLANK_R, BLANK_W = 0.020, 0.010       # metres
MM = 1000.0

# The train: four cylinders standing in for gears on three shafts, every shaft +Z.
SHAFTS = (("S1", 0.040, 0.040), ("S2", 0.100, 0.040), ("S3", 0.100, 0.110),
          ("S4", 0.300, 0.040), ("S5", 0.315, 0.040))   # S4, S5: a pinion inside a plain annulus
RING_OUTER, RING_INNER = 0.050, 0.040   # metres: an annulus with no teeth, round a pinion of BLANK_R
GEARS = (  # name, shaft, z of its front face (m), placed turned (degrees)
    ("GearA", "S1", 0.000, 10.0),
    ("GearB", "S2", 0.000, 0.0),
    ("GearC", "S2", 0.015, 37.0),     # locked to GearB, not mated to the shaft
    ("GearD", "S3", 0.015, 0.0),
)
TEETH = {"GearA": 20, "GearB": 40, "GearC": 20, "GearD": 50}
NEW_TEETH_D = 60                      # the remake
DRIVE_FROM, DRIVE_TO = 10.0, 40.0


# -- the listings the entries quote -------------------------------------------------------------

def call(obj, name, *args):
    """Late-bound member: invoked when given arguments, read by attribute access otherwise."""
    member = getattr(obj, name)
    return member(*args) if args else member


def null():
    return VARIANT(pythoncom.VT_DISPATCH, None)              # a typed Nothing


def out_long():
    return VARIANT(pythoncom.VT_BYREF | pythoncom.VT_I4, 0)  # a by-reference long


def read_member(obj, name):
    """A zero-argument member: read, and called only if late binding handed back a method."""
    value = call(obj, name)
    return value() if type(value).__name__ in ("method", "function") else value


def put_indexed(obj, name, index, value):
    """An indexed property put (eqm.Equation(i) = text in VBA), which late binding cannot spell."""
    oleobj = obj._oleobj_
    oleobj.Invoke(oleobj.GetIDsOfNames(name), 0, pythoncom.DISPATCH_PROPERTYPUT, False, index, value)


def selected_count(doc):
    return int(call(call(doc, "SelectionManager"), "GetSelectedObjectCount2", -1) or 0)


def top_features(doc):
    out, feature = [], call(doc, "FirstFeature")
    while feature is not None:
        out.append(feature)
        feature = call(feature, "GetNextFeature")
    return out


def planes(doc):
    """The reference planes in tree order: Front, Top, Right in an English template."""
    return [f for f in top_features(doc) if call(f, "GetTypeName2") == "RefPlane"]


def select_feature(doc, feature, append=False, mark=0):
    """IFeature.Select2, judged by the selection count and retried briefly; then SelectByID2 by name."""
    if not append:
        call(doc, "ClearSelection2", True)
    before = selected_count(doc)
    for _ in range(4):
        if call(feature, "Select2", append, mark) and selected_count(doc) > before:
            return True
        time.sleep(0.25)
    kind = {"RefPlane": "PLANE", "RefAxis": "AXIS", "ProfileFeature": "SKETCH"}.get(
        call(feature, "GetTypeName2"), "BODYFEATURE")
    return bool(call(call(doc, "Extension"), "SelectByID2", str(call(feature, "Name")), kind, 0.0, 0.0, 0.0,
                     append, mark, null(), 0)) and selected_count(doc) > before


def mate_features(asm):
    """The sub-features of the MateGroup, in walk order."""
    out = []
    for feature in top_features(asm):
        if call(feature, "GetTypeName2") == "MateGroup":
            child = call(feature, "GetFirstSubFeature")
            while child is not None:
                out.append(child)
                child = call(child, "GetNextSubFeature")
    return out


def mate_feature(asm, name):
    return next(f for f in mate_features(asm) if str(call(f, "Name")) == name)


def add_mate(asm, kind, align, flip=False, distance_m=0.0, angle_rad=0.0, ratio=(1.0, 1.0)):
    """IAssemblyDoc.AddMate5 on what is selected at mark 1: type, align, flip, distance and its two
    limits, the gear ratio's numerator and denominator, angle and its two limits, for-positioning-only,
    lock rotation, width option, error status. Returns (mate, status, names of the new mates)."""
    before = {str(call(f, "Name")) for f in mate_features(asm)}
    d, a = distance_m, angle_rad
    status = out_long()
    mate = call(asm, "AddMate5", kind, align, flip, d, d, d, float(ratio[0]), float(ratio[1]),
                a, a, a, False, False, 0, status)
    call(asm, "ClearSelection2", True)
    made = [str(call(f, "Name")) for f in mate_features(asm) if str(call(f, "Name")) not in before]
    return mate, status.value, made


def rename(feature, name):
    """An IFeature.Name put, read back: SolidWorks renames quietly on a collision."""
    feature.Name = name
    return str(call(feature, "Name"))


def fix(asm, component):
    """Select the component, then IAssemblyDoc.FixComponent() with parentheses."""
    if call(component, "IsFixed"):
        return True
    call(asm, "ClearSelection2", True)
    if not call(component, "Select4", False, null(), False):
        return False
    asm.FixComponent()
    call(asm, "ClearSelection2", True)
    return bool(call(component, "IsFixed"))


def unfix(asm, component):
    """Select the component, then IAssemblyDoc.UnfixComponent() with parentheses."""
    if not call(component, "IsFixed"):
        return True
    call(asm, "ClearSelection2", True)
    if not call(component, "Select4", False, null(), False):
        return False
    asm.UnfixComponent()           # reached by attribute access alone it would only be fetched
    call(asm, "ClearSelection2", True)
    return not call(component, "IsFixed")


def select_feature_of(asm, component, name, append, mark=1):
    """A component's plane or axis: IComponent2.FeatureByName, then IFeature.Select2(append, mark);
    else SelectByID2("<feature>@<component>@<assembly>")."""
    if not append:
        call(asm, "ClearSelection2", True)
    before = selected_count(asm)
    feature = call(component, "FeatureByName", name)
    if feature is not None and call(feature, "Select2", append, mark) and selected_count(asm) > before:
        return True
    kind = "AXIS" if feature is not None and call(feature, "GetTypeName2") == "RefAxis" else "PLANE"
    assembly = str(call(asm, "GetTitle")).rsplit(".", 1)[0]
    full = f"{name}@{call(component, 'Name2')}@{assembly}"
    return bool(call(call(asm, "Extension"), "SelectByID2", full, kind, 0.0, 0.0, 0.0, append, mark,
                     null(), 0)) and selected_count(asm) > before


def select_origin(asm, component, append, mark=1):
    """Point1@<origin feature>@<component>@<assembly>, as an EXTSKETCHPOINT (assemblies/04)."""
    part = call(component, "GetModelDoc2")
    origin = next(str(call(f, "Name")) for f in top_features(part)
                  if call(f, "GetTypeName2") == "OriginProfileFeature")
    assembly = str(call(asm, "GetTitle")).rsplit(".", 1)[0]
    if not append:
        call(asm, "ClearSelection2", True)
    before = selected_count(asm)
    full = f"Point1@{origin}@{call(component, 'Name2')}@{assembly}"
    return bool(call(call(asm, "Extension"), "SelectByID2", full, "EXTSKETCHPOINT", 0.0, 0.0, 0.0,
                     append, mark, null(), 0)) and selected_count(asm) > before


def hold_on_shaft(asm, gear, skeleton, shaft_axis, skeleton_front, z_front_m):
    """Unfix a gear, put its Gear Axis on the skeleton's shaft axis, and hold its origin
    z_front_m (metres, signed) from the skeleton's Front plane. Returns each AddMate5's answer."""
    if not unfix(asm, gear):
        raise RuntimeError("the gear would not unfix")
    if not (select_feature_of(asm, gear, "Gear Axis", False) and
            select_feature_of(asm, skeleton, shaft_axis, True)):
        raise RuntimeError("the two axes could not be selected")
    made = [add_mate(asm, COINCIDENT, CLOSEST)]
    if not (select_origin(asm, gear, False) and select_feature_of(asm, skeleton, skeleton_front, True)):
        raise RuntimeError("the origin and the Front plane could not be selected")
    if abs(z_front_m) < 1e-12:
        made.append(add_mate(asm, COINCIDENT, CLOSEST))
    else:   # a point's distance is along the plane's normal: Flip for the negative side (GOTCHAS §42)
        made.append(add_mate(asm, DISTANCE, CLOSEST, flip=z_front_m < 0, distance_m=abs(z_front_m)))
    return made


def select_by_corresponding(asm, component, feature_name, append, mark=1):
    """The assembly's instance of one of the part's features, selected at a mark."""
    if not append:
        call(asm, "ClearSelection2", True)
    part = call(component, "GetModelDoc2")
    feature = next(f for f in top_features(part) if str(call(f, "Name")) == feature_name)
    entity = call(component, "GetCorresponding", feature)
    data = call(call(asm, "SelectionManager"), "CreateSelectData")
    data.Mark = mark
    return bool(call(entity, "Select4", append, data))


def select_components(asm, components):
    """Whole components at mark 1: IComponent2.Select4(append, data, False) with data.Mark = 1."""
    call(asm, "ClearSelection2", True)
    for position, component in enumerate(components):
        before = selected_count(asm)
        data = call(call(asm, "SelectionManager"), "CreateSelectData")
        data.Mark = 1
        if not (call(component, "Select4", position > 0, data, False) and selected_count(asm) > before):
            return False
    return True


def constrained_status(component):
    """2 under-defined, 3 fully defined, 4 over-defined (swConstrainedStatus_e)."""
    value = call(component, "GetConstrainedStatus")
    return value() if type(value).__name__ == "method" else value


def error_code(feature):
    """IFeature.GetErrorCode2: (code, is only a warning), with the warning flag as a by-reference bool."""
    flag = VARIANT(pythoncom.VT_BYREF | pythoncom.VT_BOOL, False)
    result = call(feature, "GetErrorCode2", flag)
    if isinstance(result, tuple):                  # pywin32 may hand the out value back in a tuple
        return result[0], (result[1] if len(result) > 1 else None)
    return result, flag.value


def whats_wrong(asm):
    """IModelDocExtension.GetWhatsWrongCount, and GetWhatsWrong with its three out parameters."""
    ext = call(asm, "Extension")
    count = call(ext, "GetWhatsWrongCount")
    # Its three arrays are out parameters: with none passed it raised "Parameter not optional".
    outs = [VARIANT(pythoncom.VT_BYREF | pythoncom.VT_VARIANT, None) for _ in range(3)]
    returned = call(ext, "GetWhatsWrong", *outs)
    listed = returned if isinstance(returned, tuple) else (returned,) + tuple(o.value for o in outs)
    features = [str(call(item, "Name")) for item in (listed[1] or ())]
    return {"count": count, "returned": listed[0], "features": features,
            "codes": listed[2], "warnings": listed[3]}


def is_suppressed(feature):
    """IFeature.IsSuppressed2 in this configuration (one flag per configuration asked for)."""
    value = call(feature, "IsSuppressed2", THIS_CONFIGURATION, null())
    value = value[0] if isinstance(value, tuple) else value
    return bool(value[0] if isinstance(value, (list, tuple)) else value)


def set_suppressed(asm, name, on):
    feature = mate_feature(asm, name)
    call(feature, "SetSuppression2", SUPPRESS if on else UNSUPPRESS, THIS_CONFIGURATION, None)
    call(asm, "ClearSelection2", True)
    return is_suppressed(feature) is on


def delete_mate(asm, name):
    """Select the mate, then IModelDoc2.EditDelete() with parentheses; judged by the tree."""
    feature = next((f for f in mate_features(asm) if str(call(f, "Name")) == name), None)
    if feature is None:
        return False
    call(asm, "ClearSelection2", True)
    call(feature, "Select2", False, 0)
    asm.EditDelete()               # attribute access alone would only fetch it
    call(asm, "ClearSelection2", True)
    return all(str(call(f, "Name")) != name for f in mate_features(asm))


def remake_gear_mate(asm, name, first_component, second_component, z_first, z_second):
    """Delete a gear mate and make it again at a new ratio, Flip False, under its old name."""
    if not delete_mate(asm, name):
        return None
    a = call(asm, "GetComponentByName", first_component)
    b = call(asm, "GetComponentByName", second_component)
    if not (select_feature_of(asm, a, "Gear Axis", False) and select_feature_of(asm, b, "Gear Axis", True)):
        return None
    mate, status, made = add_mate(asm, GEAR, CLOSEST, flip=False, ratio=(z_first, z_second))
    if mate is None or len(made) != 1:
        return None
    feature = mate_feature(asm, made[0])
    feature.Name = name                                   # read it back: SolidWorks renames on collision
    return str(call(feature, "Name"))


def gear_mate_sense_read_back(asm, name, internal):
    """Whether a made gear mate turns its gears as they mesh, read back: exactly when
    (IGearMateFeatureData.Reverse == its two MateEntity directions point the same way) == internal."""
    feature = mate_feature(asm, name)
    reverse = bool(call(call(feature, "GetDefinition"), "Reverse"))
    mate = call(feature, "GetSpecificFeature2")
    d0, d1 = [list(call(call(mate, "MateEntity", i), "EntityParams"))[3:6] for i in (0, 1)]
    parallel = sum(a * b for a, b in zip(d0, d1)) > 0
    return (reverse == parallel) == internal, {"Reverse": reverse, "parallel": parallel}


def read_gear_ratio(asm, name):
    """IFeature.GetDefinition of a gear mate, its two ratio fields read; nothing modified."""
    data = call(mate_feature(asm, name), "GetDefinition")    # an IGearMateFeatureData
    ratio = (float(call(data, "GearRatioNumerator")), float(call(data, "GearRatioDenominator")))
    reverse = bool(call(data, "Reverse"))
    del data                                                  # released
    return ratio, reverse


def make_mate_folder(asm, mate_names, folder_name):
    """Select mates (IFeature.Select2, appended), then IFeatureManager.InsertFeatureTreeFolder2(2)."""
    call(asm, "ClearSelection2", True)
    for position, name in enumerate(mate_names):
        call(mate_feature(asm, name), "Select2", position > 0, 0)
    folder = call(call(asm, "FeatureManager"), "InsertFeatureTreeFolder2", FOLDER_CONTAINING)
    call(asm, "ClearSelection2", True)
    if folder is None:
        return None
    return rename(folder, folder_name)


def walk_mate_group(asm):
    """(name, GetTypeName2) of every MateGroup sub-feature, folder markers included."""
    return [(str(call(f, "Name")), str(call(f, "GetTypeName2"))) for f in mate_features(asm)]


def rebuild(asm, route):
    """One assembly rebuild by the route named; what it returned (None for no rebuild at all)."""
    if route == "ForceRebuild3(True)":
        return call(asm, "ForceRebuild3", True)       # top level only
    if route == "EditRebuild3":
        return call(asm, "EditRebuild3")
    if route == "ForceRebuild3(False)":
        return call(asm, "ForceRebuild3", False)      # everything
    return None


def doc_at(app, path):
    """The open document with this path, components loaded by an assembly included; None if not loaded."""
    want = os.path.normcase(os.path.abspath(path))
    doc = call(app, "GetFirstDocument")
    while doc is not None:
        have = str(call(doc, "GetPathName") or "")
        if have and os.path.normcase(os.path.abspath(have)) == want:
            return doc
        doc = call(doc, "GetNext")
    return None


def save_flags(app, paths):
    """GetSaveFlag of each labelled document; None for one not in memory."""
    out = {}
    for label, path in paths.items():
        doc = doc_at(app, path)
        out[label] = None if doc is None else bool(call(doc, "GetSaveFlag"))
    return out


def rebuild_status(doc):
    ext = call(doc, "Extension")
    return {"NeedsRebuild": read_member(ext, "NeedsRebuild"), "NeedsRebuild2": read_member(ext, "NeedsRebuild2")}


def insert(asm, path, x_m=0.0, y_m=0.0, z_m=0.0):
    """IAssemblyDoc.AddComponent5; None when SolidWorks would not insert it."""
    return call(asm, "AddComponent5", path, 0, "", False, "", x_m, y_m, z_m)


def open_doc(app, path, doc_type):
    """ISldWorks.OpenDoc6; returns (document, errors, warnings)."""
    errors, warnings = out_long(), out_long()
    doc = call(app, "OpenDoc6", path, doc_type, OPEN_SILENT, "", errors, warnings)
    return doc, errors.value, warnings.value


def activate(app, title):
    """ISldWorks.ActivateDoc3: bring an open document to the front."""
    return call(app, "ActivateDoc3", title, False, 0, out_long())


def save_as(doc, path):
    """IModelDocExtension.SaveAs3, current version, silent; it overwrites without asking."""
    return call(call(doc, "Extension"), "SaveAs3", path, SAVE_AS_CURRENT, SAVE_AS_SILENT,
                null(), null(), out_long(), out_long())


def documents(app):
    out, doc = [], call(app, "GetFirstDocument")
    while doc is not None:
        out.append(doc)
        doc = call(doc, "GetNext")
    return out


def save_created_parts(app, created):
    """Save, in place, every modified part this script made and had already saved to a path."""
    for doc in documents(app):
        title = str(call(doc, "GetTitle"))
        path = str(call(doc, "GetPathName") or "")
        if title in created and path and int(call(doc, "GetType")) == SW_DOC_PART and call(doc, "GetSaveFlag"):
            save_as(doc, path)


def quit_in(app, folder):
    """Close every open document under folder WITHOUT saving (ISldWorks.QuitDoc), assemblies
    first; returns the titles still open under it."""
    root = os.path.normcase(os.path.abspath(folder)) + os.sep

    def under(path):
        return bool(path) and os.path.normcase(os.path.abspath(path)).startswith(root)

    for kind in (SW_DOC_ASSEMBLY, SW_DOC_PART):
        for doc in documents(app):
            if under(str(call(doc, "GetPathName") or "")) and int(call(doc, "GetType")) == kind:
                call(app, "QuitDoc", str(call(doc, "GetTitle")))
    return [str(call(d, "GetTitle")) for d in documents(app) if under(str(call(d, "GetPathName") or ""))]


def close_in(app, folder):
    """The same with ISldWorks.CloseDoc."""
    root = os.path.normcase(os.path.abspath(folder)) + os.sep

    def under(path):
        return bool(path) and os.path.normcase(os.path.abspath(path)).startswith(root)

    for kind in (SW_DOC_ASSEMBLY, SW_DOC_PART):
        for doc in documents(app):
            if under(str(call(doc, "GetPathName") or "")) and int(call(doc, "GetType")) == kind:
                call(app, "CloseDoc", str(call(doc, "GetTitle")))
    return [str(call(d, "GetTitle")) for d in documents(app) if under(str(call(d, "GetPathName") or ""))]


def _invoke_method(obj, name, *args):
    """Invoke a COM member as a method, where late binding would reach it as a property get."""
    oleobj = obj._oleobj_
    return oleobj.Invoke(oleobj.GetIDsOfNames(name), 0, pythoncom.DISPATCH_METHOD, True, *args)


def axis_to_right_plane_m(asm, axis_ref):
    """IMeasure between a component's axis ("<axis>@<component>@<assembly>") and the assembly's Right plane."""
    ext = call(asm, "Extension")
    call(asm, "ClearSelection2", True)
    try:
        if not (call(ext, "SelectByID2", axis_ref, "AXIS", 0.0, 0.0, 0.0, False, 0, null(), 0)
                and selected_count(asm) == 1):
            return None
        if not select_feature(asm, planes(asm)[2], append=True) or selected_count(asm) != 2:
            return None
        measure = call(ext, "CreateMeasure")
        if measure is None or not _invoke_method(measure, "Calculate", null()):
            return None
        return float(call(measure, "Distance")), float(call(measure, "NormalDistance"))   # metres
    finally:
        call(asm, "ClearSelection2", True)


def create_transform(app, data16):
    """IMathUtility.CreateTransform invoked as a method with a double array (assemblies/04)."""
    utility = call(app, "GetMathUtility")
    oleobj = utility._oleobj_
    raw = oleobj.Invoke(oleobj.GetIDsOfNames("CreateTransform"), 0, pythoncom.DISPATCH_METHOD, True,
                        VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_R8, data16))
    return raw if hasattr(raw, "ArrayData") else dynamic.Dispatch(raw)


def frame_data(rotation_rows, origin_m):
    """16 numbers for CreateTransform: the rotation by columns, the origin in metres, scale 1, three zeros."""
    columns = [rotation_rows[i][j] for j in range(3) for i in range(3)]
    return columns + [float(v) for v in origin_m] + [1.0, 0.0, 0.0, 0.0]


def rot_z(degrees):
    c, s = math.cos(math.radians(degrees)), math.sin(math.radians(degrees))
    return ((c, -s, 0.0), (s, c, 0.0), (0.0, 0.0, 1.0))


def frame_of(component):
    """A component's rotation (rows) and origin (metres) from Transform2.ArrayData."""
    d = [float(v) for v in call(call(component, "Transform2"), "ArrayData")]
    rows = tuple(tuple(d[j * 3 + i] for j in range(3)) for i in range(3))
    return rows, (d[9], d[10], d[11])


def turn_about_z(before_rows, after_rows):
    """The turn, in degrees, from one frame to another about +Z."""
    x0 = math.atan2(before_rows[1][0], before_rows[0][0])
    x1 = math.atan2(after_rows[1][0], after_rows[0][0])
    return (math.degrees(x1 - x0) + 180.0) % 360.0 - 180.0


def put_frame(app, asm, component, rotation_rows, origin_m, top_only=True):
    """IComponent2.Transform2 put, then the rebuild."""
    component.Transform2 = create_transform(app, frame_data(rotation_rows, origin_m))
    return call(asm, "ForceRebuild3", top_only)


def turn_about_own_axis(component, degrees):
    """The relative move x' = R x + (p - R p): a turn about the component's own Z axis through its
    origin, as 16 numbers (rotation by columns, translation in metres, scale 1, three zeros)."""
    d = [float(v) for v in call(call(component, "Transform2"), "ArrayData")]
    axis, p = d[6:9], d[9:12]                    # the component's Z column, and its origin
    x, y, z = axis
    c, s = math.cos(math.radians(degrees)), math.sin(math.radians(degrees))
    k = 1.0 - c
    r = ((c + x * x * k, x * y * k - z * s, x * z * k + y * s),
         (y * x * k + z * s, c + y * y * k, y * z * k - x * s),
         (z * x * k - y * s, z * y * k + x * s, c + z * z * k))
    rp = [sum(r[i][j] * p[j] for j in range(3)) for i in range(3)]
    columns = [r[i][j] for j in range(3) for i in range(3)]
    return columns + [p[i] - rp[i] for i in range(3)] + [1.0, 0.0, 0.0, 0.0]


def drag_by_recipe(app, asm, component, degrees, steps):
    """assemblies/05's recipe: AddComponent(component, False), TransformType 0, UseAbsoluteTransform
    False, DragMode as it came, BeginDrag, one relative Drag per step about the component's own axis,
    EndDrag. What each call answered."""
    op = read_member(asm, "GetDragOperator")
    out = {"DragMode as it came": read_member(op, "DragMode")}
    out["AddComponent"] = call(op, "AddComponent", component, False)
    op.TransformType = 0
    op.UseAbsoluteTransform = False
    out["BeginDrag"] = read_member(op, "BeginDrag")
    step = create_transform(app, turn_about_own_axis(component, degrees / steps))
    try:
        out["Drag"] = [call(op, "Drag", step) for _ in range(steps)]
    finally:
        out["EndDrag"] = read_member(op, "EndDrag")
    return out


def global_index(eqm, name):
    for index in range(int(call(eqm, "GetCount"))):
        if re.match(rf'^\s*"{re.escape(name)}"\s*=', str(call(eqm, "Equation", index))):
            return index
    return None


def set_global(eqm, name, value):
    """Change a global in place by an indexed put of Equation(i); what it reads back."""
    index = global_index(eqm, name)
    put_indexed(eqm, "Equation", index, f'"{name}"= {value:g}')
    return str(call(eqm, "Equation", index))


def dimensions_of(feature):
    """IFeature.GetFirstDisplayDimension / GetNextDisplayDimension, each IDisplayDimension.GetDimension2(0)."""
    out, display = [], call(feature, "GetFirstDisplayDimension")
    while display is not None:
        out.append(call(display, "GetDimension2", 0))
        display = call(feature, "GetNextDisplayDimension", display)
    return out


# -- fixtures --------------------------------------------------------------------------------

def new_document(app, doc_type):
    template = call(app, "GetUserPreferenceStringValue", PART_TEMPLATE if doc_type == SW_DOC_PART
                    else ASSEMBLY_TEMPLATE)
    doc = call(app, "NewDocument", template, 0, 0.0, 0.0)
    if doc is None:
        raise RuntimeError(f"NewDocument returned nothing for document type {doc_type}")
    return doc


def last_feature(doc):
    return call(doc, "FeatureByPositionReverse", 0)


def cylinder_part(app, path, radii=(BLANK_R,)):
    """A saved cylinder r 20 x 10 mm (or, given two radii, an annulus) extruded from the Front plane,
    with "Gear Axis" made from Top then Right."""
    doc = new_document(app, SW_DOC_PART)
    front, top, right = planes(doc)[:3]
    if not select_feature(doc, front):
        raise RuntimeError("the Front plane did not select")
    manager = call(doc, "SketchManager")
    manager.AddToDB = True
    call(manager, "InsertSketch", True)
    call(doc, "ClearSelection2", True)
    for radius in radii:
        call(manager, "CreateCircleByRadius", 0.0, 0.0, 0.0, radius)
    call(manager, "InsertSketch", True)
    manager.AddToDB = False
    sketch = last_feature(doc)
    if not select_feature(doc, sketch):
        raise RuntimeError("the sketch did not select")
    blank = call(call(doc, "FeatureManager"), "FeatureExtrusion3", True, False, False, 0, 0, BLANK_W, 0.0,
                 False, False, False, False, 0.0, 0.0, False, False, False, False, True, True, True, 0, 0.0,
                 False)
    call(doc, "ClearSelection2", True)
    if blank is None:
        raise RuntimeError("FeatureExtrusion3 returned nothing")
    rename(blank, "Blank")
    if not (select_feature(doc, top) and select_feature(doc, right, append=True)):
        raise RuntimeError("Top and Right did not select for the axis")
    call(doc, "InsertAxis2", True)
    call(doc, "ClearSelection2", True)
    axis = last_feature(doc)
    rename(axis, "Gear Axis")
    if not save_as(doc, path) or not os.path.isfile(path):
        raise RuntimeError("the part did not save")
    return doc


def layout_part(app, path):
    """A body-less skeleton: per shaft a plane offset from Right by X and one from Top by Y, and an axis
    "<shaft> Axis" through them, the Top-parallel plane selected first (so the axis reads +Z)."""
    doc = new_document(app, SW_DOC_PART)
    top, right = planes(doc)[1], planes(doc)[2]
    feature_manager = call(doc, "FeatureManager")
    for shaft, x, y in SHAFTS:
        made = {}
        for base, value, letter in ((right, x, "X"), (top, y, "Y")):
            if not select_feature(doc, base):
                raise RuntimeError(f"{call(base, 'Name')} did not select")
            plane = call(feature_manager, "InsertRefPlane", PLANE_DISTANCE, value, 0, 0.0, 0, 0.0)
            call(doc, "ClearSelection2", True)
            if plane is None:
                raise RuntimeError(f"InsertRefPlane made nothing for {shaft} {letter}")
            rename(plane, f"{shaft} {letter} Plane")
            made[letter] = plane
        if not (select_feature(doc, made["Y"]) and select_feature(doc, made["X"], append=True)):
            raise RuntimeError(f"{shaft}'s planes did not select")
        call(doc, "InsertAxis2", True)
        call(doc, "ClearSelection2", True)
        rename(last_feature(doc), f"{shaft} Axis")
    call(doc, "ForceRebuild3", False)
    if not save_as(doc, path) or not os.path.isfile(path):
        raise RuntimeError("the skeleton did not save")
    return doc


def plane_names(component):
    return [str(call(p, "Name")) for p in planes(call(component, "GetModelDoc2"))]


# -- session, safety, recording ---------------------------------------------------------------

MONIKER = re.compile(r"^SolidWorks_PID_(\d+)$", re.IGNORECASE)


def solidworks_in_rot():
    """(pid, moniker) of every SolidWorks registered in the Running Object Table; nothing is attached."""
    rot, ctx, out = pythoncom.GetRunningObjectTable(), pythoncom.CreateBindCtx(0), []
    for moniker in rot.EnumRunning():
        try:
            name = moniker.GetDisplayName(ctx, None)
        except pythoncom.com_error:
            continue
        match = MONIKER.match(name)
        if match:
            out.append((int(match.group(1)), moniker))
    return out


def attach(moniker):
    rot = pythoncom.GetRunningObjectTable()
    return dynamic.Dispatch(rot.GetObject(moniker).QueryInterface(pythoncom.IID_IDispatch))


class Recorder:
    """Steps and their facts; written to <out>/gear-train-check-<stamp>.{json,txt} after every step."""

    def __init__(self, out_dir, scratch):
        self.out_dir, self.scratch = out_dir, scratch
        self.stamp = time.strftime("%Y%m%d-%H%M%S")
        self.meta = {"stamp": self.stamp, "runner": "code/python/gear_train/gear_train_check.py"}
        self.steps, self.dialogs, self.current = [], [], None
        self.lock = threading.Lock()

    def scrub(self, value):
        """No scratch path, home folder or user name in what is written, however many times escaped."""
        text = json.dumps(value, default=repr)
        separator = r"(?:\\+|/)"
        parts = [re.escape(part) for part in re.split(r"[\\/]+", self.scratch) if part]
        text = re.sub(separator.join(parts), "<scratch>", text, flags=re.IGNORECASE)
        text = re.sub(r"[A-Za-z]:" + separator + r"Users" + separator + r"[^\\/\"']+", "<home>", text,
                      flags=re.IGNORECASE)
        user = os.environ.get("USERNAME") or ""
        if len(user) > 2:
            text = re.sub(re.escape(user), "<user>", text, flags=re.IGNORECASE)
        return json.loads(text)

    def write(self):
        with self.lock:
            os.makedirs(self.out_dir, exist_ok=True)
            data = self.scrub({"meta": self.meta, "steps": self.steps, "dialogs": self.dialogs,
                               "summary": self.summary()})
            base = os.path.join(self.out_dir, f"gear-train-check-{self.stamp}")
            with open(base + ".json", "w", encoding="utf-8") as handle:
                json.dump(data, handle, indent=1, sort_keys=True)
            with open(base + ".txt", "w", encoding="utf-8") as handle:
                handle.write(f"{data['meta']}\n")
                for step in data["steps"]:
                    handle.write(f"\n{step['status'].upper():5} {step['name']} ({step.get('seconds')} s)\n")
                    if step.get("error"):
                        handle.write(f"      error: {step['error']}\n")
                    for key, value in step["facts"].items():
                        handle.write(f"      {key} = {json.dumps(value)}\n")
                for dialog in data["dialogs"]:
                    handle.write(f"\nDIALOG {dialog}\n")
                handle.write(f"\n{data['summary']}\n")

    def summary(self):
        out = {}
        for step in self.steps:
            out[step["status"]] = out.get(step["status"], 0) + 1
        return out

    def step(self, name):
        recorder = self

        class Step:
            def __enter__(self):
                self.record = {"name": name, "status": "running", "facts": {}, "started": time.time()}
                with recorder.lock:
                    recorder.steps.append(self.record)
                    recorder.current = self.record
                print(f"step  {name}", flush=True)
                return self

            def fact(self, key, value):
                self.record["facts"][key] = value

            def check(self, ok, what):
                self.record["facts"].setdefault("checks", []).append([bool(ok), what])
                if not ok:
                    self.record["status"] = "fail"
                return ok

            def __exit__(self, kind, exc, tb):
                self.record["seconds"] = round(time.time() - self.record.pop("started"), 2)
                if exc is not None:
                    self.record["status"] = "error"
                    self.record["error"] = "".join(traceback.format_exception_only(kind, exc)).strip()
                elif self.record["status"] == "running":
                    self.record["status"] = "pass"
                print(f"      {self.record['status']} ({self.record['seconds']} s)", flush=True)
                recorder.current = None
                recorder.write()
                return True     # record and go on: later steps report what they can

        return Step()


def watch_dialogs(pid, recorder, stop):
    """Log every visible dialog box (#32770) of the SolidWorks process. Never answers one."""
    seen = set()
    while not stop.is_set():
        found = []

        def each(hwnd, _):
            try:
                if win32gui.IsWindowVisible(hwnd) and win32gui.GetClassName(hwnd) == "#32770" and \
                        win32process.GetWindowThreadProcessId(hwnd)[1] == pid:
                    children = []
                    win32gui.EnumChildWindows(hwnd, lambda h, acc: acc.append(win32gui.GetWindowText(h)), children)
                    found.append((hwnd, win32gui.GetWindowText(hwnd), tuple(t for t in children if t)))
            except Exception:  # noqa: BLE001 - a window may vanish mid-read
                pass
            return True

        try:
            win32gui.EnumWindows(each, None)
        except Exception:  # noqa: BLE001
            pass
        for hwnd, title, texts in found:
            if (hwnd, title, texts) not in seen:
                seen.add((hwnd, title, texts))
                step = recorder.current["name"] if recorder.current else None
                with recorder.lock:
                    recorder.dialogs.append({"step": step, "title": title, "texts": list(texts),
                                             "at": time.strftime("%H:%M:%S")})
                print(f"DIALOG during {step}: {title!r} {list(texts)}", flush=True)
        stop.wait(0.5)


def watchdog(recorder, pid, timeout, stop):
    """Kill the SolidWorks this script started if one step runs past the timeout; write what there is."""
    while not stop.wait(5.0):
        current = recorder.current
        if current and time.time() - current.get("started", time.time()) > timeout:
            current["status"] = "hung"
            current["error"] = f"no answer in {timeout} s; SolidWorks (the one this script started) was killed"
            recorder.write()
            subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"], capture_output=True)
            print(f"HUNG  {current['name']}: killed SolidWorks PID {pid}", flush=True)
            os._exit(3)


# -- the run ----------------------------------------------------------------------------------

def run(app, scratch, rec):
    """Every step, in order. Each records what it saw; a failing step does not stop the next."""
    base = os.path.join(scratch, "train")
    os.makedirs(base)
    paths = {name: os.path.join(base, f"{name}.SLDPRT") for name, *_ in GEARS}
    paths["Layout"] = os.path.join(base, "Layout.SLDPRT")
    paths["Pinion"] = os.path.join(base, "Pinion.SLDPRT")
    paths["Ring"] = os.path.join(base, "Ring.SLDPRT")
    paths["Train"] = os.path.join(base, "Train.SLDASM")
    state = {}

    with rec.step("fixtures: four cylinders and a skeleton, saved") as s:
        for name, *_ in GEARS:
            cylinder_part(app, paths[name])
        cylinder_part(app, paths["Pinion"])
        cylinder_part(app, paths["Ring"], (RING_OUTER, RING_INNER))
        layout_part(app, paths["Layout"])
        s.fact("files", sorted(os.path.basename(p) for p in os.listdir(base)))
        s.check(all(os.path.isfile(paths[k]) for k in paths if k != "Train"), "every part saved")

    with rec.step("train: inserted, placed and fixed") as s:
        asm = new_document(app, SW_DOC_ASSEMBLY)
        layout = insert(asm, paths["Layout"])
        put_frame(app, asm, layout, rot_z(0.0), (0.0, 0.0, 0.0))
        s.check(fix(asm, layout), "the skeleton is fixed")
        shafts = {shaft: (x, y) for shaft, x, y in SHAFTS}
        gears = {}
        for name, shaft, z, turned in GEARS:
            x, y = shafts[shaft]
            component = insert(asm, paths[name], x, y, z)
            s.check(component is not None, f"{name} is inserted")
            put_frame(app, asm, component, rot_z(turned), (x, y, z))
            fix(asm, component)
            gears[name] = component
        state.update(asm=asm, layout=layout, gears=gears)
        s.fact("components", {k: str(call(c, "Name2")) for k, c in gears.items()})
        state["placed"] = {k: frame_of(c) for k, c in gears.items()}

    asm, layout, gears = state["asm"], state["layout"], state["gears"]
    front = plane_names(layout)[0]

    with rec.step("shaft mates: concentric refused, coincident held, corresponding selection") as s:
        s.check(unfix(asm, gears["GearD"]), "GearD floats")
        if select_feature_of(asm, gears["GearD"], "Gear Axis", False) and \
                select_feature_of(asm, layout, "S3 Axis", True):
            mate, status, made = add_mate(asm, CONCENTRIC, CLOSEST)
            s.fact("concentric between two axes", {"returned": None if mate is None else type(mate).__name__,
                                                   "status": status, "made": made})
            if made:               # not expected; never leave it in the train
                s.fact("unexpected concentric deleted", delete_mate(asm, made[0]))
        s.fact("select_by_corresponding Gear Axis", select_by_corresponding(asm, gears["GearB"], "Gear Axis", False))
        s.fact("selected after it", selected_count(asm))
        call(asm, "ClearSelection2", True)
        held = {}
        for name, shaft, z, _ in GEARS:
            if name == "GearC":
                continue
            answers = hold_on_shaft(asm, gears[name], layout, f"{shaft} Axis", front, z)
            names = [rename(mate_feature(asm, made[0]), label)
                     for (_, _, made), label in zip(answers, (f"{name} on {shaft} Axis", f"{name} along {shaft}"))]
            held[name] = {"statuses": [a[1] for a in answers], "renamed": names}
        s.fact("held", held)
        s.check(all(v["statuses"] == [1, 1] for v in held.values()), "every shaft mate solved (status 1)")

    with rec.step("lock and gear mates, each renamed straight after AddMate5") as s:
        s.check(unfix(asm, gears["GearC"]), "GearC floats")
        s.fact("lock selection", select_components(asm, (gears["GearB"], gears["GearC"])))
        mate, status, made = add_mate(asm, LOCK, CLOSEST)
        s.fact("lock", {"status": status, "renamed": rename(mate_feature(asm, made[0]), "GearC locked to GearB")})
        for first, second in (("GearA", "GearB"), ("GearC", "GearD")):
            select_feature_of(asm, gears[first], "Gear Axis", False)
            select_feature_of(asm, gears[second], "Gear Axis", True)
            mate, status, made = add_mate(asm, GEAR, CLOSEST, flip=False, ratio=(TEETH[first], TEETH[second]))
            s.fact(f"{first} meshes {second}", {"status": status, "ratio_passed": [TEETH[first], TEETH[second]],
                                                "renamed": rename(mate_feature(asm, made[0]), f"{first} meshes {second}")})
        s.fact("rebuild", call(asm, "ForceRebuild3", True))
        s.fact("errors", {str(call(f, "Name")): list(error_code(f)) for f in mate_features(asm)})
        s.fact("constrained", {k: constrained_status(c) for k, c in gears.items()})
        moved = {k: max(abs(a - b) for a, b in zip(frame_of(c)[1], state["placed"][k][1])) * MM
                 for k, c in gears.items()}
        s.fact("moved_mm_by_mating", moved)
        s.check(max(moved.values()) < 1e-6, "no gear moved when mated")
        for name in ("GearA meshes GearB", "GearC meshes GearD"):
            ratio, reverse = read_gear_ratio(asm, name)
            entity = call(call(mate_feature(asm, name), "GetSpecificFeature2"), "MateEntity", 0)
            s.fact(f"{name} read back", {"ratio": list(ratio), "Reverse": reverse,
                                         "MateEntity(0)": str(call(call(entity, "ReferenceComponent"), "Name2"))})
            s.fact(f"{name} sense read back", gear_mate_sense_read_back(asm, name, internal=False))

    with rec.step("drive: an angle mate on a global, and the turns") as s:
        eqm = call(asm, "GetEquationMgr")
        s.fact("global added", call(eqm, "Add2", -1, f'"Drive"= {DRIVE_FROM:g}', True))
        select_feature_of(asm, gears["GearA"], plane_names(gears["GearA"])[1], False)
        select_feature_of(asm, layout, plane_names(layout)[1], True)
        mate, status, made = add_mate(asm, ANGLE, CLOSEST, angle_rad=math.radians(DRIVE_FROM))
        drive = rename(mate_feature(asm, made[0]), "Drive Angle")
        dims = [str(call(d, "Name")) for d in dimensions_of(mate_feature(asm, drive))]
        s.fact("drive mate", {"status": status, "name": drive, "dimensions": dims})
        s.fact("link", call(eqm, "Add2", -1, f'"{dims[0]}@{drive}"= "Drive"', True))
        s.fact("rebuild", call(asm, "ForceRebuild3", True))
        s.fact("constrained driven", {k: constrained_status(c) for k, c in gears.items()})
        before = {k: frame_of(c)[0] for k, c in gears.items()}
        s.fact("set", set_global(eqm, "Drive", DRIVE_TO))
        s.fact("rebuild after", call(asm, "ForceRebuild3", True))
        turns = {k: round(turn_about_z(before[k], frame_of(c)[0]), 9) for k, c in gears.items()}
        s.fact("turns", turns)
        a = turns["GearA"]
        want = {"GearA": a, "GearB": -a * 20 / 40, "GearC": -a * 20 / 40, "GearD": a * 20 / 40 * 20 / 50}
        s.check(all(abs(turns[k] - want[k]) < 1e-6 for k in want), f"turns as the ratios say: {want}")
        state["eqm"] = eqm

    with rec.step("measure: a skeleton axis to the assembly's Right plane") as s:
        title = str(call(asm, "GetTitle")).rsplit(".", 1)[0]
        got = axis_to_right_plane_m(asm, f"S2 Axis@{call(layout, 'Name2')}@{title}")
        s.fact("distance_normal_m", got)
        s.check(got is not None and abs(got[0] - SHAFTS[1][1]) < 1e-9, "the measure reads S2's X")

    with rec.step("save the train and close everything") as s:
        s.fact("saved", save_as(asm, paths["Train"]))
        save_created_parts(app, {os.path.basename(p) for p in paths.values()})
        s.fact("left open", close_in(app, base))

    def reopen(folder):
        doc, errors, warnings = open_doc(app, os.path.join(folder, "Train.SLDASM"), SW_DOC_ASSEMBLY)
        components = {name: call(doc, "GetComponentByName", f"{name}-1") for name, *_ in GEARS}
        return doc, components, call(doc, "GetComponentByName", "Layout-1"), {"errors": errors, "warnings": warnings}

    with rec.step("reopened: save flags, resolved state, gear mate definitions read") as s:
        asm, gears, layout, opened = reopen(base)
        s.fact("open", opened)
        files = {k: v for k, v in paths.items()}
        s.fact("flags on open", save_flags(app, files))
        s.fact("GetSuppression2", {k: call(c, "GetSuppression2") for k, c in gears.items()})
        s.fact("ratios read", {n: list(read_gear_ratio(asm, n)[0]) for n in ("GearA meshes GearB", "GearC meshes GearD")})
        s.fact("flags after the reads", save_flags(app, files))
        s.fact("walk", walk_mate_group(asm))
        state.update(asm=asm, gears=gears, layout=layout, eqm=call(asm, "GetEquationMgr"))

    asm, gears, layout, eqm = state["asm"], state["gears"], state["layout"], state["eqm"]
    files = dict(paths)

    def drive_by(step_deg):
        index = global_index(eqm, "Drive")
        value = float(call(eqm, "Value", index))
        before = {k: frame_of(c)[0] for k, c in gears.items()}
        set_global(eqm, "Drive", value + step_deg)
        call(asm, "ForceRebuild3", True)
        return {k: round(turn_about_z(before[k], frame_of(c)[0]), 9) for k, c in gears.items()}

    with rec.step("unsuppress a lock that is already on: the save flags straight around the call") as s:
        before = save_flags(app, files)
        s.fact("returned", call(mate_feature(asm, "GearC locked to GearB"), "SetSuppression2", UNSUPPRESS,
                                THIS_CONFIGURATION, None))
        s.fact("flags before", before)
        s.fact("flags after", save_flags(app, files))
        s.fact("suppressed after", is_suppressed(mate_feature(asm, "GearC locked to GearB")))

    with rec.step("re-phase: a put on GearD with its gear mate on, then a drive") as s:
        rows, origin = frame_of(gears["GearD"])
        others = {k: frame_of(c) for k, c in gears.items() if k != "GearD"}
        turned = tuple(tuple(sum(rot_z(7.0)[i][k] * rows[k][j] for k in range(3)) for j in range(3)) for i in range(3))
        s.fact("put rebuild", put_frame(app, asm, gears["GearD"], turned, origin))
        s.fact("GearD kept", round(turn_about_z(rows, frame_of(gears["GearD"])[0]), 9))
        s.fact("others turned", {k: round(turn_about_z(v[0], frame_of(gears[k])[0]), 9) for k, v in others.items()})
        s.fact("drive +10", drive_by(10.0))

    with rec.step("a put on GearC with its lock on, then a drive") as s:
        rows, origin = frame_of(gears["GearC"])
        b_rows = frame_of(gears["GearB"])[0]
        turned = tuple(tuple(sum(rot_z(5.0)[i][k] * rows[k][j] for k in range(3)) for j in range(3)) for i in range(3))
        put_frame(app, asm, gears["GearC"], turned, origin)
        s.fact("GearC turned", round(turn_about_z(rows, frame_of(gears["GearC"])[0]), 9))
        s.fact("GearB turned", round(turn_about_z(b_rows, frame_of(gears["GearB"])[0]), 9))
        s.fact("errors", {n: list(error_code(f)) for f in mate_features(asm)
                          for n in [str(call(f, "Name"))] if error_code(f)[0]})
        s.fact("drive +10", drive_by(10.0))

    with rec.step("over-define, error codes, What's Wrong, suppressed reads 0, delete") as s:
        b, c = gears["GearB"], gears["GearC"]
        relative = turn_about_z(frame_of(b)[0], frame_of(c)[0])
        select_feature_of(asm, c, plane_names(c)[1], False)
        select_feature_of(asm, b, plane_names(b)[1], True)
        mate, status, made = add_mate(asm, ANGLE, CLOSEST, angle_rad=math.radians(abs(relative) + 10.0))
        s.fact("conflicting angle", {"status": status, "made": made, "relative_deg": round(relative, 6)})
        s.fact("rebuild", call(asm, "ForceRebuild3", True))
        s.fact("errors", {n: list(error_code(f)) for f in mate_features(asm)
                          for n in [str(call(f, "Name"))] if error_code(f)[0]})
        s.fact("whats_wrong", whats_wrong(asm))
        s.fact("constrained", {"GearB": constrained_status(b), "GearC": constrained_status(c)})
        if made:
            s.fact("suppressed", set_suppressed(asm, made[0], True))
            s.fact("suppressed conflict's code", list(error_code(mate_feature(asm, made[0]))))
            s.fact("deleted", delete_mate(asm, made[0]))
            call(asm, "ForceRebuild3", True)
            s.fact("errors after", {n: list(error_code(f)) for f in mate_features(asm)
                                    for n in [str(call(f, "Name"))] if error_code(f)[0]})
            s.fact("constrained after", {"GearB": constrained_status(b), "GearC": constrained_status(c)})

    with rec.step("suppress and unsuppress the lock") as s:
        s.fact("suppressed", set_suppressed(asm, "GearC locked to GearB", True))
        s.fact("its code while suppressed", list(error_code(mate_feature(asm, "GearC locked to GearB"))))
        s.fact("unsuppressed", set_suppressed(asm, "GearC locked to GearB", False))
        call(asm, "ForceRebuild3", True)

    with rec.step("remake GearC meshes GearD at a new ratio") as s:
        before = [n for n, _ in walk_mate_group(asm)]
        s.fact("remade", remake_gear_mate(asm, "GearC meshes GearD", "GearC-1", "GearD-1", TEETH["GearC"], NEW_TEETH_D))
        after = [n for n, _ in walk_mate_group(asm)]
        s.fact("position", {"before": before.index("GearC meshes GearD"), "after": after.index("GearC meshes GearD"),
                            "count": len(after)})
        s.fact("read back", list(read_gear_ratio(asm, "GearC meshes GearD")[0]))
        call(asm, "ForceRebuild3", True)
        turns = drive_by(10.0)
        s.fact("drive +10", turns)
        s.check(abs(turns["GearD"] - turns["GearA"] * 20 / 40 * 20 / NEW_TEETH_D) < 1e-6, "GearD at the new ratio")

    with rec.step("drag GearD by assemblies/05's recipe, the drive suppressed") as s:
        s.fact("drive suppressed", set_suppressed(asm, "Drive Angle", True))
        call(asm, "ForceRebuild3", True)
        before = {k: frame_of(c)[0] for k, c in gears.items()}
        s.fact("calls", drag_by_recipe(app, asm, gears["GearD"], 10.0, 10))
        s.fact("turns", {k: round(turn_about_z(before[k], frame_of(c)[0]), 9) for k, c in gears.items()})
        s.fact("drive unsuppressed", set_suppressed(asm, "Drive Angle", False))
        call(asm, "ForceRebuild3", True)

    with rec.step("mate folders: one, nested, suppressed") as s:
        s.fact("outer", make_mate_folder(asm, ["GearC locked to GearB", "GearC meshes GearD"], "Folder A"))
        s.fact("inner", make_mate_folder(asm, ["GearC meshes GearD"], "Folder B"))
        call(asm, "ForceRebuild3", True)
        s.fact("walk", walk_mate_group(asm))
        s.fact("FeatureByName", {n: call(asm, "FeatureByName", n) is not None
                                 for n in ("GearC locked to GearB", "GearC meshes GearD")})
        folder = mate_feature(asm, "Folder A")
        s.fact("folder suppressed", call(folder, "SetSuppression2", SUPPRESS, THIS_CONFIGURATION, None))
        s.fact("mates then suppressed", {n: is_suppressed(mate_feature(asm, n))
                                         for n in ("GearC locked to GearB", "GearC meshes GearD")})
        s.fact("folder unsuppressed", call(folder, "SetSuppression2", UNSUPPRESS, THIS_CONFIGURATION, None))
        s.fact("mates after", {n: is_suppressed(mate_feature(asm, n))
                               for n in ("GearC locked to GearB", "GearC meshes GearD")})
        call(asm, "ForceRebuild3", True)
        s.fact("saved", save_as(asm, paths["Train"]))
        save_created_parts(app, {os.path.basename(p) for p in paths.values()})
        s.fact("left open", close_in(app, base))

    with rec.step("mate folders after a reopen") as s:
        asm, gears, layout, opened = reopen(base)
        s.fact("walk", walk_mate_group(asm))
        s.fact("FeatureByName", {n: call(asm, "FeatureByName", n) is not None
                                 for n in ("GearC locked to GearB", "GearC meshes GearD")})
        s.fact("left open", close_in(app, base))

    for route in ("ForceRebuild3(True)", "EditRebuild3", "ForceRebuild3(False)"):
        folder = os.path.join(scratch, {"ForceRebuild3(True)": "top", "EditRebuild3": "edit",
                                        "ForceRebuild3(False)": "full"}[route])
        shutil.copytree(base, folder)
        with rec.step(f"rebuild route {route}: what it marks") as s:
            local = {k: os.path.join(folder, os.path.basename(v)) for k, v in paths.items()}
            asm, gears, layout, opened = reopen(folder)
            eqm = call(asm, "GetEquationMgr")
            s.fact("flags on open", save_flags(app, local))
            index = global_index(eqm, "Drive")
            set_global(eqm, "Drive", float(call(eqm, "Value", index)) + 30.0)
            s.fact("status before the route, after a global", rebuild_status(asm))
            s.fact("returned", rebuild(asm, route))
            s.fact("status after the route", rebuild_status(asm))
            s.fact("flags after a global and the route", save_flags(app, local))
            skeleton, errors, warnings = open_doc(app, local["Layout"], SW_DOC_PART)
            s.fact("skeleton open", {"errors": errors, "warnings": warnings})
            activate(app, str(call(skeleton, "GetTitle")))
            plane = next(f for f in top_features(skeleton) if str(call(f, "Name")) == "S3 X Plane")
            dimension = dimensions_of(plane)[0]
            dimension.SystemValue = float(call(dimension, "SystemValue")) + 0.005
            s.fact("skeleton rebuild", call(skeleton, "ForceRebuild3", False))
            activate(app, str(call(asm, "GetTitle")))
            d_before = frame_of(gears["GearD"])[1][0] * MM
            s.fact("status before the route, after the skeleton change", rebuild_status(asm))
            s.fact("GearD x before the route", round(d_before, 9))
            s.fact("returned after the skeleton change", rebuild(asm, route))
            s.fact("GearD x after", round(frame_of(gears["GearD"])[1][0] * MM, 9))
            s.fact("flags after the skeleton change and the route", save_flags(app, local))
            for doc in documents(app):     # nothing left to ask about on any version
                if str(call(doc, "GetPathName") or "").lower().startswith(folder.lower()) and call(doc, "GetSaveFlag"):
                    save_as(doc, str(call(doc, "GetPathName")))
            s.fact("left open", close_in(app, folder))

    for closer in ("CloseDoc", "QuitDoc"):
        folder = os.path.join(scratch, f"unsaved-{closer.lower()}")
        shutil.copytree(base, folder)
        with rec.step(f"unsaved close by {closer}, the changed part open in its own window") as s:
            local = {k: os.path.join(folder, os.path.basename(v)) for k, v in paths.items()}
            asm, gears, layout, opened = reopen(folder)
            part, errors, warnings = open_doc(app, local["GearD"], SW_DOC_PART)
            s.fact("part open", {"errors": errors, "warnings": warnings})
            activate(app, str(call(part, "GetTitle")))
            depth = dimensions_of(next(f for f in top_features(part) if str(call(f, "Name")) == "Blank"))[0]
            depth.SystemValue = float(call(depth, "SystemValue")) + 0.002
            s.fact("part rebuild", call(part, "ForceRebuild3", False))
            activate(app, str(call(asm, "GetTitle")))
            s.fact("assembly rebuild", call(asm, "ForceRebuild3", True))
            s.fact("flags before the close", save_flags(app, local))
            stamps = {name: os.path.getmtime(os.path.join(folder, name)) for name in os.listdir(folder)
                      if not name.startswith("~$")}        # SolidWorks's own lock files come and go
            dialogs_before = len(rec.dialogs)
            started = time.time()
            if closer == "CloseDoc":
                call(app, "CloseDoc", str(call(asm, "GetTitle")))
            else:
                call(app, "QuitDoc", str(call(asm, "GetTitle")))
            s.fact("seconds for the assembly's close", round(time.time() - started, 2))
            time.sleep(1.0)
            s.fact("dialogs during it", rec.dialogs[dialogs_before:])
            s.fact("still open after the assembly", [str(call(d, "GetTitle")) for d in documents(app)])
            s.fact("flags then", save_flags(app, local))
            s.fact("left open", (close_in if closer == "CloseDoc" else quit_in)(app, folder))
            s.fact("files written", sorted(n for n, t in stamps.items()
                                           if not os.path.isfile(os.path.join(folder, n)) or
                                           os.path.getmtime(os.path.join(folder, n)) != t))

    with rec.step("insert a closed part; a second new assembly beside an unsaved one") as s:
        other = os.path.join(scratch, "second")
        os.makedirs(other)
        part_path = os.path.join(other, "GearA.SLDPRT")
        shutil.copyfile(paths["GearA"], part_path)
        first = new_document(app, SW_DOC_ASSEMBLY)
        s.fact("insert closed part", insert(first, part_path) is None)
        part, errors, warnings = open_doc(app, part_path, SW_DOC_PART)
        activate(app, str(call(first, "GetTitle")))
        made = {}
        for label, doc in (("unsaved", first), ("second", None)):
            if doc is None:
                doc = new_document(app, SW_DOC_ASSEMBLY)
            component = insert(doc, part_path)
            unfix(doc, component)
            select_feature_of(doc, component, plane_names(component)[0], False)
            select_feature(doc, planes(doc)[0], append=True, mark=1)
            mate, status, names = add_mate(doc, COINCIDENT, CLOSEST)
            made[label] = {"title": str(call(doc, "GetTitle")), "component": str(call(component, "Name2")),
                           "mate": names, "status": status, "doc": doc}
        saved_path = os.path.join(other, "Second.SLDASM")
        s.fact("second saved", save_as(made["second"]["doc"], saved_path))
        s.fact("second title after save", str(call(made["second"]["doc"], "GetTitle")))
        s.fact("assemblies", {k: {kk: vv for kk, vv in v.items() if kk != "doc"} for k, v in made.items()})
        call(app, "CloseDoc", str(call(made["second"]["doc"], "GetTitle")))
        call(app, "CloseDoc", made["unsaved"]["title"])
        s.fact("left open", close_in(app, other) + [str(call(d, "GetTitle")) for d in documents(app)])

    with rec.step("a pinion inside a plain annulus: the turn and the read-back, Flip False then True") as s:
        for key in ("Layout", "Ring", "Pinion"):
            open_doc(app, paths[key], SW_DOC_PART)
        pair = new_document(app, SW_DOC_ASSEMBLY)
        skeleton = insert(pair, paths["Layout"])
        put_frame(app, pair, skeleton, rot_z(0.0), (0.0, 0.0, 0.0))
        fix(pair, skeleton)
        shafts = {shaft: (x, y) for shaft, x, y in SHAFTS}
        parts = {}
        for key, shaft, turned in (("Ring", "S4", 0.0), ("Pinion", "S5", DRIVE_FROM)):
            x, y = shafts[shaft]
            parts[key] = insert(pair, paths[key], x, y, 0.0)
            put_frame(app, pair, parts[key], rot_z(turned), (x, y, 0.0))
            fix(pair, parts[key])
            hold_on_shaft(pair, parts[key], skeleton, f"{shaft} Axis", plane_names(skeleton)[0], 0.0)
        eqm = call(pair, "GetEquationMgr")
        call(eqm, "Add2", -1, f'"Drive"= {DRIVE_FROM:g}', True)
        select_feature_of(pair, parts["Pinion"], plane_names(parts["Pinion"])[1], False)
        select_feature_of(pair, skeleton, plane_names(skeleton)[1], True)
        mate, status, made = add_mate(pair, ANGLE, CLOSEST, angle_rad=math.radians(DRIVE_FROM))
        drive = rename(mate_feature(pair, made[0]), "Drive Angle")
        dims = [str(call(d, "Name")) for d in dimensions_of(mate_feature(pair, drive))]
        call(eqm, "Add2", -1, f'"{dims[0]}@{drive}"= "Drive"', True)
        call(pair, "ForceRebuild3", True)
        for flip in (False, True):
            if flip:
                delete_mate(pair, "Pinion meshes Ring")
            select_feature_of(pair, parts["Pinion"], "Gear Axis", False)
            select_feature_of(pair, parts["Ring"], "Gear Axis", True)
            mate, status, made = add_mate(pair, GEAR, CLOSEST, flip=flip, ratio=(20.0, 60.0))
            rename(mate_feature(pair, made[0]), "Pinion meshes Ring")
            call(pair, "ForceRebuild3", True)
            right, read = gear_mate_sense_read_back(pair, "Pinion meshes Ring", internal=True)
            before = {k: frame_of(c)[0] for k, c in parts.items()}
            value = float(call(eqm, "Value", global_index(eqm, "Drive")))
            set_global(eqm, "Drive", value + 30.0)
            call(pair, "ForceRebuild3", True)
            turns = {k: round(turn_about_z(before[k], frame_of(c)[0]), 9) for k, c in parts.items()}
            same_way = turns["Pinion"] * turns["Ring"] > 0
            s.fact(f"Flip {flip}", {"status": status, "read_back_says_right": right, **read, "turns": turns,
                                    "turned_as_it_meshes": same_way})
            s.check(right == same_way, f"Flip {flip}: the read-back agrees with the turn")
        call(app, "QuitDoc", str(call(pair, "GetTitle")))
        s.fact("left open", close_in(app, base))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--sldworks", required=True, help="path of the SLDWORKS.exe to start")
    parser.add_argument("--scratch", required=True, help="an empty or new folder on a local drive")
    parser.add_argument("--out", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "results"))
    parser.add_argument("--step-timeout", type=int, default=600)
    args = parser.parse_args(argv)

    scratch = os.path.abspath(args.scratch)
    if os.path.exists(scratch) and os.listdir(scratch):
        print(f"refused: {scratch} is not empty", file=sys.stderr)
        return 2
    os.makedirs(scratch, exist_ok=True)
    pythoncom.CoInitialize()
    if solidworks_in_rot():
        print("refused: another SolidWorks is already running; this script starts and exits its own", file=sys.stderr)
        return 2
    process = subprocess.Popen([args.sldworks])
    app, pid, deadline = None, None, time.time() + 600
    while app is None and time.time() < deadline:
        time.sleep(5)
        found = solidworks_in_rot()
        if found:                  # none was registered before the launch: this one is ours
            pid, app = found[0][0], attach(found[0][1])
    if app is None:
        process.kill()
        print("refused: SolidWorks did not register within 10 minutes", file=sys.stderr)
        return 2
    time.sleep(20)                 # let it finish loading before the first call
    if documents(app):
        print("refused: the SolidWorks attached has documents open that this script did not make", file=sys.stderr)
        return 2
    app.Visible = True

    rec = Recorder(os.path.abspath(args.out), scratch)
    rec.meta.update({"version": f"SolidWorks revision {call(app, 'RevisionNumber')}",
                     "revision": str(call(app, "RevisionNumber")), "python": sys.version.split()[0]})
    stop = threading.Event()
    threading.Thread(target=watch_dialogs, args=(pid, rec, stop), daemon=True).start()
    threading.Thread(target=watchdog, args=(rec, pid, args.step_timeout, stop), daemon=True).start()
    try:
        run(app, scratch, rec)
    except Exception:  # noqa: BLE001 - a fixture that failed ends the run; recorded
        rec.meta["stopped"] = traceback.format_exc()
    finally:
        with rec.step("close what is left and exit SolidWorks") as s:
            left = [str(call(d, "GetTitle")) for d in documents(app)]
            for doc in documents(app):
                if str(call(doc, "GetPathName") or "").lower().startswith(scratch.lower()) or \
                        not str(call(doc, "GetPathName") or ""):
                    call(app, "QuitDoc", str(call(doc, "GetTitle")))
            s.fact("left before", left)
            s.fact("left after", [str(call(d, "GetTitle")) for d in documents(app)])
            app.ExitApp()          # returns nothing: attribute access alone would only fetch it
        stop.set()
        rec.write()
        for _ in range(60):
            if process.poll() is not None or not any(p == pid for p, _ in solidworks_in_rot()):
                break
            time.sleep(1)
        else:
            subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"], capture_output=True)
            rec.meta["exit"] = "ExitApp did not end SolidWorks within 60 s; it was killed"
            rec.write()
        if "exit" not in rec.meta:
            rec.meta["exit"] = "ExitApp ended SolidWorks"
            rec.write()
    failed = [s["name"] for s in rec.steps if s["status"] != "pass"]
    print(f"done  {rec.summary()}; not passing: {failed}")
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())
