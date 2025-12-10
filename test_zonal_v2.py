import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.iec_62305 import GeometricParameters, ZoneParameters, LineParameters, EngineIEC62305

def test_v2_risk():
    print("Testing IEC 62305-2 V2 Logic...")
    
    # Setup V2 Objects
    geom = GeometricParameters(L=20, W=10, H=10, Ng=2.0, Cd=1.0)
    lines = [LineParameters(name="Power", length=139.75, ce=1.0, ci=0.5)] # Approx theoretical length for test
    
    # Zone with specific V2 atoms
    z = ZoneParameters(
        name="Zone Test",
        pta=1.0, pb=0.2, # LPS IV
        lt_r1=1e-4, 
        lf1_r1=0.0, # Physical loss for R1 usually 0 unless special
        rp=1.0, rf=1.0, hz=1.0,
        pspd=1.0, cld=1.0, ks3=1.0, uw=1.5,
        is_explosive=False
    )
    
    eng = EngineIEC62305(geom, [z], lines)
    r1 = eng.compute_risk_R1()
    
    print(f"R1 Total: {r1['total']}")
    
    # R1 Basic Sanity
    assert r1['total'] > 0
    assert r1['total'] < 1.0 # Should be small risk
    
    # Check R1 components existence
    dets = r1['zones']['Zone Test']
    assert 'Ra' in dets
    assert 'Rb' in dets
    assert dets['Rc'] == 0.0 # No explosion
    
    print("V2 Test Passed.")

if __name__ == "__main__":
    test_v2_risk()
