import streamlit as st
import os
import json
import logging
from streamlit_lottie import st_lottie
from datetime import datetime
from typing import List, Dict
from groq import Groq


st.set_page_config(
    page_title='ChatBOT',
    page_icon='🦙',
    layout='centered',
    initial_sidebar_state='auto'
)

logging.basicConfig(level=logging.ERROR)


def load_config(config_path: str) -> Dict:
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError:
        st.error("Config file is not valid JSON. Please check its content.")
        logging.error("Invalid JSON in config file.")
        st.stop()
    except FileNotFoundError:
        st.error("Config file not found! Please ensure the file exists in the working directory.")
        logging.error("Config file not found.")
        st.stop()


def initialize_groq_client(api_key: str) -> Groq:
    os.environ['GROQ_API_KEY'] = api_key
    return Groq()


def get_groq_response(client: Groq, messages: List[Dict]) -> str:
    try:
        response = client.chat.completions.create(
            model='llama-3.2-11b-vision-preview',
            messages=messages
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"Error in Groq API call: {e}")
        logging.error(f"Groq API call error: {e}")
        st.stop()




def save_chat_history(chat_history: List[Dict]) -> None:
    history_path = os.path.join(working_dir, 'chat_history.json')
    with open(history_path, 'w') as f:
        json.dump(chat_history, f)
    st.success("Chat history saved successfully!")


def load_chat_history() -> List[Dict]:
    history_path = os.path.join(working_dir, 'chat_history.json')
    if os.path.exists(history_path):
        with open(history_path, 'r') as f:
            return json.load(f)
    else:
        st.warning("No saved chat history found.")
        return []


def handle_file_io(file_path: str, mode: str, data: List[Dict] = None) -> List[Dict]:
    if mode == 'write':
        with open(file_path, 'w') as f:
            json.dump(data, f)
        st.success("File saved successfully!")
    elif mode == 'read':
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                return json.load(f)
        else:
            st.warning("No saved file found.")
            return []
    else:
        st.error("Invalid mode. Please use 'write' or 'read'.")

# Define creator and project name
creator_name = "Pramit Acharjya"
project_name = "Alpaca"

# Get the directory of the current file
working_dir = os.path.dirname(os.path.abspath(__file__))

# Load configuration
config_path = os.path.join(working_dir, 'config.json')
config_data = load_config(config_path)

# Set environment variable for Groq API key
GROQ_API_KEY = os.getenv('GROQ_API_KEY', config_data.get('GROQ_API_KEY'))
if not GROQ_API_KEY:
    st.error("GROQ_API_KEY not found in environment or config file!")
    logging.error("GROQ_API_KEY not found.")
    st.stop()

# Initialize Groq client
client = initialize_groq_client(GROQ_API_KEY)

# Initialize chat history if not already in session state
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = load_chat_history()

# Sidebar for settings and actions
with st.sidebar:
    st.header("Settings")
    st.button("Save Chat History", on_click=lambda: save_chat_history(st.session_state.chat_history))
    st.button("Load Chat History", on_click=lambda: st.session_state.update({'chat_history': load_chat_history()}))
    st.button("Clear Chat History", on_click=lambda: st.session_state.update({'chat_history': []}))

# Title of the app with Lottie animation on the right
col1, col2 = st.columns([4, 1])
with col1:
    st.title('🦙 Chat Bot')
    st.write("Welcome! How can I assist you today?")
with col2:
    try:
        st_lottie(
            'https://lottie.host/821ab3ff-400b-402a-90c9-377859e96ce5/0EGj4ONb7d.json',
            height=120,
            width=120,
            key="lottie"
        )
    except Exception as e:
        st.warning(f"Failed to load animation: {e}")

# Display chat history
for m in st.session_state.chat_history:
    with st.chat_message(m['role']):
        st.markdown(f"{m['content']}  \n<sub><i>{m['timestamp']}</i></sub>", unsafe_allow_html=True)

# Input from the user
user_input = st.chat_input('Enter your Prompt...')
if user_input:
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    st.chat_message('user').markdown(f"{user_input}  \n<sub><i>{timestamp}</i></sub>", unsafe_allow_html=True)
    st.session_state.chat_history.append({'role': 'user', 'content': user_input, 'timestamp': timestamp})

    messages = [
        {'role': 'system', 'content': f'You are a chill chat assistant from the hood created by {creator_name}. This chatbot is called {project_name}.'},
        *[{'role': m['role'], 'content': m['content']} for m in st.session_state.chat_history]
    ]

    # Call the Groq API and get the response
    with st.spinner('Processing your request...'):
        assistant_response = get_groq_response(client, messages)

    # Append assistant response to chat history and display it
    st.session_state.chat_history.append({'role': 'assistant', 'content': assistant_response, 'timestamp': timestamp})
    with st.chat_message('assistant'):
        st.markdown(f"{assistant_response}  \n<sub><i>{timestamp}</i></sub>", unsafe_allow_html=True)
