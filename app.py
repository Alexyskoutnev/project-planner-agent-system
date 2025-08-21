import os
import logging
import asyncio
import uuid
import streamlit as st
from agents import Runner, SQLiteSession
from naii_agents.agents import product_manager
from naii_agents.tools import read_doc, CURRENT_WORKING_DOC

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

st.set_page_config(page_title="NAI System Configurator AI", page_icon="🚀", layout="wide")
st.title("NAI Project Agent")

if "session_id" not in st.session_state:
    st.session_state.session_id = f"nai-proj-{uuid.uuid4()}"
    # Clear any existing document for new session
    if os.path.exists(CURRENT_WORKING_DOC):
        os.remove(CURRENT_WORKING_DOC)

if "chat_history" not in st.session_state:
    st.session_state.chat_history = [
        ("assistant", "Hello! I'm NAI's Product Manager AI. I'm here to help you define and plan your new hardware project. To get started, could you tell me what market problem your new product will solve?")
    ]

session = SQLiteSession(st.session_state.session_id, "nai_conversations.sqlite")

col1, col2 = st.columns([1, 1])

with col1:
    chat_container = st.container(height=600)
    
    # Display chat history
    for role, text in st.session_state.chat_history:
        with chat_container.chat_message(role):
            st.markdown(text)

with col2:
    doc_container = st.container(height=600)
    doc_content = read_doc()
    logging.info(f"Current document content:\n{doc_content}")
    with doc_container:
        st.markdown(doc_content)
        try:
            if os.path.exists(CURRENT_WORKING_DOC) and os.path.getsize(CURRENT_WORKING_DOC) > 0:
                with open(CURRENT_WORKING_DOC, "rb") as f:
                    file_bytes = f.read()
                st.download_button(
                    label="Download Document",
                    data=file_bytes,
                    file_name=os.path.basename(CURRENT_WORKING_DOC),
                    mime="text/markdown",
                )
            else:
                st.info("No document available to download")
        except Exception as e:
            logging.error(f"Error preparing document for download: {e}")
            st.error("Could not prepare document for download.")

user_msg = st.chat_input("Tell me about your project requirements...")

if user_msg:
    # Add user message to chat history
    st.session_state.chat_history.append(("user", user_msg))
    
    # Display user message immediately
    with chat_container.chat_message("user"):
        st.markdown(user_msg)
    
    # Show processing indicator
    with st.spinner("AI agents are collaborating on your project..."):
        try:
            result = asyncio.run(
                Runner.run(
                    starting_agent=product_manager,
                    input=user_msg,
                    session=session,
                )
            )
            reply = result.final_output or "I apologize, but I wasn't able to process your request. Could you please try rephrasing?"
            st.session_state.chat_history.append(("assistant", reply))
            
        except Exception as e:
            logging.error(f"Error running agents: {e}")
            error_msg = f"I encountered an error while processing your request: {str(e)}. Please try again."
            st.session_state.chat_history.append(("assistant", error_msg))
    st.rerun()