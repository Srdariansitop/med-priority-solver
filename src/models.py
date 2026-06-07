from dataclasses import dataclass, field
from typing import List, Dict
from datetime import datetime
from dictionary.chronic_disease_weights import CHRONIC_DISEASE_WEIGHTS
from dictionary.specialists_constants import VALID_SPECIALISTS
from dictionary.equipment_constants import VALID_EQUIPMENT

# Tiempos máximos de espera permitidos (en minutos) por categoría Mánchester
MAX_WAIT_TIMES: Dict[str, int] = {
    "1_Resuscitation": 0,    
    "2_Emergent": 10,        
    "3_Urgent": 60,          
    "4_Standard": 120,       
    "5_Routine": 240         
}

@dataclass
class HospitalResources:
    """Define los límites físicos, de personal y equipamiento de un Hospital Nivel IV."""
    hospital_name: str

    # ===== INFRAESTRUCTURA FÍSICA =====
    standard_beds_available: int      # Camillas normales de urgencias (Pacientes amarillos/verdes)
    trauma_beds_available: int        # Boxes de reanimación (Solo para pacientes "1_Resuscitation")
    isolation_beds_available: int     # Habitaciones de presión negativa (Si patient.is_isolated == True)
    icu_beds_available: int           # Camas de Cuidados Intensivos (Post-cirugía o críticos)
    operating_rooms_available: int    # Quirófanos libres
    available_doctors_time_minutes: int # Capacidad de tiempo global para el turno

    # ===== PERSONAL MÉDICO DINÁMICO =====
    # Diccionario que mapea especialista -> cantidad disponible
    # Inicializado con TODOS los especialistas válidos (ver VALID_SPECIALISTS)
    specialists_available: Dict[str, int] = field(default_factory=lambda: {spec: 0 for spec in VALID_SPECIALISTS})
    
    # ===== EQUIPAMIENTO DINÁMICO =====
    # Diccionario que mapea equipo -> cantidad disponible
    # Inicializado con TODOS los equipos válidos (ver VALID_EQUIPMENT)
    equipment_available: Dict[str, int] = field(default_factory=lambda: {equip: 0 for equip in VALID_EQUIPMENT})

    is_on_diversion: bool = False     # True si el hospital colapsa y desvía ambulancias
    
@dataclass
class Vitals:
    """Signos vitales estructurados para cálculo matemático rápido."""
    heart_rate_bpm: int          # Frecuencia cardíaca (ej. 80)
    oxygen_saturation_pct: int   # SpO2 (ej. 98)
    systolic_bp: int             # Presión sistólica (ej. 120)
    diastolic_bp: int            # Presión diastólica (ej. 80)
    temperature_c: float         # Temperatura en Celsius (ej. 37.5)
    pain_level: int              # Escala del dolor del 1 al 10
    consciousness_level: str = "Alert" # Escala AVPU: Alert, Voice, Pain, Unresponsive
    glasgow_coma_scale: int = 15       # Escala GCS (3 a 15). Menor a 8 = coma/crítico

@dataclass
class Patient:
    """Modelo completo del paciente."""
    patient_id: str
    first_name: str
    last_name: str
    age: int
    gender: str                  # "M", "F", "Other"
    insurance_type: str          # "Public", "Private", "None"
    arrival_time: datetime       # Fundamental para desempatar y calcular tiempos de espera
    triage_notes: str            # Texto libre escrito por enfermería al llegar
    medical_history_text: str    # Resumen del historial médico previo
    vitals: Vitals

    is_pregnant: bool = False    # Triaje prioritario / requiere obstetra
    is_isolated: bool = False    # Requiere cama de presión negativa
    chronic_diseases: List[str] = field(default_factory=list)  # Ej: ["diabetes_type_2", "hypertension"]
    reported_symptoms: List[str] = field(default_factory=list) # Ej: ["chest_pain", "syncope"]
    allergies: List[str] = field(default_factory=list)         # Ej: ["penicillin"]
    initial_triage_category: str = "3_Urgent"                  # Sistema Mánchester
    base_urgency_score: float = 0.0      # Puntaje algorítmico base (signos vitales/enfermedades)
    llm_context_modifier: float = 1.0    # Multiplicador ajustado por el LLM tras leer las notas
    final_priority_score: float = 0.0    # Puntuación final para el optimizador
    needs_bed: int = 1                   # 1 si requiere cama, 0 si es consulta rápida ambulatoria
    doctor_time_estimated_min: int = 30  # Minutos estimados de atención
    time_waiting_min: int = 0                  # Minutos reales que lleva esperando
    max_safe_wait_time_min: int = 60           # Límite seguro, inicializado según Mánchester
    has_deteriorated: bool = False             # True si sufre un evento en la sala (convulsión, desmayo)
    deterioration_event_notes: str = ""        # Contexto del evento para que el LLM lo evalúe
    requires_equipment: List[str] = field(default_factory=list)  # Validado contra equipment_constants.py
    requires_specialist: List[str] = field(default_factory=list) # Validado contra specialists_constants.py
    
    # ===== CAMPOS PARA RED DE HOSPITALES =====
    arrival_hospital_id: str = "HOSP-01"      # ID del hospital donde llega el paciente
    current_hospital_id: str = "HOSP-01"      # ID del hospital donde está actualmente (puede cambiar por transferencia)
    status: str = "Waiting"                    # Estado: "Waiting", "In-Treatment", "Discharged", "Transferred", "Deceased"
    ai_reasoning: str = ""                    # Razonamiento clínico de la IA (para logs y auditoría)