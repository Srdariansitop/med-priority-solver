import random
import uuid
from datetime import datetime, timedelta
from models import Patient, Vitals
from dictionary.chronic_disease_weights import CHRONIC_DISEASE_WEIGHTS

# Listas básicas para generar identidades
FIRST_NAMES = ["Carlos", "Ana", "Luis", "Maria", "Jorge", "Elena", "Miguel", "Lucia", "Diego", "Sofia", "Darian", "Laura"]
LAST_NAMES = ["Garcia", "Martinez", "Lopez", "Gonzalez", "Perez", "Rodriguez", "Sanchez", "Ramirez", "Cruz", "Gomez"]

CRITICAL_NOTES = [
    "Paciente refiere dolor opresivo en región esternal. Menciona que siente 'un elefante sentado en el pecho' que se irradia a mandíbula y brazo izquierdo. Disnea evidente.",
    "Traído por familiares tras sufrir pérdida súbita del conocimiento (síncope) en vía pública. Se observa desorientado, pálido y con sudoración profusa.",
    "Dificultad respiratoria severa de inicio súbito. El paciente utiliza músculos accesorios para respirar y apenas puede articular frases completas.",
    "Paciente ingresa con agitación psicomotriz severa, lenguaje incoherente y agresividad. Enfermería reporta ideación suicida activa y riesgo de autolisis."
]

NORMAL_NOTES = [
    "Paciente acude por cefalea leve de 3 días de evolución que no cede con analgésicos comunes. Sin signos de focalización neurológica.",
    "Ingresa por traumatismo en tobillo derecho tras tropiezo. Presenta leve edema, dolor a la palpación, pero deambula por sus propios medios.",
    "Refiere congestión nasal, odinofagia y tos no productiva de 48 horas de evolución. Refiere malestar general leve.",
    "Dolor abdominal difuso tipo cólico de baja intensidad, asociado a aparente ingesta de alimentos en mal estado. Sin signos de abdomen agudo."
]

DISEASE_DESCRIPTIONS = {
    "chronic_kidney_disease_stage_5": "Insuficiencia Renal Crónica Estadio 5 en tratamiento de hemodiálisis (Lunes, Miércoles y Viernes).",
    "leukemia": "Leucemia Mieloide Aguda en tratamiento con quimioterapia activa (último ciclo hace 5 días).",
    "schizophrenia": "Trastorno esquizofrénico de larga evolución. Reporta abandono de tratamiento farmacológico hace semanas.",
    "bronchiectasis": "Bronquiectasias infectadas recurrentes. Dependiente de oxígeno domiciliario nocturno a 2L/min.",
    "major_depressive_disorder": "Trastorno depresivo mayor con antecedentes de intentos previos de autolisis.",
    "polymyalgia_rheumatica": "Polimialgia reumática en tratamiento con corticoides sistémicos.",
    "hypertension": "Hipertensión arterial bajo tratamiento médico irregular.",
    "diabetes_type_2": "Diabetes Mellitus Tipo 2 con mal control metabólico."
}


def generate_random_vitals(is_critical: bool) -> Vitals:
    """Genera signos vitales coherentes. Si es crítico, los valores son extremos."""
    if is_critical:
        # Signos vitales alterados (Ej: Shock, ACV, Infarto, Trauma severo)
        return Vitals(
            heart_rate_bpm=random.choice([random.randint(30, 50), random.randint(130, 180)]),
            oxygen_saturation_pct=random.randint(75, 92),
            systolic_bp=random.choice([random.randint(70, 85), random.randint(180, 220)]),
            diastolic_bp=random.choice([random.randint(40, 50), random.randint(110, 130)]),
            temperature_c=round(random.uniform(35.0, 40.5), 1),
            pain_level=random.randint(8, 10),
            consciousness_level=random.choice(["Voice", "Pain", "Unresponsive"]),
            glasgow_coma_scale=random.randint(3, 12)
        )
    else:
        # Signos vitales normales o levemente alterados (Ej: Resfriado, esguince)
        return Vitals(
            heart_rate_bpm=random.randint(60, 100),
            oxygen_saturation_pct=random.randint(95, 100),
            systolic_bp=random.randint(110, 130),
            diastolic_bp=random.randint(70, 85),
            temperature_c=round(random.uniform(36.5, 37.8), 1),
            pain_level=random.randint(0, 5),
            consciousness_level="Alert",
            glasgow_coma_scale=15
        )

def generate_mock_patients(num_patients: int = 10) -> list[Patient]:
    """Genera una lista de pacientes aleatorios llegando a urgencias."""
    patients = []
    now = datetime.now()
    
    # Obtenemos la lista de enfermedades de tu diccionario
    possible_diseases = list(CHRONIC_DISEASE_WEIGHTS.keys())
    
    for _ in range(num_patients):
        age = random.randint(1, 90)
        gender = random.choice(["M", "F", "Other"])
        
        # 20% de probabilidad de que el paciente llegue en estado crítico
        is_critical = random.random() < 0.2 
        
        # Le asignamos entre 0 y 3 enfermedades crónicas aleatorias
        num_diseases = random.randint(0, 3)
        patient_diseases = random.sample(possible_diseases, num_diseases)
        
        vitals = generate_random_vitals(is_critical)
        
        # Estimación cruda del triaje inicial basado en la gravedad
        if is_critical:
            initial_triage = random.choice(["1_Resuscitation", "2_Emergent"])
        else:
            initial_triage = random.choice(["3_Urgent", "4_Standard", "5_Routine"])

        if is_critical:
            triage_notes = random.choice(CRITICAL_NOTES)
        else:
            triage_notes = random.choice(NORMAL_NOTES)

        if not patient_diseases:
            medical_history_text = "Sin historial médico de relevancia."
        else:
            history_pieces = [DISEASE_DESCRIPTIONS.get(d, f"Antecedente diagnosticado de {d.replace('_', ' ')}.") for d in patient_diseases]
            medical_history_text = " ".join(history_pieces)

        patient = Patient(
            patient_id=f"PAT-{uuid.uuid4().hex[:6].upper()}",
            first_name=random.choice(FIRST_NAMES),
            last_name=random.choice(LAST_NAMES),
            age=age,
            gender=gender,
            insurance_type=random.choice(["Public", "Private", "None"]),
            # Simulamos que llegaron en algún momento de las últimas 2 horas
            arrival_time=now - timedelta(minutes=random.randint(0, 120)), 
            is_pregnant=(gender == "F" and 15 <= age <= 45 and random.random() < 0.05),
            
            vitals=vitals,
            chronic_diseases=patient_diseases,
            
            # Ahora inyectamos las notas e historial enriquecidos semánticamente
            triage_notes=triage_notes, 
            medical_history_text=medical_history_text,
            initial_triage_category=initial_triage
        )
        patients.append(patient)
        
    return patients