import json
import os
import inspect
from datetime import datetime
from typing import List, Dict, Any
from models import Patient, Vitals  
from analyzer.llm_analyzer import analyze_patient_with_ai  

def load_json_data(hospitals_path: str, patients_path: str):
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

            if "vitals" in p and isinstance(p["vitals"], dict):
                p["vitals"] = Vitals(**p["vitals"])

            filtered_p = {k: v for k, v in p.items() if k in valid_keys and k != 'self'}
            patient_obj = Patient(**filtered_p)
            
            patient_obj.arrival_hospital_id = p.get("arrival_hospital_id", "HOSP-01")
            patient_obj.current_hospital_id = p.get("current_hospital_id", "HOSP-01")
            patient_obj.assigned_hospital_id = p.get("assigned_hospital_id")
            patient_obj.status = p.get("status", "Waiting")
            
            patients.append(patient_obj)
            
    return hospitals, patients

def _calculate_dummy_base_score(patient: Patient):
    """
    Función temporal para dar un score base a los pacientes.
    REEMPLAZAR LUEGO CON TU MOTOR MATEMÁTICO REAL.
    """
    scores = {
        "1_Resuscitation": 50.0,
        "2_Emergent": 30.0,
        "3_Urgent": 15.0,
        "4_Standard": 5.0,
        "5_Routine": 2.0
    }
    patient.base_urgency_score = scores.get(patient.initial_triage_category, 10.0)

def get_missing_resources(patient: Patient, hospital: Dict[str, Any]) -> List[str]:
    """Evalúa qué recursos específicos le faltan al hospital para atender al paciente."""
    missing = []
    
    # Verificar Especialistas
    for specialist in patient.requires_specialist:
        available_count = hospital["specialists_available"].get(specialist, 0)
        if available_count <= 0:
            missing.append(f"Especialista: {specialist}")
            
    # Verificar Equipamiento
    for equipment in patient.requires_equipment:
        available_count = hospital["equipment_available"].get(equipment, 0)
        if available_count <= 0:
            missing.append(f"Equipo: {equipment}")
            
    return missing

def find_alternative_hospital(patient: Patient, hospitals: Dict[str, Dict], current_hosp_id: str, hospital_queues: Dict[str, List]) -> str:
    """Busca el hospital alternativo que tenga los recursos Y la cola más corta (Load Balancing)."""
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

def print_system_statistics(queues: Dict[str, List[Patient]], transfers: List[Dict[str, Any]], total_patients: int):
    """Muestra un dashboard final con estadísticas impresionantes en consola."""
    print("\n" + "█"*70)
    print("📊 ESTADÍSTICAS GLOBALES DEL MOTOR DE TRIAJE")
    print("█"*70)

    total_transfers = len(transfers)
    local_admissions = total_patients - total_transfers
    transfer_rate = (total_transfers / total_patients) * 100 if total_patients > 0 else 0

    triage_counts = {"1_Resuscitation": 0, "2_Emergent": 0, "3_Urgent": 0, "4_Standard": 0, "5_Routine": 0}
    
    for h_id, patient_list in queues.items():
        for p in patient_list:
            if getattr(p, 'assigned_hospital_id', None) == h_id:
                triage_counts[p.initial_triage_category] = triage_counts.get(p.initial_triage_category, 0) + 1

    print(f"\n👥 Total de Pacientes Procesados: {total_patients}")
    print(f"🏥 Atendidos en Hospital de Origen: {local_admissions} ({(local_admissions/total_patients)*100:.1f}%)")
    print(f"🚑 Trasladados (Load Balancing/Recursos): {total_transfers} ({transfer_rate:.1f}%)\n")

    print("📈 DISTRIBUCIÓN POR NIVEL DE TRIAJE:")
    print(f"   🔴 Resucitación (1): {triage_counts.get('1_Resuscitation', 0):02d}")
    print(f"   🟠 Emergencia (2):   {triage_counts.get('2_Emergent', 0):02d}")
    print(f"   🟡 Urgencia (3):     {triage_counts.get('3_Urgent', 0):02d}")
    print(f"   🟢 Estándar (4):     {triage_counts.get('4_Standard', 0):02d}")
    print(f"   🔵 Rutina (5):       {triage_counts.get('5_Routine', 0):02d}\n")

    print("⚖️ CARGA FINAL DE PACIENTES POR HOSPITAL:")
    
    # Ordenar hospitales de mayor a menor carga
    sorted_hospitals = sorted(
        queues.items(), 
        key=lambda x: len([p for p in x[1] if getattr(p, 'assigned_hospital_id', None) == x[0]]), 
        reverse=True
    )
    
    for h_id, p_list in sorted_hospitals:
        assigned = len([p for p in p_list if getattr(p, 'assigned_hospital_id', None) == h_id])
        # Crear una barra de progreso visual en la consola
        bar = "▓" * assigned + "░" * (15 - assigned if assigned < 15 else 0) 
        print(f"   {h_id} | {assigned:02d} | {bar}")

    print("\n" + "█"*70 + "\n")

def run_simulation(hospitals_path: str, patients_path: str):
    hospitals, patients = load_json_data(hospitals_path, patients_path)
    total_patients_count = len(patients)
    
    hospital_queues: Dict[str, List[Patient]] = {h_id: [] for h_id in hospitals.keys()}
    transferred_patients_log: List[Dict[str, Any]] = []

    print(f"🏥 Iniciando Simulación de Triaje e Ingesta para {total_patients_count} pacientes...\n")

    for idx, patient in enumerate(patients, 1):
        arrival_hosp_id = getattr(patient, 'arrival_hospital_id', 'HOSP-01')
        
        if getattr(patient, 'base_urgency_score', 0.0) == 0.0:
            _calculate_dummy_base_score(patient)
        
        print(f"🔄 [{idx}/{total_patients_count}] Analizando clínicamente a {patient.first_name} {patient.last_name}...")
        
        analyzed_patient = analyze_patient_with_ai(patient)
        current_hospital = hospitals.get(arrival_hosp_id)
        
        missing_resources = get_missing_resources(analyzed_patient, current_hospital) if current_hospital else ["Hospital no encontrado"]
        
        if not missing_resources:
            analyzed_patient.assigned_hospital_id = arrival_hosp_id
            analyzed_patient.status = "Waiting"
            hospital_queues[arrival_hosp_id].append(analyzed_patient)
        else:
            target_hospital_id = find_alternative_hospital(analyzed_patient, hospitals, arrival_hosp_id, hospital_queues)
            analyzed_patient.assigned_hospital_id = target_hospital_id
            analyzed_patient.status = "Transferred"
            
            if target_hospital_id.startswith("HOSP"):
                hospital_queues[target_hospital_id].append(analyzed_patient)
            
            missing_str = ", ".join(missing_resources)
            transferred_patients_log.append({
                "patient_id": analyzed_patient.patient_id,
                "name": f"{analyzed_patient.first_name} {analyzed_patient.last_name}",
                "reason": f"Faltan recursos: [{missing_str}]",
                "transfer_log": f"Trasladado del {arrival_hosp_id} al {target_hospital_id}"
            })

    print("\n⚖️ Ordenando colas de atención prioritarias...")
    for h_id in hospital_queues:
        hospital_queues[h_id].sort(key=lambda p: getattr(p, 'final_priority_score', 0.0), reverse=True)

    print_simulation_report(hospital_queues, transferred_patients_log)
    
    # 🌟 AÑADIDO: Llamada a la nueva función de estadísticas al final del proceso
    print_system_statistics(hospital_queues, transferred_patients_log, total_patients_count)

def print_simulation_report(queues: Dict[str, List[Patient]], transfers: List[Dict[str, Any]]):
    print("\n======================================================================")
    print("📋 REPORTE FINAL DEL ORDEN DE ATENCIÓN POR HOSPITAL")
    print("======================================================================")
    
    for h_id, patient_list in queues.items():
        assigned_patients = [p for p in patient_list if getattr(p, 'assigned_hospital_id', None) == h_id]
        
        print(f"\n🏥 HILO DE ESPERA: {h_id} ({len(assigned_patients)} pacientes en cola)")
        if not assigned_patients:
            print("  (Sin pacientes en espera actualmente)")
        for rank, p in enumerate(assigned_patients, 1):
            score = getattr(p, 'final_priority_score', 0.0)
            print(f"  {rank}°. [Score: {score:.2f}] ID: {p.patient_id} - {p.first_name} {p.last_name} | Triaje: {p.initial_triage_category}")

    print("\n======================================================================")
    print("🚑 REGISTRO DE PACIENTES TRASLADADOS (FUERA DE COLA LOCAL)")
    print("======================================================================")
    if not transfers:
        print("  Ningún paciente requirió traslado.")
    for t in transfers:
        print(f"  🔴 {t['name']} ({t['patient_id']}) -> {t['transfer_log']}\n     ↳ Motivo: {t['reason']}")

if __name__ == "__main__":
    import sys
    from pathlib import Path
    
    sys.path.insert(0, str(Path(__file__).parent.parent)) 
    
    HOSPITALS_JSON = "data/hospitals.json"
    PATIENTS_JSON = "data/patients.json"
    
    if not os.path.exists(HOSPITALS_JSON):
        print(f"❌ Error: No se encontró el archivo de hospitales en: {HOSPITALS_JSON}")
        sys.exit(1)
        
    if not os.path.exists(PATIENTS_JSON):
        print(f"❌ Error: No se encontró el archivo de pacientes en: {PATIENTS_JSON}")
        sys.exit(1)

    run_simulation(HOSPITALS_JSON, PATIENTS_JSON)