# 🏥 Medical Priority Solver

<p align="center">
  <img src="img.png" width="700">
</p>

Sistema inteligente de priorización clínica para servicios de urgencias con recursos limitados. Combina un LLM externo (Groq) para generar pacientes sintéticos con notas de triaje realistas, y un LLM local (Qwen2.5-0.5B) para analizar el lenguaje natural, ajustar la urgencia y sugerir recursos necesarios. El sistema incluye un motor de scoring fisiológico (basado en signos vitales, comorbilidades y tiempos de espera), un módulo de simulación temporal con traslados automáticos entre hospitales de distinta complejidad, y una arquitectura modular que permite probar y extender cada componente de forma aislada. Los datos generados y los resultados de la simulación se almacenan en JSON para su posterior análisis.

## 🤖 Configuración del uso del LLMS

El sistema utiliza dos modelos de lenguaje con propósitos distintos:

* **Groq (LLM externo)**: utiliza `llama-3.3-70b-versatile` para generar notas de triaje realistas durante la creación del dataset de pacientes sintéticos. La autenticación se realiza mediante la variable de entorno `GROQ_API_KEY`.

* **Modelo local (Transformers)**: utiliza `Qwen/Qwen2.5-0.5B-Instruct` para analizar pacientes dentro del simulador, ajustando prioridades y sugiriendo recursos médicos. Se ejecuta automáticamente en GPU (float16) si está disponible o en CPU (float32), sin necesidad de API ni costes adicionales.

Esta separación permite aprovechar la calidad de un LLM grande para generar datos clínicos y la rapidez y privacidad de un modelo local para la toma de decisiones en tiempo real.

## 🚀 Requisitos previos

* Python 3.10 o superior.
* Git (opcional, para clonar el repositorio).
* Una clave API de Groq para la generación de pacientes sintéticos.

## 📦 Configuración

### 1. Clonar el repositorio

```bash
git clone https://github.com/tu-usuario/tu-repo.git
cd tu-repo
```

### 2. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 3. Configurar Groq

Crear un archivo `.env` en la raíz del proyecto:

```env
GROQ_API_KEY=tu_clave_aqui
```

### 4. Modelo local

El modelo `Qwen/Qwen2.5-0.5B-Instruct` se descargará automáticamente en su primer uso. No requiere configuración adicional, aunque necesita conexión a Internet la primera vez.

## 🧪 Prueba del sistema

Ejecuta el script de prueba:

```bash
python analyzer/test_hybrid_triage.py
```

El sistema generará pacientes sintéticos usando Groq y posteriormente los analizará mediante el modelo local, mostrando el razonamiento de la IA y la prioridad final de cada paciente.

## 🏥 Ejecución del entorno de simulación

Para ejecutar el simulador, debe ejecutarse el siguiente comando desde la raíz del proyecto:

```bash
python src/simulation_engine.py
```

Al iniciar el programa se mostrará un menú interactivo con las siguientes opciones:

* **Analizar el Sistema de Hospitales Completo (Red Global):** Ejecuta la simulación utilizando todos los pacientes disponibles en data y permite evaluar el comportamiento global de la red hospitalaria, incluyendo colas, prioridades y traslados.

* **Analizar por Hospital Específico:** Filtra la simulación a un único hospital, permitiendo estudiar su carga de pacientes, recursos disponibles y gestión interna de prioridades.

* **Generar y Analizar 5 Pacientes Aleatorios (Prueba de Estrés):** Genera nuevos pacientes sintéticos mediante Groq y evalúa la respuesta del sistema ante casos clínicos nuevos.

* **Salir:** Finaliza la ejecución del simulador.

