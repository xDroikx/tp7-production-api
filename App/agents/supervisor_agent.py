import os
from typing import Literal
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage

from ..state import AgentState

class SupervisorDecision(BaseModel):
    next: Literal["Investigador", "Analista", "FINALIZAR"] = Field(
        ...,
        description="El siguiente agente a delegar ('Investigador', 'Analista') o 'FINALIZAR' cuando ambos hayan respondido o la respuesta este completa."
    )
    razon: str = Field(
        default="",
        description="Justificación breve de la decisión."
    )

def supervisor_node(state: AgentState):
    """Nodo Supervisor con corte garantizado para evitar bucles de recursion."""
    mensajes = list(state.get("messages", []))
    
    # Inspeccionamos los remitentes o contenidos en el historial
    textos_historial = " ".join([m.content for m in mensajes if hasattr(m, 'content')])
    
    tiene_investigacion = "ventas" in textos_historial.lower() or "costos" in textos_historial.lower()
    tiene_analisis = "margen" in textos_historial.lower() or "%" in textos_historial or "ganancia" in textos_historial.lower()

    # Si ya participaron ambos o si el historial tiene mas de 3 respuestas de agentes, forzar FINALIZAR
    if (tiene_investigacion and tiene_analisis) or len(mensajes) >= 5:
        return {"next": "FINALIZAR"}

    llm = ChatOpenAI(
        model=os.getenv("OPENAI_MODEL_NAME", "gpt-4o-mini"),
        temperature=0.0
    )

    system_prompt = (
        "Eres el supervisor del flujo de trabajo multi-agente.\n"
        "Tu equipo:\n"
        "- 'Investigador': Aporta datos de ventas y costos.\n"
        "- 'Analista': Calcula el margen de ganancia a partir de los datos investigados.\n\n"
        "Reglas estrictas:\n"
        "1. Si el usuario hace una pregunta y nadie ha investigado ventas/costos, delega a 'Investigador'.\n"
        "2. Si el Investigador ya dio las cifras y falta el calculo de margen, delega a 'Analista'.\n"
        "3. Si ya se calcularon los margenes o ya respondieron ambos, selecciona OBLIGATORIAMENTE 'FINALIZAR'."
    )

    structured_llm = llm.with_structured_output(SupervisorDecision)

    try:
        decision: SupervisorDecision = structured_llm.invoke(
            [SystemMessage(content=system_prompt)] + mensajes
        )
        next_step = decision.next
    except Exception:
        # Fallback de seguridad
        if not tiene_investigacion:
            next_step = "Investigador"
        elif not tiene_analisis:
            next_step = "Analista"
        else:
            next_step = "FINALIZAR"

    return {"next": next_step}