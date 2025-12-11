"""
IEC 62305-2 Normative Tables (V2 Strict)
Updated: PLI now separated by line type (Power/Communication) - v2.1
"""

# --- ANNEX A: Environmental & Location ---

# Table A.1 - Factor Cd (Structure Location)
CD_FACTOR = {
    "Estructura rodeada por objetos más altos": 0.25,
    "Estructura rodeado por objetos de la misma altura o inferior": 0.5,
    "Estructura aislada: sin otros objetos en las proximidades": 1.0,
    "Estructura aislada en la parte superior de una colina o de un montículo": 2.0,
}

# Table A.2 - Factor Ci (Line Installation)
CI_FACTOR = {
    "Aérea": 1.0,
    "Enterrada": 0.5,
    "Enterrada con pantalla (conductiva)": 0.01, # Approx convention if not strict equation
}

# Table A.3 - Factor Ct (Line Type)
CT_FACTOR = {
    "Línea de potencia de BT, línea de datos o de telecomunicación": 1.0, # Default for direct connection
    "Línea de potencia de AT (con transformador AT/BT)": 0.2,
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
    "Sin medidas de protección": 1.0,
    "Avisos de peligro": 0.1,
    "Aislamiento eléctrico": 0.01,
    "Equipotencialización efectiva": 0.01,
    "Restricciones físicas o armadura metálica del edificio": 0,
}

# Table B.2 - Probability Pb (Physical Damage / LPS)
PB_VALUES = {
    "Sin LPS": 1.0,
    "LPS Clase IV": 0.2,
    "LPS Clase III": 0.1,
    "LPS Clase II": 0.05,
    "LPS Clase I": 0.02,
    "Captador de nivel I, con armaduras metálicas continuas": 0.01,
    "Con techo metálico o con sistema de captación": 0.001,
}

# Table B.3 - Probability Pspd (SPDs)
# Note: Prompt condition: If LPL II exists, PB=0.05. 
PSPD_VALUES = {
    "Sin SPDs": 1.0,
    "SPD III-IV (LPL III/IV)": 0.05,
    "SPD II (LPL II)": 0.02,
    "SPD I (LPL I)": 0.01,
    "SPD que tengan unas características de protección mejores": 0.005,
}

# Table B.4 - Factor Cld (Line shielding/routing)
CLD_VALUES = {
    "Línea aérea sin apantallar": 1.0,
    "Línea enterrada sin apantallar": 1.0, # Depends on resistance usually, simplified 1.0 or user input
    "Línea de potencia con multi puesta a tierra del neutro": 1.0,
    "Línea enterrada apantallada (potencia o telecomunicación)": 1.0, 
    "Línea aérea apantallada (potencia o telecomunicación)": 1.0,
    "Línea enterrada apantallada (potencia o telecomunicación)": 1.0,
    "Línea aérea apantallada (potencia o telecomunicación)": 1.0,
    "Sin blindaje particular": 1.0,
    "No hay línea externa": 0,
}

# Table B.5 - Factor Ks3 (Internal Wiring)
KS3_VALUES = {
    "Cable sin apantallar_sin precauciones de cableado para evitar bucles": 1.0,
    "Cable sin apantallar_precauciones de cableado para evitar grandes bucles": 0.2,  # Default option
    "Cable sin apantallar_precauciones de cableado para evitar bucles": 0.01, 
    "Cables apantallados en conductos metálicos": 0.0001,
}

# Table B.6 - Probability Ptu (Shock from Line)
PTU_VALUES = {
    "Sin medidas de protección": 1.0,
    "Avisos": 0.1,
    "Aislamiento eléctrico": 0.01,
    "Restricciones físicas": 0.0,
}

# Table B.7 - Probability Peb (Physical from Line)
PEB_VALUES = {
    "Sin SPD": 1.0,
    "SPD III-IV": 0.05, 
    "SPD II": 0.02,
    "SPD I": 0.01,
    "SPD que tengan unas características de protección mejores": 0.005,
}

# Table B.8 - Probability Pld (Line Failure)
PLD_VALUES = {
    "1 kV": 1,
    "1,5 kV": 1,
    "2,5 kV": 1,
    "4 kV": 1,
    "6 kV": 1,
}

# Table B.9 - Probability Pli (Induced Failure)
# Separated by line type: Power Lines (LP) and Communication Lines (LC)
PLI_VALUES_LP = {
    "1 kV": 1,
    "1,5 kV": 0.6,
    "2,5 kV": 0.3,
    "4 kV": 0.16,
    "6 kV": 0.1,
}

PLI_VALUES_LC = {
    "1 kV": 1,
    "1,5 kV": 0.5,
    "2,5 kV": 0.2,
    "4 kV": 0.08,
    "6 kV": 0.04,
}



# --- ANNEX C: Losses ---

# Table C.2 - Lf1 (Mental/Physical Loss R1)
LF1_VALUES = {
    "Riesgo de explosión": 0.1,
    "Hospitales, hoteles, escuelas, edificio público": 0.1,
    "Eventos públicos, iglesias, museos": 0.05,
    "Industrial, comercios": 0.02,
    "Otros": 0.01,
}

# Values for Lo1 (Prompt: 0 unless hospital/explosive)
# We handle the "0 default" via code logic or a "Ninguno" entry?
# Prompt: "3.3.1. Lo1=Tabla C.2 (Por defecto --> 0 siempre que no se trate de un hospital...)"
# So we add a "Ninguno" option.
LO1_VALUES = {
    "Ninguno (Por defecto)": 0.0,
    "Unidad de cuidado intensivos y quirófanos de un hospital": 1e-2,
    "Hospital / Reanimación": 1e-3,
    "Riesgo Explosión": 1e-1,
}

# Table C.12 - Lt (Injury)
# Prompt: "Por defecto --> 10^-2"
LT_VALUES = {
    "Por defecto (10^-2)": 1e-2,
    "Todos los tipos (D1)": 1e-2,
}

# Table C.3 - rt (Reduction Step/Touch)
RT_VALUES = {
    "Agrícola / Hormigón (Defecto)": 1e-2,
    "Mármol, cerámica": 1e-3, 
    "Grava, moqueta, alfombra": 1e-4,
    "Asfalto, linóleo, madera": 1e-5,
}

# Table C.4 - rp (Fire Protection)
# Prompt: "Una de las siguientes medidas: extintores; ..."
RP_VALUES = {
    "Sin medidas": 1.0,
    "Extintores / Mangueras / Alarma": 0.5,
    "Fijo Automático (Rociadores)": 0.2,
}

# Table C.5 - rf (Fire Risk)
RF_VALUES = {
    "Fuego Normal": 0.01,
    "Explosión (Zonas 0, 20 y explosivos sólidos)": 1.0,
    "Explosión (Zonas 1, 21)": 0.1,
    "Explosión (Zonas 2, 22)": 0.001,
    "Fuego Alto": 0.1,
    "Fuego Bajo": 0.001,
    "Ninguno": 0,
}

# Table C.6 - hz (Panic)
HZ_VALUES = {
    "Nivel bajo de pánico (<100 pers, <2 pisos)": 2.0, # Prompt default
    "Sin riesgo especial": 1.0,
    "Pánico alto (>100 pers)": 5.0,
    "Difícil evacuación": 5.0,
    "Nivel alto de pánico": 10.0,
}

# Table C.8 - Lf2, Lo2 (Service Loss)
LF2_VALUES = {
    "Gas/Agua/Suministro": 1e-1,
    "TV/Teleco": 1e-2,
}

LO2_VALUES = {
    "Gas/Agua/Suministro": 1e-2,
    "TV/Teleco": 1e-3,
}

# Table C.12 - Lf4, Lo4 (Economic) - And Animals (Lt type)
LF4_VALUES = {
    "Todos (Riesgo Explosión)": 1.0,
    "Hospital/Industrial/Museo": 0.5,
    "Hotel/Escuela/Oficina": 0.2,
    "Otros": 0.1,
}
LO4_VALUES = {
    "Riesgo Explosión": 0.1,
    "Hospital/Industrial/Oficinas": 0.01,
    "Museos/Agricultura/Escuelas": 1e-3,
    "Otros": 1e-4,
}

# --- Economic Values (R4 Risk) ---

# Default economic values for R4 (currency units)
DEFAULT_ECONOMIC_VALUES = {
    "ca": 0,      # Valor de los animales en la zona (por defecto 0)
    "cb": 350,    # Valor del edificio relevante de la zona
    "cc": 50,     # Valor del contenido en la zona
    "cs": 75,     # Valor de los sistemas internos incluidas sus actividades de la zona
    "ct": 500,    # Valor total de la estructura
}
