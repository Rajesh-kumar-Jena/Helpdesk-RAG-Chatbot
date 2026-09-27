"""
Optional web UI.

Run `python ingest.py` once first, then:
    streamlit run streamlit_app.py
"""
import uuid

import streamlit as st

from chatbot import HelpDeskBot

st.set_page_config(page_title="Help Desk Assistant", page_icon="🛠️")
st.title("🛠️ Help Desk Assistant")
st.caption("Ask about VPN, password resets, printers, Wi-Fi, email, or software installs.")

if "bot" not in st.session_state:
    st.session_state.bot = HelpDeskBot()
    st.session_state.session_id = str(uuid.uuid4())
    st.session_state.messages = []

for role, content in st.session_state.messages:
    with st.chat_message(role):
        st.markdown(content)

if prompt := st.chat_input("Describe your issue..."):
    st.session_state.messages.append(("user", prompt))
    with st.chat_message("user"):
        st.markdown(prompt)

    result = st.session_state.bot.chat(st.session_state.session_id, prompt)
    answer = result["answer"]
    if result["sources"] and not result["escalated"]:
        answer += f"\n\n*Sources: {', '.join(result['sources'])}*"

    st.session_state.messages.append(("assistant", answer))
    with st.chat_message("assistant"):
        st.markdown(answer)

    if result["escalated"]:
        st.warning(f"Escalated to a human agent — ticket #{result['ticket']['ticket_id']}")
