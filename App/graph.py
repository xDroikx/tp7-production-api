import os
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

# Usamos importaciones relativas para que no dependa de si la carpeta es 'App' o 'app'
from .state import AgentState
from .agents.supervisor_agent import supervisor_node
from .agents.research_agent import research_node
from .agents.analyst_agent import analyst_node

# 1. Definir nodo de Aprobacion Humana (Accion Critica)
def human_approval_node(state: AgentState):
    """
    Nodo critico que requiere confirmacion humana.
    El grafo se pausara antes de ejecutar este nodo si esta configurado en interrupt_before.
    """
    return {
        "messages": [{
            "role": "system",
            "content": "Accion critica aprobada por el operador humano. Procediendo a finalizar."
        }]
    }

# 2. Construccion del flujo
workflow = StateGraph(AgentState)

workflow.add_node("Supervisor", supervisor_node)
workflow.add_node("Investigador", research_node)
workflow.add_node("Analista", analyst_node)
workflow.add_node("AprobacionHumana", human_approval_node)

# Conexiones de regreso al supervisor
workflow.add_edge("Investigador", "Supervisor")
workflow.add_edge("Analista", "Supervisor")
workflow.add_edge("AprobacionHumana", END)

workflow.add_edge(START, "Supervisor")

def route_next(state: AgentState):
    decision = state.get("next")
    if decision == "FINALIZAR":
        return "AprobacionHumana"  # Pausa antes de la accion critica
    return decision

workflow.add_conditional_edges(
    "Supervisor",
    route_next,
    {
        "Investigador": "Investigador",
        "Analista": "Analista",
        "AprobacionHumana": "AprobacionHumana"
    }
)

# 3. Compilador con memoria y punto de interrupcion HITL
checkpointer = MemorySaver()

# interrupt_before=["AprobacionHumana"] detiene la ejecucion para esperar confirmacion humana
app_graph = workflow.compile(
    checkpointer=checkpointer,
    interrupt_before=["AprobacionHumana"]
)