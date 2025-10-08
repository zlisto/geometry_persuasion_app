import plotly.graph_objects as go
import numpy as np
from ast import literal_eval
from openai import OpenAI
import dotenv

dotenv.load_dotenv()    
client = OpenAI()

OpenAI_API_model = "gpt-4.1-mini"
OpenAI_embedding_model = "text-embedding-3-large"

def get_embedding(text, model=OpenAI_embedding_model):
    text = text.replace("\n", " ")
    return client.embeddings.create(input = [text], model=model).data[0].embedding

def generate_text(system_prompt, message, model='gpt-4o'):
    response = client.responses.create(
            model=model,
            temperature=1,
            input=[
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": message or "Respond to the user.",
                },
            ],
        )
    return response.output_text.strip()


def get_manifold_vectors(topic:str, model='gpt-4o'):
    
    prompt_0 = f"""Write a statement with a sentiment of 1/100 on this topic: {topic}"""
    prompt_1 = f"""Write a statement with a sentiment of 100/100 on this topic: {topic}"""

    text_0 = generate_text(prompt_0, message=topic, model=model)
    text_1 = generate_text(prompt_1, message=topic, model=model)
    
    vector_0 = get_embedding(text_0, model=OpenAI_embedding_model)
    vector_1 = get_embedding(text_1, model=OpenAI_embedding_model)
    
    return vector_0, vector_1




def manifold_coords(u: np.ndarray, v0: np.ndarray, v1: np.ndarray):
    """
    Map u into coordinates (x, y) in the plane spanned by {v0, v1},
    with v0 mapped to (-1, 1) and v1 mapped to (1, 1).
    """
    u, v0, v1 = map(lambda v: np.asarray(v, float).ravel(), (u, v0, v1))
    x_dir = v1 - v0
    e1 = x_dir / np.linalg.norm(x_dir)

    # e2: orthogonal within the plane
    v_mid = 0.5 * (v0 + v1)
    e2 = v_mid - np.dot(v_mid, e1) * e1
    e2 /= np.linalg.norm(e2)

    # center origin halfway between v0, v1
    origin = 0.5 * (v0 + v1)

    # coordinates of u relative to origin
    rel = u - origin
    x_raw, y_raw = np.dot(rel, e1), np.dot(rel, e2)

    # scale x so v0=-1, v1=1
    half_span = np.dot((v1 - origin), e1)
    x = x_raw / half_span
    # set y so midpoint baseline = 1
    y0 = np.dot((v0 - origin), e2)
    y = 1 + (y_raw - y0)
    return float(x), float(y)




def plot_manifold(manifold_data, conversation_points=None):
    """
    Plot the topic manifold with v0, v1 points and optional conversation points.
    
    Parameters
    ----------
    manifold_data : dict
        Dictionary containing manifold coordinates with keys: 'x0', 'y0', 'x1', 'y1'
    conversation_points : list, optional
        List of (x, y) tuples representing conversation message coordinates
        
    Returns
    -------
    plotly.graph_objs._figure.Figure
        A chart showing the manifold and conversation points.
    """
    fig = go.Figure()
    
    if manifold_data:
        # Add the line connecting the two manifold points (dashed purple)
        fig.add_trace(
            go.Scatter(
                x=[manifold_data['x0'], manifold_data['x1']],
                y=[manifold_data['y0'], manifold_data['y1']],
                mode="lines",
                line=dict(width=3, color="purple", dash="dash"),
                name="Manifold Line",
                showlegend=False,
            )
        )
        # Add v0 point (red)
        fig.add_trace(
            go.Scatter(
                x=[manifold_data['x0']],
                y=[manifold_data['y0']],
                mode="markers",
                marker=dict(size=15, color="red", symbol="x"),
                name="1/100 Sentiment",
                hovertemplate="1/100 Sentiment: (%{x:.2f}, %{y:.2f})<extra></extra>",
            )
        )
        # Add v1 point (blue)
        fig.add_trace(
            go.Scatter(
                x=[manifold_data['x1']],
                y=[manifold_data['y1']],
                mode="markers",
                marker=dict(size=15, color="blue", symbol="x"),
                name="100/100 Sentiment",
                hovertemplate="100/100 Sentiment: (%{x:.2f}, %{y:.2f})<extra></extra>",
            )
        )
    
    # Add conversation points if available
    if conversation_points:
        # Separate user and assistant points
        user_points = [point for point in conversation_points if point[2] == "user"]
        assistant_points = [point for point in conversation_points if point[2] == "assistant"]
        
        # Add user points with connecting line (orange circles)
        if user_points:
            x_coords = [point[0] for point in user_points]
            y_coords = [point[1] for point in user_points]
            message_nums = [point[3] for point in user_points]
            fig.add_trace(
                go.Scatter(
                    x=x_coords,
                    y=y_coords,
                    mode="lines+markers",
                    line=dict(width=2, color="orange", dash="solid"),
                    marker=dict(size=10, color="orange", symbol="circle"),
                    name="User Messages",
                    customdata=message_nums,
                    hovertemplate="Message %{customdata}: User<br>(%{x:.2f}, %{y:.2f})<extra></extra>",
                )
            )
        
        # Add assistant points with connecting line (green squares)
        if assistant_points:
            x_coords = [point[0] for point in assistant_points]
            y_coords = [point[1] for point in assistant_points]
            message_nums = [point[3] for point in assistant_points]
            fig.add_trace(
                go.Scatter(
                    x=x_coords,
                    y=y_coords,
                    mode="lines+markers",
                    line=dict(width=2, color="green", dash="solid"),
                    marker=dict(size=10, color="green", symbol="square"),
                    name="Assistant Messages",
                    customdata=message_nums,
                    hovertemplate="Message %{customdata}: Assistant<br>(%{x:.2f}, %{y:.2f})<extra></extra>",
                )
            )
    
    fig.update_layout(
        title={"text": "Topic Manifold", "font": {"size": 28, "color": "#ff69b4"}},
        xaxis_title={"text": "Sentiment", "font": {"size": 22, "color": "#ff69b4"}},
        yaxis_title={"text": "Relevance", "font": {"size": 22, "color": "#ff69b4"}},
        template="plotly_dark",
        paper_bgcolor="#000000",
        plot_bgcolor="#000000",
        font=dict(size=20, color="#ff69b4"),
        margin=dict(l=40, r=20, t=60, b=40),
        height=600,
        xaxis=dict(range=[-1.1, 1.1]),
        yaxis=dict(range=[0, 1.1]),
    )
    fig.update_xaxes(showgrid=True, gridcolor="rgba(255,105,180,0.25)", zerolinecolor="#ff69b4")
    fig.update_yaxes(showgrid=True, gridcolor="rgba(255,105,180,0.25)", zerolinecolor="#ff69b4")
    return fig

def plot_conversation(messages):
    """
    Simple plotting function for conversation messages.

    Parameters
    ----------
    messages : list[dict]
        Sequence of chat messages with keys: 'role' in {"system","user","assistant"}, 'content': str

    Returns
    -------
    plotly.graph_objs._figure.Figure
        A simple line+marker chart indexing user/assistant turns.
    """
    turns = [m for m in messages if m.get("role") in ("user", "assistant")]
    n = max(len(turns), 1)

    x_vals = list(range(1, n + 1))
    y_vals = x_vals[:]
    roles = [m.get("role", "?") for m in turns]
    texts = [m.get("content", "") for m in turns]
    custom = [[r, t] for r, t in zip(roles, texts)]

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=x_vals,
            y=y_vals,
            mode="lines+markers",
            line=dict(width=3, color="#ff69b4"),
            marker=dict(size=10, color="#ff69b4"),
            name="Messages",
            customdata=custom,
            hovertemplate="Message %{x}<br>%{customdata[0]}: %{customdata[1]}<extra></extra>",
        )
    )
    fig.update_layout(
        title={"text": "Conversation — Messages by Index", "font": {"size": 28, "color": "#ff69b4"}},
        xaxis_title={"text": "Message index", "font": {"size": 22, "color": "#ff69b4"}},
        yaxis_title={"text": "Message index", "font": {"size": 22, "color": "#ff69b4"}},
        template="plotly_dark",
        paper_bgcolor="#000000",
        plot_bgcolor="#000000",
        font=dict(size=20, color="#ff69b4"),
        margin=dict(l=40, r=20, t=60, b=40),
        height=600,
    )
    fig.update_xaxes(showgrid=True, gridcolor="rgba(255,105,180,0.25)", zerolinecolor="#ff69b4")
    fig.update_yaxes(showgrid=True, gridcolor="rgba(255,105,180,0.25)", zerolinecolor="#ff69b4")
    return fig