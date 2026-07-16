import streamlit as st


st.set_page_config(page_title="Agentic Data Modeling Studio", layout="wide")
st.title("Agentic Data Modeling Studio")
st.caption("Source Data Dictionary, Silver, Gold, and STTM review workspace")

st.info(
    "The DAB-compliant review application shell is ready. Artifact views and "
    "decision workflows will be added only after their contracts are approved."
)

st.subheader("Planned review areas")
st.markdown(
    """
- Engagement and run scope
- Reconstructed Source Data Dictionary
- Silver ODS model
- Gold dimensional model
- Source-to-target mappings
- Requirement coverage and gaps
- Evidence, validation findings, and review decisions
"""
)
