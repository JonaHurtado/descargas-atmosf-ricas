import unittest
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.iec_62305 import EngineIEC62305, GeometricParameters, ZoneParameters, LineParameters, EconomicParameters

class TestEconomicLogic(unittest.TestCase):
    def test_cpm_calculation(self):
        # CPM = CP * (i + a + m)
        e_params = EconomicParameters(cost_protection_total=1000.0, interest_rate=0.04, amortization_rate=0.05, maintenance_rate=0.01)
        # Expected: 1000 * (0.10) = 100.0
        
        # We can test this by calling perform_economic_analysis on engine
        geom = GeometricParameters(L=10, W=10, H=10, Ng=1.0)
        engine = EngineIEC62305(geom, [], []) # No zones needed for CPM check logic if isolated (but method requires inputs)
        
        # We need at least one zone to run perform_economic_analysis without crashing on loops?
        # Actually logic is robust.
        res = engine.perform_economic_analysis(e_params, 1.0, 1.0, 1.0, 1.0)
        self.assertAlmostEqual(res['CPM'], 100.0)

    def test_viability_logic(self):
        # S = CRL - (CPM + CL)
        # If CRL = 1000, CPM = 100, CL = 100 -> S = 800 > 0 (Viable)
        
        e_params = EconomicParameters(cost_protection_total=1000.0, interest_rate=0.04, amortization_rate=0.05, maintenance_rate=0.01) # CPM=100
        
        geom = GeometricParameters(L=10, W=10, H=10, Ng=1.0)
        # We need a zone that generates Loss
        # Unprotected Loss (CRL) needs to be high.
        # Protected Loss (CL) needs to be low.
        
        z = ZoneParameters(
             name="Z1", rf=0.1, rp=1.0, hz=1.0, 
             val_Lf=0.1, val_Lt=0.0, val_Lo=0.0, # Just physical damage
             cost_structure=100000.0, cost_content=0.0,
             citations={"rf": "Test"}
        )
        
        engine = EngineIEC62305(geom, [z], [])
        
        # 1. CRL (Unprotected)
        # Rb_unprot = Nd * 1.0 * (Value * Lf * 1.0 * 1.0)
        # Ad ~ 100+1200+...  geom logic...
        # Nd = Ng * Ad * ...
        
        # To verify S > 0, we just run it and check logic consistency.
        # We assume protection measures reduce risk (e.g. current_pb < 1.0)
        
        res = engine.perform_economic_analysis(e_params, current_pb=0.1, current_pv=0.1, current_rp=1.0, current_rf=1.0)
        
        # CRL should use P=1.0. CL uses P=0.1.
        # So CL < CRL.
        self.assertLess(res['CL'], res['CRL'])
        
        # S = CRL - (CPM + CL)
        s_expected = res['CRL'] - (res['CPM'] + res['CL'])
        self.assertAlmostEqual(res['S'], s_expected)
        
    def test_citation_storage(self):
        cit = {"rf": "Table C.3"}
        z = ZoneParameters(name="Z", citations=cit)
        self.assertEqual(z.citations['rf'], "Table C.3")

if __name__ == '__main__':
    unittest.main()
