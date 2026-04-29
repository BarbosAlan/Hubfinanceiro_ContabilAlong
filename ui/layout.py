from __future__ import annotations

import streamlit as st

from ui.styles import BASE_CSS


PAGES = {
    "dashboard": {"label": "Início", "icon": "⊞", "path": "Home.py", "badge": ""},
    "ip": {
        "label": "Importação IP",
        "icon": "⇄",
        "path": "pages/01_Importacao_Transacoes_IP.py",
        "badge": "CSV",
    },
    "genial": {
        "label": "Extrato Genial",
        "icon": "◈",
        "path": "pages/02_Extrato_Genial.py",
        "badge": "XLSX",
    },
}


def init_state() -> None:
    st.session_state.setdefault("global_files_processed", 0)
    st.session_state.setdefault("global_lines_processed", 0)


def apply_base_styles() -> None:
    st.markdown(f"<style>{BASE_CSS}</style>", unsafe_allow_html=True)


def _nav_link(key: str) -> str:
    page = PAGES[key]
    badge = f'<span class="nav-badge">{page["badge"]}</span>' if page.get("badge") else ""
    label = f'{page["icon"]}  {page["label"]}'
    st.page_link(page["path"], label=label)
    if badge:
        st.markdown(f'<div class="nav-badge-row">{badge}</div>', unsafe_allow_html=True)
    return page["path"]


def render_sidebar(active_key: str) -> None:
    with st.sidebar:
        st.markdown(
            """
            <div class="sidebar-brand">
              <div class="brand-name">CONTABIL ALONG</div>
              <div class="brand-sub">Sistema interno</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown('<div class="sidebar-section">MÓDULOS</div>', unsafe_allow_html=True)

        # Use native page links to avoid navigation flicker/black screen.
        for key in ["dashboard", "ip", "genial"]:
            _nav_link(key)

        st.markdown(
            """
            <div class="sidebar-section" style="margin-top: 8px;">EM BREVE</div>
            <div class="nav-item disabled">
              <span class="nav-icon">+</span>
              Novo módulo
            </div>
            <div class="sidebar-footer">v1.0 · uso interno</div>
            """,
            unsafe_allow_html=True,
        )


def render_topbar(title: str, breadcrumb: str) -> None:
    st.markdown(
        f"""
        <div class="topbar">
          <div class="topbar-breadcrumb"><span>{breadcrumb}</span></div>
          <div class="topbar-spacer"></div>
          <div class="topbar-title">{title}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def page_layout(*, active_key: str, title: str, breadcrumb: str) -> None:
    init_state()
    apply_base_styles()
    render_sidebar(active_key)
    render_topbar(title=title, breadcrumb=breadcrumb)

