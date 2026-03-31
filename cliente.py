# ==========================================
# SOFTWARE: SOL Laprida (Sistema de Ofertas)
# VERSIÓN: 29.8 (RESTAURACIÓN QUIRÚRGICA)
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

# --- CONFIGURACIÓN DE RUTAS DE SEGURIDAD (S&M Labs) ---
BASE_ROOT = os.path.dirname(os.path.abspath(__file__))
DATABASE_DIR = os.path.join(BASE_ROOT, "database")
ASSETS_DIR = os.path.join(BASE_ROOT, "assets")

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
    return {}

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
        
        # 1. Agrupamos productos por su "Nombre Completo" para separar tipos (ej: Papel Cocina vs Papel Higiénico)
        grupos_especificos = {}
        
        for i, o in enumerate(todas_las_ofertas):
            if i in ids_mostrados: continue
            
            prod_nom = str(o.get('producto', '')).lower()
            prod_norm = prod_nom.replace("á","a").replace("é","e").replace("í","i").replace("ó","o").replace("ú","u").strip()
            
            if p_norm in prod_norm:
                # Usamos las primeras 2 o 3 palabras como 'llave' del grupo para que no mezcle
                palabras = prod_norm.split()
                llave_grupo = " ".join(palabras[:2]) # Ej: "papel cocina" o "papel higienico"
                
                if llave_grupo not in grupos_especificos:
                    grupos_especificos[llave_grupo] = []
                grupos_especificos[llave_grupo].append({"id": i, "data": o})

        # 2. Procesamos cada grupo específico por separado
        for nombre_grupo, items in grupos_especificos.items():
            # Verificamos si hay competencia de comercios en este grupo específico
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
                        
                        if st.button(f"Validar Victoria: {nom_g}", key=f"btn_{nombre_grupo.replace(' ','_')}"):
                            sumar_punto_ranking(nom_g)
                            st.rerun()

    if not hay_duelos:
        st.info("Homeostasis estable: No hay disparidades en productos idénticos.")
    st.markdown("---")


# --- BARRA LATERAL ---
with st.sidebar:
    logo_path = os.path.join(ASSETS_DIR, "logo_sol.png")
    if os.path.exists(logo_path): 
        st.image(logo_path, width=200)
    
    st.title("☀️ SOL Laprida")
    st.caption("Infraestructura S&M Labs | v29.8")
    st.markdown("---")
    
    st.subheader("⛅ El Tiempo")
    @st.cache_data(ttl=600)
    def obtener_clima_laprida():
        try:
            url = "https://wttr.in/Laprida,BuenosAires?format=%t|%C|%w|%p"
            res = requests.get(url, timeout=10)
            if res.status_code == 200:
                texto = res.text.encode('utf-8').decode('utf-8')
                return texto.replace("Â", "").replace("°C", "°")
        except: return None
    
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
        st.subheader("🏆 Podio de Competitividad")
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

    # 2. VEREDICTOS
    mostrar_veredictos(ofertas_raw)

    # 3. BUSCADOR
    st.subheader("🔍 Buscador de Ofertas")
    busqueda = st.text_input("¿Qué necesitás comprar?", placeholder="Ej: Aceite, Harina...")
    
    filtro = [o for o in ofertas_raw if busqueda.lower() in o.get('producto', '').lower() or busqueda.lower() in o.get('comercio_nombre', '').lower()]
    
    if not filtro:
        st.error(f"No se encontraron ofertas para '{busqueda}'.")
    else:
        grid = st.columns(2)
        for idx, of in enumerate(filtro):
            with grid[idx % 2]:
                with st.container():
                    st.markdown(f"""
                        <div class="oferta-card">
                            <h3 style="margin-top:0;">{of.get('producto', 'Producto')}</h3>
                            <p class="precio">$ {of.get('precio', 0):,.2f}</p>
                            <p>🏢 <b>Comercio:</b> {of.get('comercio_nombre', 'Comercio')}</p>
                            <p>📅 <b>Vence:</b> {of.get('fecha_vencimiento', 'Consultar')}</p>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    wa_num = "".join(filter(str.isdigit, str(of.get('comercio_wa', ''))))
                    if wa_num:
                        st.link_button(f"📲 Contactar", f"https://wa.me/{wa_num}?text=Hola!%20Vi%20tu%20oferta%20en%20SOL")

st.markdown("---")
st.caption("© 2026 S&M Labs | Sociología de Alto Impacto")