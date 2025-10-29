"""Spawn inputs + scale ×k + metal bars / panels (u/v, diagrid, inset, bake)"""
import System
from System import Decimal
import System.Drawing as sd
import Grasshopper.Kernel as ghk
import Grasshopper.Kernel.Special as ghs
import Rhino
import Rhino.Geometry as rg

# ---- stubs for editor warnings (Grasshopper injects these at runtime) ----
try:
    x, scale, style, uDiv, vDiv, thick, diag, barProfile, barW, barH, inset, triangulate, bake, layer
except NameError:
    x = scale = style = uDiv = vDiv = thick = diag = barProfile = barW = barH = inset = triangulate = bake = layer = None
# --------------------------------------------------------------------------

doc  = ghenv.Component.OnPingDocument()
comp = ghenv.Component

# --- auto-add any missing inputs/outputs (runs once) ---
want_in  = ["x","scale","style","uDiv","vDiv","thick","diag","barProfile","barW","barH","inset","triangulate","bake","layer"]
want_out = ["a","bars","panels"]

if doc and not getattr(comp, "_io_ready", False):
    have_in  = [p.NickName for p in comp.Params.Input]
    have_out = [p.NickName for p in comp.Params.Output]

    # add inputs with suitable param types
    for name in want_in[len(have_in):]:
        if name == "x":
            p = ghk.Parameters.Param_Geometry()
        elif name == "layer":
            p = ghk.Parameters.Param_String()
        elif name in ("style","uDiv","vDiv","barProfile"):
            p = ghk.Parameters.Param_Integer()
        elif name in ("diag","triangulate","bake"):
            p = ghk.Parameters.Param_Boolean()
        else:
            p = ghk.Parameters.Param_Number()
        p.Name = p.NickName = name
        comp.Params.RegisterInputParam(p)

    # add outputs
    for name in want_out[len(have_out):]:
        if name in ("bars","panels"):
            q = ghk.Parameters.Param_Brep()
        else:
            q = ghk.Parameters.Param_GenericObject()
        q.Name = q.NickName = name
        comp.Params.RegisterOutputParam(q)

    comp.Params.OnParametersChanged()
    comp._io_ready = True
    comp.ExpireSolution(True)  # re-run with new ports

# ---------- helpers for spawning UI controls & wiring (only when unwired) ----------
def _has_input(i):
    try: return i < len(comp.Params.Input)
    except: return False

def _is_wired(i):
    try: return comp.Params.Input[i].SourceCount > 0
    except: return True

def _pt(base, dx, dy):
    p = base.Pivot; return sd.PointF(p.X + dx, p.Y + dy)

def _add(obj):
    doc.AddObject(obj, False); return obj

def _wire_after(pairs):
    if not pairs: return
    def _wire(_doc):
        for i, src in pairs:
            try: comp.Params.Input[i].AddSource(src)
            except: pass
        comp.ExpireSolution(True)
    doc.ScheduleSolution(5, ghk.GH_Document.GH_ScheduleDelegate(_wire))

# ---------- SPAWN CONTROLS (only when unwired; runs once) ----------
if doc and not getattr(comp, "_spawned_ui", False):
    base = comp.Attributes
    to_wire = []

    def add_slider(nick, mn, mx, dps, val, off):
        s = ghs.GH_NumberSlider(); s.CreateAttributes()
        s.NickName = nick
        s.Slider.Minimum = Decimal(mn); s.Slider.Maximum = Decimal(mx)
        s.Slider.DecimalPlaces = int(dps); s.Slider.Value = Decimal(val)
        s.Attributes.Pivot = _pt(base, *off); return _add(s)

    def add_bool(nick, off, val=False):
        b = ghs.GH_BooleanToggle(); b.CreateAttributes()
        b.NickName = nick; b.Value = bool(val)
        b.Attributes.Pivot = _pt(base, *off); return _add(b)

    def add_list(nick, items, off):
        vl = ghs.GH_ValueList(); vl.CreateAttributes()
        vl.NickName = nick; vl.ListMode = ghs.GH_ValueListMode.DropDown
        vl.ListItems.Clear()
        from Grasshopper.Kernel.Special import GH_ValueListItem
        for name, expr in items: vl.ListItems.Add(GH_ValueListItem(name, expr))
        vl.Attributes.Pivot = _pt(base, *off); return _add(vl)

    def add_panel(nick, text, off):
        p = ghs.GH_Panel(); p.CreateAttributes(); p.NickName = nick
        p.UserText = text; p.Attributes.Pivot = _pt(base, *off); return _add(p)

    # x
    if _has_input(0) and not _is_wired(0):
        p_geo = ghk.Parameters.Param_Geometry(); p_geo.NickName = "x"; p_geo.CreateAttributes()
        p_geo.Attributes.Pivot = _pt(base, -220, 0); _add(p_geo); to_wire.append((0, p_geo))
    # scale
    if _has_input(1) and not _is_wired(1):
        s = add_slider("scale", 1, 10, 0, 6, (-220, 40)); to_wire.append((1, s))
    # style
    if _has_input(2) and not _is_wired(2):
        vl = add_list("style", [("Metal Bar","0"), ("Panels","1")], (-220, 80)); to_wire.append((2, vl))
    # u/v
    if _has_input(3) and not _is_wired(3):
        uS = add_slider("uDiv", 2, 100, 0, 20, (-220, 120)); to_wire.append((3, uS))
    if _has_input(4) and not _is_wired(4):
        vS = add_slider("vDiv", 2, 100, 0, 12, (-220, 160)); to_wire.append((4, vS))
    # thick
    if _has_input(5) and not _is_wired(5):
        tS = add_slider("thick", 0.05, 5, 2, 0.5, (-220, 200)); to_wire.append((5, tS))
    # diag
    if _has_input(6) and not _is_wired(6):
        dg = add_bool("diag", (-220, 240), False); to_wire.append((6, dg))
    # barProfile
    if _has_input(7) and not _is_wired(7):
        bp = add_list("barProfile", [("Round","0"), ("Rect","1")], (-220, 280)); to_wire.append((7, bp))
    # barW/H
    if _has_input(8) and not _is_wired(8):
        bw = add_slider("barW", 0.05, 10, 2, 0.5, (-220, 320)); to_wire.append((8, bw))
    if _has_input(9) and not _is_wired(9):
        bh = add_slider("barH", 0.05, 10, 2, 0.3, (-220, 360)); to_wire.append((9, bh))
    # inset
    if _has_input(10) and not _is_wired(10):
        ins = add_slider("inset", 0.0, 0.45, 2, 0.10, (-220, 400)); to_wire.append((10, ins))
    # triangulate
    if _has_input(11) and not _is_wired(11):
        tri = add_bool("triangulate", (-220, 440), False); to_wire.append((11, tri))
    # bake + layer
    if _has_input(12) and not _is_wired(12):
        bk = add_bool("bake", (-220, 480), False); to_wire.append((12, bk))
    if _has_input(13) and not _is_wired(13):
        ly = add_panel("layer", "fabrication", (-220, 520)); to_wire.append((13, ly))

    if to_wire: _wire_after(to_wire)
    comp._spawned_ui = True

# ---------- geometry helpers ----------
def unwrap(g):
    geo = getattr(g, "Geometry", None)
    if geo is not None: return geo
    try:
        import rhinoscriptsyntax as rs
        cg = rs.coercegeometry(g)
        if cg is not None: return cg
    except: pass
    return g

def dup(g):
    for name in ("Duplicate", "DuplicateShallow", "DuplicateBrep"):
        if hasattr(g, name):
            try: return getattr(g, name)()
            except: pass
    return g

def bbox_center(geos):
    bb = rg.BoundingBox.Empty
    for g in geos:
        try: bb = rg.BoundingBox.Union(bb, g.GetBoundingBox(True))
        except: pass
    return bb.Center

def largest_face(brep):
    if not isinstance(brep, rg.Brep) or brep.Faces.Count == 0: return None
    bestI, bestA = 0, -1.0
    for i in range(brep.Faces.Count):
        amp = rg.AreaMassProperties.Compute(brep.Faces[i])
        a = amp.Area if amp else 0.0
        if a > bestA: bestI, bestA = i, a
    return brep.Faces[bestI]

def face_grid(face, uN, vN):
    srf = face.ToNurbsSurface()
    du, dv = srf.Domain(0), srf.Domain(1)
    us = [du.ParameterAt(i/float(uN)) for i in range(uN+1)]
    vs = [dv.ParameterAt(j/float(vN)) for j in range(vN+1)]
    u_curves = [srf.IsoCurve(1, v) for v in vs]
    v_curves = [srf.IsoCurve(0, u) for u in us]
    pts = [[srf.PointAt(u,v) for v in vs] for u in us]
    return u_curves, v_curves, pts

def diagonal_curves_from_pts(pts):
    uLen, vLen = len(pts), len(pts[0])
    crvs = []
    for i in range(uLen-1):
        for j in range(vLen-1):
            crvs.append(rg.Polyline([pts[i][j], pts[i+1][j+1]]).ToNurbsCurve())
            crvs.append(rg.Polyline([pts[i+1][j], pts[i][j+1]]).ToNurbsCurve())
    return crvs

def pipes_from_curves(crvs, r):
    out = []
    for c in crvs:
        try:
            breps = rg.Brep.CreatePipe(c, r, False, rg.PipeCapMode.Flat, True, 0.01, 0.01)
            if breps: out.extend(breps)
        except: pass
    return out

def rect_sweep_from_curve(c, w, h, steps=12):
    t0, t1 = c.Domain.T0, c.Domain.T1
    ts = [t0 + (t1-t0)*i/float(steps) for i in range(steps+1)]
    sects = []
    for t in ts:
        ok, frame = c.FrameAt(t)
        if not ok: continue
        pl = rg.Plane(frame.Origin, frame.XAxis, frame.YAxis)
        rect = rg.Rectangle3d(pl, w, h)
        sects.append(rect.ToNurbsCurve())
    if len(sects) >= 2:
        try:
            brep = rg.Brep.CreateFromLoft(sects, rg.Point3d.Unset, rg.Point3d.Unset, rg.LoftType.Normal, False)
            if brep: return list(brep)
        except: pass
    return []

def inset_quad(p00, p10, p11, p01, f):
    if f <= 0: return [p00, p10, p11, p01]
    c = rg.Point3d((p00.X+p10.X+p11.X+p01.X)/4.0,
                   (p00.Y+p10.Y+p11.Y+p01.Y)/4.0,
                   (p00.Z+p10.Z+p11.Z+p01.Z)/4.0)
    def lerp(a): return rg.Point3d(a.X + (c.X-a.X)*f, a.Y + (c.Y-a.Y)*f, a.Z + (c.Z-a.Z)*f)
    return [lerp(p00), lerp(p10), lerp(p11), lerp(p01)]

def quads_or_tris_from_pts(pts, inset_f=0.0, tri=False):
    breps = []
    for i in range(len(pts)-1):
        for j in range(len(pts[0])-1):
            q = inset_quad(pts[i][j], pts[i+1][j], pts[i+1][j+1], pts[i][j+1], inset_f)
            if tri:
                if (i + j) % 2 == 0:
                    tris = [(q[0], q[1], q[2]), (q[0], q[2], q[3])]
                else:
                    tris = [(q[0], q[1], q[3]), (q[1], q[2], q[3])]
                for a,b,c in tris:
                    crv = rg.Polyline([a,b,c,a]).ToNurbsCurve()
                    res = rg.Brep.CreatePlanarBreps(crv, 0.01)
                    if res: breps.extend(res)
            else:
                pl = rg.Polyline(q + [q[0]]).ToNurbsCurve()
                res = rg.Brep.CreatePlanarBreps(pl, 0.01)
                if res: breps.extend(res)
    return breps

# ---------- read inputs & defaults ----------
geom_in = x if isinstance(x, (list, tuple)) else [x] if 'x' in globals() else []
geom_in = [unwrap(g) for g in geom_in if g is not None]

k = 6.0
try: k = float(scale) if scale is not None else 6.0
except: pass

_style = 0
try: _style = int(style) if style is not None else 0
except: pass

uN = 20
try: uN = max(2, int(uDiv)) if uDiv is not None else 20
except: pass

vN = 12
try: vN = max(2, int(vDiv)) if vDiv is not None else 12
except: pass

rDia = 0.5
try: rDia = float(thick) if thick is not None else 0.5
except: pass

_doDiag = False
try: _doDiag = bool(diag)
except: pass

_prof = 0
try: _prof = int(barProfile) if barProfile is not None else 0  # 0 round, 1 rect
except: pass

w = 0.5
try: w = float(barW) if barW is not None else 0.5
except: pass
h = 0.3
try: h = float(barH) if barH is not None else 0.3
except: pass

inset_f = 0.1
try: inset_f = max(0.0, min(0.45, float(inset))) if inset is not None else 0.1
except: pass

_doTri = False
try: _doTri = bool(triangulate)
except: pass

_doBake = False
try: _doBake = bool(bake)
except: pass

layer_name = "fabrication"
try:
    if isinstance(layer, str) and layer.strip():
        layer_name = layer.strip()
except: pass

# ---------- main ----------
if not geom_in:
    a = bars = panels = None
else:
    # scale input first
    pivot = bbox_center(geom_in)
    xf = rg.Transform.Scale(pivot, k)
    scaled = []
    for g in geom_in:
        g2 = dup(g)
        if hasattr(g2, "Transform"): g2.Transform(xf)
        scaled.append(g2)

    all_bars, all_panels = [], []

    for g in scaled:
        if isinstance(g, rg.Surface): g = rg.Brep.CreateFromSurface(g)
        if isinstance(g, rg.Brep):
            face = largest_face(g)
            if not face: continue
            uC, vC, P = face_grid(face, uN, vN)

            if _style == 0:  # Metal Bar
                crvs = diagonal_curves_from_pts(P) if _doDiag else (uC + vC)
                if _prof == 0:
                    all_bars += pipes_from_curves(crvs, rDia * 0.5)
                else:
                    for c in crvs:
                        all_bars += rect_sweep_from_curve(c, w, h)
            else:            # Panels
                all_panels += quads_or_tris_from_pts(P, inset_f=inset_f, tri=_doTri)
        else:
            # non-surface input: pass through (scaled)
            all_panels.append(g)

    # assign outputs
    a      = (all_bars if _style == 0 else all_panels) or None
    bars   = all_bars or None
    panels = all_panels or None

    # optional bake
    if _doBake and (all_bars or all_panels):
        rdoc = Rhino.RhinoDoc.ActiveDoc
        li = rdoc.Layers.FindByFullPath(layer_name, -1)
        if li < 0:
            li = rdoc.Layers.Add(layer_name, System.Drawing.Color.FromArgb(30,30,30))
        attr = Rhino.DocObjects.ObjectAttributes(); attr.LayerIndex = li
        for b in all_bars:
            try: rdoc.Objects.AddBrep(b, attr)
            except: pass
        for p in all_panels:
            try:
                if isinstance(p, rg.Brep): rdoc.Objects.AddBrep(p, attr)
                elif isinstance(p, rg.Extrusion): rdoc.Objects.AddExtrusion(p, attr)
            except: pass
        rdoc.Views.Redraw()
