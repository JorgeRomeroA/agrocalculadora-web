import streamlit as st
import tempfile
from fpdf import FPDF
import os
import plotly.graph_objects as go

# --- 1. DATOS AGRONÓMICOS ---
EXTRACCIONES = {
    "Alfalfa": {"N": 27.5, "P": 7.0, "K": 23.0}, "Algodón": {"N": 175.0, "P": 75.0, "K": 150.0},
    "Arroz": {"N": 18.0, "P": 8.0, "K": 18.5}, "Avena": {"N": 27.0, "P": 12.0, "K": 29.0},
    "Cebada": {"N": 26.0, "P": 11.0, "K": 27.0}, "Colza": {"N": 67.5, "P": 25.0, "K": 95.0},
    "Garbanzos": {"N": 45.0, "P": 8.0, "K": 35.0}, "Girasol": {"N": 45.0, "P": 19.0, "K": 95.0},
    "Guisantes": {"N": 43.0, "P": 20.0, "K": 30.0}, "Habas": {"N": 60.0, "P": 17.0, "K": 45.0},
    "Judías": {"N": 50.0, "P": 20.0, "K": 32.0}, "Maíz": {"N": 28.5, "P": 11.5, "K": 25.0},
    "Olivo": {"N": 11.0, "P": 5.0, "K": 16.0}, "Soja": {"N": 80.0, "P": 16.0, "K": 45.0},
    "Sorgo": {"N": 31.0, "P": 12.0, "K": 27.0}, "Tabaco": {"N": 55.0, "P": 9.0, "K": 80.0},
    "Trigo": {"N": 34.0, "P": 12.0, "K": 27.5}, "Triticale": {"N": 25.0, "P": 12.5, "K": 20.0},
    "Alcachofa": {"N": 7.75, "P": 3.25, "K": 15.5}, "Cebolla": {"N": 3.25, "P": 1.25, "K": 3.25},
    "Espinaca": {"N": 5.5, "P": 1.5, "K": 7.5}, "Frutal de hueso": {"N": 3.5, "P": 1.25, "K": 4.75},
    "Frutal de pepita": {"N": 3.0, "P": 1.0, "K": 4.0}, "Lechuga": {"N": 3.5, "P": 1.5, "K": 7.0},
    "Patata": {"N": 4.5, "P": 1.8, "K": 7.0}, "Remolacha": {"N": 4.25, "P": 1.55, "K": 6.0},
    "Remolacha (F)": {"N": 3.95, "P": 1.05, "K": 6.5}, "Tomate": {"N": 3.5, "P": 1.0, "K": 5.25},
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
    n_fondo, p_fondo, k_fondo = n_real * 0.30, p_total, k_total
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
        resultados["coste_fondo"], resultados["coste_cobertera_a"] = coste_fondo, urea_cobertera * p_urea
        resultados["coste_cobertera_b"] = nac_cobertera * p_nac
        resultados["coste_total_a"] = coste_fondo + resultados["coste_cobertera_a"]
        resultados["coste_total_b"] = coste_fondo + resultados["coste_cobertera_b"]
        resultados["euros_ahorrados"] = (min(n_agua, n_total_teorico) / 0.46) * p_urea if n_agua > 0 else 0

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
    
    fd, path = tempfile.mkstemp(suffix=".pdf")
    os.close(fd)
    pdf.output(path)
    return path

# --- 4. INTERFAZ WEB PREMIUM (STREAMLIT) ---
st.set_page_config(page_title="Agro SaaS", page_icon="🌾", layout="wide", initial_sidebar_state="expanded")

# --- CSS ULTRA AGRESIVO PARA LOOK SAAS ---
st.markdown("""
    <style>
    /* Importar fuente Inter de Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;800&display=swap');

    /* Forzar la tipografía en toda la app */
    html, body, [class*="css"], [class*="st-"], p, h1, h2, h3, h4, h5, h6, span, div {
        font-family: 'Inter', sans-serif !important;
    }

    /* Fondo de la aplicación principal (Patrón muy sutil) */
    .stApp {
        background-color: #f4f7f6;
        background-image: radial-gradient(#d1d5db 1px, transparent 1px);
        background-size: 20px 20px;
    }

    /* Ocultar elementos nativos de Streamlit */
    #MainMenu, header, footer {visibility: hidden;}
    .block-container {padding-top: 2rem;}

    /* Mejorar Sidebar */
    [data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #e5e7eb;
        box-shadow: 2px 0 10px rgba(0,0,0,0.03);
    }

    /* Botón Primario Premium */
    .stButton>button {
        background-color: #059669 !important; /* Emerald 600 */
        color: white !important;
        border-radius: 8px !important;
        border: none !important;
        padding: 0.8rem 1.2rem !important;
        font-weight: 700 !important;
        letter-spacing: 0.5px !important;
        width: 100% !important;
        box-shadow: 0 4px 6px -1px rgba(5, 150, 105, 0.2), 0 2px 4px -1px rgba(5, 150, 105, 0.1) !important;
        transition: all 0.2s ease-in-out !important;
    }
    .stButton>button:hover {
        background-color: #047857 !important; /* Emerald 700 */
        box-shadow: 0 10px 15px -3px rgba(5, 150, 105, 0.3), 0 4px 6px -2px rgba(5, 150, 105, 0.15) !important;
        transform: translateY(-2px) !important;
    }

    /* Tarjetas de Métricas Elegantes */
    div[data-testid="stMetric"] {
        background-color: #ffffff;
        border: 1px solid #e5e7eb;
        padding: 1.2rem;
        border-radius: 12px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
        transition: box-shadow 0.3s ease;
    }
    div[data-testid="stMetric"]:hover {
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
    }
    div[data-testid="stMetricValue"] {
        color: #064e3b;
        font-weight: 800;
        font-size: 2.2rem;
    }
    div[data-testid="stMetricLabel"] {
        font-size: 0.95rem;
        color: #6b7280;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    /* Contenedores */
    [data-testid="stVerticalBlock"] > [style*="flex-direction: column;"] > [data-testid="stVerticalBlock"] {
        background: white;
        padding: 2rem;
        border-radius: 12px;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06);
        border: 1px solid #e5e7eb;
    }
    </style>
""", unsafe_allow_html=True)

# --- SIDEBAR: CONTROLES ---
with st.sidebar:
    st.markdown("## 🌾 **AgroCalculadora**")
    st.caption("Panel de Control v2.0")
    st.divider()
    
    st.markdown("### 🌱 Cultivo y Terreno")
    cultivo_sel = st.selectbox("Selecciona el cultivo", sorted(list(EXTRACCIONES.keys())))
    rendimiento_sel = st.number_input("Rendimiento objetivo (t/ha)", min_value=0.1, value=5.0, step=0.5)
    sistema_sel = st.radio("Sistema Hídrico", ["Secano", "Regadío"], horizontal=True)
    
    n_agua = 0.0
    if sistema_sel == "Regadío":
        with st.expander("💧 Datos de Riego (Opcional)", expanded=True):
            ppm_agua = st.number_input("Nitratos en agua (ppm)", min_value=0.0, value=0.0, step=1.0)
            m3_agua = st.number_input("Dosis de Riego (m³/ha)", min_value=0.0, value=0.0, step=100.0)
            n_agua = (ppm_agua * m3_agua / 1000) * 0.2258

    st.divider()
    
    st.markdown("### 💰 Mercado Actual")
    calc_econ = st.toggle("Habilitar Módulo Financiero", value=True)
    p_urea, p_super, p_kcl = 0.45, 0.40, 0.50
    if calc_econ:
        p_urea = st.number_input("Urea (€/kg)", value=0.45, step=0.05)
        p_super = st.number_input("Superfosfato (€/kg)", value=0.40, step=0.05)
        p_kcl = st.number_input("Cloruro Potásico (€/kg)", value=0.50, step=0.05)
        
    st.divider()
    generar_btn = st.button("🚜 GENERAR REPORTE")

# --- ÁREA PRINCIPAL ---
if generar_btn:
    if rendimiento_sel <= 0:
        st.error("El rendimiento debe ser mayor a 0.")
    else:
        with st.spinner("Procesando matriz nutricional..."):
            inputs = {
                "cultivo": cultivo_sel, "rendimiento": rendimiento_sel, "sistema": sistema_sel.lower(),
                "n_agua": n_agua, "p_urea": p_urea, "p_super": p_super, "p_kcl": p_kcl, "calc_econ": calc_econ
            }
            
            res = calcular_necesidades(**inputs)
            pdf_path = generar_pdf(res, inputs)
            
            # Encabezado Principal
            st.markdown(f"## 📊 Informe Agronómico: **{cultivo_sel}**")
            st.caption(f"Objetivo de producción: {rendimiento_sel} t/ha | Sistema: {sistema_sel}")
            st.markdown("<br>", unsafe_allow_html=True)
            
            # --- FILA SUPERIOR: GRAFICO + METRICAS ---
            col_chart, col_metrics = st.columns([1, 2])
            
            with col_chart:
                # GRÁFICO INTERACTIVO PLOTLY
                fig = go.Figure(data=[go.Pie(
                    labels=['Nitrógeno (N)', 'Fósforo (P)', 'Potasio (K)'],
                    values=[res['n_real'], res['p_total'], res['k_total']],
                    hole=.5,
                    hoverinfo="label+percent+value",
                    textinfo="none",
                    marker=dict(colors=['#059669', '#d97706', '#dc2626'])
                )])
                fig.update_layout(
                    title_text="Balance N-P-K",
                    title_x=0.5,
                    margin=dict(t=40, b=0, l=0, r=0),
                    showlegend=True,
                    legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
                    height=280,
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)'
                )
                st.plotly_chart(fig, use_container_width=True)

            with col_metrics:
                st.markdown("### Requerimiento Puro (kg/ha)")
                c1, c2, c3 = st.columns(3)
                c1.metric("Nitrógeno (N)", f"{res['n_real']:.1f}")
                c2.metric("Fósforo (P2O5)", f"{res['p_total']:.1f}")
                c3.metric("Potasio (K2O)", f"{res['k_total']:.1f}")
                
                if n_agua > 0:
                    st.success(f"🌱 Aporte natural del agua descontado: **-{n_agua:.1f} kg N/ha**")

            st.markdown("<br><hr><br>", unsafe_allow_html=True)

            # --- FILA INFERIOR: FERTILIZANTES COMERCIALES ---
            st.markdown("### 🚜 Prescripción Comercial (Sacos a aplicar)")
            
            st.markdown("#### 1. Abonado de Fondo (Pre-siembra)")
            cf1, cf2, cf3 = st.columns(3)
            cf1.metric("Urea (46%)", f"{res['urea_fondo']:.0f} kg/ha")
            cf2.metric("Superfosfato (46%)", f"{res['superfosfato_fondo']:.0f} kg/ha")
            cf3.metric("Cloruro Potásico (60%)", f"{res['cloruro_fondo']:.0f} kg/ha")

            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("#### 2. Abonado de Cobertera (Elige una opción)")
            cc1, cc2 = st.columns(2)
            cc1.metric("Opción A: Urea (46%)", f"{res['urea_cobertera']:.0f} kg/ha")
            cc2.metric("Opción B: NAC (27%)", f"{res['nac_cobertera']:.0f} kg/ha")

            # --- MÓDULO FINANCIERO ---
            if calc_econ:
                st.markdown("<br><hr><br>", unsafe_allow_html=True)
                st.markdown("### 💰 Impacto Financiero")
                ce1, ce2, ce3 = st.columns(3)
                ce1.metric("Coste Fondo", f"{res['coste_fondo']:.2f} €/ha")
                ce2.metric("Total (Vía Urea)", f"{res['coste_total_a']:.2f} €/ha", help="Fondo + Cobertera A")
                ce3.metric("Total (Vía NAC)", f"{res['coste_total_b']:.2f} €/ha", help="Fondo + Cobertera B")

            st.markdown("<br>", unsafe_allow_html=True)
            with open(pdf_path, "rb") as pdf_file:
                st.download_button(
                    label="📄 Exportar Plan a PDF",
                    data=pdf_file,
                    file_name=f"Plan_{cultivo_sel}.pdf",
                    mime="application/pdf"
                )

else:
    # Pantalla de bienvenida
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    st.markdown("<h1 style='text-align: center; color: #064e3b;'>🚜 Bienvenido a tu Suite Agronómica</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #6b7280; font-size: 1.2rem;'>Configura los parámetros en el menú lateral izquierdo para generar un plan de abonado profesional y optimizado.</p>", unsafe_allow_html=True)