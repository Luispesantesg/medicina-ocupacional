import streamlit as st

def modulo_constantes_vitales():
    st.markdown("### Sección E. Constantes Vitales y Antropometría")
    
    # Uso de columnas para optimizar el espacio visual
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        temp = st.number_input("Temperatura (°C)", min_value=30.0, max_value=42.0, value=36.5, step=0.1)
        peso = st.number_input("Peso (Kg)", min_value=20.0, max_value=300.0, value=70.0, step=0.1)
        
    with col2:
        ta_sistolica = st.number_input("PA Sistólica (mmHg)", min_value=50, max_value=250, value=120)
        talla = st.number_input("Talla (cm)", min_value=100, max_value=250, value=170)
        
    with col3:
        ta_diastolica = st.number_input("PA Diastólica (mmHg)", min_value=30, max_value=150, value=80)
        fc = st.number_input("Frecuencia Cardíaca (lpm)", min_value=30, max_value=200, value=75)
        
    with col4:
        fr = st.number_input("Frecuencia Respiratoria (rpm)", min_value=8, max_value=60, value=16)
        sato2 = st.number_input("Sat. Oxígeno (%)", min_value=50, max_value=100, value=98)
        perimetro_abd = st.number_input("Perímetro Abdominal (cm)", min_value=50, max_value=200, value=90)

    # Cálculo automático del IMC basado en la evidencia
    if talla > 0:
        talla_metros = talla / 100
        imc = peso / (talla_metros ** 2)
        st.metric(label="IMC Calculado", value=f"{imc:.2f} kg/m²")
    
    # Construcción del diccionario (JSON) que se enviará a Supabase
    dict_seccion_e = {
        "temperatura_c": temp,
        "presion_arterial": f"{ta_sistolica}/{ta_diastolica}",
        "frecuencia_cardiaca": fc,
        "frecuencia_respiratoria": fr,
        "saturacion_o2": sato2,
        "peso_kg": peso,
        "talla_cm": talla,
        "imc": round(imc, 2),
        "perimetro_abdominal_cm": perimetro_abd
    }
    
    return dict_seccion_e