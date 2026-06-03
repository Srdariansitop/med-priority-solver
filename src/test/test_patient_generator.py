if __name__ == "__main__":
    # Simulación de prueba de generador de pacientes
    import sys
    from pathlib import Path
    
    # Añadir el directorio padre (src) al path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    
    from patient_generator import generate_mock_patients
    
    print("🏥 Generando flujo de pacientes en Urgencias...\n")
    mock_db = generate_mock_patients(5) # Generamos 5 pacientes
    
    for i, p in enumerate(mock_db, 1):
        embarazo = " (Embarazada)" if p.is_pregnant else ""
        print(f"\n{'='*80}")
        print(f"📋 PACIENTE #{i}")
        print(f"{'='*80}")
        print(f"ID: {p.patient_id} | {p.first_name} {p.last_name}, {p.age} años | {p.gender}{embarazo}")
        print(f"Categoría Triaje: [{p.initial_triage_category}] | Seguro: {p.insurance_type}")
        print(f"Tiempo de espera: {p.time_waiting_min} min | Llegada: {p.arrival_time.strftime('%H:%M:%S')}")
        
        print(f"\n📊 SIGNOS VITALES:")
        print(f"   • Frecuencia Cardíaca: {p.vitals.heart_rate_bpm} lpm")
        print(f"   • Saturación de Oxígeno: {p.vitals.oxygen_saturation_pct}%")
        print(f"   • Presión Arterial: {p.vitals.systolic_bp}/{p.vitals.diastolic_bp} mmHg")
        print(f"   • Temperatura: {p.vitals.temperature_c}°C")
        print(f"   • Nivel de Dolor: {p.vitals.pain_level}/10")
        print(f"   • GCS (Glasgow Coma Scale): {p.vitals.glasgow_coma_scale}")
        print(f"   • Nivel de Conciencia: {p.vitals.consciousness_level}")
        
        print(f"\n📝 NOTAS DEL TRIAJE MÉDICO:")
        print(f"   {p.triage_notes}")
        
        print(f"\n📋 HISTORIAL MÉDICO:")
        print(f"   {p.medical_history_text}")
        
        if p.chronic_diseases:
            print(f"\n🔴 ENFERMEDADES CRÓNICAS ASOCIADAS:")
            for disease in p.chronic_diseases:
                print(f"   • {disease.replace('_', ' ').title()}")
        else:
            print(f"\n✅ Sin enfermedades crónicas reportadas.")
        
        print(f"\n{'-'*80}")
