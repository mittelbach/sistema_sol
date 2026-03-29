# ==========================================
# SOFTWARE: SOL Laprida (Sistema de Ofertas)
# VERSIÓN: 29.6 (RESTAURACIÓN COMPLETA)
# MÓDULO: cliente.py
# DESARROLLADO POR: S&M Labs
# ==========================================

import streamlit as st  # <--- ESTO ES LO QUE TE FALTABA EN EL ERROR
import json
import os
import requests
import re
from datetime import datetime
from PIL import Image

# --- CONFIGURACIÓN DE IDENTIDAD (PARA QUE NO SE PISEN LAS APPS) ---
st.set_page_config(page_title="SOL Laprida", page_icon="☀️", layout="wide")

# --- CONFIGURACIÓN DE RUTAS DINÁMICAS (PROTECCIÓN DE DATOS) ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
DATABASE_DIR = os.path.join(BASE_DIR, "database")

DB_JSON_PATH = os.path.join(DATABASE_DIR, "data_publica.json")
RANKING_JSON_PATH = os.path.join(DATABASE_DIR, "ranking_sio.json")

# Configuración de interfaz
st.set_page_config(page_title="SOL Laprida - Ofertas", page_icon="☀️", layout="wide")

# --- ESTILOS CSS PERSONALIZADOS (IDENTIDAD VISUAL S&M) ---
st.markdown("""
    <style>
    .oferta-card {
        background-color: #ffffff;
        border-radius: 12px;
        padding: 20px;
        border-left: 6px solid #ffcc00;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .precio {
        color: #d32f2f;
        font-size: 26px;
        font-weight: bold;
    }
    .veredicto-container {
        background-color: #f0f7ff;
        border-radius: 10px;
        padding: 18px;
        border: 1px solid #007bff;
        margin-bottom: 25px;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    .ranking-card {
        background: linear-gradient(135deg, #ffd700 0%, #ff8c00 100%);
        color: white;
        padding: 20px;
        border-radius: 15px;
        text-align: center;
        font-weight: bold;
        box-shadow: 0 6px 20px rgba(0,0,0,0.15);
    }
    .highlight-win {
        color: #2e7d32;
        font-weight: bold;
        background-color: #e8f5e9;
        padding: 5px 10px;
        border-radius: 5px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- NÚCLEO DE FUNCIONES (ALGORITMO DE PERSISTENCIA) ---
def cargar_datos(ruta):
    if os.path.exists(ruta):
        try:
            with open(ruta, "r", encoding="utf-8") as f:
                return json.load(f)
        except: return []
    return []

def obtener_ranking():
    if os.path.exists(RANKING_JSON_PATH):
        try:
            with open(RANKING_JSON_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data if isinstance(data, dict) else {}
        except: return {}
    return {}

def sumar_punto_ranking(comercio):
    ranking = obtener_ranking()
    ranking[comercio] = ranking.get(comercio, 0) + 1
    try:
        with open(RANKING_JSON_PATH, "w", encoding="utf-8") as f:
            json.dump(ranking, f, indent=4)
        st.success(f"¡Victoria registrada para {comercio}!")
    except:
        st.error("Error de escritura en el hipotálamo del ranking.")

# --- LÓGICA DE VEREDICTOS SIO (COMPARADOR DE ENTROPÍA DE PRECIOS) ---
def mostrar_veredictos(todas_las_ofertas):
    # Palabras clave del Sabotaje del Hipotálamo Social (Canasta Básica)
    palabras_clave = ["Harina", "Yerba", "Aceite", "Leche", "Azucar", "Fideos", "Pan", "Carne"]
    hay_duelos = False

    st.markdown("## ⚖️ Veredictos de Ahorro Crítico")
    
    for p in palabras_clave:
        # Filtramos items que coincidan con la categoría
        items = [o for o in todas_las_ofertas if p.lower() in o['producto'].lower()]
        comercios_distintos = set(i['comercio_nombre'] for i in items)
        
        # Si hay al menos dos comercios compitiendo por el mismo producto
        if len(comercios_distintos) >= 2:
            hay_duelos = True
            with st.expander(f"⚔️ DUELO DETECTADO: {p.upper()}", expanded=True):
                # Ordenar por precio para identificar al ganador
                items_ordenados = sorted(items, key=lambda x: x['precio'])
                
                for item in items_ordenados:
                    st.write(f"📍 **{item['comercio_nombre']}:** {item['producto']} — <span class='precio'>${item['precio']:,.2f}</span>", unsafe_allow_html=True)
                
                ganador = items_ordenados[0]
                perdedor = items_ordenados[-1]
                
                if perdedor['precio'] > ganador['precio']:
                    brecha = perdedor['precio'] - ganador['precio']
                    porcentaje = (brecha / perdedor['precio']) * 100
                    
                    st.markdown(f"""
                        <div class="veredicto-container">
                            🚀 <b>DIAGNÓSTICO SIO:</b> Comprando en <b>{ganador['comercio_nombre']}</b> 
                            ahorrás <b>${brecha:,.2f}</b> (<span class="highlight-win">{porcentaje:.1f}% menos</span>).
                        </div>
                    """, unsafe_allow_html=True)
                    
                    if st.button(f"Validar Victoria: {ganador['comercio_nombre']}", key=f"btn_{p}_{ganador['comercio_nombre']}"):
                        sumar_punto_ranking(ganador['comercio_nombre'])
                        st.rerun()

    if not hay_duelos:
        st.info("No hay duelos de precios directos hoy. La homeostasis del mercado está estable.")
    st.markdown("---")

# --- BARRA LATERAL (CENTRO DE CONTROL) ---
with st.sidebar:
    logo_path = os.path.join(ASSETS_DIR, "logo_sol.png")
    if os.path.exists(logo_path): 
        st.image(logo_path, width=200)
    
    st.title("☀️ SOL Laprida")
    st.caption("Infraestructura S&M Labs | v29.6")
    st.markdown("---")
    
    # --- EL CLIMA (Versión Robusta)---
   # --- EL CLIMA (RESTAURACIÓN QUIRÚRGICA DEL BACKUP) ---
    st.subheader("⛅ El Tiempo")
    @st.cache_data(ttl=600)
    def obtener_clima_laprida():
        try:
            # Tu URL original que sabemos que funciona
            url = "https://wttr.in/Laprida,BuenosAires?format=%t|%C|%w|%p"
            import requests
            import re
            res = requests.get(url, timeout=10)
            if res.status_code == 200:
                # Limpieza de caracteres para que se vea impecable
                texto = res.text.encode('utf-8').decode('utf-8')
                return texto.replace("Â", "").replace("°C", "°")
        except: return None
    
    datos_clima = obtener_clima_laprida()
    if datos_clima:
        try:
            temp, cond, viento, lluvia = datos_clima.split("|")
            import re
            v_limpio = re.sub(r'[^\x00-\x7F]+', '', viento).strip()
            
            # Usamos las métricas nativas de Streamlit (como en tu backup)
            c1, c2 = st.columns([1, 1])
            with c1: st.metric("Temp.", temp)
            with c2: st.metric("Estado", cond)
            st.write(f"💨 **Viento:** {v_limpio} | ☔ **Lluvia:** {lluvia}")
        except: 
            st.caption("Sincronizando...")
    else:
        st.caption("Clima temporalmente fuera de línea")

    # RADIOS LOCALES (Vínculo Social)
    st.subheader("📻 Sintonía Local")
    st.markdown("""
        <div style="line-height: 2;">
            <a style="text-decoration:none; color:#d32f2f; font-weight:bold;" href="https://www.radiopowerlaprida.com.ar/" target="_blank">🎙️ Power 102.1</a><br>
            <a style="text-decoration:none; color:#d32f2f; font-weight:bold;" href="https://radioshowlaprida.com/" target="_blank">🎙️ Show 101.3</a><br>
            <a style="text-decoration:none; color:#d32f2f; font-weight:bold;" href="https://www.radiolaprida.com/" target="_blank">🎙️ Laprida 104.5</a>
        </div>
    """, unsafe_allow_html=True)

# --- CUERPO PRINCIPAL (VISUALIZADOR DE OFERTAS) ---
st.title("🚀 SOL: Sistema de Ofertas Laprida")
st.markdown("#### Inteligencia Neguentrópica aplicada al consumo local.")

ofertas_raw = cargar_datos(DB_JSON_PATH)

if not ofertas_raw:
    st.warning("⚠️ Sincronizando con el nodo local de Laprida... Por favor, aguarde.")
else:
    # 1. PODIO DE COMPETITIVIDAD (RANKING HISTÓRICO)
    ranking_data = obtener_ranking()
    if ranking_data:
        st.subheader("🏆 Podio de Competitividad")
        # Ordenamos los comercios por victorias
        sorted_rank = sorted(ranking_data.items(), key=lambda x: x[1], reverse=True)
        
        cols_ranking = st.columns(min(len(sorted_rank), 3))
        for i, (comercio, puntos) in enumerate(sorted_rank[:3]):
            with cols_ranking[i]:
                medalla = "🥇" if i == 0 else "🥈" if i == 1 else "🥉"
                st.markdown(f"""
                    <div class="ranking-card">
                        <div style="font-size: 35px;">{medalla}</div>
                        <div style="font-size: 18px; margin: 5px 0;">{comercio}</div>
                        <div style="font-size: 22px;">{puntos} Victorias</div>
                    </div>
                """, unsafe_allow_html=True)
        st.markdown("---")

    # 2. SECCIÓN DE VEREDICTOS
    mostrar_veredictos(ofertas_raw)

    # 3. FILTRO DE BÚSQUEDA Y GRILLA DE PRODUCTOS
    st.subheader("🔍 Buscador de Ofertas")
    busqueda = st.text_input("¿Qué necesitás comprar?", placeholder="Ej: Aceite, Harina, Coca Cola...")
    
    # Lógica de filtrado
    filtro = [o for o in ofertas_raw if busqueda.lower() in o['producto'].lower() or busqueda.lower() in o['comercio_nombre'].lower()]
    
    if not filtro:
        st.error(f"No se encontraron ofertas para '{busqueda}'.")
    else:
        # Mostramos en columnas de a 2
        grid = st.columns(2)
        for idx, of in enumerate(filtro):
            with grid[idx % 2]:
                with st.container():
                    st.markdown(f"""
                        <div class="oferta-card">
                            <h3 style="margin-top:0;">{of['producto']}</h3>
                            <p class="precio">$ {of['precio']:,.2f}</p>
                            <p>🏢 <b>Comercio:</b> {of['comercio_nombre']}</p>
                            <p>📅 <b>Vence:</b> {of.get('fecha_vencimiento', 'Consultar')}</p>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    # Botón de contacto directo
                    wa_num = "".join(filter(str.isdigit, of.get('comercio_wa', '')))
                    if wa_num:
                        st.link_button(f"📲 Contactar a {of['comercio_nombre']}", f"https://wa.me/{wa_num}?text=Hola!%20Vi%20tu%20oferta%20de%20{of['producto']}%20en%20SOL%20Laprida")

st.markdown("---")
st.caption("© 2026 S&M Labs | Sociología de Alto Impacto - Algoritmo de Homeostasis Global")
