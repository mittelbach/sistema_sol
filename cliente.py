import streamlit as st
import json
import os
import streamlit.components.v1 as components

# --- CONFIGURACIÓN DE RUTAS DINÁMICAS (PARA LA NUBE) ---
# Usamos el directorio donde está este archivo como base
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

ASSETS_DIR = os.path.join(BASE_DIR, "assets")
DB_JSON_PATH = os.path.join(BASE_DIR, "database", "data_publica.json")
RANKING_JSON_PATH = os.path.join(BASE_DIR, "database", "ranking_sio.json")

st.set_page_config(page_title="SOL Laprida - Ofertas", page_icon="☀️", layout="wide")

# --- ESTILO CSS ---
st.markdown("""
    <style>
    .oferta-card {
        background-color: #f9f9f9;
        border-radius: 10px;
        padding: 20px;
        border-left: 5px solid #ffcc00;
        margin-bottom: 20px;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
    }
    .precio {
        color: #d32f2f;
        font-size: 24px;
        font-weight: bold;
    }
    .veredicto-container {
        background-color: #e3f2fd;
        border-radius: 10px;
        padding: 15px;
        border: 1px solid #90caf9;
        margin-bottom: 25px;
    }
    .ranking-card {
        background: linear-gradient(135deg, #ffd700 0%, #ffae00 100%);
        color: white;
        padding: 20px;
        border-radius: 15px;
        text-align: center;
        font-weight: bold;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    }
    </style>
    """, unsafe_allow_html=True)

# --- FUNCIONES DE RANKING ---
def obtener_ranking():
    if os.path.exists(RANKING_JSON_PATH):
        try:
            with open(RANKING_JSON_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except: return {}
    return {}

def sumar_punto_ranking(comercio):
    ranking = obtener_ranking()
    ranking[comercio] = ranking.get(comercio, 0) + 1
    try:
        with open(RANKING_JSON_PATH, "w", encoding="utf-8") as f:
            json.dump(ranking, f, indent=4)
    except: pass

# --- LÓGICA DE VEREDICTOS ---
def mostrar_veredictos(todas_las_ofertas):
    palabras_clave = ["Harina", "Yerba", "Aceite", "Leche", "Azucar", "Fideos"]
    duelos_visibles = False

    st.markdown("## ⚖️ Veredictos de Ahorro Hoy")
    
    for p in palabras_clave:
        items = [o for o in todas_las_ofertas if p.lower() in o['producto'].lower()]
        comercios = set(i['comercio_nombre'] for i in items)
        
        if len(comercios) >= 2:
            duelos_visibles = True
            with st.expander(f"Duelo Detectado: {p}", expanded=True):
                for item in items:
                    st.write(f"🔹 **{item['comercio_nombre']}:** {item['producto']} — **${item['precio']:,.2f}**")
                
                ganador = min(items, key=lambda x: x['precio'])
                perdedor = max(items, key=lambda x: x['precio'])
                
                if perdedor['precio'] > ganador['precio']:
                    ahorro = ((perdedor['precio'] - ganador['precio']) / perdedor['precio']) * 100
                    st.markdown(f"""
                        <div class="veredicto-container">
                            <b>VEREDICTO SIO:</b> El ahorro está en <b>{ganador['comercio_nombre']}</b>. 
                            Ahorrás un <b>{ahorro:.0f}%</b> en esta opción.
                        </div>
                    """, unsafe_allow_html=True)
                    
                    if st.button(f"Validar Victoria de {ganador['comercio_nombre']}", key=f"v_{p}"):
                        sumar_punto_ranking(ganador['comercio_nombre'])
                        st.rerun()

    if not duelos_visibles:
        st.write("Sin comparativas directas en este momento.")
    st.markdown("---")

# --- BARRA LATERAL ---
with st.sidebar:
    logo_path = os.path.join(ASSETS_DIR, "logo_sol.png")
    if os.path.exists(logo_path): 
        st.image(logo_path, width=200)
    
    st.title("☀️ SOL Laprida")
    st.markdown("---")
    
    # --- EL CLIMA (VERSIÓN IFRAME ROBUSTA) ---
    st.subheader("⛅ El Tiempo")
    
    # Imagen dinámica de Meteored para Laprida
    clima_url = "https://www.meteored.com.ar/wimages/foto76f0d368d3744957e8417c870f20966d.png"
    
    st.markdown(f"""
        <div style="background-color: white; padding: 10px; border-radius: 10px; text-align: center; border: 1px solid #eee;">
            <img src="{clima_url}" style="width: 100%; border-radius: 5px;">
            <p style="font-size: 12px; color: #666; margin-top: 5px;">Laprida, BA</p>
        </div>
    """, unsafe_allow_html=True)
    
    st.caption("[Ver pronóstico extendido](https://www.meteored.com.ar/tiempo-en_Laprida-America+Sur-Argentina-Provincia+de+Buenos+Aires-1-16885.html)")

# --- CUERPO PRINCIPAL ---
st.title("🚀 Ofertas Destacadas en Laprida")

if not os.path.exists(DB_JSON_PATH):
    st.info("Sincronizando ofertas locales...")
else:
    try:
        with open(DB_JSON_PATH, "r", encoding="utf-8") as f:
            ofertas = json.load(f)
    except:
        ofertas = []

    if ofertas:
        # 1. RANKING
        ranking_data = obtener_ranking()
        if ranking_data:
            st.subheader("🏆 Podio de Competitividad Local")
            sorted_rank = sorted(ranking_data.items(), key=lambda x: x[1], reverse=True)
            cols_rank = st.columns(min(len(sorted_rank), 3))
            for i, (com, pts) in enumerate(sorted_rank[:3]):
                with cols_rank[i]:
                    st.markdown(f"""<div class="ranking-card">
                        <p style="font-size:30px; margin:0;">{'🥇' if i==0 else '🥈' if i==1 else '🥉'}</p>
                        <p style="margin:0;">{com}</p>
                        <p style="font-size:20px; margin:0;">{pts} Victorias</p>
                    </div>""", unsafe_allow_html=True)
            st.markdown("---")

        # 2. VEREDICTOS
        mostrar_veredictos(ofertas)
        
        # 3. LISTADO GENERAL
        busqueda = st.text_input("🔍 Buscar por nombre de producto...").lower()
        filtro = [o for o in ofertas if busqueda in o['producto'].lower()]
        
        st.subheader("Listado de Ofertas")
        cols = st.columns(2)
        for i, of in enumerate(filtro):
            with cols[i % 2]:
                st.markdown(f"""<div class="oferta-card">
                    <h3>{of['producto']}</h3>
                    <p class="precio">$ {of['precio']:,.2f}</p>
                    <p>📍 {of['comercio_nombre']}</p>
                </div>""", unsafe_allow_html=True)
                
                # Limpiar WA para el link
                tel = "".join(filter(str.isdigit, of['comercio_wa']))
                st.link_button(f"Pedir a {of['comercio_nombre']}", f"https://wa.me/{tel}")

st.markdown("---")
st.caption("Desarrollado por S&M Labs - Homeostasis Social Aplicada")
