"""
IEC 62305-2 Risk Calculation Engine - R1 Focus
Implements R1 = Ra1 + Rb1 + Rc1* + Rm1* + Ru1 + Rv1 + Rw1* + Rz1*
"""
import math
from dataclasses import dataclass
from typing import Optional, List, Dict

@dataclass
class GeometricParameters:
    """Global geometric parameters for the structure"""
    L: float  # Length (m)
    W: float  # Width (m)
    H: float  # Height (m)
    Ng: float = 1.0  # Ground flash density (flashes/km²/year)
    Cd: float = 1.0  # Location factor (Table A.1)
    Ad_manual: Optional[float] = None  # Manual override for Ad
    Am_manual: Optional[float] = None  # Manual override for Am

@dataclass
class LineParameters:
    """Parameters for incoming service lines"""
    name: str
    length: float  # Ll - Line length (m)
    ci: float = 0.5  # Installation factor (Table A.2) - default: Buried
    ce: float = 1.0  # Environment factor (Table A.4) - default: Rural
    ct: float = 0.2  # Type factor (Table A.3) - default: With transformer
    
    # Adjacent structure parameters (for Ndj calculation)
    Lj: float = 0.0  # Adjacent structure length (m)
    Wj: float = 0.0  # Adjacent structure width (m)
    Hj: float = 0.0  # Adjacent structure height (m)
    Cdj: float = 1.0  # Adjacent structure location factor (Table A.1)

@dataclass
class ZoneParameters:
    """Parameters for a single zone - R1 components only"""
    name: str
    
    # === Conditional flags ===
    is_explosion_risk: bool = False  # Activates Rc*, Rm*, Rw*, Rz*
    is_hospital: bool = False  # Activates Rc*, Rm*, Rw*, Rz*
    
    # === Component Ra: Impact on Structure (Nd·Pa·La1) ===
    # 1.2. Pa = Pta × Pb
    pta: float = 0.01  # Table B.1 - default: "Aislamiento eléctrico"
    pb: float = 1.0  # Table B.2 - default: "Estructura no protegida por un SPCR"
    # 1.3. La1 = rt × Lt × (nz/nt) × (tz/8760)
    rt: float = 0.01  # Table C.3 - default: "Agrícola, hormigón"
    lt: float = 1e-2  # Table C.12 - default: 10^-2
    nz: float = 1.0  # Number of persons in zone
    nt: float = 1.0  # Total number of persons
    tz: float = 8760.0  # Time persons are in zone (hours/year)
    
    # === Component Rb: Fire in Structure (Nd·Pb·Lb1) ===
    # Uses same Nd and Pb as Ra
    # 2.3. Lb1 = rp × rf × hz × Lf1 × (nz/nt) × (tz/8760)
    rp: float = 0.5  # Table C.4 - default: "Extintores/instalaciones manuales"
    rf: float = 0.01  # Table C.5 - default: "Fuego Normal"
    hz: float = 2.0  # Table C.6 - default: "Nivel bajo de pánico"
    lf1: float = 0.02  # Table C.2 - default: "Industrial, comercios"
    nz_rb: float = 1.0  # Allow different occupancy for fire risk
    nt_rb: float = 1.0
    tz_rb: float = 8760.0
    
    # === Component Rc*: Failure on Structure (Nd·Pc·Lc1) ===
    # Only if explosion_risk or hospital
    # 3.2. Pc = Pspd × Cld
    pspd: float = 0.02  # Table B.3 - default: "Nivel de protección II"
    cld: float = 1.0  # Table B.4 - default: "Línea enterrada sin apantallar"
    # 3.3. Lc1 = Lo1 × (nz/nt) × (tz/8760)
    lo1: float = 0.0  # Table C.2 - default: 0 (unless hospital/explosion)
    nz_rc: float = 1.0
    nt_rc: float = 1.0
    tz_rc: float = 8760.0
    
    # === Component Rm*: Failure near Structure (Nm·Pm·Lm1) ===
    # Only if explosion_risk or hospital
    # 4.2. Pm = Pspd × Pms, where Pms = (Ks1·Ks2·Ks3·Ks4)²
    wm1: float = 2.0  # Width of external SPD protection zone (m)
    wm2: float = 2.0  # Width of internal SPD protection zone (m)
    ks3: float = 1.0  # Table B.5 - Internal wiring factor
    uw: float = 1.0  # Withstand voltage (kV)
    # Lm1 = Lc1 (reused)
    
    # === Component Ru: Shock from Line ((Nl+Ndj)·Pu·Lu1) ===
    # 5.3. Pu = Ptu × Peb × Pld × Cld (Equation B.8)
    ptu: float = 0.01  # Table B.6 - default: "Aislamiento eléctrico"
    peb: float = 0.02  # Table B.7 - default: "NPR II"
    pld: float = 1.0  # Table B.8 - default: "Línea sin apantallar"
    cld_u: float = 1.0  # Table B.4
    # 5.4. Lu1 = rt × Lt × (nz/nt) × (tz/8760) (same structure as La1)
    rt_u: float = 0.01
    lt_u: float = 1e-2
    nz_u: float = 1.0
    nt_u: float = 1.0
    tz_u: float = 8760.0
    
    # === Component Rv: Fire from Line ((Nl+Ndj)·Pv·Lv1) ===
    # 6.3. Pv = Peb × Pld × Cld (Equation B.9)
    peb_v: float = 0.02  # Table B.7
    pld_v: float = 1.0  # Table B.8
    cld_v: float = 1.0  # Table B.4
    # Lv1 = Lb1 (reused)
    
    # === Component Rw*: Failure from Line ((Nl+Ndj)·Pw·Lw1) ===
    # Only if explosion_risk or hospital
    # 7.3. Pw = Pspd × Pld × Cld
    pspd_w: float = 0.02  # Same as Rc
    pld_w: float = 1.0
    cld_w: float = 1.0
    # Lw1 = Lc1 (reused)
    
    # === Component Rz*: Induced Failure (Ni·Pz·Lz1) ===
    # Only if explosion_risk or hospital
    # 8.2. Pz = Pspd × Pli × Cli
    pspd_z: float = 0.02
    pli: float = 1.0  # Table B.9 - default: 1
    cli: float = 1.0  # Table B.4 - default: "Línea enterrada sin apantallar"
    # Lz1 = Lc1 (reused)


class Calculators:
    """Helper methods for IEC 62305-2 calculations"""
    
    @staticmethod
    def calculate_Ad(L: float, W: float, H: float) -> float:
        """
        Calculate collection area of structure (Equation A.2)
        Ad = L·W + 6·H·(L+W) + 9·π·H²
        """
        return (L * W) + (6 * H * (L + W)) + (9 * math.pi * H**2)
    
    @staticmethod
    def calculate_Am(L: float, W: float) -> float:
        """
        Calculate collection area near structure (Equation A.7)
        Am = 2·500·(L+W) + π·500²
        """
        dm = 500.0
        return (2 * dm * (L + W)) + (math.pi * dm**2)
    
    @staticmethod
    def calculate_Adj(Lj: float, Wj: float, Hj: float) -> float:
        """Calculate collection area of adjacent structure (same as Ad)"""
        if Lj == 0 and Wj == 0 and Hj == 0:
            return 0.0
        return Calculators.calculate_Ad(Lj, Wj, Hj)
    
    @staticmethod
    def calculate_Ks1(wm1: float) -> float:
        """Equation B.5: Ks1 = 0.12 × wm1, max 1.0"""
        return min(0.12 * wm1, 1.0)
    
    @staticmethod
    def calculate_Ks2(wm2: float) -> float:
        """Equation B.6: Ks2 = 0.12 × wm2, max 1.0"""
        return min(0.12 * wm2, 1.0)
    
    @staticmethod
    def calculate_Ks4(uw: float) -> float:
        """Equation B.7: Ks4 = 1/Uw, max 1.0"""
        if uw <= 0:
            return 1.0
        return min(1.0 / uw, 1.0)
    
    @staticmethod
    def calculate_Pms(wm1: float, wm2: float, ks3: float, uw: float) -> float:
        """Calculate Pms = (Ks1 × Ks2 × Ks3 × Ks4)²"""
        ks1 = Calculators.calculate_Ks1(wm1)
        ks2 = Calculators.calculate_Ks2(wm2)
        ks4 = Calculators.calculate_Ks4(uw)
        return (ks1 * ks2 * ks3 * ks4) ** 2


class EngineIEC62305:
    """IEC 62305-2 Risk Calculation Engine - R1 Only"""
    
    def __init__(self, geom: GeometricParameters, zones: List[ZoneParameters], lines: List[LineParameters]):
        self.geom = geom
        self.zones = zones
        self.lines = lines if lines else []
        
        # Calculate structure area Ad
        if geom.Ad_manual:
            self.Ad = geom.Ad_manual
        else:
            self.Ad = Calculators.calculate_Ad(geom.L, geom.W, geom.H)
        
        # Calculate collection area Am
        if geom.Am_manual:
            self.Am = geom.Am_manual
        else:
            self.Am = Calculators.calculate_Am(geom.L, geom.W)
    
    def _calculate_Nd(self) -> float:
        """Calculate Nd = Ng × Ad × Cd × 10^-6"""
        return self.geom.Ng * self.Ad * self.geom.Cd * 1e-6
    
    def _calculate_Nm(self) -> float:
        """Calculate Nm = Ng × Am × 10^-6"""
        return self.geom.Ng * self.Am * 1e-6
    
    def _calculate_Pa(self, z: ZoneParameters) -> float:
        """Calculate Pa = Pta × Pb"""
        return z.pta * z.pb
    
    def _calculate_La1(self, z: ZoneParameters) -> float:
        """Calculate La1 = rt × Lt × (nz/nt) × (tz/8760) - Equation C.1"""
        return z.rt * z.lt * (z.nz / z.nt) * (z.tz / 8760.0)
    
    def _calculate_Lb1(self, z: ZoneParameters) -> float:
        """Calculate Lb1 = rp × rf × hz × Lf1 × (nz/nt) × (tz/8760) - Equation C.3"""
        return z.rp * z.rf * z.hz * z.lf1 * (z.nz_rb / z.nt_rb) * (z.tz_rb / 8760.0)
    
    def _calculate_Lc1(self, z: ZoneParameters) -> float:
        """Calculate Lc1 = Lo1 × (nz/nt) × (tz/8760) - Equation C.4"""
        return z.lo1 * (z.nz_rc / z.nt_rc) * (z.tz_rc / 8760.0)
    
    def _calculate_Lu1(self, z: ZoneParameters) -> float:
        """Calculate Lu1 = rt × Lt × (nz/nt) × (tz/8760) - Equation C.2"""
        return z.rt_u * z.lt_u * (z.nz_u / z.nt_u) * (z.tz_u / 8760.0)
    
    def _calculate_Nl(self, line: LineParameters) -> float:
        """Calculate Nl = Ng × Al × Ci × Ce × Ct × 10^-6"""
        Al = 40.0 * line.length
        return self.geom.Ng * Al * line.ci * line.ce * line.ct * 1e-6
    
    def _calculate_Ndj(self, line: LineParameters) -> float:
        """Calculate Ndj = Ng × Adj × Cdj × Ct × 10^-6"""
        Adj = Calculators.calculate_Adj(line.Lj, line.Wj, line.Hj)
        if Adj == 0:
            return 0.0
        return self.geom.Ng * Adj * line.Cdj * line.ct * 1e-6
    
    def _calculate_Ni(self, line: LineParameters) -> float:
        """Calculate Ni = Ng × Ai × Ci × Ce × Ct × 10^-6"""
        Ai = 4000.0 * line.length
        return self.geom.Ng * Ai * line.ci * line.ce * line.ct * 1e-6
    
    def _calculate_Pu(self, z: ZoneParameters) -> float:
        """Calculate Pu = Ptu × Peb × Pld × Cld - Equation B.8"""
        return z.ptu * z.peb * z.pld * z.cld_u
    
    def _calculate_Pv(self, z: ZoneParameters) -> float:
        """Calculate Pv = Peb × Pld × Cld - Equation B.9"""
        return z.peb_v * z.pld_v * z.cld_v
    
    def _calculate_Pw(self, z: ZoneParameters) -> float:
        """Calculate Pw = Pspd × Pld × Cld"""
        return z.pspd_w * z.pld_w * z.cld_w
    
    def _calculate_Pz(self, z: ZoneParameters) -> float:
        """Calculate Pz = Pspd × Pli × Cli"""
        return z.pspd_z * z.pli * z.cli
    
    def compute_risk_R1(self) -> Dict:
        """
        Compute R1 = Ra1 + Rb1 + Rc1* + Rm1* + Ru1 + Rv1 + Rw1* + Rz1*
        Returns detailed breakdown for each zone and component
        """
        total = 0.0
        zones_output = {}
        
        # Common factors (same for all zones)
        Nd = self._calculate_Nd()
        Nm = self._calculate_Nm()
        
        for z in self.zones:
            # Check if conditional components are active
            is_critical = z.is_explosion_risk or z.is_hospital
            
            # === 1. Ra = Nd × Pa × La1 ===
            Pa = self._calculate_Pa(z)
            La1 = self._calculate_La1(z)
            Ra = Nd * Pa * La1
            
            # === 2. Rb = Nd × Pb × Lb1 ===
            Pb = z.pb
            Lb1 = self._calculate_Lb1(z)
            Rb = Nd * Pb * Lb1
            
            # === 3. Rc* = Nd × Pc × Lc1 ===
            Rc = 0.0
            Pc = 0.0
            Lc1 = self._calculate_Lc1(z)
            if is_critical:
                Pc = z.pspd * z.cld
                Rc = Nd * Pc * Lc1
            
            # === 4. Rm* = Nm × Pm × Lm1 ===
            Rm = 0.0
            Pm = 0.0
            Pms = 0.0
            if is_critical:
                Pms = Calculators.calculate_Pms(z.wm1, z.wm2, z.ks3, z.uw)
                Pm = z.pspd * Pms
                Lm1 = Lc1  # Lm1 = Lc1
                Rm = Nm * Pm * Lm1
            
            # === Line-based components ===
            Ru_sum = 0.0
            Rv_sum = 0.0
            Rw_sum = 0.0
            Rz_sum = 0.0
            
            Nl_total = 0.0
            Ndj_total = 0.0
            Ni_total = 0.0
            
            for line in self.lines:
                Nl = self._calculate_Nl(line)
                Ndj = self._calculate_Ndj(line)
                Ni = self._calculate_Ni(line)
                
                Nl_total += Nl
                Ndj_total += Ndj
                Ni_total += Ni
                
                # === 5. Ru = (Nl + Ndj) × Pu × Lu1 ===
                Pu = self._calculate_Pu(z)
                Lu1 = self._calculate_Lu1(z)
                Ru_sum += (Nl + Ndj) * Pu * Lu1
                
                # === 6. Rv = (Nl + Ndj) × Pv × Lv1 ===
                Pv = self._calculate_Pv(z)
                Lv1 = Lb1  # Lv1 = Lb1
                Rv_sum += (Nl + Ndj) * Pv * Lv1
                
                # === 7. Rw* = (Nl + Ndj) × Pw × Lw1 ===
                if is_critical:
                    Pw = self._calculate_Pw(z)
                    Lw1 = Lc1  # Lw1 = Lc1
                    Rw_sum += (Nl + Ndj) * Pw * Lw1
                
                # === 8. Rz* = Ni × Pz × Lz1 ===
                if is_critical:
                    Pz = self._calculate_Pz(z)
                    Lz1 = Lc1  # Lz1 = Lc1
                    Rz_sum += Ni * Pz * Lz1
            
            # Total R1 for this zone
            zone_total = Ra + Rb + Rc + Rm + Ru_sum + Rv_sum + Rw_sum + Rz_sum
            total += zone_total
            
            # Store detailed results
            zones_output[z.name] = {
                "Total": zone_total,
                "is_critical": is_critical,
                # Component values
                "Ra": Ra, "Rb": Rb, "Rc": Rc, "Rm": Rm,
                "Ru": Ru_sum, "Rv": Rv_sum, "Rw": Rw_sum, "Rz": Rz_sum,
                # Intermediate calculations
                "Nd": Nd, "Nm": Nm,
                "Pa": Pa, "La1": La1,
                "Pb": Pb, "Lb1": Lb1,
                "Pc": Pc, "Lc1": Lc1,
                "Pm": Pm, "Pms": Pms,
                "Nl": Nl_total, "Ndj": Ndj_total, "Ni": Ni_total,
                "Pu": self._calculate_Pu(z) if self.lines else 0.0,
                "Lu1": Lu1 if self.lines else 0.0,
                "Pv": self._calculate_Pv(z) if self.lines else 0.0,
                "Lv1": Lb1,
                "Pw": self._calculate_Pw(z) if is_critical and self.lines else 0.0,
                "Lw1": Lc1 if is_critical else 0.0,
                "Pz": self._calculate_Pz(z) if is_critical and self.lines else 0.0,
                "Lz1": Lc1 if is_critical else 0.0,
            }
        
        return {"total": total, "zones": zones_output, "Ad": self.Ad, "Am": self.Am}
