import streamlit as st
import os
import uuid
from dotenv import load_dotenv
from chatbot import StockMarketChatbot
import json

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="Stock Market Chatbot",
    page_icon="📈",
    layout="wide"
)

# Custom CSS
st.markdown("""
    <style>
    .main {
        background-color: #0e1117;
    }
    .stTextInput>div>div>input {
        background-color: #262730;
        color: white;
    }
    .chat-message {
        padding: 1.5rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        display: flex;
        flex-direction: column;
    }
    .user-message {
        background-color: #1e3a5f;
        border-left: 5px solid #4a90e2;
    }
    .assistant-message {
        background-color: #2d2d2d;
        border-left: 5px solid #50c878;
    }
    .info-box {
        background-color: #1e1e1e;
        border: 1px solid #4a90e2;
        border-radius: 0.5rem;
        padding: 1rem;
        margin: 1rem 0;
    }
    .status-complete {
        color: #50c878;
        font-weight: bold;
    }
    .status-incomplete {
        color: #ffa500;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)


def initialize_session():
    """Initialize session state variables"""
    if 'session_id' not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())

    if 'conversation_id' not in st.session_state:
        st.session_state.conversation_id = None

    if 'messages' not in st.session_state:
        st.session_state.messages = []

    if 'chatbot' not in st.session_state:
        # Initialize chatbot
        openai_key = os.getenv("OPENAI_API_KEY")
        sendgrid_key = os.getenv("SENDGRID_API_KEY")
        sender = os.getenv("SENDER_EMAIL")
        recipient = os.getenv("RECIPIENT_EMAIL")

        if not all([openai_key, sendgrid_key, sender, recipient]):
            st.error("Missing environment variables. Please set OPENAI_API_KEY, SENDGRID_API_KEY, SENDER_EMAIL, and RECIPIENT_EMAIL in .env file")
            st.stop()

        st.session_state.chatbot = StockMarketChatbot(
            openai_key, sendgrid_key, sender, recipient
        )

    if 'user_data_status' not in st.session_state:
        st.session_state.user_data_status = {
            "name": None,
            "email": None,
            "income": None,
            "complete": False
        }


def display_message(role, content):
    """Display a chat message"""
    if role == "user":
        st.markdown(f"""
            <div class="chat-message user-message">
                <strong>You:</strong><br/>
                {content}
            </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
            <div class="chat-message assistant-message">
                <strong>Market Wizard:</strong><br/>
                {content}
            </div>
        """, unsafe_allow_html=True)


def display_user_data_status():
    """Display user data collection status in sidebar"""
    st.sidebar.markdown("### 📊 Data Collection Status")

    status = st.session_state.user_data_status

    # Name status
    name_icon = "✅" if status["name"] else "⏳"
    st.sidebar.markdown(f"{name_icon} **Name:** {status['name'] if status['name'] else 'Not collected'}")

    # Email status
    email_icon = "✅" if status["email"] else "⏳"
    st.sidebar.markdown(f"{email_icon} **Email:** {status['email'] if status['email'] else 'Not collected'}")

    # Income status
    income_icon = "✅" if status["income"] else "⏳"
    st.sidebar.markdown(f"{income_icon} **Income:** {status['income'] if status['income'] else 'Not collected'}")

    # Overall status
    st.sidebar.markdown("---")
    if status["complete"]:
        st.sidebar.markdown('<p class="status-complete">✅ All data collected!</p>', unsafe_allow_html=True)
        st.sidebar.success("Data has been sent via email!")
    else:
        st.sidebar.markdown('<p class="status-incomplete">⏳ Collection in progress...</p>', unsafe_allow_html=True)


def main():
    """Main application"""
    initialize_session()

    # Header
    st.title("📈 Stock Market Chatbot")
    st.markdown("*Your sharp-tongued market wizard with real insights*")
    st.markdown("---")

    # Sidebar
    with st.sidebar:
        st.markdown("## 🔧 Settings")
        st.markdown(f"**Session ID:** `{st.session_state.session_id[:8]}...`")

        if st.button("🔄 Reset Conversation"):
            st.session_state.messages = []
            st.session_state.conversation_id = None
            st.session_state.session_id = str(uuid.uuid4())
            st.session_state.user_data_status = {
                "name": None,
                "email": None,
                "income": None,
                "complete": False
            }
            st.rerun()

        st.markdown("---")
        display_user_data_status()

        st.markdown("---")
        st.markdown("### ℹ️ About")
        st.markdown("""
        This chatbot is a stock market expert that:
        - Provides market insights
        - Discusses trading strategies
        - Analyzes trends and risks
        - Uses RAG for enhanced knowledge

        **Note:** Not financial advice!
        """)

    # Chat container
    chat_container = st.container()

    # Display chat history
    with chat_container:
        for message in st.session_state.messages:
            display_message(message["role"], message["content"])

    # Chat input
    user_input = st.chat_input("Ask me about the markets...")

    if user_input:
        # Add user message to history
        st.session_state.messages.append({
            "role": "user",
            "content": user_input
        })

        # Display user message
        with chat_container:
            display_message("user", user_input)

        # Get bot response
        with st.spinner("Market wizard is thinking..."):
            response = st.session_state.chatbot.get_response(
                user_input,
                st.session_state.session_id,
                st.session_state.conversation_id
            )

            if response["success"]:
                # Update conversation ID
                if response.get("conversation_id"):
                    st.session_state.conversation_id = response["conversation_id"]

                # Add assistant message to history
                assistant_message = response["message"]
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": assistant_message
                })

                # Update user data status
                st.session_state.user_data_status = st.session_state.chatbot.get_user_data_status(
                    st.session_state.session_id
                )

                # Display assistant message
                with chat_container:
                    display_message("assistant", assistant_message)

                # Show notification if data collection is complete
                if st.session_state.user_data_status["complete"]:
                    if any(result.get("data_complete") for result in response.get("tool_results", [])):
                        st.success("✅ All your information has been collected and sent via email!")

                # Rerun to update sidebar
                st.rerun()

            else:
                st.error(f"Error: {response.get('message', 'Unknown error')}")


if __name__ == "__main__":
    main()
