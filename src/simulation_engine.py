import json
import os
import inspect
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any
import sys
from pathlib import Path

# Inserción de path para consistencia de ejecución en submódulos
sys.path.insert(0, str(Path(__file__).parent.parent))
from models import Patient, Vitals, HospitalResources
from analyzer.llm_analyzer import analyze_patient_with_ai

# AQUÍ IMPORTAMOS TU GENERADOR CON GROK
from generator.patient_generator import generate_mock_patients

# Fallback local de límites en caso de que no se importe MAX_WAIT_TIMES de models
MANCHESTER_LIMITS = {
    "1_Resuscitation": 0,
    "2_Emergent": 10,
    "3_Urgent": 60,
    "4_Standard": 120,
    "5_Routine": 240
}

def load_json_data(hospitals_path: str, patients_path: str):
    """Carga y procesa las fuentes de datos estructurando los tipos primitivos."""
    with open(hospitals_path, "r", encoding="utf-8") as f:
        hospitals = {h["hospital_id"]: h for h in json.load(f)}

    with open(patients_path, "r", encoding="utf-8") as f:
        patients_raw = json.load(f)
        patients = []
        valid_keys = inspect.signature(Patient.__init__).parameters.keys()

        for p in patients_raw:
            if "arrival_time" in p and isinstance(p["arrival_time"], str):
                try:
                    p["arrival_time"] = datetime.fromisoformat(p["arrival_time"])
                except ValueError:
                    p["arrival_time"] = datetime.now()
            else:
                p["arrival_time"] = datetime.now()

            if "vitals" in p and isinstance(p["vitals"], dict):
                p["vitals"] = Vitals(**p["vitals"])

            filtered_p = {k: v for k, v in p.items() if k in valid_keys and k != 'self'}
            patient_obj = Patient(**filtered_p)

            patient_obj.arrival_hospital_id = p.get("arrival_hospital_id", "HOSP-01")
            patient_obj.current_hospital_id = p.get("current_hospital_id", "HOSP-01")
            patient_obj.assigned_hospital_id = p.get("assigned_hospital_id")
            patient_obj.status = p.get("status", "Waiting")

            # Asignación dinámica del límite real de Manchester
            patient_obj.max_safe_wait_time_min = MANCHESTER_LIMITS.get(patient_obj.initial_triage_category, 120)

            patients.append(patient_obj)

    # Ordenamiento cronológico estricto para el Event-Loop temporal
    patients.sort(key=lambda x: x.arrival_time)
    return hospitals, patients

def _calculate_dummy_base_score(patient: Patient):
    """Puntaje algorítmico fallback en caso de ausencia de procesamiento matemático directo."""
    scores = {
        "1_Resuscitation": 50.0,
        "2_Emergent": 30.0,
        "3_Urgent": 15.0,
        "4_Standard": 5.0,
        "5_Routine": 2.0
    }
    patient.base_urgency_score = scores.get(patient.initial_triage_category, 10.0)

def _get_clinical_summary(p: Patient) -> str:
    """Extrae de manera compacta el diagnóstico, enfermedad o síntoma del paciente."""
    if getattr(p, 'reported_symptoms', None):
        return f"Síntomas: {', '.join(p.reported_symptoms[:2])}"
    elif getattr(p, 'chronic_diseases', None):
        return f"Crónicos: {', '.join(p.chronic_diseases[:2])}"
    elif getattr(p, 'triage_notes', None):
        return p.triage_notes[:40] + "..." if len(p.triage_notes) > 40 else p.triage_notes
    return "Sin datos clínicos explícitos"

def get_missing_resources(patient: Patient, hospital: Dict[str, Any]) -> List[str]:
    """Valida la disponibilidad física y de personal del nodo de destino actual."""
    missing = []
    for specialist in getattr(patient, 'requires_specialist', []):
        if hospital.get("specialists_available", {}).get(specialist, 0) <= 0:
            missing.append(f"Especialista: {specialist}")

    for equipment in getattr(patient, 'requires_equipment', []):
        if hospital.get("equipment_available", {}).get(equipment, 0) <= 0:
            missing.append(f"Equipo: {equipment}")
    return missing

def find_alternative_hospital(patient: Patient, hospitals: Dict[str, Dict], current_hosp_id: str, hospital_queues: Dict[str, List]) -> str:
    """Balanceador de carga: Busca el nodo con menor densidad de cola que posea los recursos."""
    valid_hospitals = []
    for h_id, hospital in hospitals.items():
        if h_id == current_hosp_id:
            continue
        if not get_missing_resources(patient, hospital):
            valid_hospitals.append(h_id)

    if valid_hospitals:
        valid_hospitals.sort(key=lambda hid: len(hospital_queues[hid]))
        return valid_hospitals[0]
    return "NINGUNO (Alerta de Sistema: Sin recursos en la red)"

def apply_dynamic_scoring(queue: List[Patient], current_time: datetime):
    """
    Calcula el envejecimiento en cola añadiendo 0.5 puntos por minuto sobre la puntuación
    final calculada por el LLM (que ya contiene la penalización por espera).
    No se aplica una segunda penalización de 50 pts porque ya la incluye el analizador.
    """
    for p in queue:
        p.time_waiting_min = int((current_time - p.arrival_time).total_seconds() / 60)
        # Utilizamos el score base fijado por el LLM (almacenado tras el análisis)
        llm_base = getattr(p, 'llm_base_score', getattr(p, 'final_priority_score', 0.0))
        # Solo añadimos el envejecimiento lineal (0.5 por minuto)
        p.final_priority_score = llm_base + p.time_waiting_min * 0.5

    # Reordena la cola con los nuevos scores
    queue.sort(key=lambda p: getattr(p, 'final_priority_score', 0.0), reverse=True)

def print_live_queue(current_time: datetime, h_id: str, queue: List[Patient]):
    """Imprime el estado de la cola en tiempo real."""
    print(f"\n🏥 --- ESTADO ACTUAL COLA {h_id} | HORA: {current_time.strftime('%H:%M:%S')} ---")
    apply_dynamic_scoring(queue, current_time)

    if not queue:
        print("  [Cola Vacía]")
        return

    for rank, p in enumerate(queue[:5], 1):
        wait_warn = "⚠️" if p.time_waiting_min > p.max_safe_wait_time_min else "⏱️"
        clin_ctx = _get_clinical_summary(p)
        print(f"  {rank}°. {p.first_name} {p.last_name} | Score: {p.final_priority_score:.1f} | 🩺 {clin_ctx} | Triaje: {p.initial_triage_category[:4]} | Límite: {p.max_safe_wait_time_min}m | {wait_warn} Esperando: {p.time_waiting_min} min")

    if len(queue) > 5:
        remanente = len(queue) - 5
        texto = "paciente" if remanente == 1 else "pacientes"
        print(f"  ... y {remanente} {texto} más en espera.")
    print("-" * 70)

def print_resource_usage_summary(global_queues: Dict[str, List[Patient]]):
    """
    Reporte adicional: Cantidad de especialistas y equipos solicitados por los pacientes
    en cada hospital, después de la simulación.
    """
    print("\n📊 UTILIZACIÓN DE RECURSOS POR HOSPITAL (Especialistas y Equipamiento Solicitados):")
    for h_id, queue in global_queues.items():
        specialist_counter = {}
        equipment_counter = {}
        for p in queue:
            for spec in getattr(p, 'requires_specialist', []):
                specialist_counter[spec] = specialist_counter.get(spec, 0) + 1
            for equip in getattr(p, 'requires_equipment', []):
                equipment_counter[equip] = equipment_counter.get(equip, 0) + 1

        if not specialist_counter and not equipment_counter:
            continue

        print(f"\n🏥 {h_id}:")
        if specialist_counter:
            print("   Especialistas solicitados:")
            for spec, count in sorted(specialist_counter.items()):
                print(f"      - {spec}: {count} veces")
        if equipment_counter:
            print("   Equipamiento solicitado:")
            for equip, count in sorted(equipment_counter.items()):
                print(f"      - {equip}: {count} veces")

def simulate_time_interval(patients_to_process: List[Patient], hospitals: Dict, global_queues: Dict, transfer_log: List, mode_name: str) -> datetime:
    """Motor central basado en intervalos cronológicos discretos. Retorna el tiempo final de simulación."""
    print(f"\n🚀 INICIANDO SIMULACIÓN TEMPORAL: {mode_name}")
    print("=" * 70)

    for h_id in global_queues:
        global_queues[h_id].clear()
    transfer_log.clear()

    current_sim_time = datetime.now() # Fallback

    for idx, patient in enumerate(patients_to_process, 1):
        current_sim_time = patient.arrival_time
        arrival_hosp_id = getattr(patient, 'arrival_hospital_id', 'HOSP-01')
        clin_ctx = _get_clinical_summary(patient)

        print(f"\n🔔 [{current_sim_time.strftime('%H:%M:%S')}] NUEVO INGRESO ({idx}/{len(patients_to_process)}): {patient.first_name} {patient.last_name} -> {arrival_hosp_id}")
        print(f"   ↳ 🩺 Condición de Entrada: {clin_ctx}")

        if getattr(patient, 'base_urgency_score', 0.0) == 0.0:
            _calculate_dummy_base_score(patient)

        analyzed_patient = analyze_patient_with_ai(patient)
        # Guardamos el score final del LLM para usarlo como base en el envejecimiento dinámico
        analyzed_patient.llm_base_score = analyzed_patient.final_priority_score

        current_hospital = hospitals.get(arrival_hosp_id)
        missing_resources = get_missing_resources(analyzed_patient, current_hospital) if current_hospital else ["Hospital no encontrado"]

        if not missing_resources:
            analyzed_patient.assigned_hospital_id = arrival_hosp_id
            analyzed_patient.status = "Waiting"
            global_queues[arrival_hosp_id].append(analyzed_patient)
        else:
            target_hospital_id = find_alternative_hospital(analyzed_patient, hospitals, arrival_hosp_id, global_queues)
            analyzed_patient.assigned_hospital_id = target_hospital_id
            analyzed_patient.status = "Transferred"

            if target_hospital_id.startswith("HOSP"):
                global_queues[target_hospital_id].append(analyzed_patient)

            transfer_log.append({
                "patient_id": analyzed_patient.patient_id,
                "name": f"{analyzed_patient.first_name} {analyzed_patient.last_name}",
                "origin": arrival_hosp_id,
                "target": target_hospital_id,
                "reason": ", ".join(missing_resources),
                "clin_ctx": clin_ctx
            })
            print(f"  🚑 TRASLADO AUTOMÁTICO: Sin recursos locales ({', '.join(missing_resources)}). Desviado a {target_hospital_id}")

        if analyzed_patient.assigned_hospital_id.startswith("HOSP"):
            print_live_queue(current_sim_time, analyzed_patient.assigned_hospital_id, global_queues[analyzed_patient.assigned_hospital_id])
    
    return current_sim_time

def print_exhaustive_summary(global_queues: Dict[str, List[Patient]], transfer_log: List[Dict], total_evaluated: int, final_time: datetime, filter_hospital_id: str = None):
    """Dashboard Exhaustivo Final adaptable a contexto global o segmentado por nodo."""
    print("\n" + "█"*80)
    if filter_hospital_id:
        print(f"📋 REPORTE FINAL EXHAUSTIVO: FILTRADO POR HOSPITAL {filter_hospital_id}")
    else:
        print("📋 REPORTE FINAL EXHAUSTIVO: COMPLETO DE LA RED GLOBAL")
    print("█"*80)

    if filter_hospital_id:
        relevant_transfers = [t for t in transfer_log if t["origin"] == filter_hospital_id]
        total_admitted = len(global_queues[filter_hospital_id])
    else:
        relevant_transfers = transfer_log
        total_admitted = sum(len(q) for q in global_queues.values())

    print(f"📊 PACIENTES EVALUADOS EN EL SEGMENTO : {total_evaluated}")
    print(f"✅ ADMITIDOS EN COLA LOCAL            : {total_admitted}")
    print(f"🚑 TRASLADOS DESPACHADOS              : {len(relevant_transfers)}")

    if relevant_transfers:
        print("\n⚠️ DETALLE DE TRASLADOS EMITIDOS (Falta de Infraestructura / Personal):")
        for t in relevant_transfers:
            print(f"  - {t['name']} ({t['patient_id']}) | {t['origin']} ➔ {t['target']}")
            print(f"    ↳ 🩺 Inicial: {t['clin_ctx']}")
            print(f"    ↳ ❌ Causa: Faltan [{t['reason']}]")

    print("\n⚖️ ESTADO FINAL DE LAS COLAS DE ATENCIÓN (Prioridad Matemática Descendente):")
    hospitals_to_show = [filter_hospital_id] if filter_hospital_id else sorted(global_queues.keys())

    for h_id in hospitals_to_show:
        queue = global_queues[h_id]
        print(f"\n🏥 FLUJO DE ATENCIÓN: {h_id} ({len(queue)} en espera)")
        if not queue:
            print("  (Sin pacientes en este nodo de la red)")
            continue

        # Reaplicamos el scoring dinámico final para el reporte
        apply_dynamic_scoring(queue, final_time)

        for rank, p in enumerate(queue, 1):
            wait_warn = "⚠️ CRÍTICO" if p.time_waiting_min > p.max_safe_wait_time_min else "⏱️ Estable"
            clin_ctx = _get_clinical_summary(p)
            print(f"  {rank}°. [{p.final_priority_score:.1f} pts] {p.first_name} {p.last_name} | ID: {p.patient_id}")
            print(f"      🩺 Condición Clínica: {clin_ctx}")
            print(f"      🗂️ Triaje Asignado  : {p.initial_triage_category} | Límite Manchester: {p.max_safe_wait_time_min} min")
            print(f"      ⏳ Tiempo de Espera : {p.time_waiting_min} min ({wait_warn})")
            if getattr(p, 'ai_reasoning', ""):
                print(f"      🤖 Nota IA          : {p.ai_reasoning}")

    # --- NUEVO REPORTE: Utilización de recursos por hospital ---
    print_resource_usage_summary(global_queues)

    print("\n" + "█"*80 + "\n")


# --- INTERFAZ INTERACTIVA DE CONSOLA ---
def interactive_menu():
    HOSPITALS_JSON = "data/hospitals.json"
    PATIENTS_JSON = "data/patients.json"

    if not os.path.exists(HOSPITALS_JSON) or not os.path.exists(PATIENTS_JSON):
        print("❌ Error Fatal: Estructuras JSON ausentes en el directorio 'data/'.")
        return
    
    hospitals, all_patients = load_json_data(HOSPITALS_JSON, PATIENTS_JSON)
    global_queues = {h_id: [] for h_id in hospitals.keys()}
    transfer_log = []

    while True:
        print("\n" + "="*55)
        print(" 🏥 MOTOR DE TRIAJE IA - ENTORNO DE SIMULACIÓN AVANZADO")
        print("="*55)
        print("1. Analizar el Sistema de Hospitales Completo (Red Global)")
        print("2. Analizar por Hospital Específico")
        print("3. Generar y Analizar 5 Pacientes Aleatorios (Prueba de Estrés)")
        print("4. Salir")

        opcion = input("\nSeleccione opción analítica (1-4): ").strip()
        
        if opcion == "1":
            end_time = simulate_time_interval(all_patients, hospitals, global_queues, transfer_log, "RED GLOBAL DE HOSPITALES")
            print_exhaustive_summary(global_queues, transfer_log, len(all_patients), end_time)

        elif opcion == "2":
            print("\n🏥 Carga interna del Dataset por Hospital:")
            for h_id in hospitals.keys():
                count = sum(1 for p in all_patients if p.arrival_hospital_id == h_id)
                print(f" - {h_id} (Pacientes indexados en origen: {count})")

            selected_hosp = input("\nEscriba el ID del hospital (ej. HOSP-01): ").strip()
            if selected_hosp not in hospitals:
                print("❌ Identificador de nodo hospitalario inválido.")
                continue

            hosp_patients = [p for p in all_patients if p.arrival_hospital_id == selected_hosp]
            if not hosp_patients:
                print("⚠️ No existen entradas asignadas a este hospital en el origen de datos.")
                continue

            end_time = simulate_time_interval(hosp_patients, hospitals, global_queues, transfer_log, f"NODO {selected_hosp}")
            print_exhaustive_summary(global_queues, transfer_log, len(hosp_patients), end_time, filter_hospital_id=selected_hosp)

        elif opcion == "3":
            print("\n🏥 Generando flujo de pacientes en Urgencias mediante IA...\n")
            
            # Generamos a los pacientes usando TU GENERADOR con Grok
            mock_db = generate_mock_patients(5) 
            
            # --- CORRECCIÓN BUG 1: Ordenamiento cronológico para evitar tiempos negativos ---
            mock_db.sort(key=lambda x: x.arrival_time)
            
            for i, p in enumerate(mock_db, 1):
                # FIX BUG MANCHESTER: Le inyectamos el límite de tiempo seguro a los pacientes de Grok
                p.max_safe_wait_time_min = MANCHESTER_LIMITS.get(getattr(p, 'initial_triage_category', '4_Standard'), 120)
                
                # --- CORRECCIÓN BUG 2: Distribución en la red (ignoramos a dónde iban originalmente) ---
                p.arrival_hospital_id = random.choice(list(hospitals.keys()))

                embarazo = " (Embarazada)" if getattr(p, 'is_pregnant', False) else ""
                print(f"\n{'='*80}")
                print(f"📋 PACIENTE #{i}")
                print(f"{'='*80}")
                print(f"ID: {p.patient_id} | {p.first_name} {p.last_name}, {p.age} años | {p.gender}{embarazo}")
                print(f"Categoría Triaje: [{p.initial_triage_category}] | Seguro: {p.insurance_type}")
                print(f"Llegada: {p.arrival_time.strftime('%H:%M:%S')}")

                print(f"\n📊 SIGNOS VITALES:")
                print(f"   • Frecuencia Cardíaca: {p.vitals.heart_rate_bpm} lpm")
                print(f"   • Saturación de Oxígeno: {p.vitals.oxygen_saturation_pct}%")
                print(f"   • Presión Arterial: {p.vitals.systolic_bp}/{p.vitals.diastolic_bp} mmHg")
                print(f"   • Temperatura: {p.vitals.temperature_c}°C")
                print(f"   • Nivel de Dolor: {p.vitals.pain_level}/10")
                
                print(f"   • GCS (Glasgow Coma Scale): {getattr(p.vitals, 'glasgow_coma_scale', 'No reportado')}")
                print(f"   • Nivel de Conciencia: {getattr(p.vitals, 'consciousness_level', 'No reportado')}")

                print(f"\n📝 NOTAS DEL TRIAJE MÉDICO:")
                print(f"   {p.triage_notes}")

                print(f"\n📋 HISTORIAL MÉDICO:")
                print(f"   {p.medical_history_text}")

                if getattr(p, 'chronic_diseases', None):
                    print(f"\n🔴 ENFERMEDADES CRÓNICAS ASOCIADAS:")
                    for disease in p.chronic_diseases:
                        print(f"   • {disease.replace('_', ' ').title()}")
                else:
                    print(f"\n✅ Sin enfermedades crónicas reportadas.")

                print(f"\n{'-'*80}")
            
            # Pasamos la lista mock_db a la simulación en lugar de la random
            end_time = simulate_time_interval(mock_db, hospitals, global_queues, transfer_log, "PRUEBA DE ESTRÉS ALEATORIA (IA)")
            print_exhaustive_summary(global_queues, transfer_log, len(mock_db), end_time)

        elif opcion == "4":
            print("👋 Finalizando ejecución del simulador clínico.")
            break
        else:
            print("❌ Entrada incorrecta.")

if __name__ == "__main__":
    interactive_menu()