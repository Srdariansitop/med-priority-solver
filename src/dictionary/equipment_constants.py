"""
Diccionario CONSOLIDADO de todos los equipos médicos posibles en un Hospital Nivel IV.
Mapea nombre de equipo -> descripción de función.
"""

VALID_EQUIPMENT = [
    # ===== SOPORTE VITAL =====
    "ventilator",                       # Respiradores artificiales (soporte ventilatorio)
    "defibrillator",                    # Desfibriladores para paros cardíacos (ACLS)
    "ecmo_machine",                     # ECMO: Oxigenación por membrana extracorpórea (casos extremos)
    "cardiopulmonary_bypass_machine",   # Máquinas de circulación extracorpórea (circulación asistida)
    "crash_cart",                       # Carros de paro equipados (ACLS completo)
    
    # ===== DIAGNÓSTICO POR IMAGEN Y SEÑALES =====
    "x_ray_machine",                    # Salas de Rayos X fijas (radiografía estándar)
    "portable_x_ray",                   # Máquinas de Rayos X portátiles (cabecera)
    "ct_scanner",                       # Tomógrafos/TAC (diagnóstico detallado)
    "mri_machine",                      # Resonancia magnética (sin radiación)
    "ultrasound_machine",               # Ecógrafos (diagnóstico obstétrico, cardiaco, abdominal)
    "fluoroscopy_machine",              # Fluoroscopia (Rayos X en tiempo real)
    
    # ===== MONITOREO Y REGISTROS FISIOLÓGICOS =====
    "ecg_machine",                      # Electrocardiógrafos (registra actividad cardíaca)
    "eeg_machine",                      # Electroencefalogramas (registra actividad cerebral)
    
    # ===== PROCEDIMIENTOS ESPECÍFICOS =====
    "dialysis_machine",                 # Máquinas de diálisis (depuración renal)
    "endoscopy_tower",                  # Torres de endoscopia (procedimientos GI, visualización directa)
    "hyperbaric_chamber",               # Cámaras hiperbáricas (oxigenación hiperbárica, intoxicación CO)
    "incubator",                        # Incubadoras para neonatología (termorregulación)
]

# Mapeo de equipo -> descripción (para referencia)
EQUIPMENT_DESCRIPTIONS = {equip: VALID_EQUIPMENT[i] for i, equip in enumerate(VALID_EQUIPMENT)}

