import streamlit as st
import json
import os
import requests
import re
from datetime import datetime
from PIL import Image

# --- 1. CONFIGURACIÓN Y ESTILO (Nodo Laprida) ---
st.set_page_config(page_title="SOL Laprida", layout="wide", page_icon="☀️")

st.markdown(
    """
    <style>
    /* Aseguramos el ancho de 460px para el tridente de medios */
    [data-testid="stSidebarNav"] {padding-top: 0rem;}
    [data-testid="stSidebar"] { min-width: 460px; max-width: 460px; }
    
    /* Estilo de las métricas del Clima */
    .stMetric { background-color: #f8f9fb; padding: 10px; border-radius: 8px; border: 1px solid #e0e4e9; }
    
    /* Redondeo de imágenes y logos */
    img { border-radius: 12px; display: block; margin-left: auto; margin-right: auto; }
    </style>
    """,
    unsafe_allow_html=True,
)

# --- 2. GESTIÓN DEL LOGO (PNG LOCAL) ---
# Usamos el nombre exacto que aparece en tu carpeta: logo_sol.png
directorio_actual = os.path.dirname(os.path.abspath(__file__))
ruta_sol = os.path.join(directorio_actual, "assets", "logo_sol.png")

def renderizar_logo(tamaño):
    if os.path.exists(ruta_sol):
        imagen = Image.open(ruta_sol)
        st.image(imagen, width=tamaño)
    else:
        # Failsafe: Si no lo encuentra, muestra el texto pero no rompe el script
        st.title("☀️ SOL LAPRIDA")
        if tamaño > 100:
            st.error(f"Archivo no encontrado en: {ruta_sol}")

# --- 3. BARRA LATERAL (CLIMA + RADIO + TV) ---
with st.sidebar:
    renderizar_logo(250)
    st.caption("Sistema de Ofertas Locales - Nodo Laprida")
    st.markdown("---")
    
    # SECCIÓN CLIMA
    @st.cache_data(ttl=600)
    def obtener_clima():
        try:
            url = "https://wttr.in/Laprida,BuenosAires?format=%t|%C|%w|%p"
            res = requests.get(url, timeout=10)
            if res.status_code == 200:
                # Limpiamos el ruido visual de la codificación
                return res.text.encode('utf-8').decode('utf-8').replace("Â", "").replace("°C", "°")
        except: return None
    
    datos_clima = obtener_clima()
    if datos_clima:
        try:
            temp, cond, viento, lluvia = datos_clima.split("|")
            v_limpio = re.sub(r'[^\x00-\x7F]+', '', viento).strip()
            c1, c2 = st.columns([1.1, 1])
            with c1: st.metric("Temp.", temp)
            with c2: st.write("**Estado**"); st.write(cond)
            st.write(f"💨 **Viento:** {v_limpio} | ☔ **Lluvia:** {lluvia}")
        except: st.caption("Clima: Sincronizando...")
    
    st.markdown("---")
    st.subheader("📺 Transmisiones en Vivo")
    
    # InfoLaprida TV
    st.write("🔹 **InfoLaprida TV**")
    st.components.v1.html('<iframe width="100%" height="230" src="https://www.youtube.com/embed/r3CZ9hluChA" frameborder="0" allowfullscreen></iframe>', height=240)

    # Radio Show 102.7 FM (El Fluido)
    st.write("📻 **Radio Show 102.7 FM**")
    st.components.v1.html('<iframe src="https://radioshowlaprida.com/" width="100%" height="450" frameborder="0" allowfullscreen></iframe>', height=460)

# --- 4. CUERPO PRINCIPAL (VUELVEN LAS OFERTAS) ---
col_logo_cuerp, col_tit_cuerp = st.columns([1, 5])
with col_logo_cuerp:
    renderizar_logo(80)
with col_tit_cuerp:
    st.title("SOL: Ofertas de Laprida")

st.write(f"Bienvenido Matías. Hoy es {datetime.now().strftime('%d/%m/%Y')}")
st.markdown("---")

# CARGA DE OFERTAS DESDE EL JSON
DATA_FILE = "data_publica.json"
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        ofertas = json.load(f)
    
    for o in ofertas:
        with st.container():
            c_info, c_pre = st.columns([3, 1])
            with c_info:
                st.subheader(o['producto'])
                st.caption(f"🏪 {o.get('comercio', 'Comercio Local')}")
            with c_pre:
                st.title(f"$ {o['precio']}")
            
            # Botón de WhatsApp
            msg = f"Hola! Vi en el SOL la oferta de {o['producto']} a ${o['precio']}. Me interesa!".replace(" ", "%20")
            st.link_button("🟢 Pedir por WhatsApp", f"https://wa.me/5492284000000?text={msg}", use_container_width=True)
            st.markdown("---")
else:
    st.error("No se encontró 'data_publica.json'")