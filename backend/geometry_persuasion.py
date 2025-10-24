import plotly.graph_objects as go
import numpy as np
import math
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


def angle_between(v0, v1):
    """Return the angle (radians) between v0 and v1."""
    v0, v1 = np.array(v0), np.array(v1)
    cos_theta = np.dot(v0, v1) / (np.linalg.norm(v0) * np.linalg.norm(v1))
    return np.arccos(np.clip(cos_theta, -1.0, 1.0))

def projection_matrix(basis_vectors):
    """Projection matrix for subspace spanned by basis_vectors."""
    A = np.column_stack(basis_vectors)
    return A @ np.linalg.inv(A.T @ A) @ A.T

def projection_coefficients(projected, basis_vectors):
    """Return coefficients of projected vector in basis_vectors."""
    A = np.column_stack(basis_vectors)
    return np.linalg.lstsq(A, projected, rcond=None)[0]

def project_embedding(emb, v0, v1):
    """Project emb onto (v0, v1) plane and return Cartesian (x, y)."""
    P = projection_matrix([v0, v1])
    projected = P @ np.array(emb)
    a, b = projection_coefficients(projected, [v0, v1])

    norm_v0, norm_v1 = np.linalg.norm(v0), np.linalg.norm(v1)
    angle = angle_between(v0, v1)
    x = a * norm_v0 + b * norm_v1 * np.cos(angle)
    y = b * norm_v1 * np.sin(angle)
    return x, y, angle

def manifold_coords_v1(u: np.ndarray, v0: np.ndarray, v1: np.ndarray):
    """
    Map u into coordinates (x, y) in the plane spanned by {v0, v1},
    using Yen-Shao's method.
    """
    x, y, angle_v0v1 = project_embedding(u, v0, v1)
    r = math.hypot(x, y)
    theta = math.atan2(y, x)

    normalized_r = r / 1.0
    normalized_theta = theta / angle_v0v1
    return x, y

def manifold_coords_v0(u: np.ndarray, v0: np.ndarray, v1: np.ndarray):
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
