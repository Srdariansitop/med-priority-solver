import sys
import os

# Agregar el directorio padre (src) al path para importar correctamente
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from generator.patient_generator import generate_mock_patients
from analyzer.scoring_engine import calculate_base_urgency_score
from analyzer.llm_analyzer import analyze_patient_with_ai


def print_initial_patient_data(patients):
    """Imprime los datos iniciales de los pacientes."""
    print("\n" + "="*80)
    print("📋 DATOS INICIALES DE PACIENTES")
    print("="*80 + "\n")

    for i, p in enumerate(patients, 1):
        print(f"[{i}] ID: {p.patient_id} | {p.first_name} {p.last_name}")
        print(f"    Edad: {p.age} años | Sexo: {p.gender} | Embarazada: {'Sí' if p.is_pregnant else 'No'}")
        print(f"    Categoría Triaje Inicial: {p.initial_triage_category}")
        print(f"    \n    📝 Síntomas/Notas de Triaje:")
        print(f"    \"{p.triage_notes}\"")
        print(f"    \n    📚 Antecedentes Médicos:")
        print(f"    \"{p.medical_history_text}\"")
        print(f"    \n    🩺 Enfermedades Crónicas: {p.chronic_diseases if p.chronic_diseases else 'Ninguna'}")
        print(f"    \n    ❤️ Signos Vitales:")
        print(f"       • FC: {p.vitals.heart_rate_bpm} lpm")
        print(f"       • SpO2: {p.vitals.oxygen_saturation_pct}%")
        print(f"       • PA: {p.vitals.systolic_bp}/{p.vitals.diastolic_bp} mmHg")
        print(f"       • Temp: {p.vitals.temperature_c}°C")
        print(f"       • Dolor: {p.vitals.pain_level}/10")
        print(f"       • GCS: {p.vitals.glasgow_coma_scale}/15")
        print(f"       • Nivel de Conciencia: {p.vitals.consciousness_level}")
        print("-" * 80)


def print_final_report(patients):
    """Imprime el reporte final ordenado con el razonamiento de la IA."""
    print("\n" + "="*80)
    print("🏥 REPORTE FINAL DE TRIAJE HÍBRIDO (MATEMÁTICA + IA)")
    print("="*80 + "\n")

    for i, p in enumerate(patients, 1):
        print(f"[{i}] ID: {p.patient_id} | {p.first_name} {p.last_name} ({p.age} años)")
        print(f"    • Categoría Inicial: {p.initial_triage_category}")
        print(f"    • Score Matemático:  {getattr(p, 'base_urgency_score', 0.0)}")
        print(f"    • Modificador IA:    x{p.llm_context_modifier}")
        print(f"    • SCORE FINAL:       {p.final_priority_score}")
        print(f"    🤖 Razonamiento IA:  '{getattr(p, 'ai_reasoning', 'No analizado')}'")
        if p.requires_specialist or p.requires_equipment:
            print(f"    🚨 Requiere: {', '.join(p.requires_specialist + p.requires_equipment)}")
        print("-" * 80)


def main():
    print("🔄 1. Generando pacientes simulados...")
    # Generamos 5 pacientes para probar rápido
    patients = generate_mock_patients(5) 

    print("🧮 2. Calculando gravedad matemática pura...")
    for patient in patients:
        calculate_base_urgency_score(patient)

    print("🧠 3. Analizando casos complejos con Inteligencia Artificial...")
    for patient in patients:
        analyze_patient_with_ai(patient)

    print("📊 4. Ordenando fila de urgencias...")
    # Ordenamos por score (mayor a menor), con tie-breaker: quien llegó primero va primero (arrival_time ascendente)
    patients.sort(key=lambda x: (-x.final_priority_score, x.arrival_time))

    # Imprimir datos iniciales
    print_initial_patient_data(patients)

    # Imprimir el resultado final
    print_final_report(patients)


if __name__ == "__main__":
    main()
