import os
import tempfile
from fpdf import FPDF
import plotly.graph_objects as go
import streamlit as st

# --- 1. DATOS AGRONÓMICOS COMPLETOS ---
EXTRACCIONES = {
    "Alcachofa": {"N": 7.75, "P": 3.25, "K": 15.5},
    "Alfalfa": {"N": 27.5, "P": 7.0, "K": 23.0},
    "Algodón": {"N": 175.0, "P": 75.0, "K": 150.0},
    "Arroz": {"N": 18.0, "P": 8.0, "K": 18.5},
    "Avena": {"N": 27.0, "P": 12.0, "K": 29.0},
    "Cebada": {"N": 26.0, "P": 11.0, "K": 27.0},
    "Cebolla": {"N": 3.25, "P": 1.25, "K": 3.25},
    "Colza": {"N": 67.5, "P": 25.0, "K": 95.0},
    "Espinaca": {"N": 5.5, "P": 1.5, "K": 7.5},
    "Frutal de hueso": {"N": 3.5, "P": 1.25, "K": 4.75},
    "Frutal de pepita": {"N": 3.0, "P": 1.0, "K": 4.0},
    "Garbanzos": {"N": 45.0, "P": 8.0, "K": 35.0},
    "Girasol": {"N": 45.0, "P": 19.0, "K": 95.0},
    "Guisantes": {"N": 43.0, "P": 20.0, "K": 30.0},
    "Habas": {"N": 60.0, "P": 17.0, "K": 45.0},
    "Judías": {"N": 50.0, "P": 20.0, "K": 32.0},
    "Lechuga": {"N": 3.5, "P": 1.5, "K": 7.0},
    "Maíz": {"N": 28.5, "P": 11.5, "K": 25.0},
    "Olivo": {"N": 11.0, "P": 5.0, "K": 16.0},
    "Patata": {"N": 4.5, "P": 1.8, "K": 7.0},
    "Remolacha": {"N": 4.25, "P": 1.55, "K": 6.0},
    "Remolacha (F)": {"N": 3.95, "P": 1.05, "K": 6.5},
    "Soja": {"N": 80.0, "P": 16.0, "K": 45.0},
    "Sorgo": {"N": 31.0, "P": 12.0, "K": 27.0},
    "Tabaco": {"N": 55.0, "P": 9.0, "K": 80.0},
    "Tomate": {"N": 3.5, "P": 1.0, "K": 5.25},
    "Trigo": {"N": 34.0, "P": 12.0, "K": 27.5},
    "Triticale": {"N": 25.0, "P": 12.5, "K": 20.0},
    "Zanahoria": {"N": 4.0, "P": 1.1, "K": 6.0},
}


# --- 2. LÓGICA DE CÁLCULO ---
def calcular_necesidades(
    cultivo, rendimiento, sistema, n_agua, p_urea, p_super, p_kcl, calc_econ
):
    porcentaje_perdidas = 0.05 if sistema == "secano" else 0.10
    datos = EXTRACCIONES[cultivo]

    n_total_teorico = (datos["N"] * rendimiento) * (1 + porcentaje_perdidas)
    p_total = (datos["P"] * rendimiento) * 1.10
    k_total = (datos["K"] * rendimiento) * (1 + porcentaje_perdidas)

    n_real = max(0.0, n_total_teorico - n_agua)
    n_fondo, p_fondo, k_fondo = n_real * 0.30, p_total, k_total
    n_cobertera = n_real * 0.70

    urea_fondo = n_fondo / 0.46 if n_fondo > 0 else 0
    superfosfato_fondo = p_fondo / 0.46 if p_fondo > 0 else 0
    cloruro_fondo = k_fondo / 0.60 if k_fondo > 0 else 0
    urea_cobertera = n_cobertera / 0.46 if n_cobertera > 0 else 0
    p_nac = p_urea * 0.77
    nac_cobertera = n_cobertera / 0.27 if n_cobertera > 0 else 0

    resultados = {
        "n_total_teorico": n_total_teorico,
        "p_total": p_total,
        "k_total": k_total,
        "n_real": n_real,
        "n_fondo": n_fondo,
        "p_fondo": p_fondo,
        "k_fondo": k_fondo,
        "n_cobertera": n_cobertera,
        "urea_fondo": urea_fondo,
        "superfosfato_fondo": superfosfato_fondo,
        "cloruro_fondo": cloruro_fondo,
        "urea_cobertera": urea_cobertera,
        "nac_cobertera": nac_cobertera,
        "porcentaje_perdidas": porcentaje_perdidas,
        "p_nac": p_nac,
    }

    if calc_econ:
        coste_fondo = (
            (urea_fondo * p_urea)
            + (superfosfato_fondo * p_super)
            + (cloruro_fondo * p_kcl)
        )
        resultados["coste_fondo"] = coste_fondo
        resultados["coste_cobertera_a"] = urea_cobertera * p_urea
        resultados["coste_cobertera_b"] = nac_cobertera * p_nac
        resultados["coste_total_a"] = coste_fondo + resultados["coste_cobertera_a"]
        resultados["coste_total_b"] = coste_fondo + resultados["coste_cobertera_b"]
        resultados["euros_ahorrados"] = (
            (min(n_agua, n_total_teorico) / 0.46) * p_urea if n_agua > 0 else 0
        )

    return resultados


def generar_pdf(datos, inputs):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_fill_color(34, 139, 34)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(
        0, 15, " AGROCALCULADORA - INFORME", border=0, ln=1, align="C", fill=True
    )
    fd, path = tempfile.mkstemp(suffix=".pdf")
    os.close(fd)
    pdf.output(path)
    return path


# --- 3. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Agro SaaS",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- 4. BARRA SUPERIOR (NAVBAR) ---
st.markdown(
    """
    <div class="navbar">
        <div class="logo">🌾 AgroSaaS Pro</div>
        <div class="nav-links">
            <a href="#" style="color: #059669; font-weight: 600;">Dashboard</a>
            <a href="#">Mis Parcelas</a>
            <a href="#">Historial</a>
        </div>
        <div class="user-profile">
            <img src="https://cdn-icons-png.flaticon.com/512/3135/3135715.png" alt="User">
            <span>Mi Cuenta</span>
        </div>
    </div>
""",
    unsafe_allow_html=True,
)

# --- 5. ESTILOS CSS PERSONALIZADOS ---
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    html, body, [class*="css"], [class*="st-"], p, h1, h2, h3, h4, h5, span, div, label {
        font-family: 'Inter', sans-serif !important;
    }

    /* ---------------------------------------------------
       1. LIMPIEZA DE STREAMLIT (ELIMINAR BARRA MOLESTA)
       --------------------------------------------------- */
    #MainMenu, footer {
        visibility: hidden; 
        display: none;
    }
    
    header[data-testid="stHeader"] {
        background: transparent !important;
        box-shadow: none !important;
    }

    /* Ocultar los iconos de Github, Share, Deploy... TODO menos el botón lateral */
    [data-testid="stToolbar"], .stAppDeployButton {
        display: none !important;
    }

    /* ---------------------------------------------------
       2. REUBICAR Y ARREGLAR EL BOTÓN LATERAL
       --------------------------------------------------- */
    [data-testid="stSidebarCollapsedControl"] {
        z-index: 1000000 !important; /* Para que quede por encima de nuestra navbar */
        display: flex !important;
        top: 15px !important; 
        left: 15px !important;
        background-color: #ffffff !important;
        border: 1px solid #e5e7eb !important;
        border-radius: 6px !important;
        padding: 4px !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05) !important;
    }

    /* Margen superior de la app principal para que no se coma la navbar */
    .block-container {
        padding-top: 5.5rem !important; 
    }

    /* ---------------------------------------------------
       3. NUESTRA NAVBAR PERSONALIZADA
       --------------------------------------------------- */
    .navbar {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        height: 65px;
        background-color: #ffffff;
        border-bottom: 1px solid #e5e7eb;
        z-index: 99999;
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 0 2rem 0 70px; /* 70px de hueco a la izq. para que viva tranquilo el botón nativo */
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    
    .navbar .logo {
        font-size: 1.3rem;
        font-weight: 800;
        color: #111827;
        letter-spacing: -0.5px;
    }
    .navbar .nav-links a {
        text-decoration: none;
        color: #6b7280;
        margin: 0 1rem;
        font-weight: 500;
        font-size: 0.95rem;
        transition: color 0.2s;
    }
    .navbar .nav-links a:hover {
        color: #059669;
    }
    .navbar .user-profile {
        display: flex;
        align-items: center;
        gap: 10px;
        font-weight: 600;
        color: #374151;
        cursor: pointer;
    }
    .navbar .user-profile img {
        width: 32px;
        height: 32px;
        border-radius: 50%;
    }

    /* Fondo general del dashboard */
    .stApp {
        background-color: #f8fafc;
        background-image: radial-gradient(#d1d5db 1px, transparent 1px);
        background-size: 20px 20px;
    }

    /* ---------------------------------------------------
       4. ESTILOS DE LA BARRA LATERAL Y SU FONDO
       --------------------------------------------------- */
    section[data-testid="stSidebar"] {
        background-color: #ffffff !important;
        border-right: 1px solid #e5e7eb !important;
        margin-top: 65px !important; /* Empezar justo debajo de la navbar */
        height: calc(100vh - 65px) !important;
        z-index: 999999;
    }
    
    /* Forzar fondo blanco en las capas internas del menú de Streamlit */
    section[data-testid="stSidebar"] > div {
        background-color: #ffffff !important;
    }

    [data-testid="stSidebar"] label {
        color: #374151 !important;
        font-weight: 600 !important;
        font-size: 0.88rem !important;
    }
    
    .stSelectbox div[data-baseweb="select"], 
    .stNumberInput div[data-baseweb="input"] {
        background-color: #f9fafb !important;
        border: 1px solid #d1d5db !important;
        border-radius: 8px !important;
        transition: all 0.2s ease;
    }
    
    .stSelectbox div[data-baseweb="select"]:hover, 
    .stNumberInput div[data-baseweb="input"]:hover {
        border-color: #059669 !important;
        box-shadow: 0 0 0 1px #059669 !important;
    }

    /* Botón verde de la Sidebar */
    .stButton>button {
        background-color: #059669 !important;
        color: white !important;
        border-radius: 8px !important;
        border: none !important;
        padding: 0.75rem !important;
        font-weight: 700 !important;
        width: 100% !important;
        box-shadow: 0 4px 6px -1px rgba(5,150,105,0.2) !important;
    }
    .stButton>button:hover {
        background-color: #047857 !important;
        transform: translateY(-1px) !important;
    }

    /* Cajas de métricas */
    div[data-testid="stMetric"] {
        background-color: #ffffff;
        border: 1px solid #e5e7eb;
        padding: 1.2rem;
        border-radius: 12px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
    }
    </style>
""",
    unsafe_allow_html=True,
)

# --- 6. BARRA LATERAL (CONTROLES) ---
with st.sidebar:
    st.markdown("### ⚙️ Parámetros de Cálculo")
    st.divider()

    cultivo_sel = st.selectbox(
        "Selecciona el cultivo", sorted(list(EXTRACCIONES.keys()))
    )
    rendimiento_sel = st.number_input(
        "Rendimiento objetivo (t/ha)", min_value=0.1, value=5.0, step=0.5
    )
    sistema_sel = st.radio(
        "Sistema Hídrico", ["Secano", "Regadío"], horizontal=True
    )

    n_agua = 0.0
    if sistema_sel == "Regadío":
        st.markdown("<br>", unsafe_allow_html=True)
        ppm_agua = st.number_input(
            "Nitratos en agua (ppm)", min_value=0.0, value=0.0, step=1.0
        )
        m3_agua = st.number_input(
            "Dosis de Riego (m³/ha)", min_value=0.0, value=0.0, step=100.0
        )
        n_agua = (ppm_agua * m3_agua / 1000) * 0.2258

    st.divider()
    calc_econ = st.toggle("Habilitar Módulo Financiero", value=True)
    p_urea, p_super, p_kcl = 0.45, 0.40, 0.50
    if calc_econ:
        p_urea = st.number_input("Urea (€/kg)", value=0.45, step=0.05)
        p_super = st.number_input("Superfosfato (€/kg)", value=0.40, step=0.05)
        p_kcl = st.number_input("Cloruro Potásico (€/kg)", value=0.50, step=0.05)

    st.divider()
    generar_btn = st.button("🚜 GENERAR REPORTE")

# --- 7. PANEL PRINCIPAL ---
if generar_btn:
    with st.spinner("Procesando matriz nutricional..."):
        inputs = {
            "cultivo": cultivo_sel,
            "rendimiento": rendimiento_sel,
            "sistema": sistema_sel.lower(),
            "n_agua": n_agua,
            "p_urea": p_urea,
            "p_super": p_super,
            "p_kcl": p_kcl,
            "calc_econ": calc_econ,
        }
        res = calcular_necesidades(**inputs)

        st.markdown(f"## 📊 Informe Agronómico: **{cultivo_sel}**")
        st.caption(
            f"Objetivo de producción: {rendimiento_sel} t/ha | Sistema: {sistema_sel}"
        )
        st.markdown("<br>", unsafe_allow_html=True)

        col_chart, col_metrics = st.columns([1, 2])

        with col_chart:
            fig = go.Figure(
                data=[
                    go.Pie(
                        labels=[
                            "Nitrógeno (N)",
                            "Fósforo (P)",
                            "Potasio (K)",
                        ],
                        values=[res["n_real"], res["p_total"], res["k_total"]],
                        hole=0.5,
                        marker=dict(
                            colors=["#059669", "#d97706", "#dc2626"]
                        ),
                    )
                ]
            )
            fig.update_layout(
                title_text="Balance N-P-K",
                margin=dict(t=40, b=0, l=0, r=0),
                height=280,
            )
            st.plotly_chart(fig, use_container_width=True)

        with col_metrics:
            st.markdown("### Requerimiento Puro (kg/ha)")
            c1, c2, c3 = st.columns(3)
            c1.metric("Nitrógeno (N)", f"{res['n_real']:.1f}")
            c2.metric("Fósforo (P₂O₅)", f"{res['p_total']:.1f}")
            c3.metric("Potasio (K₂O)", f"{res['k_total']:.1f}")

        st.markdown("<br><hr><br>", unsafe_allow_html=True)
        st.markdown("### 🚜 Prescripción Comercial (Sacos a aplicar)")
        cf1, cf2, cf3 = st.columns(3)
        cf1.metric("Urea (46%)", f"{res['urea_fondo']:.0f} kg/ha")
        cf2.metric("Superfosfato (46%)", f"{res['superfosfato_fondo']:.0f} kg/ha")
        cf3.metric("Cloruro Potásico (60%)", f"{res['cloruro_fondo']:.0f} kg/ha")

else:
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    st.markdown(
        "<h1 style='text-align: center; color: #111827;'>🚜 Bienvenido a tu Panel Agronómico</h1>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<p style='text-align: center; color: #6b7280; font-size: 1.1rem;'>Configura los parámetros en el menú lateral para empezar.</p>",
        unsafe_allow_html=True,
    )