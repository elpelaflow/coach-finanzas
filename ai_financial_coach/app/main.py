from __future__ import annotations

import streamlit as st
from dotenv import load_dotenv

from ai_financial_coach.app.context import get_prompt_loader
from ai_financial_coach.app.dashboard import render_dashboard
from ai_financial_coach.core.database import init_db

PROMPTS_CACHE_KEY = "prompts_registry"


def ensure_prompts_loaded() -> None:
    loader = get_prompt_loader()
    if PROMPTS_CACHE_KEY not in st.session_state:
        st.session_state[PROMPTS_CACHE_KEY] = loader.load_all()


def main() -> None:
    load_dotenv()
    st.set_page_config(page_title="Asesor Financiero ARS", layout="wide")
    init_db()
    ensure_prompts_loaded()
    render_dashboard()


if __name__ == "__main__":
    main()

