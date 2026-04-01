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
# ---linea que esta comentada el la linea 98---
st.set_page_config(page_title="SOL Laprida - Ofertas", page_icon="☀️", layout="wide")

# --- LÍNEA 16: REFUNDACIÓN DE IDENTIDAD VISUAL (CLON MAQUETA) ---
st.markdown("""
<style>
    /* 1. Fondo Crema TOTAL (Forzado para Laptop y Celular) */
    .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"], .main {
        background-color: #fdfaf5 !important;
    }

    /* Esto elimina cualquier residuo blanco que Streamlit ponga por defecto */
    [data-testid="stAppViewContainer"] > section:nth-child(2) {
        background-color: transparent !important;
    }
    
    /* 2. Títulos y Secciones Estilo S&M */
    .main-title { font-size: 2.2rem; font-weight: 900; color: #1a1a1a; text-align: center; margin-bottom: 5px; letter-spacing: -1px; }
    .subtitle { font-size: 1.1rem; color: #555; text-align: center; margin-bottom: 30px; }
    .section-header { font-size: 1.6rem; font-weight: 800; color: #333; margin-top: 25px; margin-bottom: 15px; }

    /* 3. El Podio (Lista Blanca de la Maqueta) */
    .podio-container {
        background: white;
        border-radius: 15px;
        padding: 5px 15px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        margin-bottom: 25px;
        border: 1px solid #eee;
    }
    .podio-item {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 12px 0;
        border-bottom: 1px solid #f0f0f0;
    }
    .podio-item:last-child { border-bottom: none; }
    .podio-name { font-weight: 700; font-size: 1.1rem; color: #1a1a1a; margin-left: 10px; flex-grow: 1; }

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
</style>
""", unsafe_allow_html=True)


# --- CONFIGURACIÓN DE RUTAS DE SEGURIDAD (S&M Labs) ---
BASE_ROOT = os.path.dirname(os.path.abspath(__file__))
DATABASE_DIR = os.path.join(BASE_ROOT, "database")
ASSETS_DIR = os.path.join(BASE_ROOT, "assets")

DB_JSON_PATH = os.path.join(DATABASE_DIR, "data_publica.json")
RANKING_JSON_PATH = os.path.join(DATABASE_DIR, "ranking_sio.json")

# Configuración de interfaz
# st.set_page_config(page_title="SOL Laprida - Ofertas", page_icon="☀️", layout="wide")



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
    st.caption("Infraestructura S&M Labs | v30.0-CREMA")
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
        # --- NUEVO PODIO ESTILO PREMIUM ---
        st.markdown('<div class="section-header">🏆 Podio de Competitividad</div>', unsafe_allow_html=True)
        
        sorted_rank = sorted(ranking_data.items(), key=lambda x: x[1], reverse=True)

        # 1. ABRIMOS LA CAJA BLANCA (NUEVO)
        st.markdown('<div class="podio-container">', unsafe_allow_html=True)

        for i, (comercio, puntos) in enumerate(sorted_rank[:3]):
            medallas = ["🥇", "🥈", "🥉"]
            # 2. USAMOS LA CLASE CORRECTA 'podio-item'
            st.markdown(f"""
                <div class="podio-item">
                    <span style="font-size: 1.5rem;">{medallas[i]}</span>
                    <span class="podio-name">{comercio}</span>
                    <span style="color: #666; font-size: 0.9rem; font-weight:600;">{puntos} Victorias</span>
                </div>
            """, unsafe_allow_html=True)

        # 3. CERRAMOS LA CAJA (NUEVO)
        st.markdown('</div>', unsafe_allow_html=True)

    # 2. VEREDICTOS
    mostrar_veredictos(ofertas_raw)

    # 3. BUSCADOR
    # # 3. BUSCADOR (Estilo Neguentrópico)
    st.markdown('<div class="section-header">🔍 Buscar producto o comercio...</div>', unsafe_allow_html=True)
    
    # Input sin etiqueta (label_visibility="collapsed") para que no robe espacio
    busqueda = st.text_input("", placeholder="Ej: Aceite, Harina, Coca Cola...", label_visibility="collapsed")

    filtro = [o for o in ofertas_raw if busqueda.lower() in o.get('producto', '').lower() or busqueda.lower() in o.get('comercio', '').lower()]

    st.markdown('<div class="section-header">🚨 Ofertas Detectadas</div>', unsafe_allow_html=True)
    
    if not filtro:
        st.error(f"No se encontraron ofertas para '{busqueda}'.")
    else:
        # En el móvil, Streamlit apila estas dos columnas automáticamente
        col1, col2 = st.columns(2)
        for idx, of in enumerate(filtro):
            with col1 if idx % 2 == 0 else col2:
                
                # Usamos la clase 'oferta-card' que ya tenés en tu CSS

                # Este es el nuevo dibujo premium
                ahorro = of.get('ahorro_pct', 0)
                clase_alerta = "critical-card" if ahorro > 15 else ""
                
                st.markdown(f"""
                    <div class="oferta-card-clon {clase_alerta}">
                        <h3 class="prod-name">{of.get('producto', 'Producto')}</h3>
                        <div class="prod-price">$ {of.get('precio', 0):,.2f}</div>
                        <div class="info-line">🏪 <b>{of.get('comercio', 'S/D')}</b></div>
                        <div class="info-line">
                            <span class="tag-premium">🔥 AHORRO: {ahorro:.1f}%</span>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
                
                # Botón de WhatsApp funcional debajo de la tarjeta
                wa_num = "".join(filter(str.isdigit, str(of.get('comercio_wa', ''))))
                if wa_num:
                    st.link_button(f"📲 Contactar a {of.get('comercio')}", 
                                  f"https://wa.me/{wa_num}?text=Hola!%20Vi%20tu%20oferta%20de%20{of.get('producto')}%20en%20SOL")
# st.markdown("---")
st.caption("© 2026 S&M Labs | Sociología de Alto Impacto")