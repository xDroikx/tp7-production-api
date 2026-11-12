import os

def setup_observability():
    """Configura la instrumentacion de trazas sin bloquear el arranque de FastAPI."""
    try:
        from openinference.instrumentation.langchain import LangChainInstrumentor
        LangChainInstrumentor().instrument()
        print("🔭 Instrumentacion de observabilidad activada.")
    except Exception as e:
        print(f"⚠️ No se pudo instrumentar LangChain: {e}")

    try:
        import phoenix as px
        # Intentamos iniciar la sesion sin bloquear
        session = px.launch_app(run_in_thread=True)
        print(f"🔭 Phoenix UI disponible en: {session.url}")
        return session
    except Exception as e:
        print(f"⚠️ Phoenix UI local no disponible ({e}). Continuando con la API...")
        return None