import json
import random
from pathlib import Path
from models import HospitalResources
from dictionary.specialists_constants import VALID_SPECIALISTS
from dictionary.equipment_constants import VALID_EQUIPMENT

class HospitalGenerator:
    """Generador realista de recursos hospitalarios según su nivel de complejidad."""

    @staticmethod
    def generate(tier: str, name: str = None) -> HospitalResources:
        tier = tier.lower()
        if tier not in ["modest", "regional", "elite"]:
            raise ValueError("El tier debe ser 'modest', 'regional' o 'elite'.")

        if not name:
            names = {
                "modest": ["Puesto de Salud Comunitario San José", "Clínica Rural El Centenario", "Centro Médico Local Esperanza"],
                "regional": ["Hospital General de la Ciudad", "Centro Médico Regional San Juan", "Hospital Provincial del Distrito"],
                "elite": ["Hospital Universitario de Alta Complejidad Nivel IV", "Centro Médico Global Vanguardia", "Hospital Metropolitano Elite"]
            }
            name = random.choice(names[tier])

        if tier == "modest":
            standard_beds = random.randint(5, 12)
            trauma_beds = random.randint(1, 2)
            isolation_beds = random.choice([0, 1])
            icu_beds = 0
            operating_rooms = 0

            triage_nurses = random.randint(1, 2)
            general_doctors = random.randint(2, 4)
            intensivists = 0
            anesthesiologists = 0

            med_specs = {k: 0 for k in [
                "cardiologist", "neurologist", "pulmonologist", "gastroenterologist", 
                "nephrologist", "endocrinologist", "hematologist", "oncologist",
                "infectious_disease_specialist", "rheumatologist", "toxicologist"
            ]}
            
            surg_specs = {k: 0 for k in [
                "general_surgeon", "cardiovascular_surgeon", "neurosurgeon", 
                "orthopedic_surgeon", "plastic_surgeon", "burn_surgeon", 
                "maxillofacial_surgeon", "urologist", "otolaryngologist"
            ]}

            pediatricians = random.choice([0, 1])
            pop_specs = {"neonatologist": 0, "obstetrician": 0, "gynecologist": 0, "psychiatrist": 0, "ophthalmologist": 0}

            ventilators = random.randint(0, 1)
            defibrillators = random.randint(1, 2)
            ecmo = 0
            bypass = 0
            crash_carts = random.randint(1, 2)

            ct_scanner = 0
            mri = 0
            x_ray = random.choice([0, 1])
            portable_x_ray = 0
            infusion_pump = random.randint(4, 8) # Agregado para consistencia básica
            ultrasound = random.choice([0, 1])
            ecg = random.randint(1, 2)
            eeg = 0
            fluoroscopy = 0
            
            dialysis = 0
            endoscopy = 0
            hyperbaric = 0
            incubator = 0

        elif tier == "regional":
            standard_beds = random.randint(25, 50)
            trauma_beds = random.randint(3, 6)
            isolation_beds = random.randint(2, 4)
            icu_beds = random.randint(4, 10)
            operating_rooms = random.randint(2, 4)

            triage_nurses = random.randint(3, 6)
            general_doctors = random.randint(6, 12)
            intensivists = random.randint(2, 4)
            anesthesiologists = random.randint(2, 4)

            med_specs = {
                "cardiologist": random.choice([0, 1]),
                "neurologist": random.choice([0, 1]),
                "pulmonologist": random.randint(1, 2),
                "gastroenterologist": random.choice([0, 1]),
                "nephrologist": random.choice([0, 1]),
                "endocrinologist": 0, "hematologist": 0, "oncologist": 0,
                "infectious_disease_specialist": random.choice([0, 1]),
                "rheumatologist": 0, "toxicologist": 0
            }

            surg_specs = {
                "general_surgeon": random.randint(2, 4),
                "cardiovascular_surgeon": 0, "neurosurgeon": 0,
                "orthopedic_surgeon": random.randint(1, 3),
                "plastic_surgeon": 0, "burn_surgeon": 0, "maxillofacial_surgeon": 0,
                "urologist": random.choice([0, 1]),
                "otolaryngologist": random.choice([0, 1])
            }

            pediatricians = random.randint(2, 4)
            pop_specs = {
                "neonatologist": random.choice([0, 1]),
                "obstetrician": random.randint(1, 2),
                "gynecologist": random.randint(1, 2),
                "psychiatrist": random.choice([0, 1]),
                "ophthalmologist": 0
            }

            ventilators = random.randint(4, 8)
            defibrillators = random.randint(3, 6)
            ecmo = 0; bypass = 0
            crash_carts = random.randint(3, 5)

            ct_scanner = random.choice([1, 2])
            mri = 0
            x_ray = random.randint(1, 2)
            portable_x_ray = random.randint(1, 2)
            ultrasound = random.randint(2, 4)
            ecg = random.randint(3, 6)
            eeg = random.choice([0, 1])
            fluoroscopy = random.choice([0, 1])
            
            dialysis = random.randint(0, 2)
            endoscopy = random.choice([0, 1])
            hyperbaric = 0
            incubator = random.randint(1, 3)

        else:
            standard_beds = random.randint(80, 150)
            trauma_beds = random.randint(8, 15)
            isolation_beds = random.randint(6, 12)
            icu_beds = random.randint(20, 40)
            operating_rooms = random.randint(6, 12)

            triage_nurses = random.randint(8, 16)
            general_doctors = random.randint(15, 30)
            intensivists = random.randint(6, 12)
            anesthesiologists = random.randint(6, 12)

            med_specs = {k: random.randint(2, 5) for k in [
                "cardiologist", "neurologist", "pulmonologist", "gastroenterologist", 
                "nephrologist", "endocrinologist", "hematologist", "oncologist",
                "infectious_disease_specialist", "rheumatologist", "toxicologist"
            ]}

            surg_specs = {k: random.randint(1, 4) for k in [
                "general_surgeon", "cardiovascular_surgeon", "neurosurgeon", 
                "orthopedic_surgeon", "plastic_surgeon", "burn_surgeon", 
                "maxillofacial_surgeon", "urologist", "otolaryngologist"
            ]}

            pediatricians = random.randint(5, 10)
            pop_specs = {k: random.randint(2, 5) for k in [
                "neonatologist", "obstetrician", "gynecologist", "psychiatrist", "ophthalmologist"
            ]}

            ventilators = random.randint(20, 50)
            defibrillators = random.randint(10, 20)
            ecmo = random.randint(1, 3)
            bypass = random.randint(1, 3)
            crash_carts = random.randint(8, 15)

            ct_scanner = random.randint(2, 4)
            mri = random.randint(1, 2)
            x_ray = random.randint(3, 6)
            portable_x_ray = random.randint(4, 8)
            ultrasound = random.randint(6, 12)
            ecg = random.randint(8, 16)
            eeg = random.randint(2, 4)
            fluoroscopy = random.randint(1, 2)
            
            dialysis = random.randint(5, 10)
            endoscopy = random.randint(2, 4)
            hyperbaric = random.randint(1, 2)
            incubator = random.randint(5, 10)

        total_doctor_time = general_doctors * 480

        specialists_dict = {spec: 0 for spec in VALID_SPECIALISTS}
        equipment_dict = {equip: 0 for equip in VALID_EQUIPMENT}
        
        specialists_dict.update({
            "triage_nurse": triage_nurses,
            "general_doctor": general_doctors,
            "intensivist": intensivists,
            "anesthesiologist": anesthesiologists,
            **med_specs,
            **surg_specs,
            "pediatrician": pediatricians,
            **pop_specs
        })
        
        equipment_dict.update({
            "ventilator": ventilators,
            "defibrillator": defibrillators,
            "ecmo_machine": ecmo,
            "cardiopulmonary_bypass_machine": bypass,
            "crash_cart": crash_carts,
            "x_ray_machine": x_ray,
            "portable_x_ray": portable_x_ray,
            "ct_scanner": ct_scanner,
            "mri_machine": mri,
            "ultrasound_machine": ultrasound,
            "fluoroscopy_machine": fluoroscopy,
            "ecg_machine": ecg,
            "eeg_machine": eeg,
            "dialysis_machine": dialysis,
            "endoscopy_tower": endoscopy,
            "hyperbaric_chamber": hyperbaric,
            "incubator": incubator
        })

        return HospitalResources(
            hospital_name=name,
            standard_beds_available=standard_beds,
            trauma_beds_available=trauma_beds,
            isolation_beds_available=isolation_beds,
            icu_beds_available=icu_beds,
            operating_rooms_available=operating_rooms,
            available_doctors_time_minutes=total_doctor_time,
            specialists_available=specialists_dict,
            equipment_available=equipment_dict
        )

# ================================================================================
# NUEVA LÓGICA DE GENERACIÓN DE RED COMPATIBLE
# ================================================================================
def generate_hospital_network() -> list[dict]:
    """Genera la red mapeando nombres de hospitales estables a la lógica del HospitalGenerator."""
    
    hospitals_output = []
    
    # Dataset maestro de los 10 hospitales con su ubicación y mapeo de Tier correcto
    hospital_seed_data = [
        {"id": "HOSP-01", "name": "Hospital Central de Urgencias", "location": "Centro", "tier": "elite"},
        {"id": "HOSP-02", "name": "Hospital Metropolitano del Norte", "location": "Zona Norte", "tier": "elite"},
        {"id": "HOSP-03", "name": "Hospital del Sur - Traumatología", "location": "Zona Sur", "tier": "regional"},
        {"id": "HOSP-04", "name": "Hospital Infantil Pediátrico", "location": "Centro", "tier": "regional"},
        {"id": "HOSP-05", "name": "Hospital de Oncología Especializado", "location": "Zona Este", "tier": "modest"},
        {"id": "HOSP-06", "name": "Hospital General Occidental", "location": "Zona Oeste", "tier": "regional"},
        {"id": "HOSP-07", "name": "Hospital Cardiológico Regional", "location": "Centro", "tier": "regional"},
        {"id": "HOSP-08", "name": "Hospital Universitario de Investigación", "location": "Campus", "tier": "elite"},
        {"id": "HOSP-09", "name": "Hospital Comunitario Rural", "location": "Zona Rural", "tier": "modest"},
        {"id": "HOSP-10", "name": "Hospital de Geriatría y Crónicos", "location": "Zona Periurbana", "tier": "modest"},
    ]
    
    for seed in hospital_seed_data:
        # Ejecutar tu generador dinámico para obtener las capacidades reales estructuradas
        resources = HospitalGenerator.generate(tier=seed["tier"], name=seed["name"])
        
        # Estructurar el diccionario final adaptado a formato JSON
        hospital_record = {
            "hospital_id": seed["id"],
            "hospital_name": resources.hospital_name,
            "location": seed["location"],
            "tier": seed["tier"],
            "contact": f"+1-555-{int(seed['id'].split('-')[1]):04d}000",
            
            # Infraestructura (Obtenida directamente de la instancia de HospitalResources)
            "infrastructure": {
                "standard_beds_available": resources.standard_beds_available,
                "trauma_beds_available": resources.trauma_beds_available,
                "isolation_beds_available": resources.isolation_beds_available,
                "icu_beds_available": resources.icu_beds_available,
                "operating_rooms_available": resources.operating_rooms_available,
                "available_doctors_time_minutes": resources.available_doctors_time_minutes
            },
            
            # Especialistas y Equipos perfectos con llaves que coinciden con las constantes globales
            "specialists_available": resources.specialists_available,
            "equipment_available": resources.equipment_available,
            
            # Estado operacional inicial para la simulación
            "operational_status": {
                "is_on_diversion": False,
                "current_occupancy_rate": round(random.uniform(0.55, 0.75), 2),
                "last_updated": "2026-06-07T10:30:00Z"
            }
        }
        hospitals_output.append(hospital_record)
        
    return hospitals_output


def save_hospitals_to_json(hospitals: list[dict], output_path: str = None):
    """Guarda la red estructurada en un archivo JSON."""
    if output_path is None:
        output_path = Path(__file__).parent.parent / "data" / "hospitals.json"
    
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(hospitals, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Red de hospitales guardada exitosamente en: {output_path}")


def print_hospital_summary(hospitals: list[dict]):
    """Imprime resumen en consola para verificar consistencia."""
    print("\n" + "="*80)
    print("🏥 RESUMEN GENERAL DE LA RED HOSPITALARIA GENERADA")
    print("="*80 + "\n")
    
    total_beds = 0
    total_specialists = 0
    
    for hosp in hospitals:
        infra = hosp["infrastructure"]
        total_beds_hosp = (
            infra["standard_beds_available"] +
            infra["trauma_beds_available"] +
            infra["isolation_beds_available"] +
            infra["icu_beds_available"]
        )
        total_beds += total_beds_hosp
        
        total_spec = sum(hosp["specialists_available"].values())
        total_specialists += total_spec
        
        print(f"[{hosp['hospital_id']}] {hosp['hospital_name']}")
        print(f"    Ubicación: {hosp['location']} | Nivel Técnico: {hosp['tier'].upper()}")
        print(f"    Capacidad Camas: {total_beds_hosp} (UCI: {infra['icu_beds_available']}, Trauma: {infra['trauma_beds_available']})")
        print(f"    Minutos de Guardia Médica: {infra['available_doctors_time_minutes']} min")
        print(f"    Especialistas Clínicos: {total_spec} asignados.")
        print(f"    Tomógrafos (CT): {hosp['equipment_available'].get('ct_scanner', 0)} | Respiradores: {hosp['equipment_available'].get('ventilator', 0)}")
        print("-" * 80)
        
    print(f"📊 TOTALES DE LA RED CARGADA:")
    print(f"    Total Hospitales: {len(hospitals)}")
    print(f"    Total de Camas Operativas: {total_beds}")
    print(f"    Total Personal Especializado: {total_specialists}\n")


if __name__ == "__main__":
    print("🔄 Iniciando generación híbrida de infraestructura de salud...")
    network = generate_hospital_network()
    print_hospital_summary(network)
    save_hospitals_to_json(network)
