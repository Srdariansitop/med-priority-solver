import json
import random
import os
import sys
from pathlib import Path
from dataclasses import is_dataclass, asdict

# Asegurar que el directorio raíz del proyecto (src) esté en el sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from generator.patient_generator import generate_mock_patients

HOSPITAL_IDS = [
    "HOSP-01", "HOSP-02", "HOSP-03", "HOSP-04", "HOSP-05",
    "HOSP-06", "HOSP-07", "HOSP-08", "HOSP-09", "HOSP-10"
]

def safe_to_dict(obj):
    """Convierte de forma segura cualquier objeto de Python a un diccionario para JSON."""
    if hasattr(obj, 'model_dump'):
        return obj.model_dump()
    elif hasattr(obj, 'dict'):
        return obj.dict()
    elif is_dataclass(obj):
        return asdict(obj)
    else:
        # Si es una clase normal de Python, extraemos sus atributos
        d = vars(obj).copy()
        # Si tiene atributos anidados como 'vitals', también los convertimos
        if 'vitals' in d and hasattr(d['vitals'], '__dict__'):
            d['vitals'] = vars(d['vitals'])
        return d

def generate_and_save_patients(num_patients: int = 100, output_file: str = "data/patients.json"):
    print(f"🔄 Solicitando {num_patients} notas de triaje a Groq API... (Procesando lote optimizado)")
    
    patients = generate_mock_patients(num_patients)
    
    patients_data = []
    for p in patients:
        p_dict = safe_to_dict(p)
        
        # Formatear la fecha de datetime a string ISO 8601
        if 'arrival_time' in p_dict and p_dict['arrival_time']:
            if hasattr(p_dict['arrival_time'], 'isoformat'):
                p_dict['arrival_time'] = p_dict['arrival_time'].isoformat()
            
        # NUEVA LÓGICA:
        # 1. Elegimos un hospital de llegada aleatorio
        random_hospital = random.choice(HOSPITAL_IDS)
        
        # 2. Asignamos ese hospital a la llegada y al estado actual
        p_dict["arrival_hospital_id"] = random_hospital
        p_dict["current_hospital_id"] = random_hospital
        
        # 3. Ponemos assigned_hospital_id en None para que tu solver externo lo gestione
        p_dict["assigned_hospital_id"] = None
        
        patients_data.append(p_dict)
        
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(patients_data, f, indent=2, ensure_ascii=False)
        
    print(f"✅ ¡Éxito! {num_patients} pacientes listos para procesar en: {output_file}")

if __name__ == "__main__":
    generate_and_save_patients(100)