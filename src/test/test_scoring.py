if __name__ == "__main__":
    # Simulación de prueba interactiva
    import sys
    from pathlib import Path
    
    # Añadir el directorio padre (src) al path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    
    from patient_generator import generate_mock_patients
    from scoring_engine import score_entire_queue
    
    print("🔄 Generando 5 pacientes aleatorios...")
    sala_espera = generate_mock_patients(5)
    
    print("🧮 Procesando cola a través del motor matemático...")
    cola_priorizada = score_entire_queue(sala_espera)
    
    print("\n📋 ORDEN DE ATENCIÓN DE URGENCIAS OPTIMIZADO MATEMÁTICAMENTE:")
    print("=" * 70)
    for index, p in enumerate(cola_priorizada, 1):
        print(f"Posición {index} ➡️ [Score: {p.base_urgency_score}] ID: {p.patient_id} | {p.first_name} {p.last_name} ({p.age} años)")
        print(f"   • Manchester original: {p.initial_triage_category}")
        print(f"   • SpO2: {p.vitals.oxygen_saturation_pct}% | FC: {p.vitals.heart_rate_bpm} lpm | GCS: {p.vitals.glasgow_coma_scale}")
        print(f"   • Crónicos asociados: {p.chronic_diseases}")
        print("-" * 70)
