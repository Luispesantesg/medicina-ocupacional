import streamlit as st
from supabase import create_client, Client
from datetime import datetime
from fpdf import FPDF
import pandas as pd
import plotly.express as px

# ==========================================
# 1. Configuración de la Arquitectura Visual
# ==========================================
st.set_page_config(page_title="HCE Ocupacional", page_icon="⚕️", layout="wide")

# Variables de estado global
if 'paciente_activo' not in st.session_state:
    st.session_state.paciente_activo = None
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False

# ==========================================
# 2. Protocolo de Conexión al Backend
# ==========================================
@st.cache_resource
def init_connection() -> Client:
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        return create_client(url, key)
    except KeyError as e:
        st.error(f"🛑 Falla Crítica: No se encontró {e} en secrets.toml.")
        st.stop()
    except Exception as e:
        st.error(f"🛑 Error en base de datos: {e}")
        st.stop()

supabase: Client = init_connection()

# ==========================================
# 3. Módulos de la Interfaz Médica
# ==========================================

def modulo_registro_paciente():
    st.subheader("Registro de Paciente Base (Sección A)")
    with st.form("registro_paciente_form", clear_on_submit=False):
        col1, col2, col3 = st.columns(3)
        with col1:
            cedula = st.text_input("Número de Identificación*", max_chars=10)
            nombres = st.text_input("Nombres Completos*")
            apellidos = st.text_input("Apellidos Completos*")
        with col2:
            fecha_nac = st.date_input("Fecha de Nacimiento*", min_value=datetime(1940, 1, 1))
            sexo = st.selectbox("Sexo Biológico", ["Hombre", "Mujer"])
            lateralidad = st.selectbox("Lateralidad", ["Diestro", "Zurdo", "Ambidiestro"])
        with col3:
            grupo_sangre = st.selectbox("Grupo Sanguíneo", ["O+", "O-", "A+", "A-", "B+", "B-", "AB+", "AB-"])
            grupo_prioritario = st.selectbox("Atención Prioritaria", ["Ninguno", "Embarazada", "Discapacidad", "Enf. Catastrófica", "Adulto Mayor"])
            
        submit = st.form_submit_button("Guardar Registro Demográfico", type="primary")
        
        if submit:
            if not cedula or not nombres or not apellidos:
                st.warning("⚠️ Cédula, Nombres y Apellidos son obligatorios.")
            else:
                payload = {
                    "cedula": cedula.strip(),
                    "nombres": nombres.strip().upper(),
                    "apellidos": apellidos.strip().upper(),
                    "fecha_nacimiento": fecha_nac.isoformat(),
                    "sexo": sexo,
                    "grupo_sanguineo": grupo_sangre,
                    "lateralidad": lateralidad,
                    "grupo_atencion_prioritaria": grupo_prioritario
                }
                try:
                    supabase.table("pacientes").insert(payload).execute()
                    st.success(f"✅ Paciente {nombres.upper()} ingresado correctamente.")
                except Exception as ex:
                    st.error(f"❌ Falla SQL: {ex}")

def modulo_evaluacion_ocupacional():
    st.subheader("Nueva Evaluación Clínica (Punto de Control)")
    
    col_search, col_btn = st.columns([3, 1])
    with col_search:
        cedula_busqueda = st.text_input("Ingrese la cédula del paciente a evaluar:", key="cedula_nueva_eval")
    with col_btn:
        st.markdown("<br>", unsafe_allow_html=True)
        btn_buscar = st.button("Buscar en Matriz", use_container_width=True)

    if btn_buscar and cedula_busqueda:
        try:
            respuesta = supabase.table("pacientes").select("*").eq("cedula", cedula_busqueda.strip()).execute()
            datos = respuesta.data
            if datos:
                st.session_state.paciente_activo = datos[0]
                st.success("Paciente localizado con éxito.")
            else:
                st.session_state.paciente_activo = None
                st.warning("Paciente no encontrado. Proceda a registrarlo.")
        except Exception as e:
            st.error(f"Falla SQL: {e}")

    if st.session_state.paciente_activo:
        paciente = st.session_state.paciente_activo
        st.markdown("---")
        st.info(f"**PACIENTE EN ATENCIÓN:** {paciente['nombres']} {paciente['apellidos']} | **C.I:** {paciente['cedula']}")
        
        tipo_evaluacion = st.radio(
            "Vía de Exploración (Tipo de Evaluación):",
            ["Evaluación de Ingreso", "Evaluación Periódica", "Evaluación de Reintegro", "Evaluación de Retiro"],
            horizontal=True
        )
        st.markdown("---")
        
        tab_antecedentes, tab_examen, tab_riesgos, tab_diagnostico = st.tabs([
            "🏥 Antecedentes", "🩺 Examen Físico", "⚠️ Perfil de Riesgo", "📋 Diagnóstico y Aptitud"
        ])
        
        with tab_antecedentes:
            with st.expander("1. Antecedentes Clínicos, Quirúrgicos y Familiares", expanded=True):
                ant_clinicos = st.text_area("Enfermedades Preexistentes:")
                ant_quirurgicos = st.text_area("Intervenciones Quirúrgicas:")
                ant_familiares = st.text_area("Antecedentes Familiares:")
            with st.expander("2. Hábitos Tóxicos y Estilo de Vida", expanded=False):
                col_h1, col_h2 = st.columns(2)
                tabaco = col_h1.selectbox("Tabaquismo:", ["Nunca", "Ex-fumador", "Ocasional", "Diario"])
                alcohol = col_h2.selectbox("Consumo de Alcohol:", ["Nunca", "Ocasional", "Frecuente", "Problemático"])
                actividad_fisica = st.selectbox("Actividad Física:", ["Sedentario", "Leve", "Moderada", "Intensa"])
            with st.expander("3. Historial Ocupacional", expanded=False):
                empresa_actual = st.text_input("Empresa Actual / Puesto de Trabajo:")
                ant_ocupacionales = st.text_area("Exposiciones previas:")
        
        with tab_examen:
            with st.expander("1. Biometría y Signos Vitales", expanded=True):
                col_v1, col_v2, col_v3, col_v4 = st.columns(4)
                pa_sistolica = col_v1.number_input("PA Sistólica", min_value=0, max_value=300, step=1)
                pa_diastolica = col_v2.number_input("PA Diastólica", min_value=0, max_value=200, step=1)
                fc = col_v3.number_input("FC (lpm)", min_value=0, max_value=250, step=1)
                sat_o2 = col_v4.number_input("Sat. O2 (%)", min_value=0, max_value=100, step=1)
                
                col_b1, col_b2, col_b3 = st.columns(3)
                peso = col_b1.number_input("Peso (kg)", min_value=0.0, max_value=300.0, value=70.0, step=0.1)
                talla = col_b2.number_input("Talla (cm)", min_value=1.0, max_value=250.0, value=170.0, step=1.0)
                perimetro_ab = col_b3.number_input("Perímetro Abdominal (cm)", min_value=0.0, max_value=200.0, step=1.0)
                
                talla_metros = talla / 100
                imc = peso / (talla_metros ** 2)
                col_imc1, col_imc2 = st.columns(2)
                col_imc1.metric("IMC Calculado", f"{imc:.2f}")
                
                if imc < 18.5: estado_nutricional = "Bajo Peso"; col_imc2.warning(estado_nutricional)
                elif 18.5 <= imc < 24.9: estado_nutricional = "Normopeso"; col_imc2.success(estado_nutricional)
                elif 25 <= imc < 29.9: estado_nutricional = "Sobrepeso"; col_imc2.warning(estado_nutricional)
                else: estado_nutricional = "Obesidad"; col_imc2.error(estado_nutricional)
                
            with st.expander("2. Exploración Física Regional", expanded=False):
                cabeza_cuello = st.text_area("Cabeza y Cuello:", value="S/P")
                torax_cardiopulmonar = st.text_area("Tórax y Cardiopulmonar:", value="S/P")
                abdomen = st.text_area("Abdomen:", value="S/P")
                osteomuscular = st.text_area("Sistema Osteomuscular:", value="S/P")
                neurologico = st.text_area("Sistema Neurológico:", value="S/P")
        
        with tab_riesgos:
            st.markdown("Identifique la exposición a factores de riesgo:")
            with st.expander("1. Factores Físicos y Químicos", expanded=True):
                col_r1, col_r2 = st.columns(2)
                r_ruido = col_r1.checkbox("Ruido / Vibración")
                r_temperatura = col_r1.checkbox("Temperaturas Extremas")
                r_polvos = col_r2.checkbox("Polvos Inorgánicos/Orgánicos")
                r_quimicos = col_r2.checkbox("Sustancias Químicas / Vapores")

            with st.expander("2. Biológicos, Ergonómicos y Psicosociales", expanded=False):
                col_r3, col_r4 = st.columns(2)
                r_biologico = col_r3.checkbox("Exposición a Virus/Bacterias/Hongos")
                r_ergonomico = col_r3.checkbox("Movimientos Repetitivos / Posturas Forzadas")
                r_cargas = col_r3.checkbox("Levantamiento Manual de Cargas")
                r_psicosocial = col_r4.checkbox("Sobrecarga Mental / Estrés Laboral")
                r_turnos = col_r4.checkbox("Trabajo por Turnos / Nocturno")
        
        with tab_diagnostico:
            with st.expander("1. Impresión Diagnóstica", expanded=True):
                col_d1, col_d2 = st.columns([1, 3])
                cie_10 = col_d1.text_input("Código CIE-10 Principal:")
                diagnostico_desc = col_d2.text_input("Descripción del Diagnóstico:")
                cie_secundarios = st.text_area("Diagnósticos Secundarios (Opcional):")
            
            with st.expander("2. Dictamen de Aptitud", expanded=True):
                aptitud = st.radio("Aptitud Médica Laboral:", 
                                   ["Apto", "Apto en Observación", "Apto con Restricciones", "No Apto"], 
                                   horizontal=True)
                restricciones = st.text_area("Restricciones o limitaciones (si aplica):")
                recomendaciones = st.text_area("Recomendaciones Médicas:")
        
        st.markdown("---")
        submit_evaluacion = st.button("Guardar Evaluación Ocupacional", type="primary", use_container_width=True)
        
        if submit_evaluacion:
            datos_clinicos_json = {
                "antecedentes": {"clinicos": ant_clinicos, "quirurgicos": ant_quirurgicos, "familiares": ant_familiares},
                "habitos": {"tabaco": tabaco, "alcohol": alcohol, "actividad_fisica": actividad_fisica},
                "historial_ocupacional": {"empresa": empresa_actual, "exposiciones_previas": ant_ocupacionales},
                "signos_vitales_y_biometria": {
                    "pa": f"{pa_sistolica}/{pa_diastolica}", "fc": fc, "sat_o2": sat_o2,
                    "peso": peso, "talla": talla, "imc": round(imc, 2), "estado_nutricional": estado_nutricional, "perimetro_ab": perimetro_ab
                },
                "examen_regional": {"cabeza_cuello": cabeza_cuello, "torax": torax_cardiopulmonar, "abdomen": abdomen, "osteomuscular": osteomuscular, "neurologico": neurologico}
            }
            
            perfil_ocupacional_json = {
                "riesgos_fisicos": {"ruido_vibracion": r_ruido, "temperaturas": r_temperatura},
                "riesgos_quimicos": {"polvos": r_polvos, "sustancias_vapores": r_quimicos},
                "riesgos_biologicos": r_biologico,
                "riesgos_ergonomicos": {"movimientos_posturas": r_ergonomico, "cargas": r_cargas},
                "riesgos_psicosociales": {"sobrecarga_estres": r_psicosocial, "turnos": r_turnos}
            }
            
            diagnostico_json = {
                "cie_10_principal": cie_10, "descripcion": diagnostico_desc, "cie_10_secundarios": cie_secundarios,
                "dictamen_aptitud": aptitud, "limitaciones_restricciones": restricciones, "recomendaciones": recomendaciones
            }
            
            payload_evaluacion = {
                "paciente_id": paciente['id'],
                "tipo_evaluacion": tipo_evaluacion,
                "datos_clinicos": datos_clinicos_json,
                "perfil_ocupacional": perfil_ocupacional_json,
                "diagnostico_tratamiento": diagnostico_json
            }
            
            try:
                supabase.table("evaluaciones_ocupacionales").insert(payload_evaluacion).execute()
                st.success("✅ Evaluación consolidada exitosamente en PostgreSQL.")
            except Exception as ex:
                st.error(f"❌ Error SQL: {ex}")

def generar_certificado_pdf(paciente, registro):
    pdf = FPDF()
    pdf.add_page()
    
    diag_data = registro.get('diagnostico_tratamiento') or {}
    aptitud = diag_data.get('dictamen_aptitud', 'No especificada')
    
    restricciones = diag_data.get('limitaciones_restricciones', '')
    if not restricciones: restricciones = "Ninguna"
        
    recomendaciones = diag_data.get('recomendaciones', '')
    if not recomendaciones: recomendaciones = "Ninguna"
    
    pdf.set_font("helvetica", "B", 16)
    pdf.cell(0, 10, "CERTIFICADO DE APTITUD MEDICA OCUPACIONAL", ln=1, align="C")
    pdf.ln(5)
    
    nombres_paciente = f"{paciente.get('nombres') or ''} {paciente.get('apellidos') or ''}".strip()
    cedula_paciente = paciente.get('cedula') or 'S/D'
    grupo_sangre = paciente.get('grupo_sanguineo') or 'N/D'
    
    pdf.set_font("helvetica", "B", 12)
    pdf.cell(0, 10, "1. Datos del Trabajador", ln=1)
    pdf.set_font("helvetica", "", 11)
    pdf.cell(0, 8, f"Nombres: {nombres_paciente}", ln=1)
    pdf.cell(0, 8, f"Cedula de Identidad: {cedula_paciente}", ln=1)
    pdf.cell(0, 8, f"Grupo Sanguineo: {grupo_sangre}", ln=1)
    pdf.ln(5)
    
    fecha_atencion = registro.get('fecha_atencion') or 'S/D'
    tipo_evaluacion = registro.get('tipo_evaluacion') or 'S/D'
    
    pdf.set_font("helvetica", "B", 12)
    pdf.cell(0, 10, "2. Detalle de la Evaluacion", ln=1)
    pdf.set_font("helvetica", "", 11)
    pdf.cell(0, 8, f"Fecha de Atencion: {fecha_atencion}", ln=1)
    pdf.cell(0, 8, f"Tipo de Evaluacion: {tipo_evaluacion}", ln=1)
    pdf.ln(5)
    
    pdf.set_font("helvetica", "B", 12)
    pdf.cell(0, 10, "3. Dictamen Medico Laboral", ln=1)
    pdf.set_font("helvetica", "B", 11)
    pdf.cell(0, 8, f"Condicion: {aptitud.upper()}", ln=1)
    
    pdf.set_font("helvetica", "", 11)
    pdf.set_x(10)
    pdf.multi_cell(0, 8, f"Restricciones: {restricciones}")
    pdf.set_x(10)
    pdf.multi_cell(0, 8, f"Recomendaciones: {recomendaciones}")
    pdf.ln(30)
    
    pdf.set_x(10)
    pdf.set_font("helvetica", "B", 11)
    pdf.cell(0, 8, "________________________________________", ln=1, align="C")
    pdf.cell(0, 8, "Dr. Luis Pesantes Guaman", ln=1, align="C")
    pdf.set_font("helvetica", "", 10)
    pdf.cell(0, 6, "Medico General - Magister en Salud Ocupacional", ln=1, align="C")
    
    return bytes(pdf.output())

def modulo_historial_medico():
    st.subheader("Visor de Historial Clínico Ocupacional")
    
    col_search, col_btn = st.columns([3, 1])
    with col_search:
        cedula_busqueda = st.text_input("Ingrese la cédula del paciente para consultar historial:", key="cedula_historial")
    with col_btn:
        st.markdown("<br>", unsafe_allow_html=True)
        btn_buscar = st.button("Recuperar Historial", use_container_width=True)

    if btn_buscar and cedula_busqueda:
        try:
            respuesta_paciente = supabase.table("pacientes").select("*").eq("cedula", cedula_busqueda.strip()).execute()
            datos_paciente = respuesta_paciente.data
            if datos_paciente:
                st.session_state.paciente_activo = datos_paciente[0]
            else:
                st.session_state.paciente_activo = None
                st.warning("Paciente no localizado en la base de datos.")
        except Exception as e:
            st.error(f"Error de consulta estructural: {e}")

    if st.session_state.paciente_activo:
        paciente = st.session_state.paciente_activo
        st.markdown("---")
        st.info(f"**MATRIZ HISTÓRICA DE:** {paciente['nombres']} {paciente['apellidos']} | **C.I:** {paciente['cedula']}")
        
        try:
            respuesta_eval = supabase.table("evaluaciones_ocupacionales").select("*").eq("paciente_id", paciente['id']).order("fecha_atencion", desc=True).execute()
            historial = respuesta_eval.data
            
            if not historial:
                st.warning("No existen registros médicos ocupacionales previos.")
            else:
                st.success(f"Recuperación exitosa: {len(historial)} registro(s).")
                
                for registro in historial:
                    fecha_corta = registro.get('fecha_atencion') or 'S/F'
                    tipo = registro.get('tipo_evaluacion') or 'S/T'
                    
                    diag_data = registro.get('diagnostico_tratamiento') or {}
                    aptitud = diag_data.get('dictamen_aptitud', 'No especificada')
                    
                    if "No Apto" in aptitud:
                        icono = "🔴"
                    elif "Restricciones" in aptitud or "Observación" in aptitud:
                        icono = "🟡"
                    else:
                        icono = "🟢"
                    
                    with st.expander(f"{icono} {fecha_corta} | {tipo} | Dictamen: {aptitud}"):
                        
                        pdf_bytes = generar_certificado_pdf(paciente, registro)
                        st.download_button(
                            label="📄 Descargar Certificado de Aptitud (PDF)",
                            data=pdf_bytes,
                            file_name=f"Certificado_{paciente['cedula']}_{fecha_corta}.pdf",
                            mime="application/pdf",
                            type="primary",
                            key=f"btn_pdf_{registro.get('id', 'temp')}" 
                        )
                        st.markdown("---")
                        
                        st.markdown(f"**CIE-10 Principal:** {diag_data.get('cie_10_principal', 'N/A')} - {diag_data.get('descripcion', '')}")
                        st.markdown(f"**Recomendaciones:** {diag_data.get('recomendaciones', '')}")
                        
                        if diag_data.get('limitaciones_restricciones'):
                            st.warning(f"**Restricciones Operativas:** {diag_data.get('limitaciones_restricciones')}")
                        
                        st.markdown("---")
                        col_h1, col_h2 = st.columns(2)
                        
                        with col_h1:
                            st.markdown("##### 📊 Biometría y Signos Vitales")
                            datos_clinicos = registro.get('datos_clinicos') or {}
                            bio = datos_clinicos.get('signos_vitales_y_biometria') or {}
                            
                            if bio:
                                st.markdown(f"- **P. Arterial:** {bio.get('pa', 'S/D')} mmHg")
                                st.markdown(f"- **F. Cardíaca:** {bio.get('fc', 'S/D')} lpm")
                                st.markdown(f"- **Sat. O2:** {bio.get('sat_o2', 'S/D')}%")
                                st.markdown(f"- **Peso:** {bio.get('peso', 'S/D')} kg | **Talla:** {bio.get('talla', 'S/D')} cm")
                                st.markdown(f"- **IMC:** {bio.get('imc', 'S/D')} ➡️ *{bio.get('estado_nutricional', 'S/D')}*")
                            else:
                                st.info("Datos biométricos no consolidados.")
                                
                        with col_h2:
                            st.markdown("##### ⚠️ Exposición a Riesgos Identificada")
                            riesgos_bd = registro.get('perfil_ocupacional') or {}
                            riesgos_activos = []
                            
                            if isinstance(riesgos_bd, dict):
                                for categoria, valores in riesgos_bd.items():
                                    nombre_cat = categoria.replace('riesgos_', '').capitalize()
                                    if isinstance(valores, dict):
                                        for riesgo, estado in valores.items():
                                            if estado is True:
                                                nombre_riesgo = riesgo.replace('_', ' ').title()
                                                riesgos_activos.append(f"**{nombre_cat}:** {nombre_riesgo}")
                                    elif isinstance(valores, bool) and valores is True:
                                        riesgos_activos.append(f"**{nombre_cat}**")
                            
                            if riesgos_activos:
                                for r in riesgos_activos:
                                    st.markdown(f"- ☢️ {r}")
                            else:
                                st.success("✔️ Sin exposición a riesgos declarada en esta evaluación.")
        
        except Exception as e:
            st.error(f"Falla de red al recuperar matriz histórica: {e}")

def modulo_analitica_global():
    st.subheader("📊 Dashboard de Epidemiología Ocupacional")
    st.markdown("Monitorización en tiempo real de la matriz de salud poblacional.")
    
    try:
        res_pacientes = supabase.table("pacientes").select("id").execute()
        total_pacientes = len(res_pacientes.data) if res_pacientes.data else 0
        
        res_evaluaciones = supabase.table("evaluaciones_ocupacionales").select("*").execute()
        evaluaciones = res_evaluaciones.data
        
        if not evaluaciones:
            st.info("No existe masa crítica de datos (evaluaciones) para generar estadísticas.")
            return
            
        col_m1, col_m2, col_m3 = st.columns(3)
        col_m1.metric("Total Pacientes Base", total_pacientes)
        col_m2.metric("Total Evaluaciones Realizadas", len(evaluaciones))
        col_m3.metric("Última Actualización", datetime.now().strftime("%Y-%m-%d"))
        
        st.markdown("---")
        
        df = pd.DataFrame(evaluaciones)
        
        df['Aptitud'] = df['diagnostico_tratamiento'].apply(
            lambda x: (x or {}).get('dictamen_aptitud', 'No especificada') if isinstance(x, dict) else 'No especificada'
        )
        df['Estado Nutricional'] = df['datos_clinicos'].apply(
            lambda x: (x or {}).get('signos_vitales_y_biometria', {}).get('estado_nutricional', 'S/D') if isinstance(x, dict) else 'S/D'
        )
        
        col_chart1, col_chart2 = st.columns(2)
        
        with col_chart1:
            st.markdown("##### 📈 Distribución de Dictámenes de Aptitud")
            df_aptitud = df[df['Aptitud'] != 'No especificada']
            
            if df_aptitud.empty:
                st.info("Aún no hay dictámenes de aptitud procesados para mostrar.")
            else:
                aptitud_counts = df_aptitud['Aptitud'].value_counts().reset_index()
                aptitud_counts.columns = ['Aptitud', 'Frecuencia']
                
                fig_aptitud = px.pie(
                    aptitud_counts, 
                    values='Frecuencia', 
                    names='Aptitud', 
                    hole=0.4,
                    color_discrete_sequence=px.colors.qualitative.Pastel
                )
                fig_aptitud.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig_aptitud, use_container_width=True)
            
        with col_chart2:
            st.markdown("##### 🩺 Perfil Biométrico Poblacional (Estado Nutricional)")
            df_nutricion = df[df['Estado Nutricional'] != 'S/D']
            
            if df_nutricion.empty:
                st.info("Aún no hay datos biométricos procesados para mostrar.")
            else:
                imc_counts = df_nutricion['Estado Nutricional'].value_counts().reset_index()
                imc_counts.columns = ['Estado Nutricional', 'Frecuencia']
                orden_imc = ['Bajo Peso', 'Normopeso', 'Sobrepeso', 'Obesidad']
                
                fig_imc = px.bar(
                    imc_counts, 
                    x='Estado Nutricional', 
                    y='Frecuencia', 
                    color='Estado Nutricional',
                    text_auto=True,
                    category_orders={"Estado Nutricional": orden_imc}
                )
                fig_imc.update_layout(showlegend=False)
                st.plotly_chart(fig_imc, use_container_width=True)
            
    except Exception as e:
        st.error(f"Falla estructural al compilar el Dashboard: {e}")

# ==========================================
# NUEVO MÓDULO: GATEKEEPER (LOGIN)
# ==========================================
def modulo_login():
    st.markdown("<h2 style='text-align: center;'>🔐 Acceso Restringido</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>Sistema Integrado de Historia Clínica Ocupacional</p>", unsafe_allow_html=True)
    
    col_espacio1, col_login, col_espacio2 = st.columns([1, 2, 1])
    
    with col_login:
        with st.form("form_login"):
            usuario = st.text_input("Usuario Identificador")
            clave = st.text_input("Clave Criptográfica", type="password")
            submit = st.form_submit_button("Autorizar Acceso", use_container_width=True)
            
            if submit:
                try:
                    # Verifica contra las variables de entorno guardadas
                    if usuario == st.secrets["credenciales"]["usuario"] and clave == st.secrets["credenciales"]["clave"]:
                        st.session_state.autenticado = True
                        st.rerun() # Reinicia la app para levantar los módulos médicos
                    else:
                        st.error("❌ Credenciales inválidas. Acceso denegado.")
                except KeyError:
                    st.error("🛑 Error del Sistema: Las credenciales no han sido configuradas en secrets.toml.")

# ==========================================
# 4. Enrutador Principal (Sidebar y Seguridad)
# ==========================================
st.title("Sistema de Historia Clínica Ocupacional")
st.markdown("---")

# Lógica de Interceptación
if not st.session_state.autenticado:
    modulo_login()
else:
    # Si el usuario pasó el Gatekeeper, se renderiza la interfaz médica
    st.sidebar.title("Navegación Médica")
    st.sidebar.markdown(f"👨‍⚕️ Usuario Activo: **{st.secrets['credenciales']['usuario']}**")
    st.sidebar.markdown("---")
    
    menu = st.sidebar.radio("Seleccione el Módulo:", [
        "Atención Ocupacional (Nueva Eval.)", 
        "Historial Médico (Consultas)", 
        "Dashboard Analítico",
        "Registro de Nuevo Paciente"
    ])

    if menu == "Registro de Nuevo Paciente":
        modulo_registro_paciente()
    elif menu == "Atención Ocupacional (Nueva Eval.)":
        modulo_evaluacion_ocupacional()
    elif menu == "Historial Médico (Consultas)":
        modulo_historial_medico()
    elif menu == "Dashboard Analítico":
        modulo_analitica_global()
        
    st.sidebar.markdown("---")
    if st.sidebar.button("Cerrar Sesión", type="primary"):
        st.session_state.autenticado = False
        st.session_state.paciente_activo = None # Limpia la memoria del paciente
        st.rerun()