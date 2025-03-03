from fastapi import FastAPI, APIRouter, Form, HTTPException, Request, Depends, Body, status
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import os
import json
from datetime import datetime
from pathlib import Path
from pydantic import BaseModel
from infer import chat_with_model, get_vectorstore
import re
from util import load_config
import uvicorn


config = load_config('../config.yaml')  ## argument is config path
DB_PATH =  config['USER_DB_PATH']

# Initialize FastAPI app
app = FastAPI()
router = APIRouter()
app.mount("/static", StaticFiles(directory="../static"), name="static")
templates = Jinja2Templates(directory="../templates")

# Ensure DB directory exists
db_dir = os.path.dirname(DB_PATH)
if not os.path.exists(db_dir):
    os.makedirs(db_dir)

# Helper functions for user data management
def load_user_data(path):
    """Load user data from the database file."""
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return []

def save_user_data(data):
    """Save user data to the database file."""
    with open(DB_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

# Routes
@app.get("/")
async def home(request: Request):
    """
    Serve the main HTML page.
    """
    return templates.TemplateResponse("index.html", {"request": request})

# Define the request model
class ResolvePathRequest(BaseModel):
    # user_id: str
    relative_path: str
    timestamp: str = None

@app.post("/resolve_path/")
async def resolve_path(payload: ResolvePathRequest):
    """
    Resolve a relative path to an absolute path.
    """
    try:
        # user_id = payload.user_id
        user_id = config['user_id']
        relative_path = payload.relative_path
        timestamp = payload.timestamp or datetime.utcnow().isoformat()


        # Validate required fields
        if not user_id or not relative_path:
            raise HTTPException(
                status_code=400,
                detail="Missing required fields: 'user_id' or 'relative_path'."
            )

        # Resolve absolute path (example logic)
        # BASE_DIR = Path.home() / "Documents/temp"  # Example base directory ### todo
        BASE_DIR = config['BASE_DIR']
        absolute_path = (Path(BASE_DIR) / Path(relative_path)).resolve() ## use Path to regular path, e.g. if relative_path is ../xxx

        # Ensure the resolved path is within the allowed base directory
        if not absolute_path.is_relative_to(BASE_DIR):
            raise HTTPException(
                status_code=403,
                detail="Invalid path. Path is outside allowed base directory."
            )

        if os.path.exists(DB_PATH):
            print(f"Database file found at: {DB_PATH}")
            user_data = load_user_data(DB_PATH)
        else:
            print(f"Database file not found at: {DB_PATH}, build the first user database.")
            user_data = []

        # Check if user already exists
        user_entry = next((entry for entry in user_data if entry["user_id"] == user_id), None)

        if user_entry:
            # Update existing user entry
            user_entry["folder_path"] = str(absolute_path),
            user_entry["timestamp"] = timestamp

        else:
            # Add new user entry
            user_data.append({
                "user_id": user_id,
                "folder_path": str(absolute_path),
                "timestamp": timestamp
            })

        # Save updated user data
        save_user_data(user_data)

        return {"absolute_path": str(absolute_path)}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")

## Get the file folder by user_id
def get_folder_path(user_db_path: str, user_id: str):
    try:
        # Load the user database from the file
        with open(user_db_path, 'r') as file:
            user_db = json.load(file)

        # Ensure user_db is a dictionary
        if not isinstance(user_db, list):
            print("Error: The loaded data is not a list of dictionaries.")
            return None

        for user_data in user_db:
            if user_data['user_id'] == user_id:
                return user_data.get('folder_path', [None])[0] ## return an element not a one-element list
        return None

    except FileNotFoundError:
        print(f"Error: The file '{user_db_path}' was not found.")
        return None
    except json.JSONDecodeError:
        print(f"Error: The file '{user_db_path}' contains invalid JSON.")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None

# Define the request model for /chat_kb/
class ChatKBRequest(BaseModel):
    # user_id: str
    question: str
    pdf_directory: str
    timestamp: str = None

@app.post("/chat_kb/")
async def chat_kb(payload: ChatKBRequest):
    """
    Handle chat requests and return a response.
    """
    try:
        # user_id = payload.user_id
        user_id = config['user_id']
        question = payload.question
        '''dont' use pdf_directory = payload.pdf_directory, this sicne the folder in payload is c:/fakepath, need read user id to get it instead'''

        timestamp = payload.timestamp or datetime.utcnow().isoformat()
        pdf_directory = get_folder_path(DB_PATH, user_id)
        if not os.path.exists(pdf_directory):
            print(f"Error: No selected folder in {pdf_directory} set in config.yaml")

        # Validate required fields
        if not user_id or not question or not pdf_directory:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing required fields: 'user_id', 'question', or 'pdf_directory'."
            )


        vectorstore = get_vectorstore(user_id, pdf_directory)  ### TODO PDF_D 是列表
        response_message = chat_with_model(question, vectorstore)

        return {"response": format_qwen(response_message)}


    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")

def format_qwen(response):
    '''
    Extracts the content within double quotes following the marker **Response:**

    Example input:
    **Response:**
    "I am Qwen, a large language model ... with something, feel free to ask!"

    Returns:
    I am Qwen, a large language model ... with something, feel free to ask!
    '''
    # Use a regex pattern to find the content in double quotes after "**Response:**"
    match = re.search(r'\*\*Response:\*\*\s*"(.*)"', response, re.DOTALL)
    if match:
        return match.group(1).strip()  # Return the content inside the quotes
    else:
        return "Nothing"  # Return "Nothing" if no match is found

if __name__ == "__main__":
    """
    Run the FastAPI app locally.
    """
    # uvicorn.run(app, host="127.0.0.1", port=8000)
    uvicorn.run(app, host= config['host_ip'], port= config['port'])