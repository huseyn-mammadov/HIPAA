import streamlit as st
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
st.set_page_config(page_title="HIPAA Compliance Assistant", layout="wide", initial_sidebar_state="expanded")

# Custom CSS (keeping your original styling)
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
st.image('HIPAA_logo.png', width=200)  # Replace with an appropriate healthcare/HIPAA logo
st.markdown("<h1 style='text-align: center; color: white;'>HIPAA Compliance Assistant</h1>", unsafe_allow_html=True)
st.markdown("<h3 style='text-align: center; color: #2e67c0;'>(Powered by Google Gemini)</h3>", unsafe_allow_html=True)
st.markdown("<h4 style='text-align: center; color: red;'>BETA</h4>", unsafe_allow_html=True)

# Initialize session state
if 'compliance_score' not in st.session_state:
    st.session_state.compliance_score = 0
if 'current_scenario' not in st.session_state:
    st.session_state.current_scenario = None
if 'options' not in st.session_state:
    st.session_state.options = []
if 'scenario_number' not in st.session_state:
    st.session_state.scenario_number = 1
if 'expert_notes' not in st.session_state:
    st.session_state.expert_notes = ""
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'full_history' not in st.session_state:
    st.session_state.full_history = []

HIPAA_SCENARIO_PROMPT = """
Generate a detailed HIPAA compliance scenario for a healthcare provider. The scenario should involve potential privacy or security issues related to protected health information (PHI). Provide 3 response options with detailed explanations of their compliance implications.

Format:
Scenario {scenario_number}: [Title]
Description: [Detailed description of the HIPAA-related scenario, including potential risks and compliance concerns]

Options:
1. [Detailed description of option 1] (Compliance Score: [1-3])
2. [Detailed description of option 2] (Compliance Score: [1-3])
3. [Detailed description of option 3] (Compliance Score: [1-3])

Expert Notes: [Detailed notes on options, HIPAA implications, and best practices]
"""

def escape_markdown(text):
    return html.escape(text).replace('\n', '<br>')

def generate_scenario_and_options():
    model = genai.GenerativeModel('gemini-pro')
    prompt = HIPAA_SCENARIO_PROMPT.format(scenario_number=st.session_state.scenario_number)
    response = model.generate_content(prompt)
    scenario = response.text
    
    parts = scenario.split('Options:')
    scenario_description = parts[0].strip()
    
    options = []
    expert_notes = "No expert notes available"
    
    if len(parts) > 1:
        options_and_notes = parts[1].split('Expert Notes:')
        options_text = options_and_notes[0].strip()
        
        option_pattern = r'\d+\.\s+(.*?)\s+\(Compliance Score:\s+(\d+)\)'
        options = re.findall(option_pattern, options_text, re.DOTALL)
        
        if len(options_and_notes) > 1:
            expert_notes = options_and_notes[1].strip()
    
    return scenario_description, options, expert_notes

def run_hipaa_scenario():
    with st.spinner('Generating new HIPAA scenario...'):
        scenario, options, expert_notes = generate_scenario_and_options()
        st.session_state.current_scenario = scenario
        st.session_state.options = options
        st.session_state.expert_notes = expert_notes
        st.session_state.full_history.append({
            'scenario': scenario,
            'options': options,
            'expert_notes': expert_notes
        })

def choose_option(option):
    description, score = option
    score = int(score)
    st.session_state.compliance_score += score
    st.session_state.scenario_number += 1
    st.session_state.chat_history.append(("user", f"Selected: {description}"))
    st.session_state.chat_history.append(("assistant", f"Option selected. Compliance Score: {score}"))
    st.session_state.full_history[-1]['selected_option'] = description
    st.session_state.full_history[-1]['score'] = score

def clear_history():
    st.session_state.chat_history = []
    st.session_state.full_history = []
    st.session_state.scenario_number = 1
    st.session_state.current_scenario = None
    st.session_state.options = []
    st.session_state.expert_notes = ""
    st.success("History cleared.")

def reset_score():
    st.session_state.compliance_score = 0
    st.success("Compliance score reset to 0.")

def user_view():
    st.title("HIPAA Compliance Training")
    st.write(f"Current Compliance Score: {st.session_state.compliance_score}")
    display_history()
    display_chat()

def admin_view():
    st.title("Administrator View")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Generate New Scenario"):
            run_hipaa_scenario()
    with col2:
        if st.button("Clear History"):
            clear_history()
    with col3:
        if st.button("Reset Compliance Score"):
            reset_score()
    
    if st.session_state.current_scenario:
        st.markdown(f"<pre>{escape_markdown(st.session_state.current_scenario)}</pre>", unsafe_allow_html=True)
        st.subheader("Options:")
        
        for i, (description, score) in enumerate(st.session_state.options, 1):
            full_option = f"Option {i}: {description} (Compliance Score: {score})"
            if st.button(f"Select Option {i}", key=f"select_option_{i}"):
                choose_option((description, score))
            st.markdown(f"<pre>{escape_markdown(full_option)}</pre>", unsafe_allow_html=True)
        
        st.write(f"Current Compliance Score: {st.session_state.compliance_score}")
        
        if st.checkbox("Show Expert Notes"):
            st.markdown(f"<pre>{escape_markdown(st.session_state.expert_notes)}</pre>", unsafe_allow_html=True)
    
    display_history()
    display_chat()

def display_history():
    st.subheader("HIPAA Scenario History")
    for i, event in enumerate(st.session_state.full_history, 1):
        with st.expander(f"Scenario {i}: {event['scenario'].split(':')[1].strip()}"):
            st.markdown(f"<pre>{escape_markdown(event['scenario'])}</pre>", unsafe_allow_html=True)
            st.markdown("Options:")
            for j, (desc, score) in enumerate(event['options'], 1):
                st.markdown(f"<pre>{j}. {escape_markdown(desc)} (Compliance Score: {score})</pre>", unsafe_allow_html=True)
            if 'selected_option' in event:
                st.markdown(f"<pre><strong>Selected Option:</strong> {escape_markdown(event['selected_option'])}</pre>", unsafe_allow_html=True)
                st.markdown(f"<pre><strong>Compliance Score:</strong> {event['score']}</pre>", unsafe_allow_html=True)
            if st.checkbox(f"Show Expert Notes for Scenario {i}"):
                st.markdown(f"<pre>{escape_markdown(event['expert_notes'])}</pre>", unsafe_allow_html=True)

def display_chat():
    st.subheader("HIPAA Compliance Chat")
    chat_input = st.text_input("Ask a HIPAA-related question:")
    
    if st.button("Send"):
        st.session_state.chat_history.append(("user", chat_input))
        context = f"Scenario: {st.session_state.current_scenario}\nOptions: {st.session_state.options}"
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(f"Context: {context}\nHIPAA Question: {chat_input}").text
        st.session_state.chat_history.append(("assistant", response))
    
    for sender, message in st.session_state.chat_history:
        if sender == "user":
            st.markdown(f"<div style='text-align: right; color: #2e67c0;'>{escape_markdown(message)}</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div style='text-align: left; color: white;'>{escape_markdown(message)}</div>", unsafe_allow_html=True)

def main():
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Go to", ["HIPAA Training", "Administrator View"])
    
    if page == "HIPAA Training":
        user_view()
    else:
        admin_view()

if __name__ == "__main__":
    main()