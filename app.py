import streamlit as st
import os 
import json
from datetime import datetime, timedelta
from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base

# ==========================================
# 1. CONFIGURACIÓN Y RUTAS
# ==========================================
st.set_page_config(page_title="SOL Laprida", layout="wide")

BASE_ROOT = os.path.dirname(os.path.abspath(__file__)) 
DATABASE_DIR = os.path.join(BASE_ROOT, "database")
if not os.path.exists(DATABASE_DIR): 
    os.makedirs(DATABASE_DIR)

DB_SQLITE_PATH = os.path.join(DATABASE_DIR, "sio_laprida.db")
PRECIOS_FILE = os.path.join(DATABASE_DIR, "precios_abonos.json")
DB_JSON_PATH = os.path.join(DATABASE_DIR, "data_publica.json")

# ==========================================
# 2. MODELO DE BASE DE DATOS
# ==========================================
# Usamos el import recomendado por la advertencia
from sqlalchemy.orm import declarative_base
Base = declarative_base()

class Comercio(Base):
    __tablename__ = 'comercios'
    id = Column(Integer, primary_key=True)
    nombre = Column(String, nullable=False)
    responsable = Column(String)
    whatsapp = Column(String)
    direccion = Column(String)

class Oferta(Base):
    __tablename__ = 'ofertas'
    id = Column(Integer, primary_key=True)
    producto = Column(String, nullable=False)
    precio = Column(Float, nullable=False)
    descuento = Column(Float, default=0.0) # <--- EL CAMPO CLAVE
    comercio_id = Column(Integer, ForeignKey('comercios.id'))
    fecha = Column(DateTime, default=datetime.now)
    dias_vigencia = Column(Integer, default=7) 
    renovacion_auto = Column(Integer, default=0) 
    en_contienda = Column(Integer, default=1) 
    clasificacion = Column(String)
    comercio = relationship("Comercio")

# ==========================================
# 3. MOTOR Y SESIÓN (SINGLETON EN SESSION_STATE)
# ==========================================
if 'engine' not in st.session_state:
    st.session_state.engine = create_engine(f'sqlite:///{DB_SQLITE_PATH}', connect_args={'check_same_thread': False})
    Base.metadata.create_all(st.session_state.engine)
    st.session_state.Session = sessionmaker(bind=st.session_state.engine)

# Obtenemos la sesión actual
s_exp = st.session_state.Session()

# ==========================================
# 4. FUNCIONES GLOBALES
# ==========================================
def actualizar_json_publico():
    try:
        with st.session_state.Session() as session:
            ofertas = session.query(Oferta).all() 
            lista_para_json = []
            for o in ofertas:
                lista_para_json.append({
                    "producto": o.producto,
                    "precio": float(o.precio),
                    "comercio": o.comercio.nombre if o.comercio else "S/D",
                    "clasificacion": o.clasificacion,
                    "descuento": float(o.descuento or 0.0)
                })
        with open(DB_JSON_PATH, "w", encoding="utf-8") as f:
            json.dump(lista_para_json, f, indent=4, ensure_ascii=False)
    except Exception as e:
        st.error(f"Error en la sincronización: {e}")

def obtener_valor_abono(id_c, data):
    """Auxiliar para el nodo de abonos"""
    val = data.get(str(id_c), 0)
    return float(val.get("monto", 0)) if isinstance(val, dict) else float(val)

# ==========================================
# 5. MENÚ LATERAL
# ==========================================
with st.sidebar:
    st.title("☀️ SOL Laprida")
    st.write("Sociología de Alto Impacto")
    st.write("---")
    menu = st.radio(
        "Nodos de Control:", 
        ["🔄 Carga y ABM Ofertas", "🏢 Registro Comercios", "⚙️ Mantenimiento Comercios", "💰 Abonos", "📲 Cobranza"]
    )

# ==========================================
# 6. NODO 1: ABM OFERTAS (VERSION LIMPIA)
# ==========================================
if menu == "🔄 Carga y ABM Ofertas":
    st.header("🚀 Gestión de Ofertas")
    coms = s_exp.query(Comercio).all()
    
    # --- FORMULARIO DE ALTA ---
    with st.expander("➕ CARGAR NUEVA OFERTA", expanded=False):
        with st.form("f_nueva", clear_on_submit=True):
            if not coms:
                st.warning("Primero registre al menos un comercio.")
            else:
                c_sel = st.selectbox("Seleccionar Comercio", [c.nombre for c in coms])
                c1, c2 = st.columns(2)
                p = c1.text_input("Nombre del Producto")
                pr = c2.number_input("Precio ($)", min_value=0.0)
                
                lista_rubros = ["Almacen", "Ferreteria", "Indumentaria", "Hogar", "Gastro"]
                rub = st.selectbox("Rubro", lista_rubros)
                
                c_vig, c_ren, c_con = st.columns(3)
                vig = c_vig.number_input("Días de Vigencia", min_value=1, value=7)
                ren = c_ren.checkbox("Renovación Automática")
                con = c_con.checkbox("Participa en Contienda", value=True)
                
                if st.form_submit_button("🚀 PUBLICAR OFERTA"):
                    if not p or pr <= 0:
                        st.error("Producto y Precio son obligatorios.")
                    else:
                        cid = next(c.id for c in coms if c.nombre == c_sel)
                        nueva = Oferta(
                            comercio_id=cid, producto=p, precio=pr, clasificacion=rub,
                            descuento=0.0, # Por defecto 0 al crear
                            dias_vigencia=vig, renovacion_auto=1 if ren else 0, en_contienda=1 if con else 0
                        )
                        s_exp.add(nueva)
                        s_exp.commit()
                        actualizar_json_publico()
                        st.success(f"¡{p} publicada con éxito!")
                        st.rerun()

    # --- LISTADO Y EDICIÓN (ABM) ---
    st.subheader("📋 Mantenimiento de Ofertas Existentes")
    ofertas = s_exp.query(Oferta).order_by(Oferta.fecha.desc()).all()
    
    if not ofertas:
        st.info("No hay ofertas cargadas.")
    
    for o in ofertas:
        est = "🟢 EN CONTIENDA" if o.en_contienda == 1 else "🔴 FUERA DE CONTIENDA"
        desc_v = o.descuento if o.descuento else 0.0
        
        with st.expander(f"{est} | 🛒 {o.producto} - {o.comercio.nombre} (${o.precio}) | desc: {desc_v}%"):
            
            # --- FORMULARIO DE EDICIÓN ---
            with st.form(key=f"edit_form_{o.id}"):
                col1, col2, col3 = st.columns([2, 1, 1])
                up_p = col1.text_input("Producto", value=o.producto)
                up_pr = col2.number_input("Precio", value=float(o.precio))
                
                # EL CAMPO DEL DESCUENTO REAL
                up_d = col3.number_input("% Descuento", value=float(desc_v), key=f"d_{o.id}")
                
                lista_rubros = ["Almacen", "Ferreteria", "Indumentaria", "Hogar", "Gastro"]
                idx = lista_rubros.index(o.clasificacion) if o.clasificacion in lista_rubros else 0
                up_r = st.selectbox("Rubro", lista_rubros, index=idx, key=f"up_r_{o.id}")
                up_c = st.checkbox("Participa en Contienda", value=bool(o.en_contienda), key=f"up_c_{o.id}")
                
                if st.form_submit_button("💾 GUARDAR CAMBIOS"):
                    try:
                        with st.session_state.Session() as session:
                            o_db = session.merge(o)
                            o_db.producto = up_p
                            o_db.precio = up_pr
                            o_db.clasificacion = up_r
                            o_db.en_contienda = int(up_c)
                            o_db.descuento = float(up_d)
                            session.commit()
                        
                        actualizar_json_publico()
                        st.success(f"✅ ¡{up_p} actualizado con éxito!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error al guardar: {e}")
            
            # --- BOTÓN ELIMINAR ---
            st.divider()
            if st.button(f"🗑️ ELIMINAR ESTA OFERTA", key=f"del_o_{o.id}"):
                s_exp.delete(o)
                s_exp.commit()
                actualizar_json_publico()
                st.rerun()

# ==========================================
# 7. NODO 2: REGISTRO COMERCIOS
# ==========================================
elif menu == "🏢 Registro Comercios":
    st.header("🏢 Alta de Comercios")
    with st.form("f_reg", clear_on_submit=True):
        n = st.text_input("Nombre del Comercio")
        r = st.text_input("Responsable (Dueño)")
        w = st.text_input("WhatsApp (Ej: 5492284...)")
        d = st.text_input("Dirección")
        if st.form_submit_button("💾 GUARDAR COMERCIO"):
            if not n:
                st.error("El nombre del comercio es obligatorio.")
            else:
                s_exp.add(Comercio(nombre=n, responsable=r, whatsapp=w, direccion=d))
                s_exp.commit()
                st.success(f"¡{n} registrado con éxito!")

# ==========================================
# 8. OTROS NODOS (MANTENIMIENTO, ABONOS, COBRANZA)
# ==========================================
elif menu == "⚙️ Mantenimiento Comercios":
    st.header("🛠️ Gestión de Base de Datos de Comercios")
    for c in s_exp.query(Comercio).all():
        with st.expander(f"🏢 {c.nombre}"):
            with st.form(key=f"edit_c_{c.id}"):
                en = st.text_input("Nombre", value=c.nombre)
                er = st.text_input("Responsable", value=c.responsable or "")
                ew = st.text_input("WhatsApp", value=c.whatsapp or "")
                ed = st.text_input("Dirección", value=c.direccion or "")
                if st.form_submit_button("💾 ACTUALIZAR DATOS"):
                    c.nombre, c.responsable, c.whatsapp, c.direccion = en, er, ew, ed
                    s_exp.commit()
                    st.rerun()
            
            st.divider() 
            if st.button(f"🚨 ELIMINAR COMERCIO Y OFERTAS", key=f"del_c_{c.id}"):
                # Borrado en cascada manual
                s_exp.query(Oferta).filter(Oferta.comercio_id == c.id).delete()
                s_exp.delete(c)
                s_exp.commit()
                actualizar_json_publico() 
                st.rerun()

elif menu == "💰 Abonos":
    st.header("💰 Configuración de Tarifas")
    cfg = json.load(open(PRECIOS_FILE)) if os.path.exists(PRECIOS_FILE) else {}
    with st.form("f_tarifas"):
        nuevos = {}
        coms = s_exp.query(Comercio).all()
        if not coms:
            st.warning("No hay comercios registrados.")
        else:
            for c in coms:
                m = st.number_input(f"Abono {c.nombre}", value=obtener_valor_abono(c.id, cfg))
                nuevos[str(c.id)] = m
            if st.form_submit_button("💾 GUARDAR TARIFARIO"):
                with open(PRECIOS_FILE, "w") as f:
                    json.dump(nuevos, f)
                st.success("Tarifas Actualizadas")

elif menu == "📲 Cobranza":
    st.header("📲 Emisión de Facturación")
    cfg = json.load(open(PRECIOS_FILE)) if os.path.exists(PRECIOS_FILE) else {}
    coms = s_exp.query(Comercio).all()
    if not coms:
        st.warning("No hay comercios registrados.")
    else:
        for c in coms:
            m = obtener_valor_abono(c.id, cfg)
            if m > 0:
                with st.container(border=True):
                    st.write(f"**{c.nombre}**")
                    st.write(f"Monto: ${m} | Dueño: {c.responsable}")
                    link = f"https://wa.me/{c.whatsapp}?text=Hola%20{c.responsable},%20el%20abono%20de%20SOL%20es%20de%20${m}"
                    st.link_button("📲 Enviar WhatsApp", link)