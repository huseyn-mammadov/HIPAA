import streamlit as st
#import google.generativeai as genai
import google.generativeai as genai
import re
import html
import os
from dotenv import load_dotenv




# Load API key from .env file
load_dotenv()
api_key = os.getenv("API_KEY")

if api_key is None:
    raise ValueError("API key not found. Set the API_KEY environment variable.")

genai.configure(api_key=api_key)




# Page configuration
st.set_page_config(page_title="GenAI Chatbot", layout="wide", initial_sidebar_state="expanded")

# Custom CSS
st.markdown("""
    <style>
    .stApp {
        background-color: #0e1117;
        color: #ffffff;
    }
    .stButton>button {
        width: 100%;
        background-color: #2e67c0;
        color: white;
    }
    .stMarkdown {
        background-color: #1e2530;
        padding: 10px;
        border-radius: 5px;
        margin-bottom: 10px;
    }
    .stCheckbox {
        color: #ffffff;
    }
    .stRadio > label {
        color: #ffffff;
    }
    .stExpander {
        background-color: #1e2530;
    }
    pre {
        white-space: pre-wrap;
        word-wrap: break-word;
        max-width: 100%;
        overflow-x: auto;
        background-color: #1e2530;
        padding: 10px;
        border-radius: 5px;
    }
    </style>
    """, unsafe_allow_html=True)

# Header
st.image('HIPAA_logo.png', width=200)
st.markdown("<h1 style='text-align: center; color: white;'>Cyber Incident Response Simulation Engine</h1>", unsafe_allow_html=True)
st.markdown("<h3 style='text-align: center; color: #2e67c0;'>(Powered by Google Gemini)</h3>", unsafe_allow_html=True)
st.markdown("<h4 style='text-align: center; color: red;'>BETA</h4>", unsafe_allow_html=True)

# Initialize session state
if 'score' not in st.session_state:
    st.session_state.score = 0
if 'current_inject' not in st.session_state:
    st.session_state.current_inject = None
if 'options' not in st.session_state:
    st.session_state.options = []
if 'inject_number' not in st.session_state:
    st.session_state.inject_number = 1
if 'facilitator_notes' not in st.session_state:
    st.session_state.facilitator_notes = ""
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'full_history' not in st.session_state:
    st.session_state.full_history = []

SIMULATION_PROMPT = """
Generate a detailed cyber incident inject for a chain of 2500 convenience stores with gas stations. The incident should affect critical infrastructure like fuel logistics, POS systems, or customer data. Provide 3 response options with detailed explanations.

Format:
Inject {inject_number}: [Title]
Time: [Time] ([Day])
Incident: [Detailed description of the incident, including potential impacts and immediate concerns]

Options:
1. [Detailed description of option 1] (Score: [1-3])
2. [Detailed description of option 2] (Score: [1-3])
3. [Detailed description of option 3] (Score: [1-3])

Facilitator Notes: [Detailed notes on options, consequences, and factors to consider]
"""

def escape_markdown(text):
    return html.escape(text).replace('\n', '<br>')

def generate_inject_and_options():
    model = genai.GenerativeModel('gemini-pro')
    prompt = SIMULATION_PROMPT.format(inject_number=st.session_state.inject_number)
    response = model.generate_content(prompt)
    scenario = response.text
    
    parts = scenario.split('Options:')
    inject = parts[0].strip()
    
    options = []
    facilitator_notes = "No facilitator notes available"
    
    if len(parts) > 1:
        options_and_notes = parts[1].split('Facilitator Notes:')
        options_text = options_and_notes[0].strip()
        
        option_pattern = r'\d+\.\s+(.*?)\s+\(Score:\s+(\d+)\)'
        options = re.findall(option_pattern, options_text, re.DOTALL)
        
        if len(options_and_notes) > 1:
            facilitator_notes = options_and_notes[1].strip()
    
    return inject, options, facilitator_notes

def run_simulation():
    with st.spinner('Generating new scenario...'):
        inject, options, facilitator_notes = generate_inject_and_options()
        st.session_state.current_inject = inject
        st.session_state.options = options
        st.session_state.facilitator_notes = facilitator_notes
        st.session_state.full_history.append({
            'inject': inject,
            'options': options,
            'facilitator_notes': facilitator_notes
        })

def choose_option(option):
    description, score = option
    score = int(score)
    st.session_state.score += score
    st.session_state.inject_number += 1
    st.session_state.chat_history.append(("user", f"Selected: {description}"))
    st.session_state.chat_history.append(("assistant", f"Option selected. Score: {score}"))
    st.session_state.full_history[-1]['selected_option'] = description
    st.session_state.full_history[-1]['score'] = score

def clear_history():
    st.session_state.chat_history = []
    st.session_state.full_history = []
    st.session_state.inject_number = 1
    st.session_state.current_inject = None
    st.session_state.options = []
    st.session_state.facilitator_notes = ""
    st.success("Chat history cleared.")

def reset_score():
    st.session_state.score = 0
    st.success("Score reset to 0.")

def client_view():
    st.title("Client View")
    st.write(f"Current Score: {st.session_state.score}")
    display_history()
    display_chat()

def facilitator_view():
    st.title("Facilitator View")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Generate New Inject"):
            run_simulation()
    with col2:
        if st.button("Clear History"):
            clear_history()
    with col3:
        if st.button("Reset Score"):
            reset_score()
    
    if st.session_state.current_inject:
        st.markdown(f"<pre>{escape_markdown(st.session_state.current_inject)}</pre>", unsafe_allow_html=True)
        st.subheader("Options:")
        
        for i, (description, score) in enumerate(st.session_state.options, 1):
            full_option = f"Option {i}: {description} (Score: {score})"
            if st.button(f"Select Option {i}", key=f"select_option_{i}"):
                choose_option((description, score))
            st.markdown(f"<pre>{escape_markdown(full_option)}</pre>", unsafe_allow_html=True)
        
        st.write(f"Current Score: {st.session_state.score}")
        
        if st.checkbox("Show Facilitator Notes"):
            st.markdown(f"<pre>{escape_markdown(st.session_state.facilitator_notes)}</pre>", unsafe_allow_html=True)
    
    display_history()
    display_chat()

def display_history():
    st.subheader("Simulation History")
    for i, event in enumerate(st.session_state.full_history, 1):
        with st.expander(f"Inject {i}: {event['inject'].split(':')[1].strip()}"):
            st.markdown(f"<pre>{escape_markdown(event['inject'])}</pre>", unsafe_allow_html=True)
            st.markdown("Options:")
            for j, (desc, score) in enumerate(event['options'], 1):
                st.markdown(f"<pre>{j}. {escape_markdown(desc)} (Score: {score})</pre>", unsafe_allow_html=True)
            if 'selected_option' in event:
                st.markdown(f"<pre><strong>Selected Option:</strong> {escape_markdown(event['selected_option'])}</pre>", unsafe_allow_html=True)
                st.markdown(f"<pre><strong>Score:</strong> {event['score']}</pre>", unsafe_allow_html=True)
            if st.checkbox(f"Show Facilitator Notes for Inject {i}"):
                st.markdown(f"<pre>{escape_markdown(event['facilitator_notes'])}</pre>", unsafe_allow_html=True)

def display_chat():
    st.subheader("Chat")
    chat_input = st.text_input("You:")
    
    if st.button("Send"):
        st.session_state.chat_history.append(("user", chat_input))
        context = f"Inject: {st.session_state.current_inject}\nOptions: {st.session_state.options}"
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(f"Context: {context}\nQuestion: {chat_input}").text
        st.session_state.chat_history.append(("assistant", response))
    
    for sender, message in st.session_state.chat_history:
        if sender == "user":
            st.markdown(f"<div style='text-align: right; color: #2e67c0;'>{escape_markdown(message)}</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div style='text-align: left; color: white;'>{escape_markdown(message)}</div>", unsafe_allow_html=True)

def main():
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Go to", ["Client View", "Facilitator View"])
    
    if page == "Client View":
        client_view()
    else:
        facilitator_view()

if __name__ == "__main__":
    main()
