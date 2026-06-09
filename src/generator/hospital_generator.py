import random
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

        # 1. Definición de Nombres por Defecto si no se provee uno
        if not name:
            names = {
                "modest": ["Puesto de Salud Comunitario San José", "Clínica Rural El Centenario", "Centro Médico Local Esperanza"],
                "regional": ["Hospital General de la Ciudad", "Centro Médico Regional San Juan", "Hospital Provincial del Distrito"],
                "elite": ["Hospital Universitario de Alta Complejidad Nivel IV", "Centro Médico Global Vanguardia", "Hospital Metropolitano Elite"]
            }
            name = random.choice(names[tier])

        # 2. Configuración de Recursos por Rangos según el Tier
        if tier == "modest":
            # --- INFRAESTRUCTURA MODESTA ---
            # Camas y Boxes
            standard_beds = random.randint(5, 12)
            trauma_beds = random.randint(1, 2)
            isolation_beds = random.choice([0, 1])
            icu_beds = 0
            operating_rooms = 0

            # Personal Base
            triage_nurses = random.randint(1, 2)
            general_doctors = random.randint(2, 4)
            intensivists = 0
            anesthesiologists = 0

            # Especialistas Médicos (Casi todos en 0)
            med_specs = {k: 0 for k in [
                "cardiologist", "neurologist", "pulmonologist", "gastroenterologist", 
                "nephrologist", "endocrinologist", "hematologist", "oncologist",
                "infectious_disease_specialist", "rheumatologist", "toxicologist"
            ]}
            
            # Especialistas Quirúrgicos (Cero quirófanos = Cero cirujanos fijos)
            surg_specs = {k: 0 for k in [
                "general_surgeon", "cardiovascular_surgeon", "neurosurgeon", 
                "orthopedic_surgeon", "plastic_surgeon", "burn_surgeon", 
                "maxillofacial_surgeon", "urologist", "otolaryngologist"
            ]}

            # Poblacionales (Quizás un pediatra general, el resto cero)
            pediatricians = random.choice([0, 1])
            pop_specs = {"neonatologist": 0, "obstetrician": 0, "gynecologist": 0, "psychiatrist": 0, "ophthalmologist": 0}

            # Soporte Vital e Imágenes Básicas
            ventilators = random.randint(0, 1)  # Solo para traslados emergency
            defibrillators = random.randint(1, 2)
            ecmo = 0
            bypass = 0
            crash_carts = random.randint(1, 2)

            # Equipamiento Diagnóstico
            ct_scanner = 0
            mri = 0
            x_ray = random.choice([0, 1])
            portable_x_ray = 0
            ultrasound = random.choice([0, 1])
            ecg = random.randint(1, 2)
            eeg = 0
            fluoroscopy = 0
            
            # Procedimientos
            dialysis = 0
            endoscopy = 0
            hyperbaric = 0
            incubator = 0

        elif tier == "regional":
            # --- INFRAESTRUCTURA REGIONAL (INTERMEDIA) ---
            standard_beds = random.randint(25, 50)
            trauma_beds = random.randint(3, 6)
            isolation_beds = random.randint(2, 4)
            icu_beds = random.randint(4, 10)
            operating_rooms = random.randint(2, 4)

            triage_nurses = random.randint(3, 6)
            general_doctors = random.randint(6, 12)
            intensivists = random.randint(2, 4)
            anesthesiologists = random.randint(2, 4)

            # Especialidades Médicas Estándar
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

            # Quirúrgicos Básicos/Esenciales
            surg_specs = {
                "general_surgeon": random.randint(2, 4),
                "cardiovascular_surgeon": 0, "neurosurgeon": 0,
                "orthopedic_surgeon": random.randint(1, 3), # Fracturas comunes
                "plastic_surgeon": 0, "burn_surgeon": 0, "maxillofacial_surgeon": 0,
                "urologist": random.choice([0, 1]),
                "otolaryngologist": random.choice([0, 1])
            }

            # Poblacionales
            pediatricians = random.randint(2, 4)
            pop_specs = {
                "neonatologist": random.choice([0, 1]),
                "obstetrician": random.randint(1, 2),
                "gynecologist": random.randint(1, 2),
                "psychiatrist": random.choice([0, 1]),
                "ophthalmologist": 0
            }

            # Equipamiento de Nivel Medio
            ventilators = random.randint(4, 8)
            defibrillators = random.randint(3, 6)
            ecmo = 0; bypass = 0
            crash_carts = random.randint(3, 5)

            ct_scanner = random.choice([1, 2])
            mri = 0  # Raro en urgencias regionales
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
            # --- INFRAESTRUCTURA ELITE (ALTA COMPLEJIDAD NIVEL IV) ---
            standard_beds = random.randint(80, 150)
            trauma_beds = random.randint(8, 15)
            isolation_beds = random.randint(6, 12)
            icu_beds = random.randint(20, 40)
            operating_rooms = random.randint(6, 12)

            triage_nurses = random.randint(8, 16)
            general_doctors = random.randint(15, 30)
            intensivists = random.randint(6, 12)
            anesthesiologists = random.randint(6, 12)

            # Todas las especialidades médicas activas
            med_specs = {k: random.randint(2, 5) for k in [
                "cardiologist", "neurologist", "pulmonologist", "gastroenterologist", 
                "nephrologist", "endocrinologist", "hematologist", "oncologist",
                "infectious_disease_specialist", "rheumatologist", "toxicologist"
            ]}

            # Todos los cirujanos de alta complejidad activos
            surg_specs = {k: random.randint(1, 4) for k in [
                "general_surgeon", "cardiovascular_surgeon", "neurosurgeon", 
                "orthopedic_surgeon", "plastic_surgeon", "burn_surgeon", 
                "maxillofacial_surgeon", "urologist", "otolaryngologist"
            ]}

            # Poblacionales completos
            pediatricians = random.randint(5, 10)
            pop_specs = {k: random.randint(2, 5) for k in [
                "neonatologist", "obstetrician", "gynecologist", "psychiatrist", "ophthalmologist"
            ]}

            # Tecnología Avanzada Completa
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

        # 3. Cálculo dinámico del tiempo disponible de médicos (en minutos globales)
        # Asumiendo un turno base donde cada médico general aporta 480 minutos de trabajo (8 horas)
        total_doctor_time = general_doctors * 480

        # 4. Construcción dinámica de diccionarios de especialistas y equipamiento
        # Inicializar con 0 para todos los válidos, luego actualizar con valores específicos
        specialists_dict = {spec: 0 for spec in VALID_SPECIALISTS}
        equipment_dict = {equip: 0 for equip in VALID_EQUIPMENT}
        
        # Actualizar especialistas disponibles
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
        
        # Actualizar equipamiento disponible
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

        # 5. Retorno de HospitalResources optimizado (solo 5 parámetros principales)
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

