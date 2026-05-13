# """
# TailorTalk - Google Drive Search Agent
# FastAPI Backend
# """

# from fastapi import FastAPI, HTTPException
# from fastapi.middleware.cors import CORSMiddleware
# from pydantic import BaseModel
# from typing import Optional
# import json
# import os
# from datetime import datetime

# from google.oauth2.service_account import Credentials
# from google.auth.transport.requests import Request
# from googleapiclient.discovery import build

# from langchain_core.tools import Tool
# from langchain_core.messages import HumanMessage, AIMessage
# from langchain.agents import AgentExecutor, create_tool_calling_agent
# from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

# from langchain_groq import ChatGroq
# from dotenv import load_dotenv

# load_dotenv()


# app = FastAPI(title="TailorTalk", version="1.0")

# # Add CORS
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )


# class GoogleDrive:
#     """Google Drive API handler"""
    
#     def __init__(self):
#         # service_account_json = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
        
#         # if not service_account_json:
#         #     raise ValueError("Missing GOOGLE_SERVICE_ACCOUNT_JSON")
        
#         # try:
#         #     service_account_info = json.loads(service_account_json)
#         # except:
#         #     raise ValueError("Invalid JSON in GOOGLE_SERVICE_ACCOUNT_JSON")
        
#         # self.credentials = Credentials.from_service_account_info(
#         #     service_account_info,
#         #     scopes=['https://www.googleapis.com/auth/drive']
#         self.credentials = Credentials.from_service_account_file(
#     "key.json",   # <-- your file name (change if renamed)
#     scopes=['https://www.googleapis.com/auth/drive']

#         )
        
#         self.service = build('drive', 'v3', credentials=self.credentials)
#         self.folder_id = os.getenv("DRIVE_FOLDER_ID")
        
#         if not self.folder_id:
#             raise ValueError("Missing DRIVE_FOLDER_ID")
    
#     def search(self, query: str):
#         """Search files with given query"""
#         try:
#             full_query = f"'{self.folder_id}' in parents and trashed=false and {query}"
            
#             results = self.service.files().list(
#                 q=full_query,
#                 spaces='drive',
#                 fields='files(id, name, mimeType, createdTime, modifiedTime, size, webViewLink)',
#                 pageSize=10,
#             ).execute()
            
#             return results.get('files', [])
        
#         except Exception as e:
#             print(f"Drive search error: {e}")
#             return []


# # Initialize
# try:
#     drive = GoogleDrive()
# except Exception as e:
#     print(f"Warning: {e}")
#     drive = None


# # Request/Response models
# class SearchRequest(BaseModel):
#     query: str
#     conversation_history: Optional[list] = None


# class SearchResponse(BaseModel):
#     response: str
#     files: list
#     query_used: str


# # Search tool for the agent
# def drive_search(search_query: str) -> str:
#     """Search Google Drive"""
#     if not drive:
#         return "Error: Drive not connected"
    
#     files = drive.search(search_query)
    
#     if not files:
#         return "No files found."
    
#     result = f"Found {len(files)} files:\n\n"
#     for f in files:
#         result += f"📄 {f['name']}\n"
#         result += f"   Type: {f.get('mimeType', 'Unknown')}\n"
#         result += f"   Modified: {f.get('modifiedTime', 'Unknown')}\n"
#         result += f"   [Open]({f.get('webViewLink', '#')})\n\n"
    
#     return result


# # Setup LangChain
# tools = [
#     Tool(
#         name="GoogleDriveSearch",
#         func=drive_search,
#         description="""Search Google Drive files.
        
# Generate queries like:
# - name contains 'report'
# - mimeType='application/pdf'
# - modifiedTime > '2024-01-01T00:00:00'
# - fullText contains 'budget'
# - Multiple conditions with 'and' or 'or'
# """
#     )
# ]

# llm = ChatGroq(
#     model="llama-3.3-70b-versatile",
#     api_key=os.getenv("GROQ_API_KEY"),
#     temperature=0.3,
# )


# system_prompt = """You are a helpful assistant that searches Google Drive files.

# When users ask to find files, you:
# 1. Understand what they're looking for
# 2. Use the GoogleDriveSearch tool to find files
# 3. Show the results clearly with links

# Generate Google Drive API queries like:
# - name contains 'keyword' for partial matches
# - mimeType='type' for file types
# - modifiedTime > 'date' for recent files
# - fullText contains 'text' to search content
# - Combine with 'and' or 'or'

# Be helpful and conversational!"""

# prompt = ChatPromptTemplate.from_messages([
#     ("system", system_prompt),
#     MessagesPlaceholder(variable_name="chat_history"),
#     ("human", "{input}"),
#     MessagesPlaceholder(variable_name="agent_scratchpad"),
# ])

# agent = create_tool_calling_agent(llm, tools, prompt)
# agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True, max_iterations=5)


# # Endpoints
# @app.get("/")
# async def root():
#     return {"status": "TailorTalk API", "version": "1.0"}


# @app.get("/health")
# async def health():
#     drive_ok = "Connected" if drive else "Error"
#     return {
#         "status": "ok",
#         "drive": drive_ok,
#         "time": datetime.now().isoformat()
#     }


# # 
# @app.post("/search")
# async def search(request: SearchRequest):
#     try:
#         chat_history = []

#         if request.conversation_history:
#             for msg in request.conversation_history:

#                 if not msg:
#                     continue

#                 role = msg.get("role", "")
#                 content = msg.get("content", "")

#                 if role == "user":
#                     chat_history.append(
#                         HumanMessage(content=content)
#                     )
#                 else:
#                     chat_history.append(
#                         AIMessage(content=content)
#                     )

#         result = agent_executor.invoke({
#             "input": request.query,
#             "chat_history": chat_history,
#         })

#         return {
#             "response": result.get("output", "No response"),
#             "files": [],
#             "query_used": request.query
#         }

#     except Exception as e:
#         print("SEARCH ERROR:", str(e))

#         return {
#             "response": f"Error: {str(e)}",
#             "files": [],
#             "query_used": request.query
#         }
    
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))


# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=8000)


# new code
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import json
import os
from datetime import datetime

from google.oauth2.service_account import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

from langchain_core.tools import Tool, StructuredTool
from langchain_core.messages import HumanMessage, AIMessage
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from langchain_groq import ChatGroq
from dotenv import load_dotenv

load_dotenv()


app = FastAPI(title="TailorTalk", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class GoogleDrive:
    def __init__(self):
        service_account_json = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")

        if service_account_json:
            service_account_info = json.loads(service_account_json)
            self.credentials = Credentials.from_service_account_info(
                service_account_info,
                scopes=['https://www.googleapis.com/auth/drive']
            )
        else:
            self.credentials = Credentials.from_service_account_file(
                "key.json",
                scopes=['https://www.googleapis.com/auth/drive']
            )

        self.service = build('drive', 'v3', credentials=self.credentials)
        self.folder_id = os.getenv("DRIVE_FOLDER_ID")

        if not self.folder_id:
            raise ValueError("Missing DRIVE_FOLDER_ID")

    def search(self, query: str):
        try:
            full_query = f"'{self.folder_id}' in parents and trashed=false and {query}"
            results = self.service.files().list(
                q=full_query,
                spaces='drive',
                fields='files(id, name, mimeType, createdTime, modifiedTime, size, webViewLink)',
                pageSize=10,
            ).execute()
            return results.get('files', [])
        except Exception as e:
            print(f"Drive search error: {e}")
            return []


try:
    drive = GoogleDrive()
except Exception as e:
    print(f"Warning: {e}")
    drive = None


class SearchRequest(BaseModel):
    query: str
    conversation_history: Optional[list] = None


class SearchResponse(BaseModel):
    response: str
    files: list
    query_used: str


found_files = []


def drive_search(search_query: str) -> str:
    global found_files
    if not drive:
        return "Error: Drive not connected"
    files = drive.search(search_query)
    found_files = files
    if not files:
        return "No files found."
    result = f"Found {len(files)} files:\n\n"
    for f in files:
        result += f"📄 {f['name']}\n"
        result += f"   Type: {f.get('mimeType', 'Unknown')}\n"
        result += f"   Modified: {f.get('modifiedTime', 'Unknown')}\n"
        result += f"   [Open]({f.get('webViewLink', '#')})\n\n"
    return result


tools = [
    Tool(
        name="GoogleDriveSearch",
        func=drive_search,
        description="""Search Google Drive files.
Generate queries like:
- name contains 'report'
- mimeType='application/pdf'
- modifiedTime > '2024-01-01T00:00:00'
- fullText contains 'budget'
- Multiple conditions with 'and' or 'or'
"""
    )
]

llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0.3,
)

system_prompt = """You are a helpful assistant that searches Google Drive files.
When users ask to find files, you:
1. Understand what they're looking for
2. Use the GoogleDriveSearch tool to find files
3. Show the results clearly with links

Generate Google Drive API queries like:
- name contains 'keyword' for partial matches
- mimeType='type' for file types
- modifiedTime > 'date' for recent files
- fullText contains 'text' to search content
- Combine with 'and' or 'or'

Be helpful and conversational!"""

prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
])

agent = create_tool_calling_agent(llm, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True, max_iterations=5)


@app.get("/")
async def root():
    return {"status": "TailorTalk API", "version": "1.0"}


@app.get("/health")
async def health():
    drive_ok = "Connected" if drive else "Error"
    return {
        "status": "ok",
        "drive": drive_ok,
        "time": datetime.now().isoformat()
    }


@app.post("/search")
async def search(request: SearchRequest):
    global found_files
    found_files = []

    try:
        chat_history = []
        if request.conversation_history:
            for msg in request.conversation_history:
                if not msg:
                    continue
                role = msg.get("role", "")
                content = msg.get("content", "")
                if role == "user":
                    chat_history.append(HumanMessage(content=content))
                else:
                    chat_history.append(AIMessage(content=content))

        result = agent_executor.invoke({
            "input": request.query,
            "chat_history": chat_history,
        })

        return {
            "response": result.get("output", "No response"),
            "files": found_files,
            "query_used": request.query
        }

    except Exception as e:
        print("SEARCH ERROR:", str(e))
        return {
            "response": f"Error: {str(e)}",
            "files": [],
            "query_used": request.query
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
