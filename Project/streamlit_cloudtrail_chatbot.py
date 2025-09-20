#!/usr/bin/env python3
"""
Streamlit CloudTrail Chatbot App
A conversational interface for querying CloudTrail logs with memory support
"""

import streamlit as st
import asyncio
import sys
import os
from datetime import datetime

# Add current directory to path to import our agent
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from text_to_sql_agent import create_agent, query_agent

# Page configuration
st.set_page_config(
    page_title="CloudTrail SQL Assistant",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "agent" not in st.session_state:
    st.session_state.agent = None

def initialize_agent():
    """Initialize the CloudTrail agent."""
    if st.session_state.agent is None:
        with st.spinner("Initializing CloudTrail SQL Assistant..."):
            st.session_state.agent = create_agent()

def get_agent_response(query: str) -> str:
    """Get response from the agent."""
    try:
        response = asyncio.run(query_agent(st.session_state.agent, query))
        return response
    except Exception as e:
        return f"Error: {str(e)}"

def add_message(role: str, content: str):
    """Add a message to the chat history."""
    st.session_state.messages.append({
        "role": role,
        "content": content,
        "timestamp": datetime.now().strftime("%H:%M:%S")
    })

def clear_chat():
    """Clear the chat history."""
    st.session_state.messages = []
    st.rerun()

# Sidebar
with st.sidebar:
    st.title("🔍 CloudTrail SQL Assistant")
    st.markdown("---")
    
    st.subheader("Configuration")
    model_id = st.text_input(
        "Model ID", 
        value=os.getenv("STRANDS_MODEL_ID", "anthropic.claude-3-sonnet-20240229-v1:0"),
        help="Bedrock model ID to use"
    )
    
    max_tokens = st.number_input(
        "Max Tokens", 
        min_value=100, 
        max_value=8000, 
        value=int(os.getenv("STRANDS_MAX_TOKENS", "4000")),
        help="Maximum tokens for response"
    )
    
    temperature = st.slider(
        "Temperature", 
        min_value=0.0, 
        max_value=2.0, 
        value=float(os.getenv("STRANDS_TEMPERATURE", "1.0")),
        step=0.1,
        help="Model creativity (0=focused, 2=creative)"
    )
    
    # Update environment variables
    os.environ["STRANDS_MODEL_ID"] = model_id
    os.environ["STRANDS_MAX_TOKENS"] = str(max_tokens)
    os.environ["STRANDS_TEMPERATURE"] = str(temperature)
    
    st.markdown("---")
    
    st.subheader("Quick Examples")
    example_queries = [
        "Show me S3 activity today",
        "Find failed events in the last hour",
        "List EC2 instances launched today",
        "Show me all IAM policy changes",
        "Find suspicious login attempts",
        "What Lambda functions were invoked today?"
    ]
    
    for query in example_queries:
        if st.button(query, key=f"example_{query}", use_container_width=True):
            add_message("user", query)
            st.rerun()
    
    st.markdown("---")
    
    if st.button("🗑️ Clear Chat", use_container_width=True):
        clear_chat()
    
    st.markdown("---")
    st.subheader("About")
    st.markdown("""
    This chatbot helps you query AWS CloudTrail logs using natural language.
    
    **Features:**
    - Natural language to SQL conversion
    - Real-time query execution
    - Follow-up questions support
    - Session memory
    
    **Tips:**
    - Be specific about time ranges
    - Mention AWS services by name
    - Ask follow-up questions for details
    """)

# Main chat interface
st.title("🔍 CloudTrail SQL Assistant")
st.markdown("Ask questions about your AWS CloudTrail logs in natural language!")

# Initialize agent
initialize_agent()

# Display chat messages
chat_container = st.container()
with chat_container:
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            st.caption(f"⏰ {message['timestamp']}")

# Chat input
if prompt := st.chat_input("Ask about your CloudTrail logs..."):
    # Add user message
    add_message("user", prompt)
    
    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)
        st.caption(f"⏰ {datetime.now().strftime('%H:%M:%S')}")
    
    # Get and display assistant response
    with st.chat_message("assistant"):
        with st.spinner("Analyzing CloudTrail logs..."):
            # Create context from previous messages for follow-up questions
            context_messages = []
            for msg in st.session_state.messages[-6:]:  # Last 6 messages for context
                if msg["role"] == "user":
                    context_messages.append(f"User: {msg['content']}")
                elif msg["role"] == "assistant":
                    context_messages.append(f"Assistant: {msg['content']}")
            
            # Build query with context for follow-up questions
            if len(context_messages) > 2:  # If there's previous conversation
                context_str = "\n".join(context_messages[:-1])  # Exclude current question
                full_query = f"Previous conversation context:\n{context_str}\n\nCurrent question: {prompt}"
            else:
                full_query = prompt
            
            # Get response
            response = get_agent_response(full_query)
            
            # Display response
            st.markdown(response)
            st.caption(f"⏰ {datetime.now().strftime('%H:%M:%S')}")
            
            # Add assistant message
            add_message("assistant", response)

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666;'>
        CloudTrail SQL Assistant | Powered by AWS Bedrock
    </div>
    """, 
    unsafe_allow_html=True
)
