import streamlit as st
from langchain_openai import ChatOpenAI
from langchain.agents import create_react_agent, AgentExecutor
from langchain.prompts import PromptTemplate
from dotenv import load_dotenv
import os

from agent import SYSTEM_PROMPT
from tools import drug_food_interaction_tool, get_event_types, check_doctor_availability, book_doctor_appointment
from cache import save_log

load_dotenv()

st.title("💊 Drug-Food Interaction Inspector")

if "messages" not in st.session_state:
    st.session_state.messages = []

if "agent" not in st.session_state:
    llm = ChatOpenAI(model="gpt-4o", api_key=os.getenv("OPENAI_API_KEY"), base_url="https://aipipe.org/openai/v1")
    tools = [drug_food_interaction_tool, get_event_types, check_doctor_availability, book_doctor_appointment]
    prompt = PromptTemplate.from_template(SYSTEM_PROMPT + "\n\n{chat_history}\nQuestion: {input}\n{agent_scratchpad}")
    st.session_state.agent = AgentExecutor(agent=create_react_agent(llm, tools, prompt), tools=tools, handle_parsing_errors=True, return_intermediate_steps=True)

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).markdown(msg["content"])

if user_input := st.chat_input("e.g. I took aspirin and ate grapefruit, feeling dizzy..."):
    st.session_state.messages.append({"role": "user", "content": user_input})
    st.chat_message("user").markdown(user_input)

    with st.spinner("Checking..."):
        chat_history = "\n".join(f"{m['role'].capitalize()}: {m['content']}" for m in st.session_state.messages[:-1])
        result = st.session_state.agent.invoke({"input": user_input, "chat_history": chat_history})
        answer = result.get("output")

        for action, tool_output in result.get("intermediate_steps", []):
            if action.tool == "drug_food_interaction_tool":
                save_log(action.tool_input.get("drug_name", "unknown"), user_input, tool_output)

    st.chat_message("assistant").markdown(answer)
    st.session_state.messages.append({"role": "assistant", "content": answer})
