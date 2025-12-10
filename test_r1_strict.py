import pytest
import math
from src.iec_62305 import EngineIEC62305, GeometricParameters, ZoneParameters, LineParameters
from src.tables import *

class TestR1Strict:
    def test_basic_Ra_calculation(self):
        # 1. Geometry: Ng=2, L=10, W=10, H=10 => Ad (Manual) = 1100 approx?
        # Let's use fixed Ad for simplicity
        geom = GeometricParameters(L=10, W=10, H=10, Ng=2.0, Cd=1.0, Ad_manual=1000.0)
        # Nd = 2.0 * 1000.0 * 1.0 * 1e-6 = 2e-3
        
        # 2. Zone: Simple Ra
        z1 = ZoneParameters(name="Z1")
        # Ra Params
        z1.pta = 1.0
        z1.pb = 1.0
        z1.rt = 1e-2
        z1.lt_r1 = 1e-2
        z1.nz_ra = 1.0
        z1.nt_ra = 1.0
        z1.tz_ra = 8760.0
        
        # Pa = 1
        # La1 = 1e-2 * 1e-2 * 1 * 1 = 1e-4
        # Ra = Nd * 1 * 1e-4 = 2e-3 * 1e-4 = 2e-7
        
        engine = EngineIEC62305(geom, [z1], [])
        res = engine.compute_risk_R1()
        
        r1_total = res["total"]
        r1_z = res["zones"]["Z1"]
        
        assert math.isclose(r1_z["Ra"], 2e-7, rel_tol=1e-5), f"Ra expected 2e-7, got {r1_z['Ra']}"
        assert math.isclose(r1_total, 2e-7, rel_tol=1e-5)

    def test_conditional_Rc_Rm(self):
        # Explosion Risk
        geom = GeometricParameters(L=10, W=10, H=10, Ng=2.0, Cd=1.0, Ad_manual=1000.0, Am_manual=2000.0)
        # Nd = 2e-3
        # Nm = 2 * 2000 * 1e-6 = 4e-3
        
        z = ZoneParameters(name="ExZ")
        z.is_risk_explosion = True
        z.lt_r1 = 1e-2
        z.rt = 0.0 # Kill Ra for clarity
        z.lo1_r1 = 1e-1 # Lc1 Base
        
        # Rc: Pc = Pspd(0.02) * Cld(1.0) = 0.02
        # Lc1 = 1e-1 * 1 * 1 (using defaults tz=4760? No, set to 8760 for test)
        z.tz_rc = 8760.0
        # Lc1 = 1e-1
        # Rc = 2e-3 * 0.02 * 0.1 = 4e-6
        
        z.pspd = 0.02
        z.cld = 1.0
        
        engine = EngineIEC62305(geom, [z], [])
        res = engine.compute_risk_R1()
        r1 = res["zones"]["ExZ"]
        
        assert math.isclose(r1["Rc"], 4e-6, rel_tol=1e-5), f"Rc expected 4e-6, got {r1['Rc']}"
        
