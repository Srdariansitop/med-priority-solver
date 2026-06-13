import warnings
import logging
import json
import re
from models import Patient
from dictionary.specialists_constants import VALID_SPECIALISTS
from dictionary.equipment_constants import VALID_EQUIPMENT
from transformers import pipeline
import torch


# 1. SILENCIO ABSOLUTO: Apagamos las advertencias que frenan la consola de Windows
warnings.filterwarnings("ignore")
logging.getLogger("transformers").setLevel(logging.ERROR)

print("🧠 Inicializando pipeline local de Transformers (Modo Optimizado)...")

try:
    model_id = "Qwen/Qwen2.5-0.5B-Instruct"

    ai_pipeline = pipeline(
        "text-generation",
        model=model_id,
        device_map="auto",
        dtype=torch.float16 if torch.cuda.is_available() else torch.float32
    )
    print(f"✅ Modelo {model_id} cargado exitosamente en el sistema.")
except Exception as e:
    print(f"❌ Error crítico al cargar el modelo local de Transformers: {e}")
    ai_pipeline = None


def _clean_and_parse_json(raw_text: str) -> dict:
    try:
        match = re.search(r"\{.*\}", raw_text, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        return json.loads(raw_text)
    except Exception as e:
        raise ValueError(f"Fallo en el parseo de JSON local. Texto crudo: {raw_text}. Error: {e}")


def analyze_patient_with_ai(patient: Patient) -> Patient:
    """
    El paciente debe traer ya calculado su base_urgency_score desde scoring_engine.
    Esta función solo se encarga de ajustarlo con el LLM y agregar penalizaciones operativas.
    """
    # Verificar que el score base exista (lo ponemos a 0.0 si no está)
    if not hasattr(patient, 'base_urgency_score'):
        patient.base_urgency_score = 0.0

    # ------------------------------------------------------------
    # Preparación del prompt para el LLM
    # ------------------------------------------------------------
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
    
    REGLAS ESTRICTAS DE GESTIÓN DE RECURSOS:
    1. Eres un médico en un hospital público con recursos limitados. Practica la eficiencia.
    2. ESTÁ PROHIBIDO pedir equipos de imagenología pesada (TAC, MRI) o quirófanos para pacientes con síntomas leves.
    3. Si el paciente tiene un problema de rutina, NO pidas ningún equipo o pide solo lo básico.
    4. Pedir un TAC para un resfriado común será considerado un fallo crítico del sistema.
    5. Solo pide equipos de imagenología si hay signos de alarma evidentes.
    6. SOLICITA EQUIPAMIENTO DE SOPORTE VITAL AVANZADO (respirador, ECMO, desfibrilador) ÚNICAMENTE si el score matemático base es >= 30 y hay signos de fallo orgánico (p. ej., SpO2 < 90%, GCS <= 8, tensión arterial sistólica < 85 o > 180).
    
    IMPORTANTE: Tu respuesta debe comenzar directamente con la llave '{{' y terminar con '}}'.
    No uses comillas invertidas, markdown o cualquier otro texto antes o después del JSON.
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
    SCORE MATEMÁTICO BASE (MANCHESTER): {patient.base_urgency_score}

    ===SIGNOS VITALES ACTUALES===
    {vitals_summary}

    ===CONTEXTO TEXTUAL===
    NOTAS DE TRIAJE (ENFERMERÍA): "{patient.triage_notes}"
    HISTORIAL MÉDICO (ANTECEDENTES): "{patient.medical_history_text}"
    LISTA DE CRÓNICOS RECONOCIDOS: {patient.chronic_diseases}
    """

    if ai_pipeline is None:
        return _apply_fallback(patient, "Pipeline local no inicializado.")

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_content}
    ]

    try:
        outputs = ai_pipeline(
            messages,
            max_new_tokens=250,   # ← Aumentado para que el JSON no se trunque
            do_sample=False,
            return_full_text=False,
            clean_up_tokenization_spaces=False
        )

        raw_response = outputs[0]["generated_text"]
        ai_response = _clean_and_parse_json(raw_response)

        patient.ai_reasoning = ai_response.get("ai_reasoning", "Procesado localmente.")
        patient.llm_context_modifier = float(ai_response.get("llm_context_modifier", 1.0))

        ai_specialists = ai_response.get("suggested_specialists", [])
        patient.requires_specialist = [s for s in ai_specialists if s in VALID_SPECIALISTS]

        ai_equipment = ai_response.get("suggested_equipment", [])
        # Primero filtramos solo equipos válidos
        requested_equipment = [e for e in ai_equipment if e in VALID_EQUIPMENT]

        # ------------------------------------------------------------
        # NUEVOS FILTROS DE EFICIENCIA Y RACIONALIZACIÓN DE RECURSOS
        # ------------------------------------------------------------
        # Equipos considerados pesados o de soporte vital avanzado
        HEAVY_EQUIPMENT = {
            "defibrillator", "ecmo_machine", "ventilator",
            "mri", "ct_scanner", "surgical_room"   # ajusta según tu diccionario real
        }
        UCI_EQUIPMENT = {"ecmo_machine", "ventilator", "defibrillator"}  # nivel UCI

        # Filtro 1: si el triaje es bajo (categoría 4 o 5), eliminar equipos pesados
        if patient.initial_triage_category in ("4_Standard", "5_Routine"):
            requested_equipment = [e for e in requested_equipment if e not in HEAVY_EQUIPMENT]

        # Filtro 2 corregido: solo anulamos equipamiento UCI si el modificador es <= 1.0
        # Y además el paciente NO presenta signos vitales objetivamente críticos.
        # Esto evita retirar soporte vital a pacientes que realmente lo necesitan.
        vitals_criticos = (
            patient.vitals.oxygen_saturation_pct < 90 or
            patient.vitals.glasgow_coma_scale <= 8 or
            patient.vitals.systolic_bp < 85 or patient.vitals.systolic_bp > 180 or
            patient.vitals.heart_rate_bpm < 40 or patient.vitals.heart_rate_bpm > 140
        )
        if patient.llm_context_modifier <= 1.0 and not vitals_criticos:
            requested_equipment = [e for e in requested_equipment if e not in UCI_EQUIPMENT]

        patient.requires_equipment = requested_equipment

    except Exception as e:
        return _apply_fallback(patient, f"Excepción en pipeline local: {str(e)}")

    # ------------------------------------------------------------
    # PASO FINAL: Combinar score clínico ajustado por IA + penalizaciones operativas
    # ------------------------------------------------------------
    # 1. Score clínico ajustado por el LLM
    adjusted_clinical = round(patient.base_urgency_score * patient.llm_context_modifier, 2)

    # 2. Penalización por tiempo de espera (se supone que max_safe_wait_time_min y time_waiting_min ya los pobló scoring_engine)
    waiting_penalty = 0.0
    if getattr(patient, 'time_waiting_min', 0) > getattr(patient, 'max_safe_wait_time_min', 9999):
        waiting_penalty = 50.0

    # 3. Penalización por deterioro súbito en sala
    deterioration_penalty = 100.0 if getattr(patient, 'has_deteriorated', False) else 0.0

    # 4. Score final
    patient.final_priority_score = adjusted_clinical + waiting_penalty + deterioration_penalty

    return patient


def _apply_fallback(patient: Patient, error_msg: str) -> Patient:
    """Modo seguro si la IA falla."""
    patient.ai_reasoning = f"Degradación a modelo numérico puro. Motivo: {error_msg}"
    patient.llm_context_modifier = 1.0
    patient.requires_specialist = []
    patient.requires_equipment = []

    base_score = getattr(patient, 'base_urgency_score', 0.0)
    waiting_penalty = 0.0
    if getattr(patient, 'time_waiting_min', 0) > getattr(patient, 'max_safe_wait_time_min', 9999):
        waiting_penalty = 50.0
    deterioration_penalty = 100.0 if getattr(patient, 'has_deteriorated', False) else 0.0
    patient.final_priority_score = round(base_score * 1.0, 2) + waiting_penalty + deterioration_penalty
    return patient