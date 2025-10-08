from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import os
import dotenv
from geometry_persuasion import (
    get_embedding, 
    get_manifold_vectors, 
    manifold_coords,
    generate_text
)

# Load environment variables
dotenv.load_dotenv()

app = FastAPI(title="Geometry of Persuasion API", version="1.0.0")

# CORS middleware for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for now
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class TopicRequest(BaseModel):
    topic: str
    system_tail: str = "You are a salesperson trying to convince someone on a cold call to purchase the given product. Be a charismatic salesperson, ask open-ended questions, and be informative. Don't be too pushy or verbose, try to find out about the customer and see how the product would fit into their life."

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    manifold_data: Optional[Dict[str, Any]] = None

class ManifoldResponse(BaseModel):
    vector_0: List[float]
    vector_1: List[float]
    x0: float
    y0: float
    x1: float
    y1: float

class ConversationPoint(BaseModel):
    x: float
    y: float
    role: str
    message_index: int

class ChatResponse(BaseModel):
    response: str
    conversation_point: Optional[ConversationPoint] = None

@app.get("/")
async def root():
    return {"message": "Geometry of Persuasion API"}

@app.post("/compute-manifold", response_model=ManifoldResponse)
async def compute_manifold(request: TopicRequest):
    """Compute manifold vectors for a given topic."""
    try:
        vector_0, vector_1 = get_manifold_vectors(request.topic, model='gpt-4o')
        x0, y0 = manifold_coords(vector_0, vector_0, vector_1)
        x1, y1 = manifold_coords(vector_1, vector_0, vector_1)
        
        return ManifoldResponse(
            vector_0=vector_0,
            vector_1=vector_1,
            x0=x0,
            y0=y0,
            x1=x1,
            y1=y1
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error computing manifold: {str(e)}")

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Generate AI response and compute conversation point."""
    try:
        # Convert messages to the format expected by generate_text
        system_msg = next((m.content for m in request.messages if m.role == "system"), "")
        turns = [m for m in request.messages if m.role != "system"]
        conversation_text = "\n\n".join(f"{m.role.upper()}: {m.content}" for m in turns)
        
        # Generate response
        response_text = generate_text(system_msg, conversation_text or "Respond to the user.", model='gpt-4o')
        
        # Compute conversation point if manifold data is available
        conversation_point = None
        if request.manifold_data:
            # Get only messages of the assistant role (cumulative)
            assistant_messages = [m for m in request.messages if m.role == "assistant"]
            if assistant_messages:
                # Join only the assistant messages
                assistant_text = " ".join([m.content for m in assistant_messages])
                try:
                    assistant_vector = get_embedding(assistant_text)
                    x, y = manifold_coords(
                        assistant_vector, 
                        request.manifold_data['vector_0'], 
                        request.manifold_data['vector_1']
                    )
                    conversation_point = ConversationPoint(
                        x=x, 
                        y=y, 
                        role="assistant", 
                        message_index=len(assistant_messages)
                    )
                except Exception as e:
                    print(f"Error computing conversation point: {str(e)}")
        
        return ChatResponse(
            response=response_text,
            conversation_point=conversation_point
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating response: {str(e)}")

@app.post("/compute-conversation-point")
async def compute_conversation_point(
    messages: List[ChatMessage], 
    manifold_data: Dict[str, Any], 
    role: str
):
    """Compute conversation point for a specific role's messages."""
    try:
        # Get only messages of the specific role (cumulative)
        role_messages = [m for m in messages if m.role == role]
        if not role_messages:
            return None
        
        # Join only the messages of this specific role
        role_text = " ".join([m.content for m in role_messages])
        
        # Get embedding for the cumulative messages of this role only
        role_vector = get_embedding(role_text)
        # Compute manifold coordinates
        x, y = manifold_coords(role_vector, manifold_data['vector_0'], manifold_data['vector_1'])
        
        return ConversationPoint(
            x=x, 
            y=y, 
            role=role, 
            message_index=len(role_messages)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error computing conversation point: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
