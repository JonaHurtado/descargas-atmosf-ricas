import unittest
import sys
import os

# Allow importing from src by adding project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.iec_62305 import EngineIEC62305, GeometricParameters, ZoneParameters, LineParameters

class TestAuditLogic(unittest.TestCase):
    def test_manual_ad_override(self):
        # Case 1: Auto Calc
        geom_auto = GeometricParameters(L=10, W=10, H=10, Ng=2.0)
        engine_auto = EngineIEC62305(geom_auto, [], [])
        # Ad = 10*10 + 6*10*(20) + 9*pi*100 = 100 + 1200 + 2827 ~ 4127
        self.assertGreater(engine_auto.Ad, 4000)

        # Case 2: Manual Override
        geom_manual = GeometricParameters(L=10, W=10, H=10, Ng=2.0, Ad_manual=500.0)
        engine_manual = EngineIEC62305(geom_manual, [], [])
        self.assertEqual(engine_manual.Ad, 500.0)

    def test_r1_strict_logic(self):
        # Setup standard params
        geom = GeometricParameters(L=10, W=10, H=10, Ng=2.0)
        line = LineParameters(name="Pwr", length=100, is_buried=True, ce=1.0)
        
        # CASE A: No critical flags -> RC, RM, RW, RZ should be excluded from R1
        z_safe = ZoneParameters(
            name="Safe", rf=0.01, rp=1.0, hz=1.0, 
            val_Lt=1e-4, val_Lf=0.1, val_Lo=1e-3, # Lo is non-zero so components exist if enabled
            is_explosive=False, is_hospital_or_sensitive=False, is_internal_failure_danger=False
        )
        
        engine_safe = EngineIEC62305(geom, [z_safe], [line])
        res_safe = engine_safe.compute_risk_R1(PA=1.0, PB=1.0, PC=1.0, PM=1.0, PU=1.0, PV=1.0, PW=1.0, PZ=1.0)
        
        # R1 = RA + RB + RU + RV. (RC, RM, RW, RZ excluded)
        # Check details directly
        det_safe = res_safe['details']['Safe']
        self.assertFalse(det_safe['Conditions_Met'])
        self.assertIsNone(det_safe['RC'])
        self.assertIsNone(det_safe['RM'])
        self.assertEqual(det_safe['RW_sum'], 0.0)
        self.assertEqual(det_safe['RZ_sum'], 0.0)
        
        # CASE B: Critical flag -> RC, RM, RW, RZ included
        z_crit = ZoneParameters(
            name="Crit", rf=0.01, rp=1.0, hz=1.0, 
            val_Lt=1e-4, val_Lf=0.1, val_Lo=1e-3,
            is_explosive=True # EXPLOSION RISK
        )
        engine_crit = EngineIEC62305(geom, [z_crit], [line])
        res_crit = engine_crit.compute_risk_R1(PA=1.0, PB=1.0, PC=1.0, PM=1.0, PU=1.0, PV=1.0, PW=1.0, PZ=1.0)
        
        det_crit = res_crit['details']['Crit']
        self.assertTrue(det_crit['Conditions_Met'])
        self.assertIsNotNone(det_crit['RC'])
        self.assertIsNotNone(det_crit['RM'])
        # RW/RZ sum > 0 because Lo > 0 and probabilities > 0
        self.assertGreater(det_crit['RW_sum'], 0)
        self.assertGreater(det_crit['RZ_sum'], 0)

    def test_r4_strict_logic(self):
        geom = GeometricParameters(L=10, W=10, H=10, Ng=2.0)
        line = LineParameters(name="Pwr", length=100, is_buried=True, ce=1.0)
        
        # CASE A: No Animals
        z_no_anim = ZoneParameters(name="NoAnim", val_Lt=1e-4, val_Lf=0.1, has_animals=False)
        engine_no = EngineIEC62305(geom, [z_no_anim], [line])
        res_no = engine_no.compute_risk_R4(PB=1.0, PV=1.0)
        
        det_no = res_no['details']['NoAnim']
        self.assertFalse(det_no['Has_Animals'])
        self.assertIsNone(det_no['RA']) # Ra excluded
        
        # CASE B: Has Animals
        z_anim = ZoneParameters(name="Anim", val_Lt=1e-4, val_Lf=0.1, has_animals=True)
        engine_anim = EngineIEC62305(geom, [z_anim], [line])
        res_anim = engine_anim.compute_risk_R4(PB=1.0, PV=1.0)
        
        det_anim = res_anim['details']['Anim']
        self.assertTrue(det_anim['Has_Animals'])
        self.assertIsNotNone(det_anim['RA']) # Ra included

    def test_r3_structure(self):
        geom = GeometricParameters(L=10, W=10, H=10, Ng=2.0)
        z = ZoneParameters(name="Z", val_Lt=1e-4, val_Lf=0.1, rf=0.1)
        engine = EngineIEC62305(geom, [z], [])
        
        res_r3 = engine.compute_risk_R3(PB=1.0, PV=1.0)
        self.assertIsNotNone(res_r3)
        self.assertIn('value', res_r3)
        self.assertGreater(res_r3['value'], 0.0)

    def test_latex_output(self):
        # Verify the formula string format
        geom = GeometricParameters(L=10, W=10, H=10, Ng=2.0)
        z = ZoneParameters(name="Z", val_Lt=1e-4, val_Lf=0.1)
        engine = EngineIEC62305(geom, [z], [])
        
        res = engine.compute_risk_R1(PA=1.0, PB=1.0)
        ra_obj = res['details']['Z']['RA']
        
        # Expect LaTeX: "R_A = N_d \cdot ..."
        self.assertIn("R_A =", ra_obj.formula)
        self.assertIn(r"\cdot", ra_obj.formula)

if __name__ == '__main__':
    unittest.main()
