"""
IEC 62305-2 Normative Tables (V2 Strict)
"""

# --- ANNEX A: Environmental & Location ---

# Table A.1 - Factor Cd (Structure Location)
CD_FACTOR = {
    "Objeto rodeado por objetos más altos": 0.25,
    "Objeto rodeado por objetos de menor altura": 0.5,
    "Objeto aislado": 1.0,
    "Objeto aislado en colina/promontorio": 2.0,
}

# Table A.2 - Factor Ci (Line Installation)
CI_FACTOR = {
    "Aérea": 1.0,
    "Enterrada": 0.5,
    "Enterrada con pantalla (conductiva)": 0.2, # Approx convention if not strict equation
}

# Table A.3 - Factor Ct (Line Type)
CT_FACTOR = {
    "Sin transformador (HV/LV)": 1.0, # Default for direct connection
    "Con transformador (HV/LV)": 0.2,
}

# Table A.4 - Factor Ce (Line Environment)
CE_LINE_FACTOR = {
    "Rural": 1.0,
    "Suburbano": 0.5,
    "Urbano": 0.1,
    "Urbano (edificios altos >20m)": 0.01,
}

# --- ANNEX B: Probabilities ---

# Table B.1 - Probability Pta (Shock to living beings)
PTA_VALUES = {
    "Sin protección contra choque": 1.0,
    "Avisos de advertencia": 0.1,
    "Aislamiento eléctrico": 0.01,
    "Equipotencialización efectiva": 0.001,
}

# Table B.2 - Probability Pb (Physical Damage / LPS)
PB_VALUES = {
    "Sin LPS": 1.0,
    "LPS Clase IV": 0.2,
    "LPS Clase III": 0.1,
    "LPS Clase II": 0.05,
    "LPS Clase I": 0.02,
}

# Table B.3 - Probability Pspd (SPDs)
# Note: Prompt condition: If LPL II exists, PB=0.05. 
PSPD_VALUES = {
    "Sin SPDs": 1.0,
    "SPD III-IV (LPL III/IV)": 0.05,
    "SPD II (LPL II)": 0.02,
    "SPD I (LPL I)": 0.01,
    "Ninguno (Nota Usuario)": 1.0 
}

# Table B.4 - Factor Cld (Line shielding/routing)
CLD_VALUES = {
    "Línea aérea sin apantallar": 1.0,
    "Línea aérea apantallada": 1.0, # Depends on resistance usually, simplified 1.0 or user input
    "Línea enterrada sin apantallar": 1.0,
    "Línea enterrada apantallada": 1.0, 
    # Usually Cld depends on shielding strategy? 
    # Standard says: Unshielded=1, Shielded=Values <1. 
    # We will offer generic "Sin apantallamiento" and "Con apantallamiento (Default 0.3)" etc?
    # Strictly B.4 depends on resistance/inductance. 
    # For dropdown, we provide:
    "Externa, Sin Pantalla": 1.0,
    "Externa, Con Pantalla (no unida)": 1.0,
    "Externa, con Pantalla (unida equipo)": 0.0, # Ideal?
    # Simplified selection:
    "Sin blindaje particular": 1.0,
}

# Table B.5 - Factor Ks3 (Internal Wiring)
KS3_VALUES = {
    "Cable no apantallado en conducto no metálico": 1.0,
    "Cable no apantallado en conducto metálico": 0.2, # Approx
    "Cable apantallado en conducto no metálico": 0.02, 
    "Cable apantallado en conducto metálico": 0.002, 
    # Simplification for UI
}

# Table B.6 - Probability Ptu (Shock from Line)
PTU_VALUES = {
    "Sin protección (Aislamiento/Avisos)": 1.0,
    "Avisos de advertencia": 0.1,
    "Aislamiento eléctrico": 0.01,
    "Equipotencialización efectiva": 0.001,
}

# Table B.7 - Probability Peb (Physical from Line)
PEB_VALUES = {
    "Sin SPD": 1.0,
    # Usually depends on SPDs at entrance
    "SPD III-IV": 0.05, 
    "SPD II": 0.02,
    "SPD I": 0.01,
}

# Table B.8 - Probability Pld (Line Failure)
PLD_VALUES = {
    "Sin protección": 1.0,
    "SPD (III-IV)": 0.05,
    "SPD (II)": 0.02,
    "SPD (I)": 0.01,
}

# Table B.9 - Probability Pli (Induced Failure)
PLI_VALUES = {
    "Sin protección": 1.0,
    "SPD (III-IV)": 0.05,
    "SPD (II)": 0.02,
    "SPD (I)": 0.01,
}

# --- ANNEX C: Losses ---


# --- ANNEX C: Losses ---

# Table C.2 - Lf1 (Mental/Physical Loss R1)
LF1_VALUES = {
    "Industrial / Comercial": 0.05, # Prompt says "Industrial, comercios" default for Rb Lf1? Prompt says "Industrial, comercios". Usually 0.02 or 0.05. Using 0.05 per some versions or keeping standard.
    # User prompt: "2.3.4. Lf1=Tabla C.2 (Por defecto --> Industrial, comercios)"
    # Standard IEC 62305-2 Table C.2: Commercial/Industrial = 5e-2 or 2e-2 depending on risk.
    # We will provide options.
    "Hospital / Hotel / Escuela": 0.1,
    "Público / Entretenimiento": 0.05,
    "Industrial / Comercios": 0.02, # Usually 2e-2
    "Museo / Agrícola": 0.02,
    "Otros": 0.01,
    "Riesgo Explosión": 0.1,
}

# Values for Lo1 (Prompt: 0 unless hospital/explosive)
# We handle the "0 default" via code logic or a "Ninguno" entry?
# Prompt: "3.3.1. Lo1=Tabla C.2 (Por defecto --> 0 siempre que no se trate de un hospital...)"
# So we add a "Ninguno" option.
LO1_VALUES = {
    "Ninguno (Por defecto)": 0.0,
    "Hospital / Reanimación": 1e-3, # Typ value
    "Riesgo Explosión": 1e-1,
}

# Table C.12 - Lt (Injury)
# Prompt: "Por defecto --> 10^-2"
LT_VALUES = {
    "Por defecto (10^-2)": 1e-2,
    "Todos los tipos (D1)": 1e-2, 
    "Fallo Sistemas (D3)": 1e-2, 
    "Usuario Definido": 1e-2, 
}

# Table C.3 - rt (Reduction Step/Touch)
RT_VALUES = {
    "Agrícola / Hormigón (Defecto)": 0.01,
    "Suelo (Tierra)": 0.01, 
    "Mármol/Cerámica": 0.001,
    "Asfalto/Madera/Moqueta": 1e-5,
}

# Table C.4 - rp (Fire Protection)
# Prompt: "Una de las siguientes medidas: extintores; ..."
RP_VALUES = {
    "Sin medidas": 1.0,
    "Extintores / Mangueras / Alarma (Defecto)": 0.5, # Prompt default
    "Fijo Automático (Rociadores)": 0.2,
}

# Table C.5 - rf (Fire Risk)
RF_VALUES = {
    "Fuego Normal (Defecto)": 0.01, # Usually 10^-2 for ordinary fire? Prompt says "Fuego Normal". Standard says "Ordinary fire risk" = 0.01
    "Explosión (Zonas 0,1,20,21)": 1.0,
    "Explosión (Zonas 2,22)": 0.1,
    "Incendio Alto": 0.1,
    "Incendio Bajo": 0.001,
}

# Table C.6 - hz (Panic)
HZ_VALUES = {
    "Nivel bajo de pánico (<100 pers, <2 pisos)": 2.0, # Prompt default
    "Sin riesgo especial": 1.0,
    "Pánico alto (>100 pers)": 5.0,
    "Difícil evacuación": 5.0,
    "Contaminación": 20.0,
}

# Table C.8 - Lf2, Lo2 (Service Loss)
LF2_VALUES = {
    "Gas/Agua/Suministro": 1e-1,
    "TV/Teleco": 1e-2,
    "Industrial": 1e-2,
}
LO2_VALUES = {
    "Gas/Agua/Suministro": 1e-2,
    "TV/Teleco": 1e-3,
    "Industrial": 1e-3,
}

# Table C.12 - Lf4, Lo4 (Economic) - And Animals (Lt type)
LF4_VALUES = {
    "Todos (Riesgo Explosión)": 1.0,
    "Hospital/Industrial/Museo": 0.5,
    "Hotel/Escuela/Oficina": 0.2,
    "Agua/Suministro": 0.2,
}
LO4_VALUES = {
    "Riesgo Explosión": 0.1,
    "Hospital/Industrial": 0.01,
}
