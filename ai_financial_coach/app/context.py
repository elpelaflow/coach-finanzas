from __future__ import annotations

from typing import Optional

import streamlit as st

from ai_financial_coach.agents import AgentTeam
from ai_financial_coach.core.llm import LLMClient
from ai_financial_coach.core.prompts import PromptLoader
from ai_financial_coach.core.state import SharedState

STATE_SESSION_KEY = "shared_state"
PROMPT_LOADER_SESSION_KEY = "prompt_loader"
TEAM_SESSION_KEY = "agent_team"
PROMPTS_CACHE_KEY = "prompts_registry"
LLM_CLIENT_SESSION_KEY = "llm_client"
LLM_STATUS_SESSION_KEY = "llm_status"


def get_shared_state() -> SharedState:
    if STATE_SESSION_KEY not in st.session_state:
        st.session_state[STATE_SESSION_KEY] = SharedState()
    return st.session_state[STATE_SESSION_KEY]


def reset_shared_state() -> None:
    if STATE_SESSION_KEY in st.session_state:
        st.session_state[STATE_SESSION_KEY].reset()


def get_prompt_loader(base_path: Optional[str] = None) -> PromptLoader:
    if PROMPT_LOADER_SESSION_KEY not in st.session_state:
        st.session_state[PROMPT_LOADER_SESSION_KEY] = PromptLoader(base_path)
    loader: PromptLoader = st.session_state[PROMPT_LOADER_SESSION_KEY]
    if base_path:
        loader.base_path = base_path
    return loader


def get_llm_client() -> Optional[LLMClient]:
    if LLM_CLIENT_SESSION_KEY not in st.session_state:
        try:
            st.session_state[LLM_CLIENT_SESSION_KEY] = LLMClient()
        except Exception as exc:  # pragma: no cover - defensive guard
            st.session_state[LLM_CLIENT_SESSION_KEY] = None
            st.session_state[LLM_STATUS_SESSION_KEY] = {
                "ok": False,
                "error": str(exc),
            }
    return st.session_state.get(LLM_CLIENT_SESSION_KEY)


def update_llm_status(**kwargs) -> None:
    shared_state = get_shared_state()
    shared_state.update_llm_status("ui", **kwargs)
    st.session_state[LLM_STATUS_SESSION_KEY] = shared_state.llm_status


def reload_prompts() -> None:
    loader = get_prompt_loader()
    loader.refresh()
    st.session_state.pop(PROMPTS_CACHE_KEY, None)
    if TEAM_SESSION_KEY in st.session_state:
        st.session_state[TEAM_SESSION_KEY].refresh_prompts()


def get_agent_team() -> AgentTeam:
    if TEAM_SESSION_KEY not in st.session_state:
        state = get_shared_state()
        loader = get_prompt_loader()
        llm_client = get_llm_client()
        st.session_state[TEAM_SESSION_KEY] = AgentTeam(state, loader, llm_client=llm_client)
    return st.session_state[TEAM_SESSION_KEY]
