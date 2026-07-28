import streamlit as st

# Interfaz destinada al consumo de resultados de clustering de Vercel Log Drains.

pg = st.navigation(
    [
        st.Page("page_1.py", title="Agents Intelligence", icon="🔎", default=True),
    ]
)
pg.run()
