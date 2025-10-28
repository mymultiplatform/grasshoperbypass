"""Spawn inputs + scale geometry ×k (Py3, Decimal-safe)"""
import System
from System import Decimal
import System.Drawing as sd
import Grasshopper.Kernel as ghk
import Grasshopper.Kernel.Special as ghs
import Rhino.Geometry as rg

doc = ghenv.Component.OnPingDocument()

# ---------- SPAWN INPUT NODES (run once) ----------
if doc and not getattr(ghenv.Component, "_spawned", False):
    base = ghenv.Component.Attributes.Pivot

    # Geometry param for input 0 ("x")
    p_geo = ghk.Parameters.Param_Geometry()
    p_geo.NickName = "x"
    p_geo.CreateAttributes()
    p_geo.Attributes.Pivot = sd.PointF(base.X - 180, base.Y)
    doc.AddObject(p_geo, False)

    # Number slider for input 1 ("scale")
    s = ghs.GH_NumberSlider()
    s.CreateAttributes()
    s.Slider.Minimum = Decimal(1)
    s.Slider.Maximum = Decimal(10)
    s.Slider.DecimalPlaces = 0
    s.Slider.Value = Decimal(6)
    s.NickName = "scale"
    s.Attributes.Pivot = sd.PointF(base.X - 180, base.Y + 40)
    doc.AddObject(s, False)

    # Wire after current solution (correct delegate signature)
    def _wire(_doc):
        ghenv.Component.Params.Input[0].AddSource(p_geo)  # -> x
        ghenv.Component.Params.Input[1].AddSource(s)      # -> scale
        ghenv.Component.ExpireSolution(True)

    doc.ScheduleSolution(5, ghk.GH_Document.GH_ScheduleDelegate(_wire))
    ghenv.Component._spawned = True

# ---------- SCALE LOGIC ----------
def unwrap(g):
    geo = getattr(g, "Geometry", None)
    if geo is not None: 
        return geo
    try:
        import rhinoscriptsyntax as rs
        cg = rs.coercegeometry(g)
        if cg is not None: 
            return cg
    except:
        pass
    return g

def center_of(geos):
    bb = rg.BoundingBox.Empty
    for g in geos:
        try:
            bb = rg.BoundingBox.Union(bb, g.GetBoundingBox(True))
        except:
            pass
    return bb.Center

def dup(g):
    for name in ("Duplicate", "DuplicateShallow", "DuplicateBrep"):
        if hasattr(g, name):
            try: 
                return getattr(g, name)()
            except: 
                pass
    return g

# Inputs expected on this component: x (geometry), scale (optional)
geom_in = x if isinstance(x, (list, tuple)) else [x] if 'x' in globals() else []
geom_in = [unwrap(g) for g in geom_in if g is not None]

k = 6.0
if "scale" in globals() and scale is not None:
    try: 
        k = float(scale)
    except: 
        pass

if not geom_in:
    a = None
else:
    pivot = center_of(geom_in)
    xf = rg.Transform.Scale(pivot, k)
    out = []
    for g in geom_in:
        g2 = dup(g)
        if hasattr(g2, "Transform"):
            g2.Transform(xf)
            out.append(g2)
    a = out[0] if len(out) == 1 else out
