
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import firebase_admin
from firebase_admin import credentials, auth
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Firebase Admin SDK
# In a production environment, use Secret Manager to handle the service account key
# For local development, you can use a serviceAccountKey.json file
if os.getenv("FIREBASE_CONFIG"):
    cred = credentials.ApplicationDefault()
else:
    cred = credentials.Certificate("serviceAccountKey.json")

firebase_admin.initialize_app(cred)

app = FastAPI()

# Middleware to protect routes
async def get_current_user(request: Request):
    try:
        # Get the session cookie
        session_cookie = request.cookies.get("session")
        if not session_cookie:
            raise ValueError("Session cookie not found.")
        decoded_claims = auth.verify_session_cookie(session_cookie, check_revoked=True)
        return decoded_claims
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid authentication credentials: {e}")

# API routes
@app.get("/api/user")
async def get_user_data(user: dict = Depends(get_current_user)):
    return {"message": f"Hello {user['name']}!"}

@app.post("/api/login")
async def create_session_cookie(request: Request):
    id_token = (await request.json()).get("idToken")
    try:
        # Verify the ID token while checking if the token is revoked.
        decoded_claims = auth.verify_id_token(id_token, check_revoked=True)
        # Generate session cookie
        session_cookie = auth.create_session_cookie(id_token, expires_in=3600 * 24 * 5) # 5 days
        response = FileResponse("../frontend/build/index.html")
        response.set_cookie(key="session", value=session_cookie)
        return response
    except auth.InvalidIdTokenError:
        return {"error": "Invalid ID token"}
    except auth.RevokedIdTokenError:
        return {"error": "Revoked ID token"}

@app.post("/api/files/clean")
async def clean_files(user: dict = Depends(get_current_user)):
    return {"message": "File cleaning placeholder"}

@app.get("/api/groups")
async def get_groups(user: dict = Depends(get_current_user)):
    return {"message": "Group management placeholder"}

@app.get("/api/storage")
async def get_storage_data(user: dict = Depends(get_current_user)):
    return {"message": "File storage placeholder"}


# Serve frontend
app.mount("/static", StaticFiles(directory="../frontend/build/static"), name="static")

@app.get("/{full_path:path}")
async def serve_react_app(full_path: str):
    return FileResponse("../frontend/build/index.html")

