import random
import uuid
from datetime import datetime, timedelta
from models import Patient, Vitals
from chronic_disease_weights import CHRONIC_DISEASE_WEIGHTS

# Listas básicas para generar identidades
FIRST_NAMES = ["Carlos", "Ana", "Luis", "Maria", "Jorge", "Elena", "Miguel", "Lucia", "Diego", "Sofia", "Darian", "Laura"]
LAST_NAMES = ["Garcia", "Martinez", "Lopez", "Gonzalez", "Perez", "Rodriguez", "Sanchez", "Ramirez", "Cruz", "Gomez"]

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
            
            # Dejamos notas de triaje genéricas por ahora (luego las mejoraremos)
            triage_notes=f"Paciente llega con dolor nivel {vitals.pain_level}. FC: {vitals.heart_rate_bpm}.", 
            medical_history_text="Sin historial relevante." if not patient_diseases else f"Paciente con historial de {', '.join(patient_diseases)}.",
            initial_triage_category=initial_triage
        )
        patients.append(patient)
        
    return patients



if __name__ == "__main__":
    print("🏥 Generando flujo de pacientes en Urgencias...\n")
    mock_db = generate_mock_patients(5) # Generamos 5 pacientes
    
    for p in mock_db:
        embarazo = " (Embarazada)" if p.is_pregnant else ""
        print(f"[{p.initial_triage_category}] ID: {p.patient_id} | {p.first_name} {p.last_name}, {p.age} años{embarazo}")
        print(f"   -> FC: {p.vitals.heart_rate_bpm} lpm | SpO2: {p.vitals.oxygen_saturation_pct}% | GCS: {p.vitals.glasgow_coma_scale}")
        print(f"   -> Enfermedades Crónicas: {p.chronic_diseases if p.chronic_diseases else 'Ninguna'}")
        print("-" * 60)