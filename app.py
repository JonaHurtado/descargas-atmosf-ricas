import streamlit as st
from tables import *
from iec_62305 import GeometricParameters, ZoneParameters, LineParameters, EngineIEC62305

st.set_page_config(page_title="IEC 62305-2: Cálculo R1, R2 y R4", layout="wide")

def main():
    st.title("⚡ IEC 62305-2: Cálculo de Riesgos R1, R2 y R4")
    st.caption("R1 = Ra1 + Rb1 + Rc1* + Rm1* + Ru1 + Rv1 + Rw1* + Rz1* | R2 = Rb2 + Rc2* + Rm2* + Rv2 + Rw2* + Rz2* | R4 = Ra4* + Rb4 + Rc4 + Rm4 + Ru4* + Rv4 + Rw4 + Rz4")
    
    # === SIDEBAR: Global Parameters ===
    with st.sidebar:
        st.header("🌍 Parámetros Globales")
        
        st.subheader("Geometría de la Estructura")
        ng = st.number_input("Ng - Densidad de rayos (rayos/km²/año)", 0.1, 50.0, 1.0, 0.1)
        
        col1, col2, col3 = st.columns(3)
        l_dim = col1.number_input("L (m)", value=6.058, min_value=0.1)
        w_dim = col2.number_input("W (m)", value=2.438, min_value=0.1)
        h_dim = col3.number_input("H (m)", value=2.896, min_value=0.1)
        
        cd_k = st.selectbox("Cd - Situación de la estructura (Tabla A.1)", 
                           list(CD_FACTOR.keys()), 
                           index=2)  # Default: "Objeto aislado"
        
        st.divider()
        use_manual_ad = st.checkbox("Definir Ad manualmente")
        ad_manual = None
        if use_manual_ad:
            ad_manual = st.number_input("Ad (m²)", value=1000.0, min_value=0.0)
        
        use_manual_am = st.checkbox("Definir Am manualmente")
        am_manual = None
        if use_manual_am:
            am_manual = st.number_input("Am (m²)", value=100000.0, min_value=0.0)
        
        geom = GeometricParameters(
            L=l_dim, W=w_dim, H=h_dim, 
            Ng=ng, Cd=CD_FACTOR[cd_k],
            Ad_manual=ad_manual, Am_manual=am_manual
        )
    
    # === MAIN: Line Parameters ===
    st.header("⚡ Líneas Entrantes")
    with st.expander("Configuración de Línea de Energía", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Parámetros de Línea")
            ll = st.number_input("Ll - Longitud de línea (m)", value=1000.0, min_value=0.0)
            ci_k = st.selectbox("Ci - Instalación (Tabla A.2)", 
                               list(CI_FACTOR.keys()),
                               index=1)  # Default: "Enterrada"
            ce_k = st.selectbox("Ce - Entorno (Tabla A.4)", 
                               list(CE_LINE_FACTOR.keys()),
                               index=0)  # Default: "Rural"
            ct_k = st.selectbox("Ct - Tipo de línea (Tabla A.3)",
                               list(CT_FACTOR.keys()),
                               index=1)  # Default: "Con transformador"
        
        with col2:
            st.subheader("Estructura Adyacente (Ndj)")
            st.caption("Dejar en 0 si no hay estructura adyacente")
            lj = st.number_input("Lj - Longitud adyacente (m)", value=0.0, min_value=0.0)
            wj = st.number_input("Wj - Ancho adyacente (m)", value=0.0, min_value=0.0)
            hj = st.number_input("Hj - Altura adyacente (m)", value=0.0, min_value=0.0)
            cdj_k = st.selectbox("Cdj - Situación adyacente (Tabla A.1)",
                                list(CD_FACTOR.keys()),
                                index=2)
    
    line = LineParameters(
        name="Línea Principal",
        length=ll,
        ci=CI_FACTOR[ci_k],
        ce=CE_LINE_FACTOR[ce_k],
        ct=CT_FACTOR[ct_k],
        Lj=lj, Wj=wj, Hj=hj,
        Cdj=CD_FACTOR[cdj_k]
    )
    
    # === ZONES ===
    st.header("🏢 Zonas de Análisis")
    
    if 'n_zones' not in st.session_state:
        st.session_state.n_zones = 1
    
    col_add, col_remove = st.columns([1, 1])
    with col_add:
        if st.button("➕ Añadir Zona"):
            st.session_state.n_zones += 1
            st.rerun()
    with col_remove:
        if st.button("➖ Eliminar Última Zona") and st.session_state.n_zones > 1:
            st.session_state.n_zones -= 1
            st.rerun()
    
    zones_list = []
    
    for i in range(st.session_state.n_zones):
        with st.expander(f"🔧 Configuración Zona #{i+1}", expanded=(i==0)):
            z_name = st.text_input("Nombre de la zona", f"Zona {i+1}", key=f"name_{i}")
            
            # Conditional flags
            st.markdown("### ⚠️ Condiciones Especiales")
            col_ex, col_hosp = st.columns(2)
            is_explosion = col_ex.checkbox("🔥 Estructura con riesgo de explosión", key=f"expl_{i}")
            is_hospital = col_hosp.checkbox("🏥 Hospital con equipos de reanimación", key=f"hosp_{i}")
            
            if is_explosion or is_hospital:
                st.info("✓ Componentes condicionales activados: Rc*, Rm*, Rw*, Rz*")
            else:
                st.warning("Los componentes Rc*, Rm*, Rw*, Rz* serán = 0")
            
            # Create R1, R2 and R4 tabs
            tab_r1, tab_r2, tab_r4 = st.tabs(["📊 Componentes R1", "📊 Componentes R2", "📊 Componentes R4"])
            
            with tab_r1:
                # === Component Ra ===
                st.markdown("### 1️⃣ Ra: Impacto en Estructura (Nd·Pa·La1)")
                
                st.markdown("**1.2. Pa (Probabilidad de daño)**")
                col1, col2 = st.columns(2)
                pta_k = col1.selectbox("Pta - Protección choque (Tabla B.1)", 
                                       list(PTA_VALUES.keys()),
                                       index=2, key=f"pta_{i}")  # "Aislamiento eléctrico"
                pb_k = col2.selectbox("Pb - LPS (Tabla B.2)",
                                     list(PB_VALUES.keys()),
                                     index=0, key=f"pb_{i}")  # "Sin LPS"
                
                st.markdown("**1.3. La1 (Pérdidas relativas)**")
                col1, col2, col3 = st.columns(3)
                rt_k = col1.selectbox("rt - Tipo suelo (Tabla C.3)",
                                     list(RT_VALUES.keys()),
                                     index=0, key=f"rt_{i}")  # "Agrícola / Hormigón"
                lt_val = col2.number_input("Lt - Pérdida típica (Tabla C.12)",
                                          value=1e-2, format="%.1e", key=f"lt_{i}")
                
                col1, col2, col3 = st.columns(3)
                nz = col1.number_input("nz - Personas en zona", value=1.0, min_value=0.0, key=f"nz_{i}")
                nt = col2.number_input("nt - Total personas", value=1.0, min_value=0.1, key=f"nt_{i}")
                tz = col3.number_input("tz - Horas/año en zona", value=8760.0, min_value=0.0, key=f"tz_{i}")
                
                # === Component Rb ===
                st.markdown("### 2️⃣ Rb: Fuego en Estructura (Nd·Pb·Lb1)")
                st.caption("ℹ️ Usa mismo Nd y Pb que Ra")
                
                st.markdown("**2.3. Lb1 (Pérdidas por fuego)**")
                col1, col2 = st.columns(2)
                rp_k = col1.selectbox("rp - Protección fuego (Tabla C.4)",
                                     list(RP_VALUES.keys()),
                                     index=1, key=f"rp_{i}")  # "Extintores..."
                rf_k = col2.selectbox("rf - Riesgo fuego (Tabla C.5)",
                                     list(RF_VALUES.keys()),
                                     index=0, key=f"rf_{i}")  # "Fuego Normal"
                
                col1, col2 = st.columns(2)
                hz_k = col1.selectbox("hz - Pánico (Tabla C.6)",
                                     list(HZ_VALUES.keys()),
                                     index=0, key=f"hz_{i}")  # "Nivel bajo"
                lf1_k = col2.selectbox("Lf1 - Tipo edificio (Tabla C.2)",
                                      list(LF1_VALUES.keys()),
                                      index=3, key=f"lf1_{i}")  # "Industrial, comercios"
                
                col1, col2, col3 = st.columns(3)
                nz_rb = col1.number_input("nz (Rb)", value=1.0, min_value=0.0, key=f"nz_rb_{i}")
                nt_rb = col2.number_input("nt (Rb)", value=1.0, min_value=0.1, key=f"nt_rb_{i}")
                tz_rb = col3.number_input("tz (Rb)", value=8760.0, min_value=0.0, key=f"tz_rb_{i}")
                
                # === Component Rc* ===
                st.markdown("### 3️⃣ Rc*: Fallo en Estructura (Nd·Pc·Lc1)")
                if is_explosion or is_hospital:
                    st.markdown("**3.2. Pc (Probabilidad de fallo)**")
                    col1, col2 = st.columns(2)
                    pspd_k = col1.selectbox("Pspd - SPD (Tabla B.3)",
                                           list(PSPD_VALUES.keys()),
                                           index=2, key=f"pspd_{i}")  # "SPD II"
                    cld_k = col2.selectbox("Cld - Apantallamiento (Tabla B.4)",
                                          list(CLD_VALUES.keys()),
                                          index=2, key=f"cld_{i}")  # "Línea enterrada"
                    
                    
                    st.markdown("**3.3. Lc1 (Pérdidas por fallo)**")
                    lo1_k = st.selectbox("Lo1 - Pérdida fallo sistemas (Tabla C.2)",
                                         list(LO1_VALUES.keys()),
                                         index=0, key=f"lo1_{i}")  # Default: "Ninguno"
                    
                    col1, col2, col3 = st.columns(3)
                    nz_rc = col1.number_input("nz (Rc)", value=1.0, min_value=0.0, key=f"nz_rc_{i}")
                    nt_rc = col2.number_input("nt (Rc)", value=1.0, min_value=0.1, key=f"nt_rc_{i}")
                    tz_rc = col3.number_input("tz (Rc)", value=8760.0, min_value=0.0, key=f"tz_rc_{i}")
                else:
                    st.info("⊘ No activo (requiere riesgo de explosión o hospital)")
                    pspd_k = list(PSPD_VALUES.keys())[2]
                    cld_k = list(CLD_VALUES.keys())[2]
                    lo1_k = list(LO1_VALUES.keys())[0]  # Default: "Ninguno"
                    nz_rc, nt_rc, tz_rc = 1.0, 1.0, 8760.0
                
                # === Component Rm* ===
                st.markdown("### 4️⃣ Rm*: Fallo Cerca Estructura (Nm·Pm·Lm1)")
                if is_explosion or is_hospital:
                    st.caption("ℹ️ Lm1 = Lc1 (reutilizado)")
                    
                    st.markdown("**4.2. Pm (Probabilidad con SPD)**")
                    col1, col2, col3, col4 = st.columns(4)
                    wm1 = col1.number_input("wm1 (m)", value=2.0, min_value=0.0, key=f"wm1_{i}")
                    wm2 = col2.number_input("wm2 (m)", value=2.0, min_value=0.0, key=f"wm2_{i}")
                    ks3_k = col3.selectbox("Ks3 - Cableado (Tabla B.5)",
                                          list(KS3_VALUES.keys()),
                                          index=1, key=f"ks3_{i}")  # Default: "Cable sin apantallar..."
                    uw = col4.number_input("Uw (kV)", value=1.0, min_value=0.1, key=f"uw_{i}")
                else:
                    st.info("⊘ No activo (requiere riesgo de explosión o hospital)")
                    wm1, wm2, uw = 2.0, 2.0, 1.0
                    ks3_k = list(KS3_VALUES.keys())[1]  # Default: "Cable sin apantallar..."
                
                # === Component Ru ===
                st.markdown("### 5️⃣ Ru: Choque desde Línea ((Nl+Ndj)·Pu·Lu1)")
                
                st.markdown("**5.3. Pu (Probabilidad de choque)**")
                col1, col2 = st.columns(2)
                ptu_k = col1.selectbox("Ptu - Protección choque línea (Tabla B.6)",
                                      list(PTU_VALUES.keys()),
                                      index=2, key=f"ptu_{i}")  # "Aislamiento"
                peb_k = col2.selectbox("Peb - Físico línea (Tabla B.7)",
                                      list(PEB_VALUES.keys()),
                                      index=2, key=f"peb_{i}")  # "SPD II"
                
                col1, col2 = st.columns(2)
                pld_k = col1.selectbox("Pld - Fallo línea (Tabla B.8)",
                                      list(PLD_VALUES.keys()),
                                      index=0, key=f"pld_{i}")  # "Sin protección"
                cld_u_k = col2.selectbox("Cld (Ru) - Apantallamiento (Tabla B.4)",
                                        list(CLD_VALUES.keys()),
                                        index=2, key=f"cld_u_{i}")
                
                st.markdown("**5.4. Lu1 (Pérdidas)**")
                col1, col2 = st.columns(2)
                rt_u_k = col1.selectbox("rt (Lu1) - Tipo suelo",
                                       list(RT_VALUES.keys()),
                                       index=0, key=f"rt_u_{i}")
                lt_u_val = col2.number_input("Lt (Lu1)",
                                            value=1e-2, format="%.1e", key=f"lt_u_{i}")
                
                col1, col2, col3 = st.columns(3)
                nz_u = col1.number_input("nz (Ru)", value=1.0, min_value=0.0, key=f"nz_u_{i}")
                nt_u = col2.number_input("nt (Ru)", value=1.0, min_value=0.1, key=f"nt_u_{i}")
                tz_u = col3.number_input("tz (Ru)", value=8760.0, min_value=0.0, key=f"tz_u_{i}")
                
                # === Component Rv ===
                st.markdown("### 6️⃣ Rv: Fuego desde Línea ((Nl+Ndj)·Pv·Lv1)")
                st.caption("ℹ️ Lv1 = Lb1 (reutilizado)")
                
                st.markdown("**6.3. Pv (Probabilidad de fuego)**")
                col1, col2, col3 = st.columns(3)
                peb_v_k = col1.selectbox("Peb (Rv) - Físico (Tabla B.7)",
                                        list(PEB_VALUES.keys()),
                                        index=2, key=f"peb_v_{i}")
                pld_v_k = col2.selectbox("Pld (Rv) - Fallo (Tabla B.8)",
                                        list(PLD_VALUES.keys()),
                                        index=0, key=f"pld_v_{i}")
                cld_v_k = col3.selectbox("Cld (Rv) - Apantallamiento (Tabla B.4)",
                                        list(CLD_VALUES.keys()),
                                        index=2, key=f"cld_v_{i}")
                
                # === Component Rw* ===
                st.markdown("### 7️⃣ Rw*: Fallo desde Línea ((Nl+Ndj)·Pw·Lw1)")
                if is_explosion or is_hospital:
                    st.caption("ℹ️ Lw1 = Lc1 (reutilizado)")
                    
                    st.markdown("**7.3. Pw (Probabilidad de fallo)**")
                    col1, col2, col3 = st.columns(3)
                    pspd_w_k = col1.selectbox("Pspd (Rw) - SPD",
                                             list(PSPD_VALUES.keys()),
                                             index=2, key=f"pspd_w_{i}")
                    pld_w_k = col2.selectbox("Pld (Rw) - Fallo",
                                            list(PLD_VALUES.keys()),
                                            index=0, key=f"pld_w_{i}")
                    cld_w_k = col3.selectbox("Cld (Rw) - Apantallamiento",
                                            list(CLD_VALUES.keys()),
                                            index=2, key=f"cld_w_{i}")
                else:
                    st.info("⊘ No activo (requiere riesgo de explosión o hospital)")
                    pspd_w_k = list(PSPD_VALUES.keys())[2]
                    pld_w_k = list(PLD_VALUES.keys())[0]
                    cld_w_k = list(CLD_VALUES.keys())[2]
                
                # === Component Rz* ===
                st.markdown("### 8️⃣ Rz*: Fallo Inducido (Ni·Pz·Lz1)")
                if is_explosion or is_hospital:
                    st.caption("ℹ️ Lz1 = Lc1 (reutilizado)")
                    
                    st.markdown("**8.2. Pz (Probabilidad de fallo inducido)**")
                    col1, col2 = st.columns(2)
                    pspd_z_k = col1.selectbox("Pspd (Rz) - SPD",
                                             list(PSPD_VALUES.keys()),
                                             index=2, key=f"pspd_z_{i}")
                    
                    # Select line type
                    line_type = col2.selectbox("Tipo de línea",
                                              ["Línea de Potencia", "Línea de Comunicación"],
                                              index=0, key=f"line_type_{i}")
                    
                    # Select voltage level based on line type
                    if line_type == "Línea de Potencia":
                        pli_dict = PLI_VALUES_LP
                    else:
                        pli_dict = PLI_VALUES_LC
                    
                    col1, col2 = st.columns(2)
                    pli_voltage_k = col1.selectbox("Pli - Nivel de tensión (Tabla B.9)",
                                                   list(pli_dict.keys()),
                                                   index=0, key=f"pli_voltage_{i}")
                    pli_value = pli_dict[pli_voltage_k]
                    
                    cli_k = col2.selectbox("Cli - Apantallamiento (Tabla B.4)",
                                          list(CLD_VALUES.keys()),
                                          index=2, key=f"cli_{i}")
                else:
                    st.info("⊘ No activo (requiere riesgo de explosión o hospital)")
                    pspd_z_k = list(PSPD_VALUES.keys())[2]
                    pli_value = 1.0  # Default PLI value
                    cli_k = list(CLD_VALUES.keys())[2]
            
            
            # === R2 TAB ===
            with tab_r2:
                st.markdown("### ℹ️ Parámetros Reutilizados de R1")
                st.info("""
                R2 reutiliza los siguientes parámetros de R1:
                - **Nd, Nm, Nl, Ni**: Frecuencias de impacto (calculadas)
                - **Pb**: Probabilidad de daño físico (Tabla B.2)
                - **Pc, Pm, Pv, Pw, Pz**: Probabilidades de fallo (calculadas de R1)
                - **rp, rf**: Factores de protección contra fuego (Tabla C.4, C.5)
                - **Pspd, Cld, wm1, wm2, Ks3, Uw**: Parámetros SPD
                - **nz, nt**: Ocupación (a menos que se especifique diferente)
                """)
                
                st.markdown("### 🔧 Parámetros Específicos de R2")
                st.caption("⚠️ **Nota**: R2 siempre calcula los 6 componentes (Rb2, Rc2, Rm2, Rv2, Rw2, Rz2)")
                
                # === Rb2 Component ===
                st.markdown("#### 1️⃣ Rb2: Fuego en Estructura (Nd·Pb·Lb2)")
                st.caption("Usa Nd y Pb de R1. Solo define Lb2 específico para R2.")
                
                col1, col2 = st.columns(2)
                lf2_k = col1.selectbox("Lf2 - Pérdida por fuego (Tabla C.8)",
                                       list(LF2_VALUES.keys()),
                                       index=0, key=f"lf2_{i}")  # Default: "Gas/Agua/Suministro" = 10^-1
                
                st.caption("📝 Lb2 = rp × rf × Lf2 × (nz/nt) [Ecuación C.7]")
                
                # === Rc2 Component ===
                st.markdown("#### 2️⃣ Rc2: Fallo en Estructura (Nd·Pc·Lc2)")
                st.caption("Usa Nd y Pc de R1. Solo define Lo2 específico para R2.")
                
                lo2_k = st.selectbox("Lo2 - Pérdida por fallo (Tabla C.8)",
                                    list(LO2_VALUES.keys()),
                                    index=0, key=f"lo2_{i}")  # Default: "Gas/Agua/Suministro" = 10^-2
                
                st.caption("📝 Lc2 = Lo2 × (nz/nt) [Ecuación C.8]")
                
                # === Rm2 Component ===
                st.markdown("#### 3️⃣ Rm2: Fallo Cerca Estructura (Nm·Pm·Lm2)")
                
                # Show parameters if they are already defined in R1 (explosion/hospital) or allow user to define them
                if is_explosion or is_hospital:
                    st.caption("✓ Usa Nm de R1. Parámetros Pm definidos en R1 (wm1, wm2, Ks3, Uw, Pspd)")
                    # Use R1 values - already captured in the variables
                    use_r1_rm_params = True
                else:
                    st.caption("⚠️ No definido en R1. Debe definir parámetros para Pm:")
                    use_r1_rm_params = False
                    
                    # Define Rm parameters only for R2
                    col1, col2, col3, col4 = st.columns(4)
                    wm1_r2 = col1.number_input("wm1 (m) [R2]", value=2.0, min_value=0.0, key=f"wm1_r2_{i}")
                    wm2_r2 = col2.number_input("wm2 (m) [R2]", value=2.0, min_value=0.0, key=f"wm2_r2_{i}")
                    ks3_r2_k = col3.selectbox("Ks3 (Tabla B.5) [R2]",
                                              list(KS3_VALUES.keys()),
                                              index=1, key=f"ks3_r2_{i}")  # Default: "Cable sin apantallar..."
                    uw_r2 = col4.number_input("Uw (kV) [R2]", value=1.0, min_value=0.1, key=f"uw_r2_{i}")
                
                st.caption("✓ Pm = Pspd × Pms, donde Pms = (Ks1·Ks2·Ks3·Ks4)². Lm2 = Lc2")
                
                # === Other R2 Components ===
                
                st.markdown("#### 4️⃣ Rv2: Fuego desde Línea ((Nl+Ndj)·Pv·Lv2)")
                st.caption("✓ Usa Nl, Ndj, Pv de R1. Lv2 = Lb2")
                
                st.markdown("#### 5️⃣ Rw2: Fallo desde Línea ((Nl+Ndj)·Pw·Lw2)")
                st.caption("✓ Usa Nl, Ndj, Pw de R1. Lw2 = Lc2")
                
                st.markdown("#### 6️⃣ Rz2: Fallo Inducido (Ni·Pz·Lz2)")
                st.caption("✓ Usa Ni, Pz de R1. Lz2 = Lc2")
                
                # Optional: Different nz/nt for R2
                st.markdown("---")
                st.markdown("#### ⚙️ Ocupación Opcional para R2")
                use_r2_occupancy = st.checkbox("Usar ocupación diferente para R2", key=f"use_r2_occ_{i}")
                if use_r2_occupancy:
                    col1, col2 = st.columns(2)
                    nz_r2 = col1.number_input("nz (R2)", value=1.0, min_value=0.0, key=f"nz_r2_{i}")
                    nt_r2 = col2.number_input("nt (R2)", value=1.0, min_value=0.1, key=f"nt_r2_{i}")
                else:
                    nz_r2 = None
                    nt_r2 = None
            
            
            # === R4 TAB ===
            with tab_r4:
                st.markdown("### ℹ️ Parámetros Reutilizados de R1")
                st.info("""
                R4 reutiliza los siguientes parámetros de R1:
                - **Nd, Nm, Nl, Ni**: Frecuencias de impacto (calculadas)
                - **Pa, Pb, Pc, Pm, Pu, Pv, Pw, Pz**: Probabilidades (calculadas de R1)
                - **rt, lt, rp, rf**: Factores de pérdida (a menos que se especifique diferente abajo)
                - **Pspd, Cld, wm1, wm2, Ks3, Uw**: Parámetros SPD
                """)
                
                st.markdown("### 🐄 Condición para Pérdida de Animales")
                has_animal_loss = st.checkbox(
                    "Zona con riesgo de pérdida de animales", 
                    key=f"has_animal_{i}",
                    help="Si se activa, se calcularán Ra4* y Ru4*. Si no, estos componentes serán 0."
                )
                
                if has_animal_loss:
                    st.success("✓ Componentes Ra4* y Ru4* activos")
                else:
                    st.warning("⊘ Componentes Ra4* y Ru4* desactivados (= 0)")
                
                st.markdown("### 💰 Valores Económicos")
                st.caption("Definir los valores en unidades monetarias de la zona")
                
                col1, col2, col3 = st.columns(3)
                ca_val = col1.number_input(
                    "ca - Valor animales", 
                    value=0.0, min_value=0.0, 
                    key=f"ca_{i}",
                    help="Valor de los animales en la zona (por defecto 0)"
                )
                cb_val = col2.number_input(
                    "cb - Valor edificio", 
                    value=350.0, min_value=0.0, 
                    key=f"cb_{i}",
                    help="Valor del edificio relevante de la zona"
                )
                cc_val = col3.number_input(
                    "cc - Valor contenido", 
                    value=50.0, min_value=0.0, 
                    key=f"cc_{i}",
                    help="Valor del contenido en la zona"
                )
                
                col1, col2 = st.columns(2)
                cs_val = col1.number_input(
                    "cs - Valor sistemas", 
                    value=75.0, min_value=0.0, 
                    key=f"cs_{i}",
                    help="Valor de los sistemas internos incluidas sus actividades"
                )
                ct_val = col2.number_input(
                    "ct - Valor total estructura", 
                    value=500.0, min_value=0.1, 
                    key=f"ct_{i}",
                    help="Valor total de la estructura"
                )
                
                st.markdown("### 📊 Factores de Pérdida R4")
                st.caption("Seleccionar de las tablas IEC 62305-2. Si no se especifica, se reutilizan los valores de R1.")
                
                col1, col2 = st.columns(2)
                lf4_k = col1.selectbox(
                    "Lf4 - Tipo edificio (Tabla C.12)",
                    list(LF4_VALUES.keys()),
                    index=1,  # Default: "Hospital/Industrial/Oficinas"
                    key=f"lf4_{i}"
                )
                lo4_k = col2.selectbox(
                    "Lo4 - Pérdida sistemas (Tabla C.12)",
                    list(LO4_VALUES.keys()),
                    index=1,  # Default: "Hospital/Industrial/Oficinas"
                    key=f"lo4_{i}"
                )
                
                st.markdown("---")
                st.markdown("#### ⚙️ Factores Opcionales (Sobrescribir R1)")
                use_r4_factors = st.checkbox(
                    "Usar factores de pérdida diferentes para R4", 
                    key=f"use_r4_factors_{i}",
                    help="Si se activa, puede definir rt, lt, rp, rf específicos para R4"
                )
                
                if use_r4_factors:
                    col1, col2 = st.columns(2)
                    rt_r4_k = col1.selectbox(
                        "rt (R4) - Tipo suelo (Tabla C.3)",
                        list(RT_VALUES.keys()),
                        index=0,
                        key=f"rt_r4_{i}"
                    )
                    lt_r4_val = col2.number_input(
                        "Lt (R4) - Pérdida típica",
                        value=1e-2, format="%.1e",
                        key=f"lt_r4_{i}"
                    )
                    
                    col1, col2 = st.columns(2)
                    rp_r4_k = col1.selectbox(
                        "rp (R4) - Protección fuego (Tabla C.4)",
                        list(RP_VALUES.keys()),
                        index=1,
                        key=f"rp_r4_{i}"
                    )
                    rf_r4_k = col2.selectbox(
                        "rf (R4) - Riesgo fuego (Tabla C.5)",
                        list(RF_VALUES.keys()),
                        index=0,
                        key=f"rf_r4_{i}"
                    )
                else:
                    rt_r4_k = None
                    lt_r4_val = None
                    rp_r4_k = None
                    rf_r4_k = None
                
                st.markdown("---")
                st.markdown("### 📝 Componentes R4")
                st.caption("""
                - **Ra4*** = Nd × Pa × La4 (solo si hay animales)
                - **Rb4** = Nd × Pb × Lb4 (siempre)
                - **Rc4** = Nd × Pc × Lc4 (siempre)
                - **Rm4** = Nm × Pm × Lm4 (siempre)
                - **Ru4*** = (Nl+Ndj) × Pu × Lu4 (solo si hay animales)
                - **Rv4** = (Nl+Ndj) × Pv × Lv4 (siempre)
                - **Rw4** = (Nl+Ndj) × Pw × Lw4 (siempre)
                - **Rz4** = Ni × Pz × Lz4 (siempre)
                """)
            
            # Prepare R2 Rm parameters
            if is_explosion or is_hospital:
                # R1 already defines these, so R2 uses None (fallback to R1)
                wm1_r2_val = None
                wm2_r2_val = None
                ks3_r2_val = None
                uw_r2_val = None
            else:
                # Use R2-specific values
                wm1_r2_val = wm1_r2
                wm2_r2_val = wm2_r2
                ks3_r2_val = KS3_VALUES[ks3_r2_k]
                uw_r2_val = uw_r2


            
            # Create zone object
            zone = ZoneParameters(
                name=z_name,
                is_explosion_risk=is_explosion,
                is_hospital=is_hospital,
                # Ra
                pta=PTA_VALUES[pta_k],
                pb=PB_VALUES[pb_k],
                rt=RT_VALUES[rt_k],
                lt=lt_val,
                nz=nz, nt=nt, tz=tz,
                # Rb
                rp=RP_VALUES[rp_k],
                rf=RF_VALUES[rf_k],
                hz=HZ_VALUES[hz_k],
                lf1=LF1_VALUES[lf1_k],
                nz_rb=nz_rb, nt_rb=nt_rb, tz_rb=tz_rb,
                # Rc
                pspd=PSPD_VALUES[pspd_k],
                cld=CLD_VALUES[cld_k],
                lo1=LO1_VALUES[lo1_k],
                nz_rc=nz_rc, nt_rc=nt_rc, tz_rc=tz_rc,
                # Rm
                wm1=wm1, wm2=wm2,
                ks3=KS3_VALUES[ks3_k],
                uw=uw,
                # Ru
                ptu=PTU_VALUES[ptu_k],
                peb=PEB_VALUES[peb_k],
                pld=PLD_VALUES[pld_k],
                cld_u=CLD_VALUES[cld_u_k],
                rt_u=RT_VALUES[rt_u_k],
                lt_u=lt_u_val,
                nz_u=nz_u, nt_u=nt_u, tz_u=tz_u,
                # Rv
                peb_v=PEB_VALUES[peb_v_k],
                pld_v=PLD_VALUES[pld_v_k],
                cld_v=CLD_VALUES[cld_v_k],
                # Rw
                pspd_w=PSPD_VALUES[pspd_w_k],
                pld_w=PLD_VALUES[pld_w_k],
                cld_w=CLD_VALUES[cld_w_k],
                # Rz
                pspd_z=PSPD_VALUES[pspd_z_k],
                pli=pli_value,
                cli=CLD_VALUES[cli_k],
                # R2 specific
                lf2=LF2_VALUES[lf2_k],
                lo2=LO2_VALUES[lo2_k],
                nz_r2=nz_r2,
                nt_r2=nt_r2,
                wm1_r2=wm1_r2_val,
                wm2_r2=wm2_r2_val,
                ks3_r2=ks3_r2_val,
                uw_r2=uw_r2_val,
                # R4 specific
                has_animal_loss=has_animal_loss,
                ca=ca_val,
                cb=cb_val,
                cc=cc_val,
                cs=cs_val,
                ct=ct_val,
                lf4=LF4_VALUES[lf4_k],
                lo4=LO4_VALUES[lo4_k],
                rt_r4=RT_VALUES[rt_r4_k] if rt_r4_k is not None else None,
                lt_r4=lt_r4_val,
                rp_r4=RP_VALUES[rp_r4_k] if rp_r4_k is not None else None,
                rf_r4=RF_VALUES[rf_r4_k] if rf_r4_k is not None else None,
            )
            zones_list.append(zone)
    
    
    # === CALCULATION ===
    st.divider()
    
    if st.button("🔥 CALCULAR RIESGOS R1, R2 Y R4", type="primary", use_container_width=True):
        engine = EngineIEC62305(geom, zones_list, [line])
        result_r1 = engine.compute_risk_R1()
        result_r2 = engine.compute_risk_R2()
        result_r4 = engine.compute_risk_R4()
        
        # === R1 RESULTS ===
        st.header("📊 Resultados R1 (Pérdida de Vida)")
        
        # Main metric
        r1_total = result_r1['total']
        limit_r1 = 1e-5
        is_safe_r1 = r1_total <= limit_r1
        
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            st.metric(
                "R1 Total (Riesgo de Pérdida de Vida)",
                f"{r1_total:.3e}",
                delta=f"Límite: {limit_r1:.0e}",
                delta_color="normal" if is_safe_r1 else "inverse"
            )
        with col2:
            st.metric("Ad (m²)", f"{result_r1['Ad']:.2f}")
        with col3:
            st.metric("Am (m²)", f"{result_r1['Am']:.2f}")
        
        if is_safe_r1:
            st.success(f"✅ CUMPLE: R1 ({r1_total:.3e}) ≤ {limit_r1:.0e}")
        else:
            st.error(f"❌ NO CUMPLE: R1 ({r1_total:.3e}) > {limit_r1:.0e}")
        
        # Detailed breakdown by zone
        st.subheader("📋 Desglose por Zona - R1")
        
        for zone_name, zone_data in result_r1['zones'].items():
            with st.expander(f"🔍 {zone_name} - R1 = {zone_data['Total']:.3e}", expanded=False):
                # Component summary
                st.markdown("#### Componentes R1")
                
                cols = st.columns(4)
                cols[0].metric("Ra", f"{zone_data['Ra']:.3e}")
                cols[1].metric("Rb", f"{zone_data['Rb']:.3e}")
                cols[2].metric("Rc*", f"{zone_data['Rc']:.3e}")
                cols[3].metric("Rm*", f"{zone_data['Rm']:.3e}")
                
                cols = st.columns(4)
                cols[0].metric("Ru", f"{zone_data['Ru']:.3e}")
                cols[1].metric("Rv", f"{zone_data['Rv']:.3e}")
                cols[2].metric("Rw*", f"{zone_data['Rw']:.3e}")
                cols[3].metric("Rz*", f"{zone_data['Rz']:.3e}")
                
                # Intermediate values
                st.markdown("#### Valores Intermedios")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**Factores de Frecuencia**")
                    st.write(f"- Nd = {zone_data['Nd']:.3e}")
                    st.write(f"- Nm = {zone_data['Nm']:.3e}")
                    st.write(f"- Nl = {zone_data['Nl']:.3e}")
                    st.write(f"- Ndj = {zone_data['Ndj']:.3e}")
                    st.write(f"- Ni = {zone_data['Ni']:.3e}")
                
                with col2:
                    st.markdown("**Probabilidades y Pérdidas**")
                    st.write(f"- Pa = {zone_data['Pa']:.3e}")
                    st.write(f"- La1 = {zone_data['La1']:.3e}")
                    st.write(f"- Lb1 = {zone_data['Lb1']:.3e}")
                    st.write(f"- Lc1 = {zone_data['Lc1']:.3e}")
                    
                    if zone_data['is_critical']:
                        st.write(f"- Pc = {zone_data['Pc']:.3e}")
                        st.write(f"- Pm = {zone_data['Pm']:.3e}")
                        st.write(f"- Pms = {zone_data['Pms']:.3e}")
        
        st.divider()
        
        # === R2 RESULTS ===
        st.header("📊 Resultados R2 (Pérdida de Servicio)")
        
        # Main metric
        r2_total = result_r2['total']
        limit_r2 = 1e-3  # R2 typical limit
        is_safe_r2 = r2_total <= limit_r2
        
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            st.metric(
                "R2 Total (Riesgo de Pérdida de Servicio)",
                f"{r2_total:.3e}",
                delta=f"Límite: {limit_r2:.0e}",
                delta_color="normal" if is_safe_r2 else "inverse"
            )
        with col2:
            st.metric("Ad (m²)", f"{result_r2['Ad']:.2f}")
        with col3:
            st.metric("Am (m²)", f"{result_r2['Am']:.2f}")
        
        if is_safe_r2:
            st.success(f"✅ CUMPLE: R2 ({r2_total:.3e}) ≤ {limit_r2:.0e}")
        else:
            st.error(f"❌ NO CUMPLE: R2 ({r2_total:.3e}) > {limit_r2:.0e}")
        
        # Detailed breakdown by zone
        st.subheader("📋 Desglose por Zona - R2")
        
        for zone_name, zone_data in result_r2['zones'].items():
            with st.expander(f"🔍 {zone_name} - R2 = {zone_data['Total']:.3e}", expanded=False):
                # Component summary
                st.markdown("#### Componentes R2")
                
                cols = st.columns(3)
                cols[0].metric("Rb2", f"{zone_data['Rb2']:.3e}")
                cols[1].metric("Rc2", f"{zone_data['Rc2']:.3e}")
                cols[2].metric("Rm2", f"{zone_data['Rm2']:.3e}")
                
                cols = st.columns(3)
                cols[0].metric("Rv2", f"{zone_data['Rv2']:.3e}")
                cols[1].metric("Rw2", f"{zone_data['Rw2']:.3e}")
                cols[2].metric("Rz2", f"{zone_data['Rz2']:.3e}")
                
                # Intermediate values
                st.markdown("#### Valores Intermedios")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**Factores de Frecuencia (reutilizados de R1)**")
                    st.write(f"- Nd = {zone_data['Nd']:.3e}")
                    st.write(f"- Nm = {zone_data['Nm']:.3e}")
                    st.write(f"- Nl = {zone_data['Nl']:.3e}")
                    st.write(f"- Ndj = {zone_data['Ndj']:.3e}")
                    st.write(f"- Ni = {zone_data['Ni']:.3e}")
                
                with col2:
                    st.markdown("**Probabilidades y Pérdidas**")
                    st.write(f"- Pb = {zone_data['Pb']:.3e}")
                    st.write(f"- Lb2 = {zone_data['Lb2']:.3e}")
                    st.write(f"- Pc = {zone_data['Pc']:.3e}")
                    st.write(f"- Lc2 = {zone_data['Lc2']:.3e}")
                    st.write(f"- Pm = {zone_data['Pm']:.3e}")
                    st.write(f"- Pms = {zone_data['Pms']:.3e}")

        st.divider()
        
        # === R4 RESULTS ===
        st.header("📊 Resultados R4 (Pérdida Económica)")
        
        # Main metric
        r4_total = result_r4['total']
        limit_r4 = 1e-3  # R4 typical limit
        is_safe_r4 = r4_total <= limit_r4
        
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            st.metric(
                "R4 Total (Riesgo de Pérdida Económica)",
                f"{r4_total:.3e}",
                delta=f"Límite: {limit_r4:.0e}",
                delta_color="normal" if is_safe_r4 else "inverse"
            )
        with col2:
            st.metric("Ad (m²)", f"{result_r4['Ad']:.2f}")
        with col3:
            st.metric("Am (m²)", f"{result_r4['Am']:.2f}")
        
        if is_safe_r4:
            st.success(f"✅ CUMPLE: R4 ({r4_total:.3e}) ≤ {limit_r4:.0e}")
        else:
            st.error(f"❌ NO CUMPLE: R4 ({r4_total:.3e}) > {limit_r4:.0e}")
        
        # Detailed breakdown by zone
        st.subheader("📋 Desglose por Zona - R4")
        
        for zone_name, zone_data in result_r4['zones'].items():
            with st.expander(f"🔍 {zone_name} - R4 = {zone_data['Total']:.3e}", expanded=False):
                # Show animal loss status
                if zone_data['has_animals']:
                    st.info("🐄 Zona con pérdida de animales: Ra4* y Ru4* activos")
                else:
                    st.warning("⊘ Zona sin pérdida de animales: Ra4* = 0, Ru4* = 0")
                
                # Component summary
                st.markdown("#### Componentes R4")
                
                cols = st.columns(4)
                cols[0].metric("Ra4*", f"{zone_data['Ra4']:.3e}")
                cols[1].metric("Rb4", f"{zone_data['Rb4']:.3e}")
                cols[2].metric("Rc4", f"{zone_data['Rc4']:.3e}")
                cols[3].metric("Rm4", f"{zone_data['Rm4']:.3e}")
                
                cols = st.columns(4)
                cols[0].metric("Ru4*", f"{zone_data['Ru4']:.3e}")
                cols[1].metric("Rv4", f"{zone_data['Rv4']:.3e}")
                cols[2].metric("Rw4", f"{zone_data['Rw4']:.3e}")
                cols[3].metric("Rz4", f"{zone_data['Rz4']:.3e}")
                
                # Intermediate values
                st.markdown("#### Valores Intermedios")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**Factores de Frecuencia (reutilizados de R1)**")
                    st.write(f"- Nd = {zone_data['Nd']:.3e}")
                    st.write(f"- Nm = {zone_data['Nm']:.3e}")
                    st.write(f"- Nl = {zone_data['Nl']:.3e}")
                    st.write(f"- Ndj = {zone_data['Ndj']:.3e}")
                    st.write(f"- Ni = {zone_data['Ni']:.3e}")
                
                with col2:
                    st.markdown("**Probabilidades y Pérdidas**")
                    st.write(f"- Pa = {zone_data['Pa']:.3e}")
                    st.write(f"- La4 = {zone_data['La4']:.3e}")
                    st.write(f"- Pb = {zone_data['Pb']:.3e}")
                    st.write(f"- Lb4 = {zone_data['Lb4']:.3e}")
                    st.write(f"- Pc = {zone_data['Pc']:.3e}")
                    st.write(f"- Lc4 = {zone_data['Lc4']:.3e}")
                    st.write(f"- Pm = {zone_data['Pm']:.3e}")
                    st.write(f"- Pms = {zone_data['Pms']:.3e}")
                
                # Economic values
                st.markdown("#### Valores Económicos")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.write(f"- ca (animales) = {zone_data['ca']:.2f}")
                    st.write(f"- cb (edificio) = {zone_data['cb']:.2f}")
                with col2:
                    st.write(f"- cc (contenido) = {zone_data['cc']:.2f}")
                    st.write(f"- cs (sistemas) = {zone_data['cs']:.2f}")
                with col3:
                    st.write(f"- ct (total) = {zone_data['ct']:.2f}")
                    st.write(f"- Lf4 = {zone_data['lf4']:.3e}")
                    st.write(f"- Lo4 = {zone_data['lo4']:.3e}")


if __name__ == "__main__":
    main()
