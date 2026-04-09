import streamlit as st
from supabase import create_client, Client
from datetime import datetime

# ==========================================
# 1. Configuración de la Arquitectura Visual
# ==========================================
st.set_page_config(page_title="HCE Ocupacional", page_icon="⚕️", layout="wide")

# ==========================================
# 2. Protocolo de Conexión al Backend
# ==========================================
@st.cache_resource
def init_connection() -> Client:
    try:
        # Intenta leer estrictamente desde .streamlit/secrets.toml
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        return create_client(url, key)
    except KeyError as e:
        # Interrumpe la ejecución e informa el error exacto en pantalla (Evita la pantalla negra)
        st.error(f"🛑 Falla Crítica de Configuración: No se encontró la variable {e} en el archivo secrets.toml.")
        st.info("Verifique que la carpeta se llame exactamente '.streamlit' y el archivo 'secrets.toml'.")
        st.stop() 
    except Exception as e:
        st.error(f"🛑 Error inesperado en el motor de base de datos: {e}")
        st.stop()

# Inicialización del cliente Supabase
supabase: Client = init_connection()

# ==========================================
# 3. Módulo de Interfaz: Sección A
# ==========================================
def modulo_registro_paciente():
    st.title("Módulo Médico Ocupacional")
    st.markdown("---")
    st.subheader("Registro de Paciente Base (Sección A)")
    
    with st.form("registro_paciente_form", clear_on_submit=False):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Validación estricta de longitud para la cédula ecuatoriana
            cedula = st.text_input("Número de Identificación (Cédula)*", max_chars=10)
            nombres = st.text_input("Nombres Completos*")
            apellidos = st.text_input("Apellidos Completos*")
            
        with col2:
            fecha_nac = st.date_input("Fecha de Nacimiento*", min_value=datetime(1940, 1, 1))
            sexo = st.selectbox("Sexo Biológico", ["Hombre", "Mujer"])
            lateralidad = st.selectbox("Lateralidad", ["Diestro", "Zurdo", "Ambidiestro"])
            
        with col3:
            grupo_sangre = st.selectbox("Grupo Sanguíneo", 
                                        ["O+", "O-", "A+", "A-", "B+", "B-", "AB+", "AB-"])
            grupo_prioritario = st.selectbox("Grupo de Atención Prioritaria", 
                                             ["Ninguno", "Embarazada", "Persona con Discapacidad", "Enfermedad Catastrófica", "Adulto Mayor"])
            
        st.info("Los campos marcados con (*) son obligatorios para la integridad referencial de la base de datos.")
        submit = st.form_submit_button("Guardar Registro Demográfico", type="primary")
        
        # ==========================================
        # 4. Lógica Transaccional (Envío de Datos)
        # ==========================================
        if submit:
            # Control de calidad de datos en el Frontend
            if not cedula or not nombres or not apellidos:
                st.warning("⚠️ Error Lógico: Los campos Cédula, Nombres y Apellidos no pueden estar vacíos.")
            else:
                # Construcción del Diccionario JSON (Payload) estandarizado
                payload = {
                    "cedula": cedula.strip(),
                    "nombres": nombres.strip().upper(),
                    "apellidos": apellidos.strip().upper(),
                    "fecha_nacimiento": fecha_nac.isoformat(), # Formato estándar ISO 8601
                    "sexo": sexo,
                    "grupo_sanguineo": grupo_sangre,
                    "lateralidad": lateralidad,
                    "grupo_atencion_prioritaria": grupo_prioritario
                }
                
                try:
                    # Ejecución del insert hacia PostgreSQL
                    respuesta = supabase.table("pacientes").insert(payload).execute()
                    st.success(f"✅ Éxito Transaccional: Paciente {nombres.upper()} {apellidos.upper()} ingresado correctamente en la matriz.")
                except Exception as ex:
                    # Captura de errores desde el servidor (ej. Cédula duplicada)
                    st.error(f"❌ Falla en la transacción SQL. Detalle técnico: {ex}")

# ==========================================
# 5. Ejecución del Flujo
# ==========================================
modulo_registro_paciente()
