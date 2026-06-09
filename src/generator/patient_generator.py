import os
import random
import uuid
import asyncio
from datetime import datetime, timedelta
from models import Patient, Vitals
from utils.groq_client import get_async_client
from dictionary.chronic_disease_weights import CHRONIC_DISEASE_WEIGHTS, CHRONIC_DISEASE_AGE_RANGES

client = get_async_client()

# Procesamos de 1 en 1 para evitar por completo el límite estricto de 8000 TPM
MAX_CONCURRENT_REQUESTS = 1
semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)

SYSTEM_PROMPT = """Eres un médico de triaje en urgencias bajo extrema presión de tiempo.
Tu única tarea es redactar la nota clínica de ingreso del paciente basándote en los datos proporcionados.

REGLAS ESTRICTAS DE RESPUESTA (FALLO CRÍTICO SI NO SE CUMPLEN):
1. Responde ÚNICAMENTE con el texto de la nota médica. Cero palabras adicionales.
2. NO saludes, NO te despidas, NO confirmes la orden, NO uses viñetas ni formato Markdown.
3. Usa terminología médica precisa, directa y telegráfica (máximo 2 a 3 oraciones cortas).
4. Refleja la congruencia clínica: si los signos vitales son críticos, la nota debe sonar urgente y grave. Si son normales, refleja estabilidad o síntomas leves.
5. IMPORTANTE: Termina SIEMPRE la nota con una breve conclusión sobre el estado del paciente o un punto final claro (ej: "Requiere evaluación urgente" o "Estado estable, seguimiento rutinario").
6. Evita palabras técnicas como "score", "escala", "parámetros". Escribe de forma directa como si estuvieras describiendo al paciente en la camilla, no un reporte.
"""

# =====================================================================
# DATOS DE IDENTIDAD
# =====================================================================
MALE_NAMES = ["Carlos", "Luis", "Jorge", "Miguel", "Diego", "Darian", "Alejandro", "Mateo", "Daniel", "Hugo", "Martin", "Lucas", "Marcos", "Juan", "Pedro", "Andres", "Fernando", "Gabriel"]
FEMALE_NAMES = ["Ana", "Maria", "Elena", "Lucia", "Sofia", "Laura", "Valentina", "Camila", "Valeria", "Martina", "Daniela", "Julia", "Paula", "Emma", "Carmen", "Isabella", "Victoria", "Alba"]
LAST_NAMES = ["Garcia", "Martinez", "Lopez", "Gonzalez", "Perez", "Rodriguez", "Sanchez", "Ramirez", "Cruz", "Gomez", "Fernandez", "Ruiz", "Diaz", "Alvarez", "Romero", "Torres", "Navarro"]

DISEASE_DESCRIPTIONS = {
    "chronic_kidney_disease_stage_5": "Insuficiencia Renal Crónica Estadio 5 en tratamiento de hemodiálisis.",
    "leukemia": "Leucemia Mieloide Aguda en tratamiento activo.",
    "schizophrenia": "Trastorno esquizofrénico de larga evolución.",
    "bronchiectasis": "Bronquiectasias infectadas recurrentes. O2 dependiente.",
    "major_depressive_disorder": "Trastorno depresivo mayor.",
    "hypertension": "HTA mal controlada.",
    "diabetes_type_2": "DM2 con mal control metabólico."
}

def generate_random_vitals(is_critical: bool) -> Vitals:
    """Genera signos vitales numéricos base con validación fisiológica."""
    if is_critical:
        is_hypotensive = random.random() < 0.5
        if is_hypotensive:
            systolic_bp = random.randint(70, 85)
            diastolic_bp = random.randint(40, 50)
        else:
            systolic_bp = random.randint(180, 220)
            diastolic_bp = random.randint(100, 130)
        
        return Vitals(
            heart_rate_bpm=random.choice([random.randint(30, 50), random.randint(130, 180)]),
            oxygen_saturation_pct=random.randint(75, 92),
            systolic_bp=systolic_bp,
            diastolic_bp=diastolic_bp,
            temperature_c=round(random.uniform(35.0, 40.5), 1),
            pain_level=random.randint(8, 10),
            consciousness_level=random.choice(["Voice", "Pain", "Unresponsive"]),
            glasgow_coma_scale=random.randint(3, 12)
        )
    else:
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

def generate_burst_arrivals(num_patients: int) -> list[datetime]:
    """Simula patrones de llegada aleatorios o ráfagas."""
    now = datetime.now()
    times = []
    is_burst_event = random.random() < 0.3
    
    if is_burst_event:
        burst_size = int(num_patients * 0.6)
        burst_time = now - timedelta(minutes=random.randint(30, 90))
        
        for _ in range(burst_size):
            times.append(burst_time + timedelta(minutes=random.randint(0, 5)))
        for _ in range(num_patients - burst_size):
            times.append(now - timedelta(minutes=random.randint(0, 120)))
    else:
        for _ in range(num_patients):
            times.append(now - timedelta(minutes=random.randint(0, 120)))
            
    random.shuffle(times)
    return times

async def fetch_triage_note(patient_data: dict) -> str:
    """Llamada asíncrona a Groq con manejo estricto de Rate Limits (429) y Semáforos."""
    vitals = patient_data["vitals"]
    prompt = (
        f"Paciente: Edad {patient_data['age']}, Género {patient_data['gender']}. "
        f"Gravedad general esperada: {'CRÍTICA/EMERGENCIA' if patient_data['is_critical'] else 'ESTABLE/RUTINA'}. "
        f"Signos Vitales: FC {vitals.heart_rate_bpm} lpm, SatO2 {vitals.oxygen_saturation_pct}%, "
        f"PA {vitals.systolic_bp}/{vitals.diastolic_bp} mmHg, Temp {vitals.temperature_c}°C, "
        f"Dolor {vitals.pain_level}/10, Glasgow {vitals.glasgow_coma_scale}/15, Estado: {vitals.consciousness_level}. "
        f"Antecedentes: {patient_data['medical_history_text']}"
    )

    max_retries = 5
    base_wait_time = 4.5  # Tiempo prudencial óptimo basado en logs

    for attempt in range(max_retries):
        async with semaphore:
            try:
                completion = await client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.4,
                    max_tokens=150  # Subido a 150 para que las notas médicas se generen completas
                )
                return completion.choices[0].message.content.strip()
                
            except Exception as e:
                error_str = str(e)
                if "429" in error_str or "rate_limit" in error_str:
                    wait_time = base_wait_time + random.uniform(0.5, 1.5)
                    print(f"⚠️ [429 Rate Limit] Límite de tokens alcanzado. Esperando {wait_time:.2f}s antes de reintentar...")
                    await asyncio.sleep(wait_time)
                else:
                    print(f"❌ Error inesperado en la API de Groq: {e}")
                    break

    return "Nota de triaje no disponible por fallo del sistema de dictado automático."

async def generate_mock_patients_async(num_patients: int = 10) -> list[Patient]:
    """Generador principal asíncrono optimizado."""
    patients = []
    all_possible_diseases = list(CHRONIC_DISEASE_WEIGHTS.keys())
    arrival_times = generate_burst_arrivals(num_patients)
    
    patient_payloads = []
    
    for i in range(num_patients):
        age = random.randint(1, 90)
        gender = random.choice(["M", "F", "Other"])
        first_name = random.choice(MALE_NAMES) if gender == "M" else random.choice(FEMALE_NAMES) if gender == "F" else random.choice(MALE_NAMES + FEMALE_NAMES)
        last_name = random.choice(LAST_NAMES)
        
        is_critical = random.random() < 0.2
        vitals = generate_random_vitals(is_critical)
        
        valid_diseases = [d for d in all_possible_diseases if CHRONIC_DISEASE_AGE_RANGES.get(d, (18, 120))[0] <= age <= CHRONIC_DISEASE_AGE_RANGES.get(d, (18, 120))[1]]
        patient_diseases = random.sample(valid_diseases, random.randint(0, min(3, len(valid_diseases))))
        
        medical_history_text = "Sin antecedentes relevantes." if not patient_diseases else " ".join([DISEASE_DESCRIPTIONS.get(d, f"{d.replace('_', ' ').title()}.") for d in patient_diseases])

        if is_critical:
            initial_triage = random.choice(["1_Resuscitation", "2_Emergent"])
        else:
            initial_triage = random.choice(["3_Urgent", "4_Standard", "5_Routine"])

        patient_payloads.append({
            "patient_id": f"PAT-{uuid.uuid4().hex[:6].upper()}",
            "first_name": first_name,
            "last_name": last_name,
            "age": age,
            "gender": gender,
            "arrival_time": arrival_times[i],
            "is_pregnant": (gender == "F" and 15 <= age <= 45 and random.random() < 0.05),
            "insurance_type": random.choice(["Public", "Private", "None"]),
            "vitals": vitals,
            "chronic_diseases": patient_diseases,
            "medical_history_text": medical_history_text,
            "initial_triage_category": initial_triage,
            "is_critical": is_critical
        })

    tasks = [fetch_triage_note(payload) for payload in patient_payloads]
    generated_notes = await asyncio.gather(*tasks)

    for payload, note in zip(patient_payloads, generated_notes):
        patient = Patient(
            patient_id=payload["patient_id"],
            first_name=payload["first_name"],
            last_name=payload["last_name"],
            age=payload["age"],
            gender=payload["gender"],
            insurance_type=payload["insurance_type"],
            arrival_time=payload["arrival_time"],
            is_pregnant=payload["is_pregnant"],
            vitals=payload["vitals"],
            chronic_diseases=payload["chronic_diseases"],
            triage_notes=note, 
            medical_history_text=payload["medical_history_text"],
            initial_triage_category=payload["initial_triage_category"]
        )
        patients.append(patient)
        
    return patients

def generate_mock_patients(num_patients: int = 10) -> list[Patient]:
    """Wrapper síncrono para ejecutar el bucle de eventos."""
    return asyncio.run(generate_mock_patients_async(num_patients))