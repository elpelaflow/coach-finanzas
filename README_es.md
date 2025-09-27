# Coach Financiero IA - App Multi-Agente en Streamlit

El **Coach Financiero IA** es una aplicacion modular en Streamlit que coordina un equipo de agentes financieros mediante un bus de mensajes compartido. Cada especialista se enfoca en presupuesto, ahorro, deudas, inversiones o asesoramiento, mientras que un Manager conversacional organiza la ronda y mantiene informada a la persona usuaria. Los resultados aparecen tanto en los tableros clasicos como en la nueva pestaNa *Equipo IA*, donde se visualiza la conversacion interna peer-to-peer.

## Capacidades Clave

- **Equipo de agentes en modo colaborativo**
  - El agente Manager recopila contexto, aclara dudas y publica briefs con delegaciones.
  - Los agentes de Presupuesto, Ahorro, Deuda y (opcional) Inversion se coordinan usando mensajes tipados (`FINDING`, `ALERT`, `PROPOSAL`, etc.).
  - El agente Advisor sintetiza la ronda en pasos accionables para la persona usuaria.
- **Personalidades impulsadas por prompts**
  - Cada agente carga su prompt desde `ai_financial_coach/prompts/*.txt`, permitiendo ajustar tono y comportamiento sin modificar codigo.
  - Un protocolo compartido define reglas de mensajeria para asegurar consistencia entre agentes.
- **Estado compartido y bus de mensajes**
  - `SharedState` centraliza inputs, objetivos, hallazgos, planes y el log cronologico.
  - Cursores incrementales evitan loops al procesar solo la informacion nueva.
- **Experiencia de UI dual**
  - Las pestaNas existentes de *Movimientos*, *Presupuesto*, *Ahorro* y *Deuda* mantienen sus metricas y graficos.
  - La nueva pestaNa *Equipo IA* ofrece chat con el Manager, resumen de objetivos, lista de delegaciones y timeline filtrable de la conversacion interna.

## Estructura del Proyecto

```
ai_financial_coach/
+-- app/
|   +-- main.py              # Punto de entrada Streamlit
|   +-- dashboard.py         # UI multi pestaNa y flujo de analisis
|   +-- components.py        # Componentes visuales reutilizables
|   +-- context.py           # Estado compartido y fabrica de agentes
+-- agents/
|   +-- *.py                 # Manager, Budget, Savings, Debt, Investment, Advisor
|   +-- team.py              # Orquestacion de rondas y carga de prompts
+-- core/
|   +-- base_agent.py        # Interfaz comun para agentes
|   +-- state.py             # SharedState y helpers
|   +-- message_bus.py       # Bus interno con cursores
|   +-- prompts.py           # Utilidades para cargar prompts
|   +-- system.py            # Analisis simple de compatibilidad heredado
|   +-- database.py          # Helpers SQLite para movimientos
|   +-- schemas.py           # Modelos y enums Pydantic
+-- prompts/
    +-- 00_shared_protocol.txt
    +-- manager_agent.txt
    +-- budget_agent.txt
    +-- savings_agent.txt
    +-- debt_agent.txt
    +-- investment_agent.txt
    +-- advisor_agent.txt
```

La implementacion monolitica anterior sigue disponible como `ai_financial_coach_agent_backup.py` para consulta.

## Puesta en Marcha

1. **Instalar dependencias**
   ```bash
   pip install -r requirements.txt
   ```
2. **Opcional:** configurar credenciales de OpenRouter si se conectara a un LLM. El esqueleto actual funciona sin llamadas de red, pero el cliente espera `OPENROUTER_API_KEY` cuando se active.
   ```bash
   export OPENROUTER_API_KEY=tu_clave
   ```
3. **Lanzar Streamlit**
   ```bash
   streamlit run ai_financial_coach_agent.py
   ```

## Configuracion del LLM

1. Crea un archivo `.env` en la raiz del proyecto (ya incluido en este repositorio).
2. Agrega tu clave de OpenRouter (o reemplaza la existente) con el siguiente formato:
   ```
   OPENROUTER_API_KEY="tu_clave_openrouter"
   ```
3. Al iniciar la app de Streamlit, la clave se carga automaticamente gracias a `python-dotenv`.
4. Para cambiar de modelo, define `OPENROUTER_MODEL` o usa el valor por defecto `openrouter/auto`.

Si prefieres definir la clave de forma temporal, exportala antes de ejecutar Streamlit:
```bash
export OPENROUTER_API_KEY=tu_clave_openrouter
```
```
setx OPENROUTER_API_KEY "tu_clave_openrouter"  # Windows
```

## Uso del Tablero

- Registra ingresos, gastos y deudas en la pestaNa **Movimientos** y ejecuta *Analizar finanzas* para iniciar la ronda.
- Revisa los indicadores clasicos en **Presupuesto**, **Ahorro** y **Deuda** (se alimentan del estado compartido poblado por los agentes).
- Ingresa a **Equipo IA** para chatear con el Manager, consultar objetivos, ver delegaciones, disparar nuevas rondas y filtrar el timeline interno por agente o tipo de mensaje.

## Edicion de Prompts

Los prompts residen en `ai_financial_coach/prompts/`. Modifica los archivos de texto para ajustar tono o protocolos. Reinicia la app de Streamlit para recargar los cambios o agrega un control que invoca `reload_prompts()` desde `app/context.py` si necesitas recarga en caliente.

---

Sugerencias para extender el flujo multi-agente (persistencia, integracion con LLM reales, tests automatizados) son bienvenidas: abre un issue o comparte feedback.
