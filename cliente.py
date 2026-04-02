# ==========================================
# SOFTWARE: SOL Laprida (Sistema de Ofertas)
# VERSIÓN: 30.0 REBOOT TOTAL
# MÓDULO: cliente.py
# DESARROLLADO POR: S&M Labs
# ==========================================

import streamlit as st
import json
import os
import requests
import re
import statistics
from datetime import datetime
from PIL import Image

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="SOL Laprida - Ofertas", page_icon="☀️", layout="wide")

# --- REFUNDACIÓN DE IDENTIDAD VISUAL (CLON MAQUETA) ---
st.markdown("""
<style>
    /* 1. Fondo Crema TOTAL (Forzado para Laptop y Celular) */
    .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"], .main {
        background-color: #fdfaf5 !important;
    }

    /* Elimina residuo blanco de Streamlit */
    [data-testid="stAppViewContainer"] > section:nth-child(2) {
        background-color: transparent !important;
    }

    /* 2. Títulos y Secciones Estilo S&M */
    .main-title { font-size: 2.2rem; font-weight: 900; color: #1a1a1a; text-align: center; margin-bottom: 5px; letter-spacing: -1px; }
    .subtitle { font-size: 1.1rem; color: #555; text-align: center; margin-bottom: 30px; }
    .section-header { font-size: 1.6rem; font-weight: 800; color: #333; margin-top: 25px; margin-bottom: 15px; }

    /* 3. El Podio (Estilo Tarjetas con Sombra Reforzada) */
    .podio-item {
        display: flex !important;
        align-items: center !important;
        justify-content: space-between !important;
        padding: 15px 20px !important;
        margin-bottom: 12px !important;
        background-color: white !important;
        border-radius: 12px !important;
        border: 1px solid #d1d1d1 !important;
        box-shadow: 0 10px 25px rgba(0,0,0,0.2) !important; /* Sombra más profunda */
        transition: all 0.3s ease;
    }

    .podio-item:hover {
        transform: translateY(-3px);
        box-shadow: 0 15px 30px rgba(0,0,0,0.35) !important; /* Sombra extrema en hover */
    }

    .podio-name {
        font-weight: 800 !important;
        font-size: 1.2rem !important;
        color: #1a1a1a !important;
        margin-left: 15px !important;
        flex-grow: 1 !important;
    }

    .podio-victorias {
        color: #666 !important;
        font-size: 0.85rem !important;
        font-weight: 600 !important;
        background: #f0f2f6 !important;
        padding: 4px 12px !important;
        border-radius: 20px !important;
    }

    /* 4. Tarjetas de Ofertas (Clon Atómico) */
    .oferta-card-clon {
        background: white;
        border-radius: 18px;
        padding: 20px;
        margin-bottom: 15px;
        box-shadow: 0 8px 20px rgba(0,0,0,0.06);
        border: 1px solid #eee;
        border-left: 8px solid #ffcc00; /* Borde amarillo estándar */
    }

    /* Variante Roja para el "Ahorro Crítico" */
    .critical-card {
        border-left: 8px solid #d32f2f !important;
    }

    .prod-name { font-size: 1.3rem; font-weight: 800; color: #1a1a1a; margin: 0; }
    .prod-price { font-size: 1.7rem; font-weight: 900; color: #d32f2f; margin: 8px 0; }
    .info-line { font-size: 0.95rem; color: #666; margin: 4px 0; display: flex; align-items: center; gap: 5px; }

    /* 5. Tags de Ahorro */
    .tag-premium {
        display: inline-block;
        background: #e8f5e9;
        color: #2e7d32;
        padding: 3px 10px;
        border-radius: 6px;
        font-weight: 800;
        font-size: 0.8rem;
    }

    /* 6. Veredictos de Ahorro (Expander) */
    div[data-testid="stExpander"] {
        background-color: white !important;
        border-radius: 12px !important;
        border: 1px solid #d1d1d1 !important;
        box-shadow: 0 10px 20px rgba(0,0,0,0.15) !important;
        margin-bottom: 20px !important;
        overflow: hidden !important;
    }

    div[data-testid="stExpander"] > details {
        border: none !important;
    }

    div[data-testid="stExpander"] summary {
        font-weight: 800 !important;
        color: #1a1a1a !important;
        padding: 10px !important;
    }

    /* 7. REFORZADO: Tarjeta con Borde Verde Grueso y Sombra */
    .oferta-card-verde {
        background: white !important;
        border-radius: 12px !important;
        padding: 10px !important;
        display: flex !important;
        flex-direction: column !important;
        border: 4.5px solid #008000 !important; /* Tu verde exacto */
        box-shadow: 0 4px 8px rgba(0,0,0,0.1) !important;
    }

    .contenedor-grilla-sio {
        display: grid !important;
        grid-template-columns: 1fr 1fr !important; /* Fuerza las 2 columnas */
        gap: 10px !important;
        width: 100% !important;
    }
</style>
""", unsafe_allow_html=True)


# --- CONFIGURACIÓN DE RUTAS DE SEGURIDAD (S&M Labs) ---
BASE_ROOT = os.path.dirname(os.path.abspath(__file__))
DATABASE_DIR = os.path.join(BASE_ROOT, "database")
ASSETS_DIR = os.path.join(BASE_ROOT, "assets")

DB_JSON_PATH = os.path.join(DATABASE_DIR, "data_publica.json")
RANKING_JSON_PATH = os.path.join(DATABASE_DIR, "ranking_sio.json")



# --- NÚCLEO DE FUNCIONES ---
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
    return []

def sumar_punto_ranking(comercio):
    ranking = obtener_ranking()
    ranking[comercio] = ranking.get(comercio, 0) + 1
    try:
        with open(RANKING_JSON_PATH, "w", encoding="utf-8") as f:
            json.dump(ranking, f, indent=4)
        st.success(f"¡Victoria registrada para {comercio}!")
    except:
        st.error("Error de escritura en el ranking.")

# --- LÓGICA DE VEREDICTOS SIO (v31.2 - FILTRO DE SUB-CATEGORÍA) ---
def mostrar_veredictos(todas_las_ofertas):
    st.markdown("## ⚖️ Veredictos de Ahorro Crítico")
    
    # Mantenemos tu base estable de palabras clave
    palabras_clave = ["Harina", "Yerba", "Aceite", "Leche", "Azucar", "Fideos", "Pan", "Carne", "Atun", "Papel"]
    hay_duelos = False
    ids_mostrados = set() 

    for p in palabras_clave:
        p_norm = p.lower().replace("á","a").replace("é","e").replace("í","i").replace("ó","o").replace("ú","u").strip()
        
        # 1. Agrupamos productos por su "Nombre Completo" para separar tipos
        grupos_especificos = {}
        
        for i, o in enumerate(todas_las_ofertas):
            if i in ids_mostrados: continue
            
            prod_nom = str(o.get('producto', '')).lower()
            prod_norm = prod_nom.replace("á","a").replace("é","e").replace("í","i").replace("ó","o").replace("ú","u").strip()
            
            if p_norm in prod_norm:
                # Usamos las primeras 2 o 3 palabras como 'llave' del grupo
                palabras = prod_norm.split()
                llave_grupo = " ".join(palabras[:2]) 
                
                if llave_grupo not in grupos_especificos:
                    grupos_especificos[llave_grupo] = []
                grupos_especificos[llave_grupo].append({"id": i, "data": o})

        # 2. Procesamos cada grupo específico por separado
        for nombre_grupo, items in grupos_especificos.items():
            # Verificamos si hay competencia de comercios
            comercios = set(it["data"].get('comercio_nombre', it["data"].get('comercio', 'Local')) for it in items)
            
            if len(comercios) >= 2:
                hay_duelos = True
                with st.expander(f"⚔️ DUELO DETECTADO: {nombre_grupo.upper()}", expanded=True):
                    items_ordenados = sorted(items, key=lambda x: x["data"].get('precio', 0))
                    
                    for it in items_ordenados:
                        d = it["data"]
                        local = d.get('comercio_nombre', d.get('comercio', 'Comercio'))
                        st.write(f"📍 **{local}**: {d['producto']} - <span class='precio'>${d['precio']:,.2f}</span>", unsafe_allow_html=True)
                        ids_mostrados.add(it["id"])
                    
                    # Diagnóstico
                    ganador = items_ordenados[0]["data"]
                    perdedor = items_ordenados[-1]["data"]
                    p_gan = ganador.get('precio', 0)
                    p_per = perdedor.get('precio', 0)
                    
                    if p_per > p_gan:
                        brecha = p_per - p_gan
                        porc = (brecha / p_per) * 100
                        nom_g = ganador.get('comercio_nombre', ganador.get('comercio', 'Comercio'))
                        
                        st.markdown(f"""
                            <div class="veredicto-container">
                                🚀 <b>DIAGNÓSTICO SIO:</b> En <b>{nom_g}</b> ahorrás <b>${brecha:,.2f}</b> (<span class="highlight-win">{porc:.1f}% menos</span>).
                            </div>
                        """, unsafe_allow_html=True)
                        # --- Bloque de Validación con STOP ---
                        if 'votos_duelos' not in st.session_state:
                            st.session_state.votos_duelos = set()

                        id_duelo = f"voto_{nombre_grupo.replace(' ','_')}"

                        if id_duelo not in st.session_state.votos_duelos:
                            if st.button(f"Validar Victoria: {nom_g}", key=id_duelo):
                               # 1. BLOQUEO PRIMERO (Cerrar la puerta)
                                st.session_state.votos_duelos.add(id_duelo)
                                # 2. SUMAR DESPUÉS (Contar la victoria)
                                sumar_punto_ranking(nom_g)
                                st.rerun()
                        else:
                            st.markdown(f"⭐ **Victoria de {nom_g} convalidada**")
                        

    if not hay_duelos:
        st.info("Homeostasis estable: No hay disparidades en productos idénticos.")
    st.markdown("---")


# --- BARRA LATERAL ---
with st.sidebar:
    logo_path = os.path.join(ASSETS_DIR, "logo_sol.png")
    if os.path.exists(logo_path): 
        st.image(logo_path, width=200)
    
    st.title("☀️ SOL Laprida")
    st.caption("Infraestructura S&M Labs | v30.0-CREMA")
    st.markdown("---")
    
    st.subheader("⛅ El Tiempo")
    @st.cache_data(ttl=600)
    def obtener_clima_laprida():
        try:
            # ---Programacion de grados farenheit a celsius ----
            url = "https://wttr.in/Laprida,BuenosAires?format=%t|%C|%w|%p&m"
            res = requests.get(url, timeout=10)
            if res.status_code == 200:
                texto = res.text.encode('utf-8').decode('utf-8')
                return texto.replace("Â", "")
        except:
            return None
    
    datos_clima = obtener_clima_laprida()
    if datos_clima:
        try:
            temp, cond, viento, lluvia = datos_clima.split("|")
            v_limpio = re.sub(r'[^\x00-\x7F]+', '', viento).strip()
            c1, c2 = st.columns([1, 1])
            with c1: st.metric("Temp.", temp)
            with c2: st.metric("Estado", cond)
            st.write(f"💨 **Viento:** {v_limpio} | ☔ **Lluvia:** {lluvia}")
        except: 
            st.caption("Sincronizando...")

    st.subheader("📻 Sintonía Local")
    st.markdown("""
        <div style="line-height: 2;">
            <a style="text-decoration:none; color:#d32f2f; font-weight:bold;" href="https://www.radiopowerlaprida.com.ar/" target="_blank">🎙️ Power 102.1</a><br>
            <a style="text-decoration:none; color:#d32f2f; font-weight:bold;" href="https://radioshowlaprida.com/" target="_blank">🎙️ Show 101.3</a><br>
            <a style="text-decoration:none; color:#d32f2f; font-weight:bold;" href="https://www.radiolaprida.com/" target="_blank">🎙️ Laprida 104.5</a>
        </div>
    """, unsafe_allow_html=True)


# --- CUERPO PRINCIPAL ---
st.title("🚀 SOL: Sistema de Ofertas Laprida")
st.markdown("#### Inteligencia Neguentrópica aplicada al consumo local.")

ofertas_raw = cargar_datos(DB_JSON_PATH)

if not ofertas_raw:
    st.warning("⚠️ Sincronizando con el nodo local de Laprida...")
else:
    # 1. PODIO
    ranking_data = obtener_ranking()
    if ranking_data:
        st.markdown('<div class="section-header">🏆 Podio de Competitividad</div>', unsafe_allow_html=True)
        
        sorted_rank = sorted(ranking_data.items(), key=lambda x: x[1], reverse=True)

        st.markdown('<div class="podio-container">', unsafe_allow_html=True)

        for i, (comercio, puntos) in enumerate(sorted_rank[:3]):
            medallas = ["🥇", "🥈", "🥉"]
            st.markdown(f"""
                <div class="podio-item">
                    <span style="font-size: 1.5rem;">{medallas[i]}</span>
                    <span class="podio-name">{comercio}</span>
                    <span style="color: #666; font-size: 0.9rem; font-weight:600;">{puntos} Victorias</span>
                </div>
            """, unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)


    # 2. VEREDICTOS
    mostrar_veredictos(ofertas_raw)


   # 3. BUSCADOR
    st.markdown('<div class="section-header">🔍 Buscar producto o comercio...</div>', unsafe_allow_html=True)
    
    busqueda = st.text_input("Buscar producto o comercio", placeholder="Ej: Aceite, Harina, Coca Cola...", label_visibility="collapsed")

    if busqueda:
        filtro = [o for o in ofertas_raw if busqueda.lower() in o.get('producto', '').lower() or busqueda.lower() in o.get('comercio', '').lower()]
    else:
        filtro = ofertas_raw

    st.markdown('<div class="section-header">🚨 Ofertas Detectadas</div>', unsafe_allow_html=True)
    
    if not filtro:
        st.error(f"No se encontraron ofertas para '{busqueda}'.")
    else:
        # Iniciamos la grilla
        html_final = '<div class="contenedor-grilla-sio">'

        for o in filtro:
            nom = str(o.get('producto', 'Producto'))
            pre = o.get('precio', 0)
            com = str(o.get('comercio', 'S/D'))
            ahr = o.get('ahorro_pct', 0.0)

            # Construimos la tarjeta SIN usar f-strings complejas para evitar errores de renderizado
            tarjeta = '<div class="oferta-card-verde">'
            tarjeta += '<div style="font-weight:800; color:#1a1a1a; font-size:1.1rem;">' + nom + '</div>'
            tarjeta += '<div style="color:#d32f2f; font-weight:900; font-size:1.4rem; margin:5px 0;">$ ' + f"{pre:,.2f}" + '</div>'
            tarjeta += '<div style="font-size:0.9rem; color:#444;">🏪 <b>' + com + '</b></div>'
            tarjeta += '<div style="background:#e8f5e9; color:#1b5e20; display:inline-block; padding:2px 8px; border-radius:4px; font-size:0.8rem; margin-top:5px; font-weight:bold;">🔥 ¡Oportunidad SOL!</div>'
            tarjeta += '</div>'
            
            html_final += tarjeta

        html_final += '</div>' # Cerramos la grilla
        
        # MANDAMOS TODO AL RENDERIZADOR
        st.markdown(html_final, unsafe_allow_html=True)


# --- PIE DE PÁGINA (ESTO VA PEGADO AL BORDE IZQUIERDO, SIN ESPACIOS) ---
st.markdown("---")
st.caption("© 2026 S&M Labs | Sociología de Alto Impacto | v30.0-CREMA")