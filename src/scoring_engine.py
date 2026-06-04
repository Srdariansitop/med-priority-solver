from typing import List
from datetime import datetime
from models import Patient, Vitals, MAX_WAIT_TIMES
from dictionary.chronic_disease_weights import CHRONIC_DISEASE_WEIGHTS

def calculate_vitals_penalty(vitals: Vitals) -> float:
    """Evalúa la estabilidad fisiológica del paciente sumando penalizaciones."""
    penalty = 0.0

    # 1. Saturación de Oxígeno (SpO2) - El parámetro más crítico en urgencias
    if vitals.oxygen_saturation_pct < 80:
        penalty += 60.0  # Hipoxia extrema / Paro respiratorio inminente
    elif vitals.oxygen_saturation_pct < 90:
        penalty += 40.0  # Hipoxia severa
    elif vitals.oxygen_saturation_pct < 95:
        penalty += 15.0  # Hipoxia leve / Alerta

    # 2. Escala de Coma de Glasgow (GCS) y Nivel de Conciencia (AVPU)
    if vitals.glasgow_coma_scale <= 8 or vitals.consciousness_level == "Unresponsive":
        penalty += 55.0  # Trauma craneal severo / Estado de Coma
    elif vitals.glasgow_coma_scale <= 12 or vitals.consciousness_level in ["Voice", "Pain"]:
        penalty += 30.0  # Alteración moderada de la conciencia
    elif vitals.glasgow_coma_scale < 15:
        penalty += 10.0  # Desorientación leve

    # 3. Frecuencia Cardíaca (HR)
    if vitals.heart_rate_bpm > 140 or vitals.heart_rate_bpm < 40:
        penalty += 40.0  # Taquicardia/Bradicardia extrema (Shock, Arritmia letal)
    elif vitals.heart_rate_bpm > 110 or vitals.heart_rate_bpm < 50:
        penalty += 15.0  # Desviación moderada

    # 4. Presión Arterial Sistólica (Filtro de Shock Hipovolémico o Crisis Hipertensiva)
    if vitals.systolic_bp < 85:
        penalty += 45.0  # Shock distributivo / hemorrágico / cardiogénico
    elif vitals.systolic_bp < 100 or vitals.systolic_bp > 180:
        penalty += 20.0  # Hipotensión moderada o Crisis Hipertensiva peligrosa

    # 5. Temperatura Corporal
    if vitals.temperature_c >= 40.0 or vitals.temperature_c < 35.0:
        penalty += 25.0  # Hiperpirexia o Hipotermia severa
    elif vitals.temperature_c >= 38.3:
        penalty += 10.0  # Fiebre (Sospecha de Sepsis latente)

    # 6. Escala del Dolor (Subjetiva pero prioritaria)
    if vitals.pain_level >= 8:
        penalty += 15.0  # Dolor insoportable (Ej: Cólico renal, Fractura de fémur)
    elif vitals.pain_level >= 5:
        penalty += 5.0   # Dolor moderado

    return penalty

def calculate_base_urgency_score(patient: Patient) -> float:
    """Calcula el score matemático definitivo combinando todos los factores objetivos."""
    score = 0.0

    # Paso A: Evaluar el estado de los signos vitales
    score += calculate_vitals_penalty(patient.vitals)

    # Paso B: Sumar la carga de comorbilidades crónicas desde tu diccionario
    for disease in patient.chronic_diseases:
        # Si la enfermedad existe en la tabla de pesos, sumamos su valor
        if disease in CHRONIC_DISEASE_WEIGHTS:
            score += CHRONIC_DISEASE_WEIGHTS[disease]
        else:
            score += 2.0  # Penalización mínima por enfermedad crónica no listada

    # Paso C: Ajustes demográficos y condiciones críticas de vulnerabilidad
    if patient.is_pregnant:
        score += 20.0  # Protección prioritaria estricta del binomio madre-hijo

    if patient.age >= 75:
        score += 10.0  # Paciente geriátrico frágil
    elif patient.age <= 2:
        score += 12.0  # Alerta pediátrica de alta velocidad de deterioro

    # Guardamos el resultado en la variable correspondiente del modelo
    patient.base_urgency_score = round(score, 2)
    
    # Inicialmente, el score de prioridad final es igual al base
    patient.final_priority_score = patient.base_urgency_score
    
    # Paso D: Ajustes dinámicos por tiempo de espera y eventos en sala
    
    # 1. Calcular cuántos minutos lleva esperando realmente desde que llegó
    tiempo_espera_timedelta = datetime.now() - patient.arrival_time
    patient.time_waiting_min = int(tiempo_espera_timedelta.total_seconds() / 60)
    
    # 2. Obtener su límite seguro según su categoría Mánchester
    limite_seguro = MAX_WAIT_TIMES.get(patient.initial_triage_category, 120)
    patient.max_safe_wait_time_min = limite_seguro
    
    # 3. Penalización drástica si ya rebasó el tiempo seguro
    if patient.time_waiting_min > limite_seguro:
        patient.final_priority_score += 50.0  # Lo empuja a las primeras posiciones
        
    # 4. Excepción de la vida real: Si la enfermera reporta un deterioro súbito en sala
    if patient.has_deteriorated:
        patient.final_priority_score += 100.0 # Emergencia absoluta (ej. desmayo)
        
    return patient.base_urgency_score

def score_entire_queue(patients: List[Patient]) -> List[Patient]:
    """Toma la lista de la sala de espera, calcula sus scores y los ordena de mayor a menor gravedad."""
    for patient in patients:
        calculate_base_urgency_score(patient)
    
    # Ordenar la lista: los scores más altos van primero
    patients.sort(key=lambda p: p.final_priority_score, reverse=True)
    return patients