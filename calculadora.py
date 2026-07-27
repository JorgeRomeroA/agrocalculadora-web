import streamlit as st
import tempfile
from fpdf import FPDF
import os

# --- 1. DATOS AGRONÓMICOS ---
EXTRACCIONES = {
    "Alfalfa": {"N": 27.5, "P": 7.0, "K": 23.0},
    "Algodón": {"N": 175.0, "P": 75.0, "K": 150.0},
    "Arroz": {"N": 18.0, "P": 8.0, "K": 18.5},
    "Avena": {"N": 27.0, "P": 12.0, "K": 29.0},
    "Cebada": {"N": 26.0, "P": 11.0, "K": 27.0},
    "Colza": {"N": 67.5, "P": 25.0, "K": 95.0},
    "Garbanzos": {"N": 45.0, "P": 8.0, "K": 35.0},
    "Girasol": {"N": 45.0, "P": 19.0, "K": 95.0},
    "Guisantes": {"N": 43.0, "P": 20.0, "K": 30.0},
    "Habas": {"N": 60.0, "P": 17.0, "K": 45.0},
    "Judías": {"N": 50.0, "P": 20.0, "K": 32.0},
    "Maíz": {"N": 28.5, "P": 11.5, "K": 25.0},
    "Olivo": {"N": 11.0, "P": 5.0, "K": 16.0},
    "Soja": {"N": 80.0, "P": 16.0, "K": 45.0},
    "Sorgo": {"N": 31.0, "P": 12.0, "K": 27.0},
    "Tabaco": {"N": 55.0, "P": 9.0, "K": 80.0},
    "Trigo": {"N": 34.0, "P": 12.0, "K": 27.5},
    "Triticale": {"N": 25.0, "P": 12.5, "K": 20.0},
    "Alcachofa": {"N": 7.75, "P": 3.25, "K": 15.5},
    "Cebolla": {"N": 3.25, "P": 1.25, "K": 3.25},
    "Espinaca": {"N": 5.5, "P": 1.5, "K": 7.5},
    "Frutal de hueso": {"N": 3.5, "P": 1.25, "K": 4.75},
    "Frutal de pepita": {"N": 3.0, "P": 1.0, "K": 4.0},
    "Lechuga": {"N": 3.5, "P": 1.5, "K": 7.0},
    "Patata": {"N": 4.5, "P": 1.8, "K": 7.0},
    "Remolacha": {"N": 4.25, "P": 1.55, "K": 6.0},
    "Remolacha (F)": {"N": 3.95, "P": 1.05, "K": 6.5},
    "Tomate": {"N": 3.5, "P": 1.0, "K": 5.25},
    "Zanahoria": {"N": 4.0, "P": 1.1, "K": 6.0},
}

# --- 2. LÓGICA DE CÁLCULO ---
def calcular_necesidades(cultivo, rendimiento, sistema, n_agua, p_urea, p_super, p_kcl, calc_econ):
    porcentaje_perdidas = 0.05 if sistema == "secano" else 0.10
    datos = EXTRACCIONES[cultivo]
    
    n_total_teorico = (datos["N"] * rendimiento) * (1 + porcentaje_perdidas)
    p_total = (datos["P"] * rendimiento) * 1.10
    k_total = (datos["K"] * rendimiento) * (1 + porcentaje_perdidas)
    
    n_real = max(0, n_total_teorico - n_agua)

    n_fondo = n_real * 0.30
    p_fondo = p_total
    k_fondo = k_total
    n_cobertera = n_real * 0.70

    urea_fondo = n_fondo / 0.46 if n_fondo > 0 else 0
    superfosfato_fondo = p_fondo / 0.46 if p_fondo > 0 else 0
    cloruro_fondo = k_fondo / 0.60 if k_fondo > 0 else 0

    urea_cobertera = n_cobertera / 0.46 if n_cobertera > 0 else 0
    p_nac = p_urea * 0.77 
    nac_cobertera = n_cobertera / 0.27 if n_cobertera > 0 else 0

    resultados = {
        "n_total_teorico": n_total_teorico, "p_total": p_total, "k_total": k_total,
        "n_real": n_real, "n_fondo": n_fondo, "p_fondo": p_fondo, "k_fondo": k_fondo,
        "n_cobertera": n_cobertera, "urea_fondo": urea_fondo, "superfosfato_fondo": superfosfato_fondo,
        "cloruro_fondo": cloruro_fondo, "urea_cobertera": urea_cobertera, "nac_cobertera": nac_cobertera,
        "porcentaje_perdidas": porcentaje_perdidas, "p_nac": p_nac
    }

    if calc_econ:
        coste_fondo = (urea_fondo * p_urea) + (superfosfato_fondo * p_super) + (cloruro_fondo * p_kcl)
        resultados["coste_fondo"] = coste_fondo
        resultados["coste_cobertera_a"] = urea_cobertera * p_urea
        resultados["coste_cobertera_b"] = nac_cobertera * p_nac
        resultados["coste_total_a"] = coste_fondo + resultados["coste_cobertera_a"]
        resultados["coste_total_b"] = coste_fondo + resultados["coste_cobertera_b"]
        
        if n_agua > 0:
            urea_ahorrada = min(n_agua, n_total_teorico) / 0.46
            resultados["euros_ahorrados"] = urea_ahorrada * p_urea
        else:
            resultados["euros_ahorrados"] = 0

    return resultados

# --- 3. GENERADOR DE PDF ---
def generar_pdf(datos, inputs):
    pdf = FPDF()
    pdf.add_page()
    
    pdf.set_fill_color(34, 139, 34)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 15, " AGROCALCULADORA - INFORME TECNICO DE ABONADO", border=0, ln=1, align="C", fill=True)
    pdf.ln(5)

    pdf.set_text_color(50, 50, 50)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, f"Cultivo: {inputs['cultivo'].upper()}  |  Rendimiento: {inputs['rendimiento']} t/ha  |  Sistema: {inputs['sistema'].capitalize()}", ln=1)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, f"Incremento aplicado por perdidas (lixiviacion): {int(datos['porcentaje_perdidas'] * 100)}%", ln=1)
    
    pdf.set_draw_color(34, 139, 34)
    pdf.line(10, pdf.get_y()+2, 200, pdf.get_y()+2)
    pdf.ln(7)

    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(34, 139, 34)
    pdf.cell(0, 8, "1. NECESIDADES TOTALES DEL CULTIVO (Nutrientes puros)", ln=1)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 6, f"   - Nitrogeno (N) teorico: {datos['n_total_teorico']:.1f} kg/ha", ln=1)
    
    if inputs['n_agua'] > 0:
        pdf.set_text_color(34, 139, 34)
        pdf.cell(0, 6, f"   - Aporte gratis del agua de riego: -{inputs['n_agua']:.1f} kg N/ha", ln=1)
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 6, f"   - NITROGENO FINAL A APLICAR: {datos['n_real']:.1f} kg/ha", ln=1)
        if datos['n_real'] == 0:
            pdf.set_text_color(200, 50, 50)
            pdf.cell(0, 6, "     * AVISO: Tu pozo aporta todo el N necesario. Dosis extra = 0", ln=1)
        pdf.set_font("Helvetica", "", 11)
        pdf.set_text_color(0, 0, 0)

    pdf.cell(0, 6, f"   - Fosforo (P2O5): {datos['p_total']:.1f} kg/ha", ln=1)
    pdf.cell(0, 6, f"   - Potasio (K2O): {datos['k_total']:.1f} kg/ha", ln=1)
    pdf.ln(5)

    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(34, 139, 34)
    pdf.cell(0, 8, "2. ESTRATEGIA DE APLICACION (Fondo y Cobertera)", ln=1)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 6, "Abonado de Fondo (Antes de la siembra):", ln=1)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, f"   - Nitrogeno (N): {datos['n_fondo']:.1f} kg/ha (30%)", ln=1)
    pdf.cell(0, 6, f"   - Fosforo (P2O5): {datos['p_fondo']:.1f} kg/ha (100%)", ln=1)
    pdf.cell(0, 6, f"   - Potasio (K2O): {datos['k_fondo']:.1f} kg/ha (100%)", ln=1)
    pdf.ln(2)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 6, "Abonado de Cobertera (Cultivo en crecimiento):", ln=1)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, f"   - Nitrogeno (N): {datos['n_cobertera']:.1f} kg/ha (70%)", ln=1)
    pdf.ln(5)

    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(34, 139, 34)
    pdf.cell(0, 8, "3. RECOMENDACION COMERCIAL (Sacos a aplicar por hectarea)", ln=1)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 6, "Para el Fondo:", ln=1)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, f"   - {datos['urea_fondo']:.0f} kg/ha de Urea (46%)", ln=1)
    pdf.cell(0, 6, f"   - {datos['superfosfato_fondo']:.0f} kg/ha de Superfosfato Triple (46%)", ln=1)
    pdf.cell(0, 6, f"   - {datos['cloruro_fondo']:.0f} kg/ha de Cloruro Potasico (60%)", ln=1)
    pdf.ln(2)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 6, "Para la Cobertera (Elige UNA opcion):", ln=1)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, f"   - Opcion A: {datos['urea_cobertera']:.0f} kg/ha de Urea (46%)", ln=1)
    pdf.cell(0, 6, f"   - Opcion B: {datos['nac_cobertera']:.0f} kg/ha de Nitrato Amonico Calcico (27%)", ln=1)
    pdf.ln(5)

    if inputs['calc_econ']:
        pdf.set_fill_color(240, 240, 240)
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_text_color(34, 139, 34)
        pdf.cell(0, 8, "4. SIMULADOR ECONOMICO", border=1, ln=1, fill=True)
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(0, 6, f"Precios ref: Urea {inputs['p_urea']:.2f} EUR/kg | SuperP {inputs['p_super']:.2f} EUR/kg | Cloruro {inputs['p_kcl']:.2f} EUR/kg", ln=1)
        pdf.ln(2)
        pdf.cell(0, 6, f"   - Coste Abonado de Fondo: {datos['coste_fondo']:.2f} EUR", ln=1)
        pdf.cell(0, 6, f"   - Coste Cobertera (Opcion A): {datos['coste_cobertera_a']:.2f} EUR", ln=1)
        pdf.cell(0, 6, f"   - Coste Cobertera (Opcion B): {datos['coste_cobertera_b']:.2f} EUR", ln=1)
        pdf.ln(2)
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 6, f"   -> COSTE TOTAL (Fondo + Opcion A): {datos['coste_total_a']:.2f} EUR/ha", ln=1)
        pdf.cell(0, 6, f"   -> COSTE TOTAL (Fondo + Opcion B): {datos['coste_total_b']:.2f} EUR/ha", ln=1)
        
        if inputs['n_agua'] > 0:
            pdf.ln(2)
            pdf.set_text_color(34, 139, 34)
            pdf.cell(0, 6, f"   -> AHORRO ESTIMADO POR AGUA DE RIEGO: {datos['euros_ahorrados']:.2f} EUR/ha", ln=1)

    pdf.set_y(-25)
    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(150, 150, 150)
    pdf.cell(0, 10, "Informe generado automaticamente por AgroCalculadora.", align="C")

    fd, path = tempfile.mkstemp(suffix=".pdf")
    os.close(fd)
    pdf.output(path)
    return path

# --- 4. INTERFAZ WEB (STREAMLIT) ---
st.set_page_config(page_title="AgroCalculadora", page_icon="🌾", layout="centered")

st.markdown("""
    <style>
    .stApp {
        background-color: #f4f6f8;
    }
    .stButton>button {
        background-color: #2e7b32;
        color: white;
        border-radius: 8px;
        border: none;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        padding: 0.6rem 1.2rem;
        transition: all 0.3s ease;
        font-weight: bold;
        width: 100%;
    }
    .stButton>button:hover {
        background-color: #1b5e20;
        box-shadow: 0 6px 8px rgba(0,0,0,0.2);
    }
    div[data-testid="stMetricValue"] {
        color: #2e7b32;
        font-weight: bold;
        font-size: 2rem;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🌾 AgroCalculadora Web")
st.markdown("Tu asistente agronómico para el cálculo preciso de planes de abonado.")
st.markdown("---")

tab1, tab2 = st.tabs(["🧮 Calculadora", "📚 Guía Nutricional"])

with tab1:
    
    # CONTENEDOR 1: Configuración Principal
    with st.container(border=True):
        st.subheader("🌱 Configuración del Cultivo")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            cultivo_sel = st.selectbox("Selecciona el cultivo:", sorted(list(EXTRACCIONES.keys())))
        with col2:
            rendimiento_sel = st.number_input("Rendimiento esperado (t/ha):", min_value=0.1, value=5.0, step=0.5)
        with col3:
            # Cambiado de radio a selectbox para que quede alineado con los otros dos inputs
            sistema_sel = st.selectbox("Sistema de cultivo:", ["Secano", "Regadío"])

    # CONTENEDOR 2: Agua de riego (Sólo aparece si es regadío)
    n_agua = 0.0
    if sistema_sel == "Regadío":
        with st.container(border=True):
            st.subheader("💧 Aporte por Agua de Riego")
            st.caption("Si riegas con pozo, introduce los datos para descontar nitratos:")
            col_a, col_b = st.columns(2)
            with col_a:
                ppm_agua = st.number_input("Nitratos (ppm):", min_value=0.0, value=0.0, step=1.0)
            with col_b:
                m3_agua = st.number_input("Volumen a regar (m³/ha):", min_value=0.0, value=0.0, step=100.0)
            n_agua = (ppm_agua * m3_agua / 1000) * 0.2258

    # CONTENEDOR 3: Simulador Económico
    with st.container(border=True):
        st.subheader("💰 Simulador Económico")
        # Usamos toggle (interruptor moderno) en lugar de checkbox
        calc_econ = st.toggle("Activar simulación de costes", value=True)
        
        p_urea, p_super, p_kcl = 0.45, 0.40, 0.50
        if calc_econ:
            col_c, col_d, col_e = st.columns(3)
            with col_c:
                p_urea = st.number_input("Precio Urea (€/kg)", value=0.45, step=0.05)
            with col_d:
                p_super = st.number_input("Precio Superfosfato (€/kg)", value=0.40, step=0.05)
            with col_e:
                p_kcl = st.number_input("Precio Cloruro Potásico (€/kg)", value=0.50, step=0.05)

    st.markdown("<br>", unsafe_allow_html=True) # Espacio extra para respirar

    # BOTÓN PRINCIPAL
    if st.button("🚜 GENERAR PLAN DE ABONADO", type="primary"):
        if rendimiento_sel <= 0:
            st.error("El rendimiento debe ser mayor a 0.")
        elif rendimiento_sel > 200:
            st.warning("⚠️ Cuidado: El rendimiento parece demasiado alto. Recuerda introducirlo en TONELADAS por hectárea (t/ha), no en kilos.")
        else:
            with st.spinner("Calculando extracciones y generando informe..."):
                inputs = {
                    "cultivo": cultivo_sel, "rendimiento": rendimiento_sel, "sistema": sistema_sel.lower(),
                    "n_agua": n_agua, "p_urea": p_urea, "p_super": p_super, "p_kcl": p_kcl, "calc_econ": calc_econ
                }
                
                resultados = calcular_necesidades(**inputs)
                pdf_path = generar_pdf(resultados, inputs)
                
                st.success("✅ Plan de abonado generado correctamente.")
                
                # --- PANEL DE RESULTADOS VISUALMENTE AGRUPADO ---
                with st.container(border=True):
                    st.subheader("📊 1. Necesidades Totales (Nutrientes Puros)")
                    col_n, col_p, col_k = st.columns(3)
                    col_n.metric("Nitrógeno (N)", f"{resultados['n_real']:.1f} kg/ha")
                    col_p.metric("Fósforo (P2O5)", f"{resultados['p_total']:.1f} kg/ha")
                    col_k.metric("Potasio (K2O)", f"{resultados['k_total']:.1f} kg/ha")

                with st.container(border=True):
                    st.subheader("🚜 2. Recomendación de Fertilizantes Comerciales")
                    st.markdown("**Abonado de Fondo (Antes de la siembra):**")
                    col_f1, col_f2, col_f3 = st.columns(3)
                    col_f1.metric("Urea (46%)", f"{resultados['urea_fondo']:.0f} kg/ha")
                    col_f2.metric("Superfosfato (46%)", f"{resultados['superfosfato_fondo']:.0f} kg/ha")
                    col_f3.metric("Cloruro Potásico (60%)", f"{resultados['cloruro_fondo']:.0f} kg/ha")

                    st.markdown("**Abonado de Cobertera (Elegir UNA opción):**")
                    col_c1, col_c2 = st.columns(2)
                    col_c1.metric("Opción A: Urea (46%)", f"{resultados['urea_cobertera']:.0f} kg/ha")
                    col_c2.metric("Opción B: NAC (27%)", f"{resultados['nac_cobertera']:.0f} kg/ha")

                if calc_econ:
                    with st.container(border=True):
                        st.subheader("💰 3. Resumen Económico")
                        col_e1, col_e2 = st.columns(2)
                        col_e1.metric("Coste Total (Fondo + Opción A)", f"{resultados['coste_total_a']:.2f} €/ha")
                        col_e2.metric("Coste Total (Fondo + Opción B)", f"{resultados['coste_total_b']:.2f} €/ha")
                        
                        if n_agua > 0:
                            st.info(f"💧 Ahorro estimado por nitratos del pozo: **{resultados['euros_ahorrados']:.2f} €/ha**")

                st.markdown("---")
                
                with open(pdf_path, "rb") as pdf_file:
                    st.download_button(
                        label="📄 Descargar Informe Técnico Completo (PDF)",
                        data=pdf_file,
                        file_name=f"Plan_Abonado_{cultivo_sel}.pdf",
                        mime="application/pdf"
                    )

with tab2:
    with st.container(border=True):
        st.subheader("📚 Extracciones Teóricas")
        st.markdown("Revisa las necesidades en kg por cada tonelada producida:")
        cultivo_guia = st.selectbox("Consultar cultivo:", sorted(list(EXTRACCIONES.keys())), key="guia")
        datos_guia = EXTRACCIONES[cultivo_guia]
        
        col_gn, col_gp, col_gk = st.columns(3)
        col_gn.metric("Nitrógeno (N)", f"{datos_guia['N']} kg")
        col_gp.metric("Fósforo (P2O5)", f"{datos_guia['P']} kg")
        col_gk.metric("Potasio (K2O)", f"{datos_guia['K']} kg")