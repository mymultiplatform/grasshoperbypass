# --- SPAWN SLIDER + GEOMETRY PARAM & WIRE THEM TO THIS PY COMPONENT (Decimal-safe) ---
import System
from System import Decimal
import System.Drawing as sd
import Grasshopper as gh
import Grasshopper.Kernel as ghk
import Grasshopper.Kernel.Special as ghs

doc = ghenv.Component.OnPingDocument()
if doc and not hasattr(ghenv.Component, "_spawned"):
    base = ghenv.Component.Attributes.Pivot

    # 1) Geometry param for input 0 ("x")
    p_geo = ghk.Parameters.Param_Geometry()
    p_geo.NickName = "x"
    p_geo.CreateAttributes()
    p_geo.Attributes.Pivot = sd.PointF(base.X - 180, base.Y)
    doc.AddObject(p_geo, False)

    # 2) Number slider for input 1 ("scale")
    s = ghs.GH_NumberSlider()
    s.CreateAttributes()
    s.Slider.Minimum = Decimal(1)
    s.Slider.Maximum = Decimal(10)
    s.Slider.DecimalPlaces = 0
    s.Slider.Value = Decimal(6)
    s.NickName = "scale"
    s.Attributes.Pivot = sd.PointF(base.X - 180, base.Y + 40)
    doc.AddObject(s, False)

    # 3) Wire them to this Python component
    def _wire(_):
        ghenv.Component.Params.Input[0].AddSource(p_geo)
        ghenv.Component.Params.Input[1].AddSource(s)
        ghenv.Component.ExpireSolution(True)

    doc.ScheduleSolution(5, gh.Delegate_ScheduleSolution(_wire))
    ghenv.Component._spawned = True
# --- END SPAWN ---
