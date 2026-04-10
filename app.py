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
# 3. Módulos Clínicos Base
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

# ==========================================
# MÓDULO: GESTIÓN DE AUSENTISMO (SUT/IESS)
# ==========================================
def modulo_ausentismo_morbilidad():
    st.subheader("Registro de Ausentismo y Reposos Médicos")
    
    col_search, col_btn = st.columns([3, 1])
    with col_search:
        cedula_busqueda = st.text_input("Cédula del paciente para cargar certificado:", key="cedula_ausentismo")
    with col_btn:
        st.markdown("<br>", unsafe_allow_html=True)
        btn_buscar = st.button("Buscar Empleado", use_container_width=True)

    if btn_buscar and cedula_busqueda:
        try:
            respuesta = supabase.table("pacientes").select("*").eq("cedula", cedula_busqueda.strip()).execute()
            datos = respuesta.data
            if datos:
                st.session_state.paciente_activo = datos[0]
                st.success("Empleado localizado.")
            else:
                st.session_state.paciente_activo = None
                st.warning("Empleado no encontrado.")
        except Exception as e:
            st.error(f"Falla SQL: {e}")

    if st.session_state.paciente_activo:
        paciente = st.session_state.paciente_activo
        st.markdown("---")
        st.info(f"**TRABAJADOR:** {paciente['nombres']} {paciente['apellidos']} | **C.I:** {paciente['cedula']}")
        
        with st.form("form_ausentismo", clear_on_submit=True):
            st.markdown("#### Datos del Certificado Médico")
            col_a1, col_a2 = st.columns(2)
            
            with col_a1:
                fecha_inicio = st.date_input("Fecha de Inicio del Reposo:")
                dias_reposo = st.number_input("Días de Reposo Otorgados:", min_value=1, step=1)
                tipo_contingencia = st.selectbox(
                    "Tipo de Contingencia (SUT):", 
                    ["Enfermedad Común", "Accidente de Trabajo", "Enfermedad Profesional", "Maternidad/Paternidad", "Otros"]
                )
            with col_a2:
                cie10_ausentismo = st.text_input("Código CIE-10:")
                desc_ausentismo = st.text_input("Descripción del Diagnóstico:")
                emisor = st.selectbox("Entidad Emisora:", ["IESS", "Ministerio de Salud Pública (MSP)", "Dispensario Anexo", "Médico Privado"])
                validado = st.checkbox("Certificado Validado por IESS")
                
            submit_ausentismo = st.form_submit_button("Registrar Ausentismo", type="primary")
            
            if submit_ausentismo:
                if not cie10_ausentismo:
                    st.error("El código CIE-10 es obligatorio para la estadística epidemiológica.")
                else:
                    payload_ausentismo = {
                        "paciente_id": paciente['id'],
                        "fecha_inicio": fecha_inicio.isoformat(),
                        "dias_reposo": dias_reposo,
                        "tipo_contingencia": tipo_contingencia,
                        "diagnostico_cie10": cie10_ausentismo.strip().upper(),
                        "descripcion_diagnostico": desc_ausentismo.strip(),
                        "emisor": emisor,
                        "certificado_validado": validado
                    }
                    try:
                        supabase.table("registro_ausentismo").insert(payload_ausentismo).execute()
                        st.success("✅ Reposo médico registrado exitosamente en la matriz de morbilidad.")
                    except Exception as e:
                        st.error(f"Falla de registro SQL: {e}")

# ==========================================
# MÓDULOS DE LECTURA Y ANALÍTICA
# ==========================================
def generar_certificado_pdf(paciente, registro):
    pdf = FPDF()
    pdf.add_page()
    
    diag_data = registro.get('diagnostico_tratamiento') or {}
    aptitud = diag_data.get('dictamen_aptitud', 'No especificada')
    restricciones = diag_data.get('limitaciones_restricciones', '') or "Ninguna"
    recomendaciones = diag_data.get('recomendaciones', '') or "Ninguna"
    
    pdf.set_font("helvetica", "B", 16)
    pdf.cell(0, 10, "CERTIFICADO DE APTITUD MEDICA OCUPACIONAL", ln=1, align="C")
    pdf.ln(5)
    
    nombres_paciente = f"{paciente.get('nombres') or ''} {paciente.get('apellidos') or ''}".strip()
    pdf.set_font("helvetica", "B", 12)
    pdf.cell(0, 10, "1. Datos del Trabajador", ln=1)
    pdf.set_font("helvetica", "", 11)
    pdf.cell(0, 8, f"Nombres: {nombres_paciente}", ln=1)
    pdf.cell(0, 8, f"Cedula de Identidad: {paciente.get('cedula', 'S/D')}", ln=1)
    pdf.cell(0, 8, f"Grupo Sanguineo: {paciente.get('grupo_sanguineo', 'N/D')}", ln=1)
    pdf.ln(5)
    
    pdf.set_font("helvetica", "B", 12)
    pdf.cell(0, 10, "2. Detalle de la Evaluacion", ln=1)
    pdf.set_font("helvetica", "", 11)
    pdf.cell(0, 8, f"Fecha de Atencion: {registro.get('fecha_atencion', 'S/D')}", ln=1)
    pdf.cell(0, 8, f"Tipo de Evaluacion: {registro.get('tipo_evaluacion', 'S/D')}", ln=1)
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
        cedula_busqueda = st.text_input("Ingrese la cédula del paciente para consultar historial:", key="cedula_historial_medico")
    with col_btn:
        st.markdown("<br>", unsafe_allow_html=True)
        btn_buscar = st.button("Recuperar Historial", use_container_width=True)

    if btn_buscar and cedula_busqueda:
        try:
            respuesta_paciente = supabase.table("pacientes").select("*").eq("cedula", cedula_busqueda.strip()).execute()
            if respuesta_paciente.data:
                st.session_state.paciente_activo = respuesta_paciente.data[0]
            else:
                st.session_state.paciente_activo = None
                st.warning("Paciente no localizado en la base de datos.")
        except Exception as e:
            st.error(f"Error de consulta estructural: {e}")

    if st.session_state.paciente_activo:
        paciente = st.session_state.paciente_activo
        st.markdown("---")
        st.info(f"**MATRIZ HISTÓRICA DE:** {paciente['nombres']} {paciente['apellidos']} | **C.I:** {paciente['cedula']}")
        
        tab_eval, tab_aus = st.tabs(["📋 Evaluaciones Ocupacionales", "🛌 Reposos Médicos"])
        
        with tab_eval:
            try:
                res_eval = supabase.table("evaluaciones_ocupacionales").select("*").eq("paciente_id", paciente['id']).order("fecha_atencion", desc=True).execute()
                if not res_eval.data:
                    st.warning("No existen registros médicos previos.")
                else:
                    for registro in res_eval.data:
                        fecha = registro.get('fecha_atencion') or 'S/F'
                        tipo = registro.get('tipo_evaluacion') or 'S/T'
                        
                        diag_data = registro.get('diagnostico_tratamiento') or {}
                        aptitud = diag_data.get('dictamen_aptitud', 'No especificada')
                        
                        icono = "🔴" if "No Apto" in aptitud else "🟡" if "Restricciones" in aptitud or "Observación" in aptitud else "🟢"
                        
                        # --- VISTA DESEMPAQUETADA RESTAURADA ---
                        with st.expander(f"{icono} {fecha} | {tipo} | {aptitud}"):
                            st.download_button(
                                "📄 Descargar Certificado", 
                                data=generar_certificado_pdf(paciente, registro), 
                                file_name=f"Cert_{paciente['cedula']}_{fecha}.pdf", 
                                mime="application/pdf", 
                                key=f"pdf_{registro.get('id', 'temp')}"
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
                st.error(f"Error de base de datos: {e}")
                
        with tab_aus:
            try:
                res_aus = supabase.table("registro_ausentismo").select("*").eq("paciente_id", paciente['id']).order("fecha_inicio", desc=True).execute()
                if not res_aus.data:
                    st.warning("No registra ausentismo laboral.")
                else:
                    df_aus = pd.DataFrame(res_aus.data)
                    st.dataframe(df_aus[['fecha_inicio', 'dias_reposo', 'tipo_contingencia', 'diagnostico_cie10', 'emisor', 'certificado_validado']], use_container_width=True)
            except Exception as e:
                st.error(f"Error de lectura: {e}")

def modulo_analitica_global():
    st.subheader("📊 Dashboard SUT - Epidemiología y Morbilidad")
    
    with st.expander("⚙️ Parámetros de Riesgo Laboral (Modificable)", expanded=True):
        col_p1, col_p2 = st.columns(2)
        hht = col_p1.number_input("Horas Hombre Trabajadas (HHT) en el periodo:", min_value=1, value=200000, step=1000)
        k_constante = col_p2.number_input("Constante 'K' (OSHA/SUT):", value=200000, disabled=True)
    
    st.markdown("---")
    
    try:
        # Validación protegida para Ausentismo (Previene KeyErrors si la BD está vacía)
        res_ausentismo = supabase.table("registro_ausentismo").select("*").execute()
        datos_ausentismo = res_ausentismo.data or []
        df_aus = pd.DataFrame(datos_ausentismo)
        
        st.markdown("#### 🚨 Indicadores de Siniestralidad (Accidentes de Trabajo)")
        
        if not df_aus.empty and 'tipo_contingencia' in df_aus.columns and 'Accidente de Trabajo' in df_aus['tipo_contingencia'].values:
            df_at = df_aus[df_aus['tipo_contingencia'] == 'Accidente de Trabajo']
            num_accidentes = len(df_at)
            dias_perdidos_at = df_at['dias_reposo'].sum()
            
            indice_frecuencia = (num_accidentes * k_constante) / hht
            indice_gravedad = (dias_perdidos_at * k_constante) / hht
            tasa_riesgo = dias_perdidos_at / num_accidentes if num_accidentes > 0 else 0
            
            col_k1, col_k2, col_k3 = st.columns(3)
            col_k1.metric("Índice de Frecuencia (I.F)", f"{indice_frecuencia:.2f}")
            col_k2.metric("Índice de Gravedad (I.G)", f"{indice_gravedad:.2f}")
            col_k3.metric("Tasa de Riesgo (T.R)", f"{tasa_riesgo:.2f}")
        else:
            st.success("✔️ No se registran Accidentes de Trabajo en el periodo actual. Indicadores SUT en Cero.")
            
        st.markdown("---")
        
        st.markdown("#### 🦠 Análisis de Morbilidad General")
        if not df_aus.empty and 'tipo_contingencia' in df_aus.columns:
            col_g1, col_g2 = st.columns(2)
            with col_g1:
                fig_tipo = px.pie(df_aus, names='tipo_contingencia', title='Causas de Ausentismo', hole=0.4)
                st.plotly_chart(fig_tipo, use_container_width=True)
            with col_g2:
                cie10_counts = df_aus['diagnostico_cie10'].value_counts().reset_index()
                cie10_counts.columns = ['CIE-10', 'Casos']
                fig_cie = px.bar(cie10_counts.head(10), x='CIE-10', y='Casos', title='Top 10 Diagnósticos (CIE-10)')
                st.plotly_chart(fig_cie, use_container_width=True)
        else:
            st.info("No hay registros de reposos médicos para analizar gráficos de morbilidad.")
            
    except Exception as e:
        st.error(f"Falla estructural en el motor de cálculo SUT: {e}")

# ==========================================
# SEGURIDAD Y ENRUTADOR PRINCIPAL
# ==========================================
def modulo_login():
    st.markdown("<h2 style='text-align: center;'>🔐 Acceso Restringido</h2>", unsafe_allow_html=True)
    col_espacio1, col_login, col_espacio2 = st.columns([1, 2, 1])
    with col_login:
        with st.form("form_login"):
            usuario = st.text_input("Usuario Identificador")
            clave = st.text_input("Clave Criptográfica", type="password")
            submit = st.form_submit_button("Autorizar Acceso", use_container_width=True)
            if submit:
                try:
                    if usuario == st.secrets["credenciales"]["usuario"] and clave == st.secrets["credenciales"]["clave"]:
                        st.session_state.autenticado = True
                        st.rerun()
                    else:
                        st.error("❌ Credenciales inválidas.")
                except KeyError:
                    st.error("🛑 Error: Credenciales no configuradas.")

if not st.session_state.autenticado:
    modulo_login()
else:
    st.sidebar.title("Navegación Médica")
    st.sidebar.markdown(f"👨‍⚕️ Usuario Activo: **{st.secrets['credenciales']['usuario']}**")
    st.sidebar.markdown("---")
    
    menu = st.sidebar.radio("Seleccione el Módulo:", [
        "Atención Ocupacional (Nueva Eval.)", 
        "Registro de Ausentismo (Reposos)",
        "Historial Médico (Consultas)", 
        "Dashboard SUT / Analítica",
        "Registro de Nuevo Paciente"
    ])

    if menu == "Registro de Nuevo Paciente":
        modulo_registro_paciente()
    elif menu == "Atención Ocupacional (Nueva Eval.)":
        modulo_evaluacion_ocupacional()
    elif menu == "Registro de Ausentismo (Reposos)":
        modulo_ausentismo_morbilidad()
    elif menu == "Historial Médico (Consultas)":
        modulo_historial_medico()
    elif menu == "Dashboard SUT / Analítica":
        modulo_analitica_global()
        
    st.sidebar.markdown("---")
    if st.sidebar.button("Cerrar Sesión", type="primary"):
        st.session_state.autenticado = False
        st.session_state.paciente_activo = None
        st.rerun()