
import os
import json
import asyncio
from typing import AsyncIterator, Optional
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langgraph.checkpoint.memory import InMemorySaver
from prompts import CODING_SYSTEM_PROMPT, CODING_SYSTEM_PROMPT2
import feedback_manager
from tools import force_consolidate

from tools import (
    edit_file,
    glob,
    grep,
    list_files,
    memorization,
    memory_recollection,
    consolidate,
    make_directory,
    read_file,
    todo_next,
    todo_write,
    write_file,
    get_human_feedback,
    execute_command
)

# Load environment variables from a .env file
load_dotenv()

# Initialize FastAPI app
app = FastAPI(title="Deep Agent IDE")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Get workspace and memory directories
WORKSPACE_ROOT = os.path.join(os.getcwd(), "workspace")
MEMORY_ROOT = os.path.join(os.getcwd(), "memory")

if not os.path.exists(WORKSPACE_ROOT):
    os.makedirs(WORKSPACE_ROOT)
if not os.path.exists(MEMORY_ROOT):
    os.makedirs(MEMORY_ROOT)


"""
models:


glm-5
glm-4.6
glm-4.7

kimi-k2:1t
kimi-k2.5
kimi-k2-thinking

minimax-m2.5
minimax-m2.1

gpt-oss:120b

"""


# Initialize LangChain model
model = init_chat_model(
    model="kimi-k2:1t",
    model_provider="ollama",
    base_url="https://ollama.com",
    api_key=os.getenv("OLLAMA_API_KEY"),
    temperature=1,
    #max_tokens=1000,

)

tools = [
    todo_write,
    todo_next,
    read_file,
    write_file,
    edit_file,
    list_files,
    make_directory,
    grep,
    glob,
    memorization,
    memory_recollection,
    consolidate,
    get_human_feedback,
    execute_command
]





agent: any = None

def intialize_agent():
    """Initialize agent state with default thread and empty messages"""
    
    global agent    

    agent = create_agent(
    model=model,    
    tools=tools,
    system_prompt=CODING_SYSTEM_PROMPT2,
    checkpointer=InMemorySaver()
        )


intialize_agent()  # Initialize agent at startup


# Request/Response Models
class ChatMessage(BaseModel):
    content: str
    thread_id: str = "1"

class FileRequest(BaseModel):
    path: str
    folder: str = "workspace"

class FileSaveRequest(BaseModel):
    path: str
    content: str
    folder: str = "workspace"

class FeedbackResponse(BaseModel):
    feedback: str
    accepted: bool


# API Endpoints



# agent reset with empty mesage history


@app.post("/api/memory/consolidate")
async def manual_consolidate():
    """
    Manually consolidate short-term memory to long-term memory from UI
    """
    try:
        force_consolidate()  # Call the function to consolidate memory
        return {"status": "success", "message": "Memory consolidation triggered successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/files/tree")
async def get_file_tree(folder: str = "workspace"):
    """Get the file tree structure from specified folder (workspace or memory)"""
    # Select root directory based on folder parameter
    root_dir = MEMORY_ROOT if folder == "memory" else WORKSPACE_ROOT
    
    def build_tree(directory: str, prefix: str = "", is_root: bool = False):
        items = []
        try:
            entries = sorted(os.listdir(directory))
            for entry in entries:
                # Filter memory root to only show long_term_memory and short_term_memory
                if is_root and folder == "memory":
                    if entry not in ["long_term_memory", "short_term_memory"]:
                        continue
                
                full_path = os.path.join(directory, entry)
                rel_path = os.path.relpath(full_path, root_dir)
                
                if os.path.isdir(full_path):
                    items.append({
                        "name": entry,
                        "path": rel_path,
                        "type": "directory",
                        "children": build_tree(full_path, rel_path, False)
                    })
                else:
                    items.append({
                        "name": entry,
                        "path": rel_path,
                        "type": "file"
                    })
        except PermissionError:
            pass
        return items
    
    return {"tree": build_tree(root_dir, "", True), "folder": folder}

@app.post("/api/files/content")
async def get_file_content(request: FileRequest):
    """Get content of a specific file"""
    try:
        root_dir = MEMORY_ROOT if request.folder == "memory" else WORKSPACE_ROOT
        file_path = os.path.join(root_dir, request.path)
        # Security check: ensure path is within selected folder
        if not os.path.abspath(file_path).startswith(os.path.abspath(root_dir)):
            raise HTTPException(status_code=403, detail="Access denied")
        
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return {"content": content, "path": request.path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/files/save")
async def save_file_content(request: FileSaveRequest):
    """Save content to a specific file"""
    try:
        root_dir = MEMORY_ROOT if request.folder == "memory" else WORKSPACE_ROOT
        file_path = os.path.join(root_dir, request.path)
        # Security check: ensure path is within selected folder
        if not os.path.abspath(file_path).startswith(os.path.abspath(root_dir)):
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(request.content)
        
        return {"success": True, "path": request.path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@app.post("/api/chat/reset")
async def reset_chat():
    """Reset agent conversation history"""
    try:
        intialize_agent()  # Re-initialize agent to reset state
        return {"status": "success", "message": "Agent conversation reset"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/chat/stream")
async def chat_stream(message: ChatMessage):
    """Stream agent responses using Server-Sent Events"""
    
    async def event_generator() -> AsyncIterator[str]:
        try:
            # Send start event
            yield f"data: {json.dumps({'type': 'start'})}\n\n"
            await asyncio.sleep(0)  # Force flush
            
            # Create a queue for communication between threads
            import queue
            event_queue = queue.Queue()
            
            def run_agent():
                """Run agent in separate thread"""
                try:
                    for chunk in agent.stream(
                        {"messages": [{"role": "user", "content": message.content}]},
                        {"configurable": {"thread_id": "1"}},
                        stream_mode="updates",
                    ):
                        event_queue.put(("chunk", chunk))
                    event_queue.put(("done", None))
                except Exception as e:
                    event_queue.put(("error", str(e)))
            
            # Start agent in background thread
            import threading
            agent_thread = threading.Thread(target=run_agent, daemon=True)
            agent_thread.start()
            
            # Stream agent responses from queue
            while True:
                # Check queue with timeout to allow async operations
                try:
                    event_type, event_data = event_queue.get(timeout=0.1)
                except queue.Empty:
                    await asyncio.sleep(0)
                    continue
                
                if event_type == "done":
                    break
                elif event_type == "error":
                    error_data = {'type': 'error', 'message': event_data}
                    yield f"data: {json.dumps(error_data)}\n\n"
                    await asyncio.sleep(0)
                    break
                elif event_type == "chunk":
                    chunk = event_data
                    for step, data in chunk.items():
                        if 'messages' in data and len(data['messages']) > 0:
                            msg = data['messages'][-1]
                            
                            # Check if message has content_blocks
                            if hasattr(msg, 'content_blocks'):
                                content_blocks = msg.content_blocks
                                
                                for block in content_blocks:
                                    if block['type'] == 'text':
                                        # Text content - check step to determine if it's tool output or assistant message
                                        event_data = {
                                            'type': 'tool_response' if step == 'tools' else 'assistant_message',
                                            'step': step,
                                            'content': block['text']
                                        }
                                        yield f"data: {json.dumps(event_data)}\n\n"
                                        await asyncio.sleep(0)  # Force flush
                                    
                                    elif block['type'] == 'tool_call':
                                        # Tool call event
                                        event_data = {
                                            'type': 'tool_call',
                                            'step': step,
                                            'name': block['name'],
                                            'args': block.get('args', {}),
                                            'id': block.get('id', '')
                                        }
                                        yield f"data: {json.dumps(event_data)}\n\n"
                                        await asyncio.sleep(0)  # Force flush
                            
                            # Handle plain content attribute
                            elif hasattr(msg, 'content') and msg.content:
                                event_data = {
                                    'type': 'tool_response' if step == 'tools' else 'assistant_message',
                                    'step': step,
                                    'content': str(msg.content)
                                }
                                yield f"data: {json.dumps(event_data)}\n\n"
                                await asyncio.sleep(0)  # Force flush
            
            # Send completion event
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
            await asyncio.sleep(0)  # Force flush
            
        except Exception as e:
            error_data = {'type': 'error', 'message': str(e)}
            yield f"data: {json.dumps(error_data)}\n\n"
            await asyncio.sleep(0)  # Force flush
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )

# Human Feedback Endpoints
@app.get("/api/feedback/check")
async def check_feedback_request():
    """Check if feedback is being requested"""
    return feedback_manager.get_feedback_state()

@app.post("/api/feedback/submit")
async def submit_feedback(response: FeedbackResponse):
    """Submit feedback response from UI"""
    feedback_manager.set_feedback_response(response.feedback, response.accepted)
    return {"status": "success"}


# Serve static files from ui/dist directory
ui_dist_path = os.path.join(os.getcwd(), "ui", "dist")
if os.path.exists(ui_dist_path):
    app.mount("/assets", StaticFiles(directory=os.path.join(ui_dist_path, "assets")), name="assets")
    
    @app.get("/")
    async def serve_ui():
        index_path = os.path.join(ui_dist_path, "index.html")
        if os.path.exists(index_path):
            return FileResponse(index_path)
        return {"message": "UI not built yet. Run 'npm run build' in the ui directory."}
else:
    @app.get("/")
    async def root():
        return {"message": "Deep Agent IDE API is running. Build the UI to access the web interface."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)