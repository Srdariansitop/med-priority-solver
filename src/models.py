from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import datetime
from .chronic_disease_weights import CHRONIC_DISEASE_WEIGHTS

@dataclass
class HospitalResources:
    """Define los límites físicos, de personal y equipamiento del entorno."""
    hospital_name: str

    standard_beds_available: int      # Camillas normales de urgencias (Pacientes amarillos/verdes)
    trauma_beds_available: int        # Boxes de reanimación (Solo para pacientes "1_Resuscitation")
    isolation_beds_available: int     # Habitaciones de presión negativa (Si patient.is_isolated == True)
    icu_beds_available: int           # Camas de Cuidados Intensivos (Para post-cirugía o casos críticos)
   
    triage_nurses_available: int      # Atienden la puerta, determinan el AVPU inicial
    general_doctors_available: int    # Médicos de urgencias (consumen el doctor_time_estimated_min)
    specialists_available: int        # Cirujanos, neurólogos, etc. (Casos muy complejos)
    
    # Capacidad de tiempo global para el turno
    available_doctors_time_minutes: int 
    ventilators_available: int        # Respiradores artificiales (Clave si la oxigenación es bajísima o Glasgow < 8)
    operating_rooms_available: int    # Quirófanos libres
    

    # "Diversion status": Cuando un hospital colapsa, avisa a las ambulancias que vayan a otro lado.
    # En tu algoritmo, si los recursos críticos llegan a 0, esto cambia a True.
    is_on_diversion: bool = False
    
@dataclass
class Vitals:
    """Signos vitales estructurados para cálculo matemático rápido."""
    heart_rate_bpm: int          # Frecuencia cardíaca (ej. 80)
    oxygen_saturation_pct: int   # SpO2 (ej. 98)
    systolic_bp: int             # Presión sistólica (ej. 120)
    diastolic_bp: int            # Presión diastólica (ej. 80)
    temperature_c: float         # Temperatura en Celsius (ej. 37.5)
    pain_level: int              # Escala del 1 al 10
    # Escala AVPU estándar en urgencias: "Alert" (Alerta), "Voice" (Responde a la voz), 
    # "Pain" (Responde al dolor), "Unresponsive" (Inconsciente/No responde)
    consciousness_level: str = "Alert" 
    # Escala de Coma de Glasgow (3 a 15). 15 es totalmente consciente, menos de 8 es coma/crítico.
    # El LLM puede inferir este número si en la nota dice "paciente estuporoso que no abre los ojos".
    glasgow_coma_scale: int = 15 

@dataclass
class Patient:
    """Modelo completo del paciente."""
    # 1. Datos Demográficos y Administrativos
    patient_id: str
    first_name: str
    last_name: str
    age: int
    gender: str                  # "M", "F", "Other"
    insurance_type: str          # "Public", "Private", "None"
    arrival_time: datetime       # Fundamental para desempatar y calcular tiempos de espera
    is_pregnant: bool = False    # Las pacientes embarazadas tienen prioridad de triaje mandatoria
    is_isolated: bool = False    # ¿Requiere aislamiento por sospecha de virus/bacteria contagiosa?
    
    # 2. Datos Estructurados Clínicos 
    vitals: Vitals
    chronic_diseases: List[str] = field(default_factory=list)  # Ej: ["diabetes_type_2", "hypertension"]
    reported_symptoms: List[str] = field(default_factory=list) # Síntomas principales: ["chest_pain", "syncope"]
    allergies: List[str] = field(default_factory=list)         # Alertas críticas de seguridad (ej: ["penicillin"])
    
    # Clasificación inicial protocolar (Sistema Mánchester / Emergencia)
    # Valores sugeridos: "1_Resuscitation" (Rojo), "2_Emergent" (Naranja), "3_Urgent" (Amarillo), "4_Standard" (Verde), "5_Routine" (Azul)
    initial_triage_category: str = "3_Urgent"
    
    # 3. Datos No Estructurados 
    triage_notes: str            # Texto libre escrito por enfermería al llegar (Ej: "Sufrió desmayo de 2 min...")
    medical_history_text: str    # Resumen del historial médico previo
    
    # 4. Variables Calculadas por el Sistema (Inicializadas en 0 / 1.0)
    base_urgency_score: float = 0.0      # Calculado usando solo los signos vitales y algoritmos base
    llm_context_modifier: float = 1.0    # El LLM lo ajusta (ej. 1.5 si detecta riesgo oculto en notas)
    final_priority_score: float = 0.0    # Puntuación final para el algoritmo de optimización
    
    # 5. Requerimientos de Recursos (Variables para el optimizador)
    needs_bed: int = 1                   # 1 si requiere cama, 0 si es consulta rápida/ambulatorio
    doctor_time_estimated_min: int = 30  # Minutos estimados de atención requerida
