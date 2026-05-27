from dataclasses import dataclass, field
from typing import List, Dict
from datetime import datetime
from chronic_disease_weights import CHRONIC_DISEASE_WEIGHTS

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

    standard_beds_available: int      # Camillas normales de urgencias (Pacientes amarillos/verdes)
    trauma_beds_available: int        # Boxes de reanimación (Solo para pacientes "1_Resuscitation")
    isolation_beds_available: int     # Habitaciones de presión negativa (Si patient.is_isolated == True)
    icu_beds_available: int           # Camas de Cuidados Intensivos (Post-cirugía o críticos)
    operating_rooms_available: int    # Quirófanos libres
   

    # Medicos y especialistas
    triage_nurses_available: int      # Atienden la puerta, determinan el AVPU inicial
    general_doctors_available: int    # Médicos de urgencias (Filtro inicial)
    available_doctors_time_minutes: int # Capacidad de tiempo global para el turno
    intensivists_available: int       # Médicos de UCI (Cruciales para pacientes críticos)
    anesthesiologists_available: int  # Indispensables para quirófano o intubaciones difíciles
    
    cardiologists_available: int      # Infartos, arritmias graves
    neurologists_available: int       # ACV, convulsiones
    pulmonologists_available: int     # Fallo respiratorio severo
    gastroenterologists_available: int # Sangrado digestivo masivo
    nephrologists_available: int      # Falla renal aguda
    endocrinologists_available: int   # Cetoacidosis diabética, crisis tiroidea
    hematologists_available: int      # Trastornos de coagulación severos
    oncologists_available: int        # Complicaciones oncológicas agudas
    infectious_disease_specialists_available: int # Sepsis, infecciones raras
    rheumatologists_available: int    # Brotes autoinmunes severos
    toxicologists_available: int      # Sobredosis, envenenamientos
    
    general_surgeons_available: int   # Apendicitis, traumas abdominales
    cardiovascular_surgeons_available: int # Aneurismas, traumas de grandes vasos
    neurosurgeons_available: int      # Traumas craneales, hematomas cerebrales
    orthopedic_surgeons_available: int # Fracturas expuestas, poli-traumatismos
    plastic_surgeons_available: int   # Reconstrucción de tejidos blandos
    burn_surgeons_available: int      # Cirujanos especialistas en grandes quemados
    maxillofacial_surgeons_available: int # Traumas faciales severos
    urologists_available: int         # Cálculos renales obstructivos, trauma pélvico
    otolaryngologists_available: int  # Obstrucciones severas de vía aérea superior
    
    pediatricians_available: int      # Pacientes < 18 años
    neonatologists_available: int     # Recién nacidos en estado crítico
    obstetricians_available: int      # Pacientes embarazadas
    gynecologists_available: int      # Emergencias ginecológicas
    psychiatrists_available: int      # Brotes psicóticos, riesgo suicida
    ophthalmologists_available: int   # Traumas oculares severos
    

    # Equipamiento crítico para soporte vital, diagnóstico y procedimientos específicos
    ventilators_available: int        # Respiradores artificiales
    defibrillators_available: int     # Desfibriladores para paros cardíacos
    ecmo_machines_available: int      # Oxigenación por membrana extracorpórea
    cardiopulmonary_bypass_machines_available: int # Máquinas de circulación extracorpórea
    crash_carts_available: int        # Carros de paro equipados

    ct_scanners_available: int        # Tomógrafos (TAC)
    mri_machines_available: int       # Resonancia magnética
    x_ray_machines_available: int     # Salas de Rayos X fijas
    portable_x_rays_available: int    # Máquinas de Rayos X portátiles
    ultrasound_machines_available: int # Ecógrafos
    ecg_machines_available: int       # Electrocardiógrafos
    eeg_machines_available: int       # Electroencefalogramas (actividad cerebral)
    fluoroscopy_machines_available: int # Fluoroscopia (Rayos X en tiempo real)
    
    dialysis_machines_available: int  # Máquinas de diálisis
    endoscopy_towers_available: int   # Torres de endoscopia (procedimientos gastrointestinales)
    hyperbaric_chambers_available: int # Cámaras hiperbáricas (intoxicación CO)
    incubators_available: int         # Incubadoras para el área de neonatología

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