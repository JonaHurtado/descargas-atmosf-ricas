"""
IEC 62305-2 Risk Calculation Engine - R1 and R2
Implements:
  R1 = Ra1 + Rb1 + Rc1* + Rm1* + Ru1 + Rv1 + Rw1* + Rz1*
  R2 = Rb2 + Rc2 + Rm2 + Rv2 + Rw2 + Rz2
  R4 = Ra4* + Rb4 + Rc4 + Rm4 + Ru4* + Rv4 + Rw4 + Rz4
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
    
    # ========================================
    # === R2 RISK PARAMETERS (Service Loss) ===
    # ========================================
    # R2 = Rb2 + Rc2 + Rm2 + Rv2 + Rw2 + Rz2
    # Most parameters are reused from R1 (Nd, Pb, Pc, Pm, Pspd, etc.)
    # Only loss factors Lf2 and Lo2 are specific to R2
    
    # Lb2 = rp × rf × Lf2 × (nz/nt) (Equation C.7)
    lf2: float = 1e-1  # Table C.8 - default: "Gas, agua, electricidad"
    
    # Lc2 = Lo2 × (nz/nt) (Equation C.8)
    lo2: float = 1e-2  # Table C.8 - default: "Gas, agua, electricidad"
    
    # Optional: Allow different nz/nt for R2 (default: reuse from R1)
    nz_r2: Optional[float] = None  # If None, reuse nz from R1
    nt_r2: Optional[float] = None  # If None, reuse nt from R1
    
    # Optional: Rm parameters for R2 if not defined in R1 (when not explosion/hospital)
    wm1_r2: Optional[float] = None  # If None, reuse wm1 from R1
    wm2_r2: Optional[float] = None  # If None, reuse wm2 from R1
    ks3_r2: Optional[float] = None  # If None, reuse ks3 from R1
    uw_r2: Optional[float] = None  # If None, reuse uw from R1
    
    # ========================================
    # === R4 RISK PARAMETERS (Economic Loss) ===
    # ========================================
    # R4 = Ra4* + Rb4 + Rc4 + Rm4 + Ru4* + Rv4 + Rw4 + Rz4
    # Components marked with * only calculated for properties with animal loss
    
    # Flag to activate conditional components Ra4* and Ru4*
    has_animal_loss: bool = False  # Activates Ra4* and Ru4* only
    
    # Economic values (currency units)
    ca: float = 0      # Valor de los animales en la zona (por defecto 0)
    cb: float = 350    # Valor del edificio relevante de la zona
    cc: float = 50     # Valor del contenido en la zona
    cs: float = 75     # Valor de los sistemas internos incluidas sus actividades de la zona
    ct: float = 500    # Valor total de la estructura
    
    # R4-specific loss factors (if None, reuse from R1)
    rt_r4: Optional[float] = None   # Tabla C.3, if None uses rt from R1
    lt_r4: Optional[float] = None   # Tabla C.12, if None uses lt from R1
    rp_r4: Optional[float] = None   # Tabla C.4, if None uses rp from R1
    rf_r4: Optional[float] = None   # Tabla C.5, if None uses rf from R1
    
    # R4-specific table values for Lf4 and Lo4 (Tabla C.12)
    lf4: float = 0.2     # Tabla C.12 - default: "Hotel/Escuela/Oficina"
    lo4: float = 0.01    # Tabla C.12 - default: "Hospital/Industrial/Oficinas"




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
        Ai = 100.0 * line.length  # Ai = 100 × Ll (induced surges)
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
    
    # ========================================
    # === R2 RISK CALCULATION METHODS ===
    # ========================================
    
    def _calculate_Lb2(self, z: ZoneParameters) -> float:
        """Calculate Lb2 = rp × rf × Lf2 × (nz/nt) - Equation C.7"""
        nz_val = z.nz_r2 if z.nz_r2 is not None else z.nz
        nt_val = z.nt_r2 if z.nt_r2 is not None else z.nt
        return z.rp * z.rf * z.lf2 * (nz_val / nt_val)
    
    def _calculate_Lc2(self, z: ZoneParameters) -> float:
        """Calculate Lc2 = Lo2 × (nz/nt) - Equation C.8"""
        nz_val = z.nz_r2 if z.nz_r2 is not None else z.nz
        nt_val = z.nt_r2 if z.nt_r2 is not None else z.nt
        return z.lo2 * (nz_val / nt_val)
    
    # ========================================
    # === R4 RISK CALCULATION METHODS ===
    # ========================================
    
    def _calculate_La4(self, z: ZoneParameters) -> float:
        """Calculate La4 = rt × Lt × (ca/ct) - Equation C.10"""
        rt_val = z.rt_r4 if z.rt_r4 is not None else z.rt
        lt_val = z.lt_r4 if z.lt_r4 is not None else z.lt
        if z.ct == 0:
            return 0.0
        return rt_val * lt_val * (z.ca / z.ct)
    
    def _calculate_Lb4(self, z: ZoneParameters) -> float:
        """Calculate Lb4 = rp × rf × Lf4 × (ca+cb+cc+cs)/ct - Equation C.12"""
        rp_val = z.rp_r4 if z.rp_r4 is not None else z.rp
        rf_val = z.rf_r4 if z.rf_r4 is not None else z.rf
        if z.ct == 0:
            return 0.0
        return rp_val * rf_val * z.lf4 * ((z.ca + z.cb + z.cc + z.cs) / z.ct)
    
    def _calculate_Lc4(self, z: ZoneParameters) -> float:
        """Calculate Lc4 = Lo4 × (cs/ct) - Equation C.13"""
        if z.ct == 0:
            return 0.0
        return z.lo4 * (z.cs / z.ct)

    
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
    
    def compute_risk_R2(self) -> Dict:
        """
        Compute R2 = Rb2 + Rc2 + Rm2 + Rv2 + Rw2 + Rz2
        R2 is the risk of loss of service to the public
        IMPORTANT: R2 always calculates ALL components (no conditional logic like R1)
        Returns detailed breakdown for each zone and component
        """
        total = 0.0
        zones_output = {}
        
        # Common factors (same for all zones, reused from R1)
        Nd = self._calculate_Nd()
        Nm = self._calculate_Nm()
        
        for z in self.zones:
            # === 1. Rb2 = Nd × Pb × Lb2 ===
            Pb = z.pb  # Reused from R1
            Lb2 = self._calculate_Lb2(z)
            Rb2 = Nd * Pb * Lb2
            
            # === 2. Rc2 = Nd × Pc × Lc2 ===
            # R2 ALWAYS calculates Rc2 (no conditional)
            Lc2 = self._calculate_Lc2(z)
            Pc = z.pspd * z.cld  # Reused from R1
            Rc2 = Nd * Pc * Lc2
            
            # === 3. Rm2 = Nm × Pm × Lm2 ===
            # R2 ALWAYS calculates Rm2 (no conditional)
            # Use R2-specific parameters if provided, otherwise use R1 values
            wm1_val = z.wm1_r2 if z.wm1_r2 is not None else z.wm1
            wm2_val = z.wm2_r2 if z.wm2_r2 is not None else z.wm2
            ks3_val = z.ks3_r2 if z.ks3_r2 is not None else z.ks3
            uw_val = z.uw_r2 if z.uw_r2 is not None else z.uw
            
            Pms = Calculators.calculate_Pms(wm1_val, wm2_val, ks3_val, uw_val)
            Pm = z.pspd * Pms
            Lm2 = Lc2  # Lm2 = Lc2
            Rm2 = Nm * Pm * Lm2
            
            # === Line-based components ===
            Rv2_sum = 0.0
            Rw2_sum = 0.0
            Rz2_sum = 0.0
            
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
                
                # === 4. Rv2 = (Nl + Ndj) × Pv × Lv2 ===
                Pv = self._calculate_Pv(z)  # Reused from R1
                Lv2 = Lb2  # Lv2 = Lb2
                Rv2_sum += (Nl + Ndj) * Pv * Lv2
                
                # === 5. Rw2 = (Nl + Ndj) × Pw × Lw2 ===
                # R2 ALWAYS calculates Rw2 (no conditional)
                Pw = self._calculate_Pw(z)  # Reused from R1
                Lw2 = Lc2  # Lw2 = Lc2
                Rw2_sum += (Nl + Ndj) * Pw * Lw2
                
                # === 6. Rz2 = Ni × Pz × Lz2 ===
                # R2 ALWAYS calculates Rz2 (no conditional)
                Pz = self._calculate_Pz(z)  # Reused from R1
                Lz2 = Lc2  # Lz2 = Lc2
                Rz2_sum += Ni * Pz * Lz2
            
            # Total R2 for this zone
            zone_total = Rb2 + Rc2 + Rm2 + Rv2_sum + Rw2_sum + Rz2_sum
            total += zone_total
            
            # Store detailed results
            zones_output[z.name] = {
                "Total": zone_total,
                # Component values
                "Rb2": Rb2, "Rc2": Rc2, "Rm2": Rm2,
                "Rv2": Rv2_sum, "Rw2": Rw2_sum, "Rz2": Rz2_sum,
                # Intermediate calculations
                "Nd": Nd, "Nm": Nm,
                "Pb": Pb, "Lb2": Lb2,
                "Pc": Pc, "Lc2": Lc2,
                "Pm": Pm, "Pms": Pms,
                "Nl": Nl_total, "Ndj": Ndj_total, "Ni": Ni_total,
                "Pv": self._calculate_Pv(z) if self.lines else 0.0,
                "Lv2": Lb2,
                "Pw": self._calculate_Pw(z) if self.lines else 0.0,
                "Lw2": Lc2,
                "Pz": self._calculate_Pz(z) if self.lines else 0.0,
                "Lz2": Lc2,
            }
        
        return {"total": total, "zones": zones_output, "Ad": self.Ad, "Am": self.Am}
    
    def compute_risk_R4(self) -> Dict:
        """
        Compute R4 = Ra4* + Rb4 + Rc4 + Rm4 + Ru4* + Rv4 + Rw4 + Rz4
        R4 is the risk of economic loss (loss of animals)
        Components marked with * only calculated for properties with animal loss
        Returns detailed breakdown for each zone and component
        """
        total = 0.0
        zones_output = {}
        
        # Common factors (same for all zones, reused from R1)
        Nd = self._calculate_Nd()
        Nm = self._calculate_Nm()
        
        for z in self.zones:
            # Check if animal loss components are active
            has_animals = z.has_animal_loss
            
            # === 1. Ra4* = Nd × Pa × La4 ===
            # Only calculated if has_animal_loss = True
            Ra4 = 0.0
            La4 = 0.0
            if has_animals:
                Pa = self._calculate_Pa(z)  # Reused from R1
                La4 = self._calculate_La4(z)
                Ra4 = Nd * Pa * La4
            
            # === 2. Rb4 = Nd × Pb × Lb4 ===
            Pb = z.pb  # Reused from R1
            Lb4 = self._calculate_Lb4(z)
            Rb4 = Nd * Pb * Lb4
            
            # === 3. Rc4 = Nd × Pc × Lc4 ===
            # Always calculated (no conditional)
            Lc4 = self._calculate_Lc4(z)
            Pc = z.pspd * z.cld  # Reused from R1
            Rc4 = Nd * Pc * Lc4
            
            # === 4. Rm4 = Nm × Pm × Lm4 ===
            # Always calculated (no conditional)
            # Reuse Pm logic from R1 (uses R1 or R2 parameters if available)
            wm1_val = z.wm1_r2 if z.wm1_r2 is not None else z.wm1
            wm2_val = z.wm2_r2 if z.wm2_r2 is not None else z.wm2
            ks3_val = z.ks3_r2 if z.ks3_r2 is not None else z.ks3
            uw_val = z.uw_r2 if z.uw_r2 is not None else z.uw
            
            Pms = Calculators.calculate_Pms(wm1_val, wm2_val, ks3_val, uw_val)
            Pm = z.pspd * Pms
            Lm4 = Lc4  # Lm4 = Lc4
            Rm4 = Nm * Pm * Lm4
            
            # === Line-based components ===
            Ru4_sum = 0.0
            Rv4_sum = 0.0
            Rw4_sum = 0.0
            Rz4_sum = 0.0
            
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
                
                # === 5. Ru4* = (Nl + Ndj) × Pu × Lu4 ===
                # Only calculated if has_animal_loss = True
                if has_animals:
                    Pu = self._calculate_Pu(z)  # Reused from R1
                    Lu4 = La4  # Lu4 = La4
                    Ru4_sum += (Nl + Ndj) * Pu * Lu4
                
                # === 6. Rv4 = (Nl + Ndj) × Pv × Lv4 ===
                Pv = self._calculate_Pv(z)  # Reused from R1
                Lv4 = Lb4  # Lv4 = Lb4
                Rv4_sum += (Nl + Ndj) * Pv * Lv4
                
                # === 7. Rw4 = (Nl + Ndj) × Pw × Lw4 ===
                # Always calculated (no conditional)
                Pw = self._calculate_Pw(z)  # Reused from R1
                Lw4 = Lc4  # Lw4 = Lc4
                Rw4_sum += (Nl + Ndj) * Pw * Lw4
                
                # === 8. Rz4 = Ni × Pz × Lz4 ===
                # Always calculated (no conditional)
                Pz = self._calculate_Pz(z)  # Reused from R1
                Lz4 = Lc4  # Lz4 = Lc4
                Rz4_sum += Ni * Pz * Lz4
            
            # Total R4 for this zone
            zone_total = Ra4 + Rb4 + Rc4 + Rm4 + Ru4_sum + Rv4_sum + Rw4_sum + Rz4_sum
            total += zone_total
            
            # Store detailed results
            zones_output[z.name] = {
                "Total": zone_total,
                "has_animals": has_animals,
                # Component values
                "Ra4": Ra4, "Rb4": Rb4, "Rc4": Rc4, "Rm4": Rm4,
                "Ru4": Ru4_sum, "Rv4": Rv4_sum, "Rw4": Rw4_sum, "Rz4": Rz4_sum,
                # Intermediate calculations
                "Nd": Nd, "Nm": Nm,
                "Pa": self._calculate_Pa(z) if has_animals else 0.0,
                "La4": La4,
                "Pb": Pb, "Lb4": Lb4,
                "Pc": Pc, "Lc4": Lc4,
                "Pm": Pm, "Pms": Pms,
                "Nl": Nl_total, "Ndj": Ndj_total, "Ni": Ni_total,
                "Pu": self._calculate_Pu(z) if has_animals and self.lines else 0.0,
                "Lu4": La4 if has_animals else 0.0,
                "Pv": self._calculate_Pv(z) if self.lines else 0.0,
                "Lv4": Lb4,
                "Pw": self._calculate_Pw(z) if self.lines else 0.0,
                "Lw4": Lc4,
                "Pz": self._calculate_Pz(z) if self.lines else 0.0,
                "Lz4": Lc4,
                # Economic values
                "ca": z.ca, "cb": z.cb, "cc": z.cc, "cs": z.cs, "ct": z.ct,
                "lf4": z.lf4, "lo4": z.lo4,
            }
        
        return {"total": total, "zones": zones_output, "Ad": self.Ad, "Am": self.Am}

