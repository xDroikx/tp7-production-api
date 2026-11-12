import uuid
from fastapi import FastAPI, BackgroundTasks, HTTPException, status
from pydantic import BaseModel, Field
from langchain_core.messages import HumanMessage

from App.observability import setup_observability
from App.worker import save_task, get_task
from App.graph import app_graph

# Iniciar observabilidad con Arize Phoenix
setup_observability()

app = FastAPI(
    title="Orquestador Multi-Agente Asincrono - TP 7",
    version="1.0.0",
    description="API de produccion con LangGraph, Redis y Human-in-the-Loop"
)

# Esquemas de entrada y salida
class CreateTaskRequest(BaseModel):
    query: str = Field(..., example="Necesito averiguar las ventas y costos de la empresa y calcular el margen.")

class TaskResponse(BaseModel):
    task_id: str
    status: str
    message: str

def run_agent_workflow(task_id: str, query: str):
    """Funcion de fondo que ejecuta el grafo y detecta interrupciones HITL."""
    config = {"configurable": {"thread_id": task_id}, "recursion_limit": 15}
    save_task(task_id, {"status": "IN_PROGRESS", "query": query, "result": None})

    try:
        # Ejecuta el grafo hasta que finalice o se detenga en interrupt_before
        for _ in app_graph.stream({"messages": [HumanMessage(content=query)]}, config=config):
            pass

        state = app_graph.get_state(config)
        
        # Verificar si quedo pausado en el nodo de aprobacion humana
        if state.next and "AprobacionHumana" in state.next:
            mensajes = [m.content for m in state.values.get("messages", [])]
            save_task(task_id, {
                "status": "PAUSED_FOR_APPROVAL",
                "query": query,
                "history": mensajes,
                "detail": "Esperando aprobacion humana antes de concluir la accion critica."
            })
        else:
            mensajes = [m.content for m in state.values.get("messages", [])]
            save_task(task_id, {
                "status": "COMPLETED",
                "query": query,
                "result": mensajes[-1] if mensajes else "Completado"
            })
    except Exception as e:
        save_task(task_id, {"status": "FAILED", "error": str(e)})

@app.post("/tasks", status_code=status.HTTP_202_ACCEPTED, response_model=TaskResponse)
async def create_task(req: CreateTaskRequest, background_tasks: BackgroundTasks):
    """Crea una nueva tarea asincrona y la delega al sistema multi-agente."""
    task_id = str(uuid.uuid4())
    save_task(task_id, {"status": "PENDING", "query": req.query})
    background_tasks.add_task(run_agent_workflow, task_id, req.query)
    
    return TaskResponse(
        task_id=task_id,
        status="ACCEPTED",
        message="Tarea recibida y encolada para procesamiento asincrono."
    )

@app.get("/tasks/{task_id}")
async def get_task_status(task_id: str):
    """Consulta el estado, historial y resultado de una tarea en proceso o pausada."""
    task = get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    return {"task_id": task_id, "data": task}

@app.post("/tasks/{task_id}/approve")
async def approve_task(task_id: str, background_tasks: BackgroundTasks):
    """Reanuda la ejecucion del agente tras la confirmacion del operador humano."""
    task = get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    
    if task.get("status") != "PAUSED_FOR_APPROVAL":
        raise HTTPException(status_code=400, detail="La tarea no esta esperando aprobacion.")

    def resume_workflow():
        config = {"configurable": {"thread_id": task_id}}
        for _ in app_graph.stream(None, config=config):
            pass
        state = app_graph.get_state(config)
        mensajes = [m.content for m in state.values.get("messages", [])]
        save_task(task_id, {
            "status": "COMPLETED",
            "query": task.get("query"),
            "result": mensajes[-1] if mensajes else "Aprobado y completado"
        })

    background_tasks.add_task(resume_workflow)
    return {"task_id": task_id, "status": "RESUMED", "message": "Aprobacion recibida. Concluyendo proceso."}