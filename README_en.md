# AI Financial Coach - Multi-Agent Streamlit App

The **AI Financial Coach** is a modular Streamlit application that orchestrates a team of financial agents through a shared message bus. Each specialist focuses on budget, savings, debt, investments, or advisory insights while a conversational Manager coordinates the workflow and keeps the user in the loop. Results are surfaced in the classic financial dashboards plus a new *Equipo IA* tab that reveals the internal peer-to-peer conversation.

## Key Capabilities

- **Peer-to-Peer Agent Team**
  - Manager agent collects context from the user, clarifies gaps, and publishes briefs with delegations.
  - Budget, Savings, Debt, and (optional) Investment agents collaborate through the bus using typed messages (`FINDING`, `ALERT`, `PROPOSAL`, etc.).
  - Advisor agent synthesises the round into human-friendly action steps.
- **Prompt-Driven Personalities**
  - Every agent loads its system prompt from `ai_financial_coach/prompts/*.txt` so tone and behaviour can be edited without touching code.
  - A shared protocol file defines messaging rules to keep communication consistent across the team.
- **Shared State & Message Bus**
  - Central `SharedState` tracks inputs, goals, findings, plans, and the chronological bus log.
  - Incremental cursors allow agents to react only to new information and avoid infinite loops.
- **Dual UI Experience**
  - Existing tabs for *Movements*, *Budget*, *Savings*, and *Debt* keep their visuals and metrics.
  - New *Equipo IA* tab offers chat with the Manager, live objectives snapshot, delegation list, and a filterable timeline of the internal conversation.

## Project Structure

```
ai_financial_coach/
+-- app/
|   +-- main.py              # Streamlit entry point
|   +-- dashboard.py         # Multi-tab UI and analysis workflow
|   +-- components.py        # Reusable visual components
|   +-- context.py           # Session-wide shared state & agent factory
+-- agents/
|   +-- *.py                 # Manager, Budget, Savings, Debt, Investment, Advisor
|   +-- team.py              # Orchestrates rounds and prompt loading
+-- core/
|   +-- base_agent.py        # Common agent interface
|   +-- state.py             # SharedState and helpers
|   +-- message_bus.py       # Internal bus with cursors
|   +-- prompts.py           # Prompt loader utilities
|   +-- system.py            # Legacy single-pass analysis placeholder
|   +-- database.py          # SQLite helpers for movements
|   +-- schemas.py           # Pydantic models & enums
+-- prompts/
    +-- 00_shared_protocol.txt
    +-- manager_agent.txt
    +-- budget_agent.txt
    +-- savings_agent.txt
    +-- debt_agent.txt
    +-- investment_agent.txt
    +-- advisor_agent.txt
```

The legacy single-file implementation remains available as `ai_financial_coach_agent_backup.py` for reference.

## Running the App

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```
2. **Optional:** configure LLM credentials if you plan to connect the agents to OpenRouter later on. The current scaffolding does not require network calls, but the client expects `OPENROUTER_API_KEY` when enabled.
   ```bash
   export OPENROUTER_API_KEY=your_key
   ```
3. **Launch Streamlit**
   ```bash
   streamlit run ai_financial_coach_agent.py
   ```

## Using the Dashboard

- Register incomes, expenses, and debts on the **Movements** tab, then click *Analizar finanzas* to trigger the first round.
- Review the classic cards and charts in the **Presupuesto**, **Ahorro**, and **Deuda** tabs (they draw data from the shared state populated by the agents).
- Open **Equipo IA** to chat with the Manager, inspect objectives, refresh delegations, kick off additional rounds, and filter the internal timeline by agent or message type.

## Editing Prompts

Prompts live under `ai_financial_coach/prompts/`. Modify the text files to adjust tone or operating procedures. Restarting the Streamlit app reloads the prompts; alternatively call `reload_prompts()` inside `app/context.py` if you wire a UI control for hot reloading.

---

Questions or ideas for extending the multi-agent workflow (persistence, richer LLM integrations, automated testing) are welcome-feel free to open an issue or share feedback.
