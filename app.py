import streamlit as st
from src.tables import *
from src.iec_62305 import GeometricParameters, ZoneParameters, LineParameters, EngineIEC62305

st.set_page_config(page_title="IEC 62305-2: Cálculo R1", layout="wide")

def main():
    st.title("⚡ IEC 62305-2: Cálculo de Riesgo R1 (Vida)")
    st.caption("R1 = Ra1 + Rb1 + Rc1* + Rm1* + Ru1 + Rv1 + Rw1* + Rz1*")
    
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
            
            # Create single R1 tab
            tab1 = st.tabs(["📊 Componentes R1"])[0]
            
            with tab1:
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
                                      index=2, key=f"lf1_{i}")  # "Industrial / Comercios"
                
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
                    lo1_val = st.number_input("Lo1 - Pérdida fallo sistemas",
                                             value=0.0, format="%.1e", key=f"lo1_{i}")
                    
                    col1, col2, col3 = st.columns(3)
                    nz_rc = col1.number_input("nz (Rc)", value=1.0, min_value=0.0, key=f"nz_rc_{i}")
                    nt_rc = col2.number_input("nt (Rc)", value=1.0, min_value=0.1, key=f"nt_rc_{i}")
                    tz_rc = col3.number_input("tz (Rc)", value=8760.0, min_value=0.0, key=f"tz_rc_{i}")
                else:
                    st.info("⊘ No activo (requiere riesgo de explosión o hospital)")
                    pspd_k = list(PSPD_VALUES.keys())[2]
                    cld_k = list(CLD_VALUES.keys())[2]
                    lo1_val = 0.0
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
                                          index=0, key=f"ks3_{i}")
                    uw = col4.number_input("Uw (kV)", value=1.0, min_value=0.1, key=f"uw_{i}")
                else:
                    st.info("⊘ No activo (requiere riesgo de explosión o hospital)")
                    wm1, wm2, uw = 2.0, 2.0, 1.0
                    ks3_k = list(KS3_VALUES.keys())[0]
                
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
                    col1, col2, col3 = st.columns(3)
                    pspd_z_k = col1.selectbox("Pspd (Rz) - SPD",
                                             list(PSPD_VALUES.keys()),
                                             index=2, key=f"pspd_z_{i}")
                    pli_k = col2.selectbox("Pli - Inducción (Tabla B.9)",
                                          list(PLI_VALUES.keys()),
                                          index=0, key=f"pli_{i}")
                    cli_k = col3.selectbox("Cli - Apantallamiento (Tabla B.4)",
                                          list(CLD_VALUES.keys()),
                                          index=2, key=f"cli_{i}")
                else:
                    st.info("⊘ No activo (requiere riesgo de explosión o hospital)")
                    pspd_z_k = list(PSPD_VALUES.keys())[2]
                    pli_k = list(PLI_VALUES.keys())[0]
                    cli_k = list(CLD_VALUES.keys())[2]
            
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
                lo1=lo1_val,
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
                pli=PLI_VALUES[pli_k],
                cli=CLD_VALUES[cli_k],
            )
            zones_list.append(zone)
    
    # === CALCULATION ===
    st.divider()
    if st.button("🔥 CALCULAR RIESGO R1", type="primary", use_container_width=True):
        engine = EngineIEC62305(geom, zones_list, [line])
        result = engine.compute_risk_R1()
        
        # Display results
        st.header("📊 Resultados")
        
        # Main metric
        r1_total = result['total']
        limit = 1e-5
        is_safe = r1_total <= limit
        
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            st.metric(
                "R1 Total (Riesgo de Pérdida de Vida)",
                f"{r1_total:.3e}",
                delta=f"Límite: {limit:.0e}",
                delta_color="normal" if is_safe else "inverse"
            )
        with col2:
            st.metric("Ad (m²)", f"{result['Ad']:.2f}")
        with col3:
            st.metric("Am (m²)", f"{result['Am']:.2f}")
        
        if is_safe:
            st.success(f"✅ CUMPLE: R1 ({r1_total:.3e}) ≤ {limit:.0e}")
        else:
            st.error(f"❌ NO CUMPLE: R1 ({r1_total:.3e}) > {limit:.0e}")
        
        # Detailed breakdown by zone
        st.subheader("📋 Desglose por Zona")
        
        for zone_name, zone_data in result['zones'].items():
            with st.expander(f"🔍 {zone_name} - R1 = {zone_data['Total']:.3e}", expanded=True):
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

if __name__ == "__main__":
    main()
