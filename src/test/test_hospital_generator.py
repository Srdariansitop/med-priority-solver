import sys
import os

# Agregar el directorio padre (src) al path para importar correctamente
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from hospital_generator import HospitalGenerator


def print_hospital_details(hospital, tier_name):
    """Imprime todos los detalles completos del hospital."""
    print("\n" + "="*80)
    print(f"🏥 {tier_name.upper()} - {hospital.hospital_name}")
    print("="*80)
    
    # ===== INFRAESTRUCTURA FÍSICA =====
    print("\n📍 INFRAESTRUCTURA FÍSICA:")
    print(f"  • Camas Estándar: {hospital.standard_beds_available}")
    print(f"  • Camas Trauma (Reanimación): {hospital.trauma_beds_available}")
    print(f"  • Camas Aislamiento: {hospital.isolation_beds_available}")
    print(f"  • Camas UCI: {hospital.icu_beds_available}")
    print(f"  • Quirófanos: {hospital.operating_rooms_available}")
    print(f"  • Tiempo Disponible Médicos: {hospital.available_doctors_time_minutes} minutos")
    
    # ===== ESPECIALISTAS MÉDICOS =====
    print("\n👨‍⚕️ ESPECIALISTAS DISPONIBLES:")
    print("  Base y Crítico:")
    print(f"    - Triage Nurses: {hospital.specialists_available.get('triage_nurse', 0)}")
    print(f"    - General Doctors: {hospital.specialists_available.get('general_doctor', 0)}")
    print(f"    - Intensivists: {hospital.specialists_available.get('intensivist', 0)}")
    print(f"    - Anesthesiologists: {hospital.specialists_available.get('anesthesiologist', 0)}")
    
    print("  Médicos Especialistas:")
    med_specs = ['cardiologist', 'neurologist', 'pulmonologist', 'gastroenterologist', 
                 'nephrologist', 'endocrinologist', 'hematologist', 'oncologist',
                 'infectious_disease_specialist', 'rheumatologist', 'toxicologist']
    for spec in med_specs:
        count = hospital.specialists_available.get(spec, 0)
        spec_name = spec.replace('_', ' ').title()
        print(f"    - {spec_name}: {count}")
    
    print("  Cirujanos Especialistas:")
    surg_specs = ['general_surgeon', 'cardiovascular_surgeon', 'neurosurgeon', 
                  'orthopedic_surgeon', 'plastic_surgeon', 'burn_surgeon', 
                  'maxillofacial_surgeon', 'urologist', 'otolaryngologist']
    for spec in surg_specs:
        count = hospital.specialists_available.get(spec, 0)
        spec_name = spec.replace('_', ' ').title()
        print(f"    - {spec_name}: {count}")
    
    print("  Especialidades Poblacionales:")
    pop_specs = ['pediatrician', 'neonatologist', 'obstetrician', 'gynecologist', 
                 'psychiatrist', 'ophthalmologist']
    for spec in pop_specs:
        count = hospital.specialists_available.get(spec, 0)
        spec_name = spec.replace('_', ' ').title()
        print(f"    - {spec_name}: {count}")
    
    # ===== EQUIPAMIENTO =====
    print("\n🔧 EQUIPAMIENTO DISPONIBLE:")
    
    print("  Soporte Vital:")
    vital_equip = ['ventilator', 'defibrillator', 'ecmo_machine', 
                   'cardiopulmonary_bypass_machine', 'crash_cart']
    for equip in vital_equip:
        count = hospital.equipment_available.get(equip, 0)
        equip_name = equip.replace('_', ' ').title()
        print(f"    - {equip_name}: {count}")
    
    print("  Diagnóstico por Imagen y Señales:")
    imaging_equip = ['x_ray_machine', 'portable_x_ray', 'ct_scanner', 'mri_machine',
                     'ultrasound_machine', 'fluoroscopy_machine', 'ecg_machine', 'eeg_machine']
    for equip in imaging_equip:
        count = hospital.equipment_available.get(equip, 0)
        equip_name = equip.replace('_', ' ').title()
        print(f"    - {equip_name}: {count}")
    
    print("  Procedimientos Específicos:")
    proc_equip = ['dialysis_machine', 'endoscopy_tower', 'hyperbaric_chamber', 'incubator']
    for equip in proc_equip:
        count = hospital.equipment_available.get(equip, 0)
        equip_name = equip.replace('_', ' ').title()
        print(f"    - {equip_name}: {count}")
    
    # ===== ESTADO OPERATIVO =====
    print("\n🚨 ESTADO OPERATIVO:")
    diversion_status = "⚠️ EN DESVIACIÓN (No acepta ambulancias)" if hospital.is_on_diversion else "✅ Operativo"
    print(f"  {diversion_status}")
    
    print("-" * 80)


def main():
    print("🏥 PROBANDO GENERADOR DE INFRAESTRUCTURA HOSPITALARIA...")
    
    # Generar hospitales de diferentes tiers
    print("\n⚙️ Generando hospitales...")
    
    hospital_modest = HospitalGenerator.generate("modest", name="Hospital Comunitario")
    hospital_regional = HospitalGenerator.generate("regional", name="Hospital Regional")
    hospital_elite = HospitalGenerator.generate("elite", name="Hospital Universitario de Alta Complejidad")
    
    # Mostrar detalles de cada hospital
    print_hospital_details(hospital_modest, "Modesto")
    print_hospital_details(hospital_regional, "Regional")
    print_hospital_details(hospital_elite, "Elite")
    
    # ===== RESUMEN COMPARATIVO =====
    print("\n" + "="*80)
    print("📊 RESUMEN COMPARATIVO ENTRE TIERS")
    print("="*80)
    
    tiers_data = [
        ("MODESTO", hospital_modest),
        ("REGIONAL", hospital_regional),
        ("ELITE", hospital_elite)
    ]
    
    print(f"\n{'Métrica':<30} {'Modesto':<15} {'Regional':<15} {'Elite':<15}")
    print("-" * 75)
    
    print(f"{'Camas UCI':<30} {hospital_modest.icu_beds_available:<15} {hospital_regional.icu_beds_available:<15} {hospital_elite.icu_beds_available:<15}")
    print(f"{'Quirófanos':<30} {hospital_modest.operating_rooms_available:<15} {hospital_regional.operating_rooms_available:<15} {hospital_elite.operating_rooms_available:<15}")
    print(f"{'Médicos Generales':<30} {hospital_modest.specialists_available.get('general_doctor', 0):<15} {hospital_regional.specialists_available.get('general_doctor', 0):<15} {hospital_elite.specialists_available.get('general_doctor', 0):<15}")
    print(f"{'TAC Scanners':<30} {hospital_modest.equipment_available.get('ct_scanner', 0):<15} {hospital_regional.equipment_available.get('ct_scanner', 0):<15} {hospital_elite.equipment_available.get('ct_scanner', 0):<15}")
    print(f"{'Cardiólogos':<30} {hospital_modest.specialists_available.get('cardiologist', 0):<15} {hospital_regional.specialists_available.get('cardiologist', 0):<15} {hospital_elite.specialists_available.get('cardiologist', 0):<15}")
    print(f"{'Neurocirujanos':<30} {hospital_modest.specialists_available.get('neurosurgeon', 0):<15} {hospital_regional.specialists_available.get('neurosurgeon', 0):<15} {hospital_elite.specialists_available.get('neurosurgeon', 0):<15}")
    print(f"{'Ventiladores':<30} {hospital_modest.equipment_available.get('ventilator', 0):<15} {hospital_regional.equipment_available.get('ventilator', 0):<15} {hospital_elite.equipment_available.get('ventilator', 0):<15}")
    print(f"{'Resonancias Magnéticas':<30} {hospital_modest.equipment_available.get('mri_machine', 0):<15} {hospital_regional.equipment_available.get('mri_machine', 0):<15} {hospital_elite.equipment_available.get('mri_machine', 0):<15}")
    
    print("\n" + "="*80)


if __name__ == "__main__":
    main()
