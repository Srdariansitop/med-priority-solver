"""
generar_reporte.py (OPTIMIZADO)
- Ejecuta la simulación UNA SOLA VEZ para experimentos 1 y 2.
- Guarda resultados en cache para regenerar reportes sin re-simular.
- Experimento de volumen (10,50,100) se ejecuta bajo demanda (usa pacientes del dataset).
"""

import os, sys, json, statistics, random, pickle
from pathlib import Path
from datetime import datetime
from collections import Counter, defaultdict
from typing import List, Dict, Any

sys.path.insert(0, str(Path(__file__).parent.parent))

from models import Patient
from simulation_engine import (
    load_json_data,
    simulate_time_interval,
    apply_dynamic_scoring,
    MANCHESTER_LIMITS,
    _get_clinical_summary
)

REPORTS_DIR = Path("reports")
CACHE_FILE = REPORTS_DIR / "ultima_simulacion_cache.pkl"

# ----------------------------------------------------------------------
# Funciones de métricas (idénticas a las tuyas)
# ----------------------------------------------------------------------
def calcular_metricas_hospital(global_queues, transfer_log, tiempo_final):
    metricas = {}
    for h_id, cola in global_queues.items():
        apply_dynamic_scoring(cola, tiempo_final)
        total = len(cola)
        tiempos = [p.time_waiting_min for p in cola]
        scores = [p.final_priority_score for p in cola]
        prom_espera = statistics.mean(tiempos) if tiempos else 0.0
        prom_score = statistics.mean(scores) if scores else 0.0
        if cola:
            top = max(cola, key=lambda p: p.final_priority_score)
            top_str = f"{top.first_name} {top.last_name} ({top.final_priority_score:.1f})"
        else:
            top_str = "N/A"
        metricas[h_id] = {
            "total_pacientes": total,
            "promedio_espera_min": round(prom_espera, 2),
            "promedio_score": round(prom_score, 2),
            "top_paciente": top_str
        }
    traslados_origen = Counter(t["origin"] for t in transfer_log)
    traslados_destino = Counter(t["target"] for t in transfer_log)
    return metricas, traslados_origen, traslados_destino

def calcular_metricas_pacientes(global_queues, transfer_log, tiempo_final):
    pacientes_info = []
    for h_id, cola in global_queues.items():
        apply_dynamic_scoring(cola, tiempo_final)
        for p in cola:
            sobrepasa = p.time_waiting_min - p.max_safe_wait_time_min
            estado = "⚠️ Sobrepasado" if sobrepasa > 0 else "✅ Dentro de límite"
            especialistas = getattr(p, 'requires_specialist', [])
            equipos = getattr(p, 'requires_equipment', [])
            total_rec = len(especialistas) + len(equipos)
            pacientes_info.append({
                "hospital": h_id,
                "id": p.patient_id,
                "nombre": f"{p.first_name} {p.last_name}",
                "score_final": round(p.final_priority_score, 2),
                "score_llm_base": round(getattr(p, 'llm_base_score', 0.0), 2),
                "tiempo_espera_min": p.time_waiting_min,
                "limite_seguro_min": p.max_safe_wait_time_min,
                "sobrepasa_por_min": sobrepasa,
                "estado": estado,
                "triage_inicial": p.initial_triage_category,
                "sintomas": getattr(p, 'reported_symptoms', []),
                "cronicos": getattr(p, 'chronic_diseases', []),
                "total_recursos": total_rec,
                "requiere_especialistas": especialistas,
                "requiere_equipos": equipos,
                "trasladado": any(t["patient_id"] == p.patient_id for t in transfer_log)
            })
    traslados_detalle = [{
        "paciente_id": t["patient_id"],
        "nombre": t["name"],
        "origen": t["origin"],
        "destino": t["target"],
        "motivo": t["reason"],
        "clinica": t["clin_ctx"]
    } for t in transfer_log]
    return pacientes_info, traslados_detalle

# ----------------------------------------------------------------------
# Reportes (sin cambios)
# ----------------------------------------------------------------------
def generar_reporte_hospitales(metricas, tras_origen, tras_destino, ruta):
    with open(ruta, "w", encoding="utf-8") as f:
        f.write("# 📊 Reporte de Métricas por Hospital\n\n")
        f.write("| Hospital | Total | Espera Prom. | Score Prom. | Paciente más prioritario |\n")
        f.write("|----------|-------|--------------|-------------|---------------------------|\n")
        for h_id, m in metricas.items():
            f.write(f"| {h_id} | {m['total_pacientes']} | {m['promedio_espera_min']} | {m['promedio_score']} | {m['top_paciente']} |\n")
        f.write("\n## Traslados originados\n")
        if tras_origen:
            f.write("| Origen | Cantidad |\n|--------|----------|\n")
            for h, c in tras_origen.most_common():
                f.write(f"| {h} | {c} |\n")
        f.write("\n## Traslados recibidos\n")
        if tras_destino:
            f.write("| Destino | Cantidad |\n|---------|----------|\n")
            for h, c in tras_destino.most_common():
                f.write(f"| {h} | {c} |\n")
    print(f"✅ Hospitales → {ruta}")

def generar_reporte_pacientes(pacientes_info, traslados_detalle, ruta):
    with open(ruta, "w", encoding="utf-8") as f:
        f.write("# 👥 Reporte Detallado de Pacientes\n\n")
        f.write("| Hosp | ID | Nombre | Score | LLM | Espera | Límite | Sobrepasa | Estado | Triaje |\n")
        f.write("|------|----|--------|-------|-----|--------|--------|-----------|--------|--------|\n")
        for p in sorted(pacientes_info, key=lambda x: x["score_final"], reverse=True):
            f.write(f"| {p['hospital']} | {p['id']} | {p['nombre']} | {p['score_final']} | {p['score_llm_base']} | {p['tiempo_espera_min']} | {p['limite_seguro_min']} | {p['sobrepasa_por_min']} | {p['estado']} | {p['triage_inicial']} |\n")
        # Triaje vs espera
        grupos = defaultdict(list)
        for p in pacientes_info:
            grupos[p["triage_inicial"]].append(p["tiempo_espera_min"])
        f.write("\n## Triaje vs Espera\n| Triaje | Espera Prom. | Pacientes |\n|--------|--------------|----------|\n")
        for tri, tiempos in sorted(grupos.items()):
            f.write(f"| {tri} | {statistics.mean(tiempos):.2f} | {len(tiempos)} |\n")
        # Recursos top
        top_rec = sorted(pacientes_info, key=lambda x: x["total_recursos"], reverse=True)[:10]
        f.write("\n## Top 10 Pacientes con más recursos\n| Hosp | ID | Nombre | Recursos | Especialistas | Equipos |\n|------|----|--------|----------|---------------|--------|\n")
        for p in top_rec:
            esp = ", ".join(p["requiere_especialistas"]) or "Ninguno"
            eq = ", ".join(p["requiere_equipos"]) or "Ninguno"
            f.write(f"| {p['hospital']} | {p['id']} | {p['nombre']} | {p['total_recursos']} | {esp} | {eq} |\n")
        # Síntomas/crónicos
        f.write("\n## Síntomas con mayor score\n| Síntoma | Score Prom. | Pacientes |\n|---------|------------|----------|\n")
        sintomas = defaultdict(list)
        for p in pacientes_info:
            for s in p["sintomas"]:
                sintomas[s].append(p["score_final"])
        for s, sc in sorted(sintomas.items(), key=lambda x: statistics.mean(x[1]), reverse=True):
            f.write(f"| {s} | {statistics.mean(sc):.2f} | {len(sc)} |\n")
        # Crónicos
        cronicos = defaultdict(list)
        for p in pacientes_info:
            for c in p["cronicos"]:
                cronicos[c].append(p["score_final"])
        f.write("\n## Crónicos con mayor score\n| Enfermedad | Score Prom. | Pacientes |\n|------------|------------|----------|\n")
        for c, sc in sorted(cronicos.items(), key=lambda x: statistics.mean(x[1]), reverse=True):
            f.write(f"| {c} | {statistics.mean(sc):.2f} | {len(sc)} |\n")
        # Traslados
        f.write("\n## Traslados\n")
        if traslados_detalle:
            f.write("| ID | Nombre | Origen | Destino | Motivo | Clínica |\n|----|--------|--------|---------|--------|--------|\n")
            for t in traslados_detalle:
                f.write(f"| {t['paciente_id']} | {t['nombre']} | {t['origen']} | {t['destino']} | {t['motivo']} | {t['clinica']} |\n")
        else:
            f.write("No hubo traslados.\n")
    print(f"✅ Pacientes → {ruta}")

def generar_reporte_volumen(resultados, ruta):
    with open(ruta, "w", encoding="utf-8") as f:
        f.write("# 📈 Impacto del Volumen de Pacientes\n\n")
        f.write("| N° Pacientes | Espera Prom. | Traslados | Hospital más ocupado (pac.) | Sobrepasaron límite |\n")
        f.write("|--------------|-------------|-----------|-----------------------------|---------------------|\n")
        for r in resultados:
            f.write(f"| {r['num_pacientes']} | {r['espera_promedio']} | {r['total_traslados']} | {r['hospital_mas_ocupado']} ({r['max_ocupacion']}) | {r['sobrepasados']} |\n")
    print(f"✅ Volumen → {ruta}")

# ----------------------------------------------------------------------
# SIMULACIÓN ÚNICA PARA EXPERIMENTOS 1 Y 2
# ----------------------------------------------------------------------
def ejecutar_simulacion_principal_y_cachear():
    """Corre la simulación con patients.json y guarda resultados en caché."""
    print("🔄 Ejecutando simulación principal (pacientes fijos)...")
    hospitals, patients = load_json_data("data/hospitals.json", "data/patients.json")
    global_queues = {h_id: [] for h_id in hospitals}
    transfer_log = []
    tiempo_final = simulate_time_interval(patients, hospitals, global_queues, transfer_log, "Simulación base")
    # Guardar en caché
    REPORTS_DIR.mkdir(exist_ok=True)
    with open(CACHE_FILE, "wb") as f:
        pickle.dump({
            "global_queues": global_queues,
            "transfer_log": transfer_log,
            "tiempo_final": tiempo_final
        }, f)
    print("✅ Simulación completada y cacheada.")
    return global_queues, transfer_log, tiempo_final

def cargar_cache():
    if CACHE_FILE.exists():
        with open(CACHE_FILE, "rb") as f:
            data = pickle.load(f)
        return data["global_queues"], data["transfer_log"], data["tiempo_final"]
    return None, None, None

# ----------------------------------------------------------------------
# Experimentos
# ----------------------------------------------------------------------
def experimento_hospitales(global_queues, transfer_log, tiempo_final):
    metricas, to, td = calcular_metricas_hospital(global_queues, transfer_log, tiempo_final)
    generar_reporte_hospitales(metricas, to, td, REPORTS_DIR / "experimento_hospitales.md")

def experimento_pacientes(global_queues, transfer_log, tiempo_final):
    p_info, t_det = calcular_metricas_pacientes(global_queues, transfer_log, tiempo_final)
    generar_reporte_pacientes(p_info, t_det, REPORTS_DIR / "experimento_pacientes.md")

def experimento_volumen():
    """
    Experimento de volumen: toma pacientes reales del dataset (patients.json)
    en muestras de 10, 50 y 100 para medir el impacto en el sistema sin depender de la API.
    """
    print("⚙️ Iniciando experimento de volumen (usando pacientes del dataset, sin API)...")
    hospitals, all_patients = load_json_data("data/hospitals.json", "data/patients.json")
    tamanos = [10, 50, 100]
    resultados = []

    for n in tamanos:
        print(f"   Simulando con {n} pacientes (muestra aleatoria del dataset)...")
        # Si hay menos pacientes en el dataset de los que se piden, usamos reemplazo
        if n > len(all_patients):
            muestra = random.choices(all_patients, k=n)
        else:
            muestra = random.sample(all_patients, n)

        # Ordenamos por tiempo de llegada para mantener coherencia temporal
        muestra.sort(key=lambda x: x.arrival_time)

        # Asignar límites Manchester y distribuir aleatoriamente entre hospitales
        for p in muestra:
            p.max_safe_wait_time_min = MANCHESTER_LIMITS.get(getattr(p, 'initial_triage_category', '4_Standard'), 120)
            p.arrival_hospital_id = random.choice(list(hospitals.keys()))

        queues = {h_id: [] for h_id in hospitals}
        trans = []
        t_fin = simulate_time_interval(muestra, hospitals, queues, trans, f"Vol {n}")

        todos = []
        for cola in queues.values():
            todos.extend(cola)
        apply_dynamic_scoring(todos, t_fin)

        espera = statistics.mean([p.time_waiting_min for p in todos]) if todos else 0
        ocupacion = {h: len(q) for h, q in queues.items()}
        mas_ocupado = max(ocupacion, key=ocupacion.get)
        sobre = sum(1 for p in todos if p.time_waiting_min > p.max_safe_wait_time_min)

        resultados.append({
            "num_pacientes": n,
            "espera_promedio": round(espera, 2),
            "total_traslados": len(trans),
            "hospital_mas_ocupado": mas_ocupado,
            "max_ocupacion": ocupacion[mas_ocupado],
            "sobrepasados": sobre
        })

    generar_reporte_volumen(resultados, REPORTS_DIR / "experimento_volumen.md")

# ----------------------------------------------------------------------
# Menú principal
# ----------------------------------------------------------------------
def menu():
    REPORTS_DIR.mkdir(exist_ok=True)
    # Intentar cargar caché para evitar re-simular si ya existe
    gq, tl, tf = cargar_cache()
    if gq is not None:
        print("📦 Datos de simulación en caché encontrados. ¿Desea usarlos? (s/n): ", end="")
        resp = input().strip().lower()
        if resp != 's':
            gq, tl, tf = None, None, None

    while True:
        print("\n" + "="*50)
        print(" 📊 GENERADOR DE REPORTES (Optimizado)")
        print("="*50)
        print("1. Ejecutar simulación base y generar reportes 1+2")
        print("2. Generar reportes 1+2 desde caché (sin re-simular)")
        print("3. Experimento de Volumen (10,50,100) – tarda más")
        print("4. TODO: simulación base + volumen + reportes")
        print("5. Salir")
        op = input("Opción: ").strip()

        if op == "1":
            gq, tl, tf = ejecutar_simulacion_principal_y_cachear()
            experimento_hospitales(gq, tl, tf)
            experimento_pacientes(gq, tl, tf)
        elif op == "2":
            if gq is None:
                print("❌ No hay caché. Ejecute primero la opción 1.")
            else:
                experimento_hospitales(gq, tl, tf)
                experimento_pacientes(gq, tl, tf)
        elif op == "3":
            experimento_volumen()
        elif op == "4":
            if gq is None:
                gq, tl, tf = ejecutar_simulacion_principal_y_cachear()
            else:
                print("ℹ️ Usando datos en caché para reportes 1+2.")
            experimento_hospitales(gq, tl, tf)
            experimento_pacientes(gq, tl, tf)
            experimento_volumen()
        elif op == "5":
            print("👋 Saliendo.")
            break
        else:
            print("❌ Opción inválida.")

if __name__ == "__main__":
    menu()