# specialists_constants.py
"""
Diccionario CONSOLIDADO de todos los especialistas médicos posibles en un Hospital Nivel IV.
Mapea nombre de especialista -> descripción de rol.
"""

VALID_SPECIALISTS = [
    # Especialidades Base y Críticas
    "triage_nurse",                      # Atienden la puerta, determinan el AVPU inicial
    "general_doctor",                    # Médicos de urgencias (Filtro inicial)
    "intensivist",                       # Médicos de UCI (Cruciales para pacientes críticos)
    "anesthesiologist",                  # Indispensables para quirófano o intubaciones difíciles
    
    # Especialidades Médicas
    "cardiologist",                      # Infartos, arritmias graves
    "neurologist",                       # ACV, convulsiones
    "pulmonologist",                     # Fallo respiratorio severo
    "gastroenterologist",                # Sangrado digestivo masivo
    "nephrologist",                      # Falla renal aguda
    "endocrinologist",                   # Cetoacidosis diabética, crisis tiroidea
    "hematologist",                      # Trastornos de coagulación severos
    "oncologist",                        # Complicaciones oncológicas agudas
    "infectious_disease_specialist",     # Sepsis, infecciones raras
    "rheumatologist",                    # Brotes autoinmunes severos
    "toxicologist",                      # Sobredosis, envenenamientos
    
    # Especialidades Quirúrgicas
    "general_surgeon",                   # Apendicitis, traumas abdominales
    "cardiovascular_surgeon",            # Aneurismas, traumas de grandes vasos
    "neurosurgeon",                      # Traumas craneales, hematomas cerebrales
    "orthopedic_surgeon",                # Fracturas expuestas, poli-traumatismos
    "plastic_surgeon",                   # Reconstrucción de tejidos blandos
    "burn_surgeon",                      # Cirujanos especialistas en grandes quemados
    "maxillofacial_surgeon",             # Traumas faciales severos
    "urologist",                         # Cálculos renales obstructivos, trauma pélvico
    "otolaryngologist",                  # Obstrucciones severas de vía aérea superior
    
    # Especialidades Poblacionales y Específicas
    "pediatrician",                      # Pacientes < 18 años
    "neonatologist",                     # Recién nacidos en estado crítico
    "obstetrician",                      # Pacientes embarazadas (parto/emergencias obstétricas)
    "gynecologist",                      # Emergencias ginecológicas
    "psychiatrist",                      # Brotes psicóticos, riesgo suicida
    "ophthalmologist",                   # Traumas oculares severos
]

# Mapeo de especialista -> descripción (para referencia)
SPECIALIST_DESCRIPTIONS = {spec: VALID_SPECIALISTS[i] for i, spec in enumerate(VALID_SPECIALISTS)}

