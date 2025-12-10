import sys
import os
sys.path.append(os.getcwd())

from src.iec_62305 import GeometricParameters, ZoneParameters, LineParameters, EngineIEC62305
from src.tables import CD_FACTOR

def test_strict_calculation():
    print("Testing Strict IEC 62305 Engine...")
    
    # 1. Geometric
    geom = GeometricParameters(
        L=20, W=15, H=10, Ng=2.0, Cd=CD_FACTOR["Objeto rodeado por objetos de menor altura"]
    )
    
    # 2. Zones (Server Room)
    z1 = ZoneParameters(
        name="Server Room",
        rf=0.01, rp=1.0, hz=1.0,
        ra_reduction=0.01, ru_reduction=0.01, # Flooring
        val_Lt=1e-4, val_Lf=0.1, val_Lo=1e-3,
        cost_structure=50000, cost_content=20000
    )
    
    # 3. Lines
    l1 = LineParameters(name="Power", length=200, is_buried=True, ce=0.5)
    
    # 4. Engine
    engine = EngineIEC62305(geom, [z1], [l1])
    
    # R1 Test
    r1 = engine.compute_risk_R1(PA=1.0, PB=0.2) # PB=0.2 (LPS Class IV)
    print(f"R1 Value: {r1['value']}")
    print(f"R1 Traceability RA: {r1['details']['Server Room']['RA'].formula}")
    
    assert r1['value'] > 0
    assert "Nd" in r1['details']['Server Room']['RA'].formula
    
    # R4 Test
    r4 = engine.compute_risk_R4(PB=0.2, PV=0.2)
    print(f"R4 Value: {r4['value']}")
    assert r4['value'] > 0
    
    print("Test Passed!")

if __name__ == "__main__":
    test_strict_calculation()
