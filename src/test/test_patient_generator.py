if __name__ == "__main__":
    # Simulación de prueba de generador de pacientes
    import sys
    from pathlib import Path
    
    # Añadir el directorio padre (src) al path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    
    from patient_generator import generate_mock_patients
    
    print("🏥 Generando flujo de pacientes en Urgencias...\n")
    mock_db = generate_mock_patients(5) # Generamos 5 pacientes
    
    for p in mock_db:
        embarazo = " (Embarazada)" if p.is_pregnant else ""
        print(f"[{p.initial_triage_category}] ID: {p.patient_id} | {p.first_name} {p.last_name}, {p.age} años{embarazo}")
        print(f"   -> FC: {p.vitals.heart_rate_bpm} lpm | SpO2: {p.vitals.oxygen_saturation_pct}% | GCS: {p.vitals.glasgow_coma_scale}")
        print(f"   -> Enfermedades Crónicas: {p.chronic_diseases if p.chronic_diseases else 'Ninguna'}")
        print("-" * 60)
