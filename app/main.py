from fastapi import FastAPI, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from app.oauth import get_google_auth_url, get_google_token
from app.analytics import get_user_analytics_data
from app.search_console import get_user_search_console_data
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

app = FastAPI()

# Serve static files (CSS, JS, images, etc.)
app.mount("/static", StaticFiles(directory="static"), name="static")


# Directory for HTML templates
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=RedirectResponse)
async def root():
    return RedirectResponse(url="/auth")

# Route to start OAuth authentication
@app.get("/auth")
async def google_login():
    auth_url = get_google_auth_url()
    return RedirectResponse(auth_url)

# OAuth callback route
@app.get("/callback", response_class=HTMLResponse)
async def oauth_callback(request: Request, code: str):
    try:
        # Exchange code for token
        token = get_google_token(code)

        # Fetch analytics data using the token
        analytics_data = get_user_analytics_data(token)
        search_console_data = get_user_search_console_data(token)

        # Render data in the HTML response
        return templates.TemplateResponse("dashboard.html", {
            "request": request,
            "analytics_data": analytics_data,
            "search_console_data": search_console_data
        })
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=400)
