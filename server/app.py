from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from dotenv import load_dotenv
import os
from routes.traffic import router as traffic_router
from routes.routing import router as routing_router
from routes.parking import router as parking_router

load_dotenv()

app = FastAPI(
    title="Urban Navigator AI",
    description="AI-Driven Predictive Urban Navigation and Mobility Optimization System",
    version="1.0.0"
)


origins = os.getenv('CORS_ORIGINS', '*').split(',')
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(traffic_router, prefix="/api/traffic", tags=["Traffic"])
app.include_router(routing_router, prefix="/api/route", tags=["Routing"])
app.include_router(parking_router, prefix="/api/parking", tags=["Parking"])

app.mount("/", StaticFiles(directory=r"c:\Users\samma\Desktop\vasai\BugSmashers_ai_horizon26\client", html=True), name="static")

@app.get("/")
async def home():
    print("Home called")
    return FileResponse(r"c:\Users\samma\Desktop\vasai\BugSmashers_ai_horizon26\client\dashboard.html", media_type="text/html")

@app.get("/api/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    host = os.getenv('API_HOST', 'localhost')
    port = int(os.getenv('API_PORT', 8000))
    uvicorn.run("app:app", host=host, port=port, reload=True)
