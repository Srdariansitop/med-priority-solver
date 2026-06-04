import json
import os
from dotenv import load_dotenv
from models import Patient
from dictionary.specialists_constants import VALID_SPECIALISTS  
from dictionary.equipment_constants import VALID_EQUIPMENT
from groq import Groq

# Cargar variables de entorno desde .env
load_dotenv()

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

def analyze_patient_with_ai(patient: Patient) -> Patient:
    """
    Envía el contexto textual del paciente al LLM.
    Asume que patient.base_urgency_score YA FUE CALCULADO por el motor matemático.
    Extrae el multiplicador de prioridad, recursos sugeridos y actualiza el score final.
    """
    
    system_prompt = f"""
    Eres el Sistema Experto de Inteligencia Artificial Médica de un Hospital de Nivel IV.
    Tu tarea es analizar las notas de triaje e historial de un paciente para detectar banderas rojas, 
    sutilezas emocionales o riesgos que el triaje numérico y los signos vitales puros no logran ver.
    
    Debes responder ESTRICTAMENTE con un objeto JSON válido que contenga las siguientes llaves exactas:
    1. "ai_reasoning": Un string corto (max 20 palabras) explicando tu razonamiento clínico para el modificador.
    2. "llm_context_modifier": Un float entre 0.5 y 2.0.
       - 1.0 significa neutral (el paciente no tiene riesgos ocultos, su score matemático es correcto).
       - > 1.0 si detectas riesgos graves ocultos (ej: dolor opresivo, riesgo de infarto con signos normales, antecedentes críticos como aneurismas ante traumas leves, riesgo suicida).
       - < 1.0 si el texto revela que es un problema crónico agudizado sin alarma inminente (ej: cefalea leve de larga evolución).
    3. "suggested_specialists": Lista de strings. Elige SOLO de esta lista permitida: {VALID_SPECIALISTS}
    4. "suggested_equipment": Lista de strings. Elige SOLO de esta lista permitida: {VALID_EQUIPMENT}
    
    No agregues introducciones, explicaciones ni formato markdown (como ```json) fuera de la estructura del JSON.
    """

    vitals_summary = f"""
    - Frecuencia Cardíaca: {patient.vitals.heart_rate_bpm} lpm
    - Saturación de Oxígeno (SpO2): {patient.vitals.oxygen_saturation_pct}%
    - Presión Arterial: {patient.vitals.systolic_bp}/{patient.vitals.diastolic_bp} mmHg
    - Temperatura: {patient.vitals.temperature_c}°C
    - Nivel de Dolor: {patient.vitals.pain_level}/10
    - Escala de Glasgow (GCS): {patient.vitals.glasgow_coma_scale}/15
    - Nivel de Conciencia: {patient.vitals.consciousness_level}
    """

    user_content = f"""
    ===DATOS DEMOGRÁFICOS Y ESTADO===
    PACIENTE: {patient.first_name} {patient.last_name}
    EDAD: {patient.age} años
    SEXO: {patient.gender}
    ¿ESTÁ EMBARAZADA?: {"SÍ" if patient.is_pregnant else "NO"}
    CATEGORÍA TRIAJE INICIAL: {patient.initial_triage_category}
    SCORE MATEMÁTICO BASE: {getattr(patient, 'base_urgency_score', 0.0)}

    ===SIGNOS VITALES ACTUALES===
    {vitals_summary}

    ===CONTEXTO TEXTUAL===
    NOTAS DE TRIAJE (ENFERMERÍA): "{patient.triage_notes}"
    HISTORIAL MÉDICO (ANTECEDENTES): "{patient.medical_history_text}"
    LISTA DE CRÓNICOS RECONOCIDOS: {patient.chronic_diseases}
    """
    try:
        # Llamada a la API de Groq usando Llama 3
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ],
            model="llama-3.1-8b-instant", 
            temperature=0.0, # Temperatura 0 para que sea estrictamente analítico y determinista
            response_format={"type": "json_object"} # Forzar la salida a JSON
        )
        
        raw_response = chat_completion.choices[0].message.content
        ai_response = json.loads(raw_response)
        
        # 1. Asignar el razonamiento (muy útil para los logs/terminal)
        patient.ai_reasoning = ai_response.get("ai_reasoning", "Sin justificación.")
        
        # 2. Asignar y blindar el modificador
        patient.llm_context_modifier = float(ai_response.get("llm_context_modifier", 1.0))
        
        # 3. Filtrar Especialistas (Defensa estricta contra alucinaciones)
        ai_specialists = ai_response.get("suggested_specialists", [])
        patient.requires_specialist = [s for s in ai_specialists if s in VALID_SPECIALISTS]
        
        # 4. Filtrar Equipamiento (Defensa estricta contra alucinaciones)
        ai_equipment = ai_response.get("suggested_equipment", [])
        patient.requires_equipment = [e for e in ai_equipment if e in VALID_EQUIPMENT]
        
    except Exception as e:
        print(f"⚠️ Error en la IA para {patient.first_name} {patient.last_name} (ID: {patient.patient_id}): {e}")
        # Degradación elegante: Si la IA falla, el modificador es neutral
        patient.ai_reasoning = "Error de conexión con la IA. Se aplica modelo matemático puro."
        patient.llm_context_modifier = 1.0
        patient.requires_specialist = []
        patient.requires_equipment = []

    # RECALCULAR EL SCORE FINAL COMBINADO
    # Verificamos que base_urgency_score exista, por si acaso el motor matemático falló antes
    base_score = getattr(patient, 'base_urgency_score', 0.0)
    
    # El score final es el matemático multiplicado por la intuición clínica de la IA
    patient.final_priority_score = round(base_score * patient.llm_context_modifier, 2)

    return patient

