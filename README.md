# Pre-entrega 7: API de Producción, Orquestación Asíncrona y Monitoreo Activo

Este repositorio implementa una API REST asíncrona construida con **FastAPI** que expone un sistema multi-agente orquestado mediante **LangGraph**, respaldado por **Redis** para la gestión de estados y persistencia de checkpoints, e integrado con **Arize Phoenix** para observabilidad, análisis de latencias y costos.

---

## 🏗️ Arquitectura del Sistema

- **FastAPI (API Asíncrona)**: Endpoint no bloqueante (`POST /tasks`) que encola trabajos en segundo plano (`BackgroundTasks`) y retorna de inmediato un `task_id` con estado HTTP `202 Accepted`.
- **Persistencia de Estado (Redis / Memory)**: Almacenamiento desacoplado del estado del ciclo de vida de los trabajos (`PENDING`, `IN_PROGRESS`, `PAUSED_FOR_APPROVAL`, `COMPLETED`, `FAILED`).
- **LangGraph Multi-Agente**:
  - **Supervisor**: Coordina la delegación hacia los agentes especializados o decide finalizar.
  - **Investigador**: Recopila datos de ventas y costos.
  - **Analista**: Computa métricas financieras y márgenes de ganancia.
- **Human-in-the-Loop (HITL)**: Implementación de `interrupt_before` en nodos de acción crítica (`AprobacionHumana`). El sistema pausa la ejecución hasta que un operador humano confirma mediante `POST /tasks/{task_id}/approve`.
- **Capa de Observabilidad (Arize Phoenix & OpenInference)**: Instrumentación automática de trazas de ejecución, cálculo de latencias (p95) y registro de consumo de tokens.

---

## 📂 Estructura del Repositorio

```text
tp7_repo/
├── App/
│   ├── __init__.py
│   ├── main.py            # API FastAPI y gestión de endpoints asíncronos
│   ├── graph.py           # Orquestador LangGraph con memoria e interrupción HITL
│   ├── state.py           # Esquemas de estado de los agentes (AgentState)
│   ├── worker.py          # Adaptador de persistencia de tareas en Redis/FakeRedis
│   ├── observability.py   # Configuración de instrumentación con Arize Phoenix
│   └── agents/
│       ├── __init__.py
│       ├── supervisor_agent.py
│       ├── research_agent.py
│       └── analyst_agent.py
├── screenshots/           # Evidencias de observabilidad y flujo HITL
│   ├── 01_hitl_paused.png
│   ├── 02_hitl_completed.png
│   └── 03_phoenix_traces.png
├── requirements.txt
├── docker-compose.yml
├── .env.example
└── README.md