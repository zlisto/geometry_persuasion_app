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
