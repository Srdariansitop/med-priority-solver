# equipment_constants.py

VALID_EQUIPMENT = [
    # Soporte Vital
    "ventilator", "defibrillator", "ecmo_machine", # ECMO: Oxigenación por membrana extracorpórea (casos extremos)
    "cardiopulmonary_bypass_machine", "crash_cart",
    
    # Diagnóstico por Imagen y Señales
    "ct_scanner", "mri_machine", "x_ray_machine", "portable_x_ray",
    "ultrasound_machine", "ecg_machine", "eeg_machine", # EEG: Electroencefalograma (cerebro)
    "fluoroscopy_machine",
    
    # Procedimientos Específicos
    "dialysis_machine", "endoscopy_tower", "hyperbaric_chamber",
    "incubator" # Para neonatología
]