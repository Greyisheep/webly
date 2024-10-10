from fastapi import FastAPI, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from app.oauth import get_google_auth_url, get_google_token
from app.analytics import get_user_analytics_data
# from app.search_console import get_user_search_console_data
from fastapi.templating import Jinja2Templates

from fastapi.staticfiles import StaticFiles

app = FastAPI()

# Serve static files (CSS, JS, images, etc.)
app.mount("/static", StaticFiles(directory="static"), name="static")


# Directory for HTML templates
templates = Jinja2Templates(directory="templates")

# Index route to display the dashboard
@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})

# Route to start OAuth authentication
@app.get("/auth")
async def google_login():
    auth_url = get_google_auth_url()
    return RedirectResponse(auth_url)

# Route to handle Google OAuth callback
@app.get("/callback")
async def oauth_callback(code: str):
    token = get_google_token(code)
    analytics_data = get_user_analytics_data(token)
    # search_console_data = get_user_search_console_data(token)
    
    # Return JSON data
    return JSONResponse({
        "analytics_data": analytics_data,
        # "search_console_data": search_console_data
    })

# Serve HTML template after successful login
@app.get("/dashboard", response_class=HTMLResponse)
async def show_dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})
