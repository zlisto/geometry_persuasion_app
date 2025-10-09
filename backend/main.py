from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import os
import dotenv
from geometry_persuasion import (
    get_embedding, 
    get_manifold_vectors, 
    manifold_coords_v1,
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
    conversation_points: List[ConversationPoint] = []

@app.get("/")
async def root():
    return {"message": "Geometry of Persuasion API"}

@app.post("/compute-manifold", response_model=ManifoldResponse)
async def compute_manifold(request: TopicRequest):
    """Compute manifold vectors for a given topic."""
    try:
        vector_0, vector_1 = get_manifold_vectors(request.topic, model='gpt-4o')
        x0, y0 = manifold_coords_v1(vector_0, vector_0, vector_1)
        x1, y1 = manifold_coords_v1(vector_1, vector_0, vector_1)
        
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
    """Generate AI response and compute conversation points for both user and assistant."""
    print(f"🔍 DEBUG: Chat endpoint called with {len(request.messages)} messages")
    print(f"🔍 DEBUG: Message roles: {[m.role for m in request.messages]}")
    print(f"🔍 DEBUG: Has manifold data: {request.manifold_data is not None}")
    
    try:
        # Convert messages to the format expected by generate_text
        system_msg = next((m.content for m in request.messages if m.role == "system"), "")
        turns = [m for m in request.messages if m.role != "system"]
        conversation_text = "\n\n".join(f"{m.role.upper()}: {m.content}" for m in turns)
        
        print(f"🔍 DEBUG: System message length: {len(system_msg)}")
        print(f"🔍 DEBUG: Conversation text length: {len(conversation_text)}")
        
        # Generate response
        print(f"🔍 DEBUG: Generating AI response...")
        response_text = generate_text(system_msg, conversation_text or "Respond to the user.", model='gpt-4o')
        print(f"🔍 DEBUG: Generated response length: {len(response_text)}")
        
        # Compute conversation points if manifold data is available
        conversation_points = []
        if request.manifold_data:
            print(f"🔍 DEBUG: Computing conversation points for both user and assistant...")
            
            # Compute user conversation point
            user_messages = [m for m in request.messages if m.role == "user"]
            if user_messages:
                print(f"🔍 DEBUG: Found {len(user_messages)} user messages")
                try:
                    user_text = " ".join([m.content for m in user_messages])
                    print(f"🔍 DEBUG: User text length: {len(user_text)}")
                    
                    print(f"🔍 DEBUG: Getting user embedding...")
                    user_vector = get_embedding(user_text)
                    print(f"🔍 DEBUG: User embedding length: {len(user_vector)}")
                    
                    print(f"🔍 DEBUG: Computing user manifold coordinates...")
                    user_x, user_y = manifold_coords_v1(
                        user_vector, 
                        request.manifold_data['vector_0'], 
                        request.manifold_data['vector_1']
                    )
                    print(f"🔍 DEBUG: User coordinates: x={user_x}, y={user_y}")
                    
                    user_point = ConversationPoint(
                        x=user_x, 
                        y=user_y, 
                        role="user", 
                        message_index=len(user_messages)
                    )
                    conversation_points.append(user_point)
                    print(f"🔍 DEBUG: Created user conversation point: {user_point}")
                except Exception as e:
                    print(f"❌ ERROR: Error computing user conversation point: {str(e)}")
                    import traceback
                    print(f"❌ ERROR: Traceback: {traceback.format_exc()}")
            else:
                print(f"🔍 DEBUG: No user messages found")
            
            # Compute assistant conversation point
            assistant_messages = [m for m in request.messages if m.role == "assistant"]
            if assistant_messages:
                print(f"🔍 DEBUG: Found {len(assistant_messages)} assistant messages")
                try:
                    assistant_text = " ".join([m.content for m in assistant_messages])
                    print(f"🔍 DEBUG: Assistant text length: {len(assistant_text)}")
                    
                    print(f"🔍 DEBUG: Getting assistant embedding...")
                    assistant_vector = get_embedding(assistant_text)
                    print(f"🔍 DEBUG: Assistant embedding length: {len(assistant_vector)}")
                    
                    print(f"🔍 DEBUG: Computing assistant manifold coordinates...")
                    assistant_x, assistant_y = manifold_coords_v1(
                        assistant_vector, 
                        request.manifold_data['vector_0'], 
                        request.manifold_data['vector_1']
                    )
                    print(f"🔍 DEBUG: Assistant coordinates: x={assistant_x}, y={assistant_y}")
                    
                    assistant_point = ConversationPoint(
                        x=assistant_x, 
                        y=assistant_y, 
                        role="assistant", 
                        message_index=len(assistant_messages)
                    )
                    conversation_points.append(assistant_point)
                    print(f"🔍 DEBUG: Created assistant conversation point: {assistant_point}")
                except Exception as e:
                    print(f"❌ ERROR: Error computing assistant conversation point: {str(e)}")
                    import traceback
                    print(f"❌ ERROR: Traceback: {traceback.format_exc()}")
            else:
                print(f"🔍 DEBUG: No assistant messages found")
        else:
            print(f"🔍 DEBUG: No manifold data provided, skipping conversation point computation")
        
        print(f"🔍 DEBUG: Returning {len(conversation_points)} conversation points")
        
        return ChatResponse(
            response=response_text,
            conversation_points=conversation_points
        )
    except Exception as e:
        print(f"❌ ERROR: Exception in chat endpoint: {str(e)}")
        import traceback
        print(f"❌ ERROR: Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error generating response: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
