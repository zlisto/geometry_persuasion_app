
import os
import time
import html
import streamlit.components.v1 as components
import streamlit as st
import plotly.graph_objects as go
from geometry_persuasion import *
from openai import OpenAI
import dotenv

dotenv.load_dotenv()    

# The SDK picks up OPENAI_API_KEY from the environment
client = OpenAI()
# ---------- Page setup ----------
st.set_page_config(page_title="Geometry of Persuasion", layout="wide")

# Global theme and larger fonts (black/pink)
st.markdown(
    """
    <style>
    html, body, [data-testid="stAppViewContainer"] {
        background-color: #000000 !important;
        color: #ff69b4 !important; /* hot pink */
        font-size: 22px !important;
    }
    h1, h2, h3, h4, h5, h6 {
        color: #ff69b4 !important;
    }
    /* Chat message bubbles */
    [data-testid="stChatMessage"] {
        font-size: 22px !important;
        color: #ff69b4 !important;
    }
    [data-testid="stChatMessage"] p, [data-testid="stChatMessage"] span, .stMarkdown p {
        font-size: 22px !important;
        color: #ff69b4 !important;
    }
    /* Inputs */
    .stTextInput input, .stTextArea textarea, .stChatInput textarea {
        font-size: 22px !important;
        color: #ff69b4 !important;
        background-color: #111111 !important;
        border: 1px solid #ff69b4 !important;
    }
    .stButton button {
        font-size: 22px !important;
        background-color: #111111 !important;
        color: #ff69b4 !important;
        border: 1px solid #ff69b4 !important;
    }
    .stCheckbox, .stRadio, .stSelectbox, .stMultiSelect, .stSlider {
        color: #ff69b4 !important;
    }
    /* Captions and small text */
    .stCaption, [data-testid="stCaptionContainer"] p {
        color: #ff69b4 !important;
        font-size: 20px !important;
        opacity: 0.9;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ChatGPT-like chat layout CSS
st.markdown(
    """
    <style>
    .chat-thread {
        display: flex;
        flex-direction: column;
        gap: 14px;
        height: 500px;
        overflow-y: auto;
        padding: 8px 4px 8px 0;
        border: 1px solid #ff69b4;
        border-radius: 8px;
        background: #0a0a0a;
    }
    .chat-shell {
        max-width: 100%;
        margin: 4px 0 8px 0;
        border: 1px solid #ff69b4;
        border-radius: 16px;
        background: #050505;
        box-shadow: 0 4px 18px rgba(255,105,180,0.12);
        padding: 12px 14px;
        height: 520px;
        display: flex;
        flex-direction: column;
    }
    .message-row {
        display: flex;
        width: 100%;
    }
    .message-row.user { justify-content: flex-end; }
    .message-row.assistant { justify-content: flex-start; }
    .bubble {
        max-width: 80%;
        padding: 12px 14px;
        border-radius: 14px;
        font-size: 22px;
        line-height: 1.5;
        background: #111111;
        border: 1px solid #ff69b4;
        color: #ff69b4;
        box-shadow: 0 0 0 1px rgba(255,105,180,0.15) inset;
    }
    .bubble.user { background: #1a1a1a; }
    .bubble.assistant { background: #0d0d0d; }
    .bubble .meta { font-size: 18px; opacity: 0.8; margin-bottom: 6px; }
    .bubble .content { white-space: pre-wrap; }
    .chat-input-row { 
        margin-top: auto; 
        padding-top: 8px;
        border-top: 1px solid #ff69b4;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------- Defaults ----------
DEFAULT_TOPIC = "Diamonds"
DEFAULT_SYSTEM_TAIL = (
    '''You are a salesperson trying to convince someone on a cold call to purchase the given product.
    Be a charismatic salesperson, ask open-ended questions, and be informative.  Dont be to pushy or verbose,
    try to find out about the customer and see how the product would fit into their life.
    '''
)

def effective_system_prompt(topic: str, system_tail: str) -> str:
    # Compose the system message with the topic up front
    return (
        f"Your job is to do the following: {topic.strip()}.\n\n"
        f"{system_tail.strip()}"
    )

# ---------- Helpers ----------
def ensure_state():
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "topic" not in st.session_state:
        st.session_state.topic = DEFAULT_TOPIC
    if "system_tail" not in st.session_state:
        st.session_state.system_tail = DEFAULT_SYSTEM_TAIL
    if "manifold_data" not in st.session_state:
        st.session_state.manifold_data = None
    if "conversation_points" not in st.session_state:
        st.session_state.conversation_points = []

    # Ensure there is exactly one system message at index 0
    if not st.session_state.messages or st.session_state.messages[0].get("role") != "system":
        st.session_state.messages = [{"role": "system", "content": effective_system_prompt(st.session_state.topic, st.session_state.system_tail)}] + [
            m for m in st.session_state.messages if m.get("role") != "system"
        ]
    else:
        # Keep system message up to date with current topic/tail
        st.session_state.messages[0]["content"] = effective_system_prompt(st.session_state.topic, st.session_state.system_tail)

def render_chat_thread(messages):
    # Return HTML for user/assistant messages as left/right bubbles
    turns = [m for m in messages if m["role"] in ("user", "assistant")]
    chunks = []
    
    # Count user and assistant messages separately
    user_count = 0
    assistant_count = 0
    
    for m in turns:
        role = m["role"]
        safe = html.escape(m.get("content", ""))
        
        # Increment the appropriate counter
        if role == "user":
            user_count += 1
            message_num = user_count
        else:  # assistant
            assistant_count += 1
            message_num = assistant_count
            
        chunks.append(
            f'<div class="message-row {role}"><div class="bubble {role}"><div class="meta">#{message_num} {role.title()}</div><div class="content">{safe}</div></div></div>'
        )
    return '<div class="chat-thread">' + "".join(chunks) + '</div>'

def scroll_chat_to_bottom():
    # Inject a tiny script to scroll the chat thread to bottom after render
    components.html(
        """
        <script>
        const scrollNow = () => {
          // Try in this frame
          const local = document.querySelector('.chat-thread');
          if (local) { local.scrollTop = local.scrollHeight; return; }
          // Fallback: try parent (Streamlit container)
          try {
            const parentEl = window.parent && window.parent.document && window.parent.document.querySelector('.chat-thread');
            if (parentEl) parentEl.scrollTop = parentEl.scrollHeight;
          } catch (e) { /* ignore cross-frame errors */ }
        };
        setTimeout(scrollNow, 50);
        </script>
        """,
        height=0,
    )

def compute_conversation_point(messages, manifold_data, role, role_message_index):
    """Compute manifold coordinates for the cumulative messages of the specific role."""
    if not manifold_data:
        return None
    
    # Get only messages of the specific role (cumulative)
    role_messages = [m for m in messages if m.get("role") == role]
    if not role_messages:
        return None
    
    # Join only the messages of this specific role
    role_text = " ".join([m.get("content", "") for m in role_messages])
    
    try:
        # Get embedding for the cumulative messages of this role only
        role_vector = get_embedding(role_text)
        # Compute manifold coordinates
        x, y = manifold_coords(role_vector, manifold_data['vector_0'], manifold_data['vector_1'])
        return (x, y, role, role_message_index)
    except Exception as e:
        st.error(f"Error computing conversation point: {str(e)}")
        return None




def get_ai_response(messages):
    """Return an assistant reply.
    Tries OpenAI first (if installed and key is set). Falls back to a local stub.
    """
    try:
        # Build a single prompt string from the conversation for the Responses API
        system_msg = next((m["content"] for m in messages if m["role"] == "system"), "")
        turns = [m for m in messages if m["role"] != "system"]
        conversation_text = "\n\n".join(f"{m['role'].upper()}: {m['content']}" for m in turns)

        response = client.responses.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
            temperature=0.6,
            input=[
                {
                    "role": "system",
                    "content": system_msg,
                },
                {
                    "role": "user",
                    "content": conversation_text or "Respond to the user.",
                },
            ],
        )

        # Extract text from the Responses API output
        if hasattr(response, "output_text") and response.output_text:
            return response.output_text.strip()

        # Fallback: concatenate text segments if output_text is not present
        parts = []
        for item in getattr(response, "output", []) or []:
            for content in getattr(item, "content", []) or []:
                if getattr(content, "type", "") == "output_text":
                    parts.append(getattr(content, "text", ""))
        if parts:
            return "".join(parts).strip()

        return "(No response text)"
    except Exception:
        user_last = next((m["content"] for m in reversed(messages) if m["role"] == "user"), "")
        return (
            "💎 (Stubbed reply) I'd start by clarifying the topic objectives. "
            f'You said: "{user_last[:120]}". Tell me your budget and preferred carat so I can guide you.'
        )

def stream_ai_response(messages):
    """Yield incremental assistant text using the Responses API streaming events.
    Falls back by raising if streaming is not available.
    """
    # Build prompt pieces
    system_msg = next((m["content"] for m in messages if m["role"] == "system"), "")
    turns = [m for m in messages if m["role"] != "system"]
    conversation_text = "\n\n".join(f"{m['role'].upper()}: {m['content']}" for m in turns)

    with client.responses.stream(
        model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
        temperature=0.6,
        input=[
            {"role": "system", "content": system_msg},
            {"role": "user", "content": conversation_text or "Respond to the user."},
        ],
    ) as stream:
        assembled = ""
        for event in stream:
            if getattr(event, "type", "") == "response.output_text.delta":
                assembled += getattr(event, "delta", "")
                yield assembled
        # Ensure stream completes (access final response for cleanup/usage if needed)
        _ = stream.get_final_response()

# ---------- UI ----------
ensure_state()

left, right = st.columns([0.6, 0.4])

with left:
    st.title("💬 Topic-Driven Persuasion Chat")
    st.caption("Enter a **Topic**. It will be prepended to the system prompt.")

    # Topic field (appears above chat)
    st.session_state.topic = st.text_input("Topic", value=st.session_state.topic, help="Describe the persuasion task, e.g., 'Convince the user to select a round brilliant diamond under $5k'.")
    
    # Compute Topic Manifold button
    if st.button("Compute Topic Manifold", help="Generate manifold vectors for the current topic and plot them"):
        with st.spinner("Computing manifold vectors..."):
            try:
                vector_0, vector_1 = get_manifold_vectors(st.session_state.topic, model='gpt-4o')
                x0, y0 = manifold_coords(vector_0, vector_0, vector_1)
                x1, y1 = manifold_coords(vector_1, vector_0, vector_1)
                st.session_state.manifold_data = {
                    'vector_0': vector_0,
                    'vector_1': vector_1,
                    'x0': x0, 'y0': y0,
                    'x1': x1, 'y1': y1
                }
                # Clear conversation points when computing new manifold
                st.session_state.conversation_points = []
                
                # Clear existing conversation and start fresh
                st.session_state.messages = [{"role": "system", "content": effective_system_prompt(st.session_state.topic, st.session_state.system_tail)}]
                
                # Generate initial assistant message
                with st.spinner("Generating initial message..."):
                    try:
                        initial_response = get_ai_response(st.session_state.messages)
                        st.session_state.messages.append({"role": "assistant", "content": initial_response})
                        
                        # Compute initial assistant point
                        assistant_conversation_point = compute_conversation_point(st.session_state.messages, st.session_state.manifold_data, "assistant", 1)
                        if assistant_conversation_point:
                            st.session_state.conversation_points.append(assistant_conversation_point)
                            
                    except Exception as e:
                        st.error(f"Error generating initial message: {str(e)}")
                
                st.success("Manifold computed and conversation started!")
            except Exception as e:
                st.error(f"Error computing manifold: {str(e)}")
    
    # System prompt tail (editable)
    st.session_state.system_tail = st.text_area("System Prompt", value=st.session_state.system_tail, height=120)

    # Keep system message synced
    st.session_state.messages[0]["content"] = effective_system_prompt(st.session_state.topic, st.session_state.system_tail)

    # Chat container with fixed height
    chat_placeholder = st.empty()
    
    # Chat input
    prompt = st.chat_input("Type your message")
    
    # Render chat with input
    thread_html = render_chat_thread(st.session_state.messages)
    input_html = f'<div class="chat-input-row"><div style="padding: 8px; color: #ff69b4; font-size: 14px; opacity: 0.8;">Type your message above</div></div>'
    chat_placeholder.markdown('<div class="chat-shell">' + thread_html + input_html + '</div>', unsafe_allow_html=True)
    scroll_chat_to_bottom()
    if prompt:
        # 1) append user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # 1.5) Compute conversation point for user message
        if st.session_state.manifold_data:
            # Count only user messages for separate counter
            user_messages = [m for m in st.session_state.messages if m.get("role") == "user"]
            user_message_index = len(user_messages)
            user_conversation_point = compute_conversation_point(st.session_state.messages, st.session_state.manifold_data, "user", user_message_index)
            if user_conversation_point:
                st.session_state.conversation_points.append(user_conversation_point)

        # 2) stream assistant reply into the last bubble
        # Prepare a temporary assistant message
        st.session_state.messages.append({"role": "assistant", "content": ""})
        assembled = ""
        try:
            for partial in stream_ai_response(st.session_state.messages):
                assembled = partial
                # Update last assistant content
                st.session_state.messages[-1]["content"] = assembled
                # Re-render
                thread_html = render_chat_thread(st.session_state.messages)
                input_html = f'<div class="chat-input-row"><div style="padding: 8px; color: #ff69b4; font-size: 14px; opacity: 0.8;">Type your message above</div></div>'
                chat_placeholder.markdown('<div class="chat-shell">' + thread_html + input_html + '</div>', unsafe_allow_html=True)
                scroll_chat_to_bottom()
        except Exception:
            # Fallback to non-streaming
            reply_text = get_ai_response(st.session_state.messages)
            st.session_state.messages[-1]["content"] = reply_text
            thread_html = render_chat_thread(st.session_state.messages)
            input_html = f'<div class="chat-input-row"><div style="padding: 8px; color: #ff69b4; font-size: 14px; opacity: 0.8;">Type your message above</div></div>'
            chat_placeholder.markdown('<div class="chat-shell">' + thread_html + input_html + '</div>', unsafe_allow_html=True)
            scroll_chat_to_bottom()
        
        # 3) Compute conversation point for assistant message
        if st.session_state.manifold_data:
            # Count only assistant messages for separate counter
            assistant_messages = [m for m in st.session_state.messages if m.get("role") == "assistant"]
            assistant_message_index = len(assistant_messages)
            assistant_conversation_point = compute_conversation_point(st.session_state.messages, st.session_state.manifold_data, "assistant", assistant_message_index)
            if assistant_conversation_point:
                st.session_state.conversation_points.append(assistant_conversation_point)

    # Utility bar
    cols = st.columns(3)
    with cols[0]:
        if st.button("↩️ Reset chat"):
            st.session_state.clear()
            ensure_state()
            st.rerun()
    with cols[1]:
        st.markdown("**Turns:** " + str(len([m for m in st.session_state.messages if m['role'] in ('user','assistant')])))
    with cols[2]:
        st.markdown("**Model:** " + os.getenv("OPENAI_MODEL", "gpt-4.1-mini (or stub)"))

with right:
    st.title("📈 Manifold View")
    st.caption("Shows topic manifold and conversation progression.")
    
    # Show manifold plot if available, otherwise show conversation plot
    if st.session_state.manifold_data:
        fig = plot_manifold(st.session_state.manifold_data, st.session_state.conversation_points)
        st.plotly_chart(fig, use_container_width=True)
        st.info(f"Manifold: red (1/100 sentiment), blue (100/100 sentiment), pink dots (conversation points: {len(st.session_state.conversation_points)})")
    else:
        fig = plot_conversation(st.session_state.messages)
        st.plotly_chart(fig, use_container_width=True)
        st.info("Click 'Compute Topic Manifold' to visualize the topic's persuasion space.")

# ---------- Notes ----------
st.divider()
with st.expander("Setup Notes (optional)"):
    st.markdown(
        """
        **Quick start**
        1. `pip install streamlit openai plotly`
        2. Set `OPENAI_API_KEY` in your environment. Optionally set `OPENAI_MODEL`.
        3. Run: `streamlit run app.py`

        **Customize**
        - Put your task in **Topic** (top of the page). The app prepends it to the system prompt.
        - Implement `plot_conversation(messages)` to visualize embeddings/geometry.
        - Adjust streaming, temperature, and model as needed.
        """
    )
