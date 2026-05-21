from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import datetime

@dataclass
class HospitalResources:
    """Define los límites físicos y de personal del entorno."""
    hospital_name: str
    total_beds: int
    available_beds: int
    total_doctors: int
    available_doctors_time_minutes: int  # Capacidad total en minutos de atención

@dataclass
class Vitals:
    """Signos vitales estructurados para cálculo matemático rápido."""
    heart_rate_bpm: int          # Frecuencia cardíaca (ej. 80)
    oxygen_saturation_pct: int   # SpO2 (ej. 98)
    systolic_bp: int             # Presión sistólica (ej. 120)
    diastolic_bp: int            # Presión diastólica (ej. 80)
    temperature_c: float         # Temperatura en Celsius (ej. 37.5)
    pain_level: int              # Escala del 1 al 10
    
    # ==========================================
    # NUEVAS VARIABLES CLÍNICAS ADICIONALES
    # ==========================================
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
    
    # Nuevas variables demográficas de alto impacto clínico:
    is_pregnant: bool = False    # Las pacientes embarazadas tienen prioridad de triaje mandatoria
    is_isolated: bool = False    # ¿Requiere aislamiento por sospecha de virus/bacteria contagiosa?
    
    # 2. Datos Estructurados Clínicos (Para tu algoritmo base)
    vitals: Vitals
    chronic_diseases: List[str] = field(default_factory=list)  # Ej: ["diabetes_type_2", "hypertension"]
    reported_symptoms: List[str] = field(default_factory=list) # Síntomas principales: ["chest_pain", "syncope"]
    allergies: List[str] = field(default_factory=list)         # Alertas críticas de seguridad (ej: ["penicillin"])
    
    # Clasificación inicial protocolar (Sistema Mánchester / Emergencia)
    # Valores sugeridos: "1_Resuscitation" (Rojo), "2_Emergent" (Naranja), "3_Urgent" (Amarillo), "4_Standard" (Verde), "5_Routine" (Azul)
    initial_triage_category: str = "3_Urgent"
    
    # 3. Datos No Estructurados (Para el procesamiento del LLM)
    triage_notes: str            # Texto libre escrito por enfermería al llegar (Ej: "Sufrió desmayo de 2 min...")
    medical_history_text: str    # Resumen del historial médico previo
    
    # 4. Variables Calculadas por el Sistema (Inicializadas en 0 / 1.0)
    base_urgency_score: float = 0.0      # Calculado usando solo los signos vitales y algoritmos base
    llm_context_modifier: float = 1.0    # El LLM lo ajusta (ej. 1.5 si detecta riesgo oculto en notas)
    final_priority_score: float = 0.0    # Puntuación final para el algoritmo de optimización
    
    # 5. Requerimientos de Recursos (Variables para el optimizador)
    needs_bed: int = 1                   # 1 si requiere cama, 0 si es consulta rápida/ambulatorio
    doctor_time_estimated_min: int = 30  # Minutos estimados de atención requerida


# =====================================================================
# TU DICCIONARIO GLOBAL DE PESOS PARA ENFERMEDADES CRÓNICAS (INTACTO)
# =====================================================================
CHRONIC_DISEASE_WEIGHTS: Dict[str, float] = {
    # =========================
    # DIABETES Y METABÓLICAS
    # =========================
    "diabetes_type_1": 1.8,
    "diabetes_type_2": 1.4,
    "prediabetes": 1.1,
    "gestational_diabetes_history": 1.2,
    "metabolic_syndrome": 1.6,
    "obesity_class_1": 1.2,
    "obesity_class_2": 1.5,
    "obesity_class_3": 2.0,
    "hyperlipidemia": 1.2,
    "hypercholesterolemia": 1.2,
    "hypertriglyceridemia": 1.3,
    "gout": 1.4,
    "osteoporosis": 1.5,
    "osteopenia": 1.2,

    # =========================
    # CARDIOVASCULARES
    # =========================
    "hypertension": 1.2,
    "resistant_hypertension": 1.8,
    "coronary_artery_disease": 2.4,
    "heart_failure": 3.2,
    "congestive_heart_failure": 3.3,
    "atrial_fibrillation": 2.0,
    "arrhythmia": 1.8,
    "peripheral_artery_disease": 2.1,
    "ischemic_heart_disease": 2.5,
    "cardiomyopathy": 2.7,
    "valvular_heart_disease": 2.2,
    "history_of_myocardial_infarction": 2.8,
    "stroke_history": 3.0,
    "transient_ischemic_attack": 2.0,
    "aneurysm": 2.7,
    "pulmonary_hypertension": 3.1,

    # =========================
    # RESPIRATORIAS
    # =========================
    "asthma": 1.5,
    "severe_asthma": 2.2,
    "copd": 2.2,
    "chronic_bronchitis": 2.0,
    "emphysema": 2.3,
    "sleep_apnea": 1.7,
    "pulmonary_fibrosis": 3.0,
    "cystic_fibrosis": 3.5,
    "bronchiectasis": 2.4,
    "interstitial_lung_disease": 3.0,

    # =========================
    # RENALES Y UROLÓGICAS
    # =========================
    "chronic_kidney_disease_stage_1": 1.5,
    "chronic_kidney_disease_stage_2": 1.8,
    "chronic_kidney_disease_stage_3": 2.5,
    "chronic_kidney_disease_stage_4": 3.2,
    "chronic_kidney_disease_stage_5": 4.0,
    "kidney_failure": 4.2,
    "dialysis_dependent": 4.5,
    "nephrotic_syndrome": 2.4,
    "polycystic_kidney_disease": 2.3,
    "chronic_urinary_retention": 1.8,

    # =========================
    # NEUROLÓGICAS
    # =========================
    "epilepsy": 1.8,
    "parkinsons_disease": 3.0,
    "alzheimers_disease": 3.5,
    "dementia": 3.2,
    "multiple_sclerosis": 3.0,
    "amyotrophic_lateral_sclerosis": 4.5,
    "migraine_chronic": 1.5,
    "neuropathy": 1.8,
    "peripheral_neuropathy": 1.9,
    "cerebral_palsy": 3.0,
    "huntingtons_disease": 4.0,
    "myasthenia_gravis": 3.2,
    "spinal_cord_injury": 3.4,
    "autonomic_dysfunction": 2.3,

    # =========================
    # AUTOINMUNES / REUMÁTICAS
    # =========================
    "rheumatoid_arthritis": 2.1,
    "systemic_lupus_erythematosus": 3.0,
    "sjogrens_syndrome": 2.0,
    "ankylosing_spondylitis": 2.2,
    "psoriatic_arthritis": 2.0,
    "vasculitis": 3.1,
    "scleroderma": 3.3,
    "sarcoidosis": 2.4,
    "celiac_disease": 1.5,
    "crohns_disease": 2.5,
    "ulcerative_colitis": 2.4,
    "fibromyalgia": 1.7,
    "chronic_fatigue_syndrome": 2.0,
    "polymyalgia_rheumatica": 2.1,

    # =========================
    # ENDOCRINAS
    # =========================
    "hypothyroidism": 1.2,
    "hyperthyroidism": 1.5,
    "hashimotos_thyroiditis": 1.5,
    "graves_disease": 1.8,
    "adrenal_insufficiency": 2.7,
    "cushings_syndrome": 2.8,
    "pituitary_disorder": 2.2,
    "acromegaly": 2.5,

    # =========================
    # HEPÁTICAS Y DIGESTIVAS
    # =========================
    "chronic_hepatitis_b": 2.3,
    "chronic_hepatitis_c": 2.5,
    "cirrhosis": 3.5,
    "fatty_liver_disease": 1.5,
    "nonalcoholic_steatohepatitis": 2.2,
    "chronic_pancreatitis": 2.8,
    "gastroesophageal_reflux_disease": 1.2,
    "irritable_bowel_syndrome": 1.3,
    "peptic_ulcer_disease": 1.6,

    # =========================
    # MENTALES Y PSIQUIÁTRICAS
    # =========================
    "major_depressive_disorder": 2.0,
    "generalized_anxiety_disorder": 1.6,
    "bipolar_disorder": 2.5,
    "schizophrenia": 3.0,
    "post_traumatic_stress_disorder": 2.2,
    "obsessive_compulsive_disorder": 2.0,
    "attention_deficit_hyperactivity_disorder": 1.4,
    "autism_spectrum_disorder": 2.0,
    "chronic_insomnia": 1.5,
    "substance_use_disorder": 2.8,
    "alcohol_use_disorder": 2.5,

    # =========================
    # ONCOLÓGICAS
    # =========================
    "active_cancer": 4.0,
    "metastatic_cancer": 5.0,
    "breast_cancer_history": 2.0,
    "lung_cancer_history": 2.5,
    "colon_cancer_history": 2.2,
    "prostate_cancer_history": 1.8,
    "leukemia": 4.2,
    "lymphoma": 4.0,
    "multiple_myeloma": 4.3,

    # =========================
    # HEMATOLÓGICAS
    # =========================
    "anemia_chronic": 1.5,
    "iron_deficiency_anemia": 1.3,
    "sickle_cell_disease": 3.2,
    "thalassemia": 2.5,
    "hemophilia": 3.0,
    "chronic_coagulation_disorder": 2.6,

    # =========================
    # INMUNOLÓGICAS / INFECCIOSAS
    # =========================
    "hiv": 3.0,
    "aids": 4.0,
    "immunodeficiency": 3.0,
    "long_covid": 2.2,
    "chronic_lyme_disease": 2.0,
    "tuberculosis_chronic": 3.0,

    # =========================
    # DERMATOLÓGICAS
    # =========================
    "psoriasis": 1.7,
    "eczema_chronic": 1.4,
    "hidradenitis_suppurativa": 2.3,
    "chronic_urticaria": 1.5,

    # =========================
    # OFTALMOLÓGICAS
    # =========================
    "glaucoma": 1.8,
    "macular_degeneration": 2.0,
    "diabetic_retinopathy": 2.3,
    "chronic_blindness": 3.0,

    # =========================
    # AUDITIVAS
    # =========================
    "hearing_loss_chronic": 1.5,
    "tinnitus_chronic": 1.4,
    "menieres_disease": 2.0,

    # =========================
    # MUSCULOESQUELÉTICAS
    # =========================
    "osteoarthritis": 1.8,
    "degenerative_disc_disease": 2.0,
    "chronic_back_pain": 1.8,
    "scoliosis": 1.6,
    "muscular_dystrophy": 3.5,

    # =========================
    # GENÉTICAS Y CONGÉNITAS
    # =========================
    "down_syndrome": 2.5,
    "marfan_syndrome": 2.4,
    "ehlers_danlos_syndrome": 2.6,
    "turner_syndrome": 2.3,

    # =========================
    # OTRAS ENFERMEDADES CRÓNICAS
    # =========================
    "chronic_pain_syndrome": 2.0,
    "malnutrition_chronic": 2.3,
    "frailty_syndrome": 2.8,
    "wheelchair_dependency": 2.0,
    "organ_transplant_history": 3.5,
    "chronic_inflammation": 1.8,
    "pressure_ulcers_chronic": 2.2,
}