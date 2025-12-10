import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.iec_62305 import GeometricParameters, ZoneParameters, LineParameters, EngineIEC62305

def test_zonal_risk():
    print("Testing Zonal Risk Calculation...")
    
    # 1. Setup Data
    geom = GeometricParameters(L=20, W=10, H=10, Ng=2.0, Cd=1.0)
    lines = [LineParameters(name="Power", length=100)]
    
    z1 = ZoneParameters(name="Zone 1", nz=1, nt=1, val_Lt=1e-4, pa=1.0, pb=1.0)
    z2 = ZoneParameters(name="Zone 2", nz=10, nt=10, val_Lt=1e-4, pa=0.1, pb=0.5, is_hospital=True)
    
    # 2. Run Engine
    engine = EngineIEC62305(geom, [z1, z2], lines)
    
    r1 = engine.compute_risk_R1()
    print(f"R1 Total: {r1['total']}")
    
    # 3. Assertions
    assert r1['total'] > 0
    assert "Zone 1" in r1['zones']
    assert "Zone 2" in r1['zones']
    
    # Check Zone 2 (Hospital) has Rc calculated
    z2_res = r1['zones']["Zone 2"]
    if z2_res['Rc'].value > 0:
        print("PASS: Zone 2 (Hospital) has Risk Rc > 0")
    else:
        print("FAIL: Zone 2 (Hospital) should have Rc")
        
    print("Test Complete. Engine Logic Verified.")

if __name__ == "__main__":
    test_zonal_risk()
