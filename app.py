import streamlit as st
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.tools import DuckDuckGoSearchRun
from langchain.agents import initialize_agent, AgentType
from langchain.memory import ConversationBufferMemory
from langchain_core.messages import SystemMessage
import os

# --- Configuración de la Página ---
st.set_page_config(
    page_title="Donny - ShowSmart AI Agent",
    page_icon="🏠",
    layout="wide"
)

# --- Estilos para impresión (Opcional) ---
st.markdown("""
    <style>
        @media print {
            [data-testid="stSidebar"] {display: none;}
            .stChatInput {display: none;}
        }
    </style>
""", unsafe_allow_html=True)

# --- Configuración de API Key ---
with st.sidebar:
    st.title("🔧 Configuración")
    # Intentamos obtener la key de st.secrets primero
    if "GOOGLE_API_KEY" in st.secrets:
        api_key = st.secrets["GOOGLE_API_KEY"]
    else:
        api_key = st.text_input("Ingresa tu Google Gemini API Key", type="password")
        if not api_key:
            st.warning("Por favor ingresa tu API Key para comenzar.")
            st.markdown("[Consigue tu API Key aquí](https://aistudio.google.com/app/apikey)")

# --- Definición del Rol (System Prompt) ---
SYSTEM_ROLE = """
**Role:** You are "Donny The ShowSmart AI Agent from AgentCoachAi.com." Your mission is to help real estate agents (like Fernando) look like elite experts during property tours.

**Step 1: Onboarding**
- Always start by saying: "Hi! I'm Donny. May I have your name?"
- Once provided, ask for the list of property addresses and the departure address.
- Use Google Search to research each property's specific features, listing remarks, and unique selling points in real-time.

**Step 2: The "Showing Circle" Route**
- Organize the properties into a geographical circle starting from the departure point to minimize travel time.
- Present the list clearly: "Fernando, here is your optimal route: #1 [Address], #2 [Address]..."

**Step 3: The Print-Ready Strategic Brief**
Format the output clearly for printing (Ctrl+P). Each stop must include:
1. **Address & Strategic Highlight:** A unique fact about the house compared to the others today.
2. **Expert Walkthrough Script (5-10 mins):** Provide a detailed, professional script for the agent to use during the tour. Highlight specific features, location perks, and quality of life. Use "(Client Name)" for placeholders.
3. **The Elimination Game:** - After House #1: "Set the baseline."
   - Starting at House #2: Provide the script: "(Client Name), between the winner of the last house and this one, if you had to pick a champion and delete the other, which one stays in the winner's circle?"

**Step 4: The Tactical Objection Handler (The "Cheat Sheet")**
Include this section at the very bottom of the printed brief:
- Provide 10 specific scripts for: Small Rooms, Dated Kitchens, Noise, Old Systems, Ugly Paint/Carpet, HOA Fees, Small Yards, Lack of Storage, Hesitation, and "Needing to think about it."
- All scripts must start with an "Agreement" statement (e.g., "I understand...") and pivot to a solution-based "Smart View."

**Step 5: The Final Close**
- Provide a professional "Office Transition" script: "Now that we’ve found today's champion, let’s head back to the office to 'check the numbers.' If the math looks as good as the house, we can discuss an offer."

**Tone:** Strategic, encouraging, and highly professional. Ensure the formatting is clean for easy reading on paper.
"""

# --- Inicialización del Agente ---
def get_agent_chain(api_key):
    # 1. Definir el LLM (Actualizado a gemini-2.5-flash)
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",  # <--- CAMBIO REALIZADO AQUÍ
        google_api_key=api_key,
        temperature=0.7,
        convert_system_message_to_human=True 
    )

    # 2. Definir Herramientas
    search = DuckDuckGoSearchRun()
    tools = [search]

    # 3. Memoria
    memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

    # 4. Inicializar Agente
    agent = initialize_agent(
        tools, 
        llm, 
        agent=AgentType.CHAT_CONVERSATIONAL_REACT_DESCRIPTION, 
        verbose=True, 
        memory=memory,
        handle_parsing_errors=True
    )
    
    # Inyectar el System Prompt
    system_message = SystemMessage(content=SYSTEM_ROLE)
    agent.agent.llm_chain.prompt.messages.insert(0, system_message)
    
    return agent

# --- Lógica de la Interfaz ---

st.title("🏠 Donny: The ShowSmart AI Agent")
st.caption("Expert Property Tours & Route Optimization - Powered by Gemini 2.5 Flash")

# Inicializar historial
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hi! I'm Donny. May I have your name?"}
    ]

# Mostrar historial
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Capturar input
if prompt := st.chat_input("Escribe aquí..."):
    
    if not api_key:
        st.error("Por favor configura tu API Key en la barra lateral.")
        st.stop()

    # Guardar mensaje usuario
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generar respuesta
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        
        if "agent" not in st.session_state:
             st.session_state.agent = get_agent_chain(api_key)
        
        try:
            with st.spinner("Donny is thinking..."):
                response = st.session_state.agent.run(input=prompt)
            
            message_placeholder.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})
        
        except Exception as e:
            st.error(f"Ocurrió un error: {e}")
            st.info("Nota: Verifica que el modelo 'gemini-2.5-flash' esté disponible para tu API Key.")