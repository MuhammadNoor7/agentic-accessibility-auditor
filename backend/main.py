from fastapi import FastAPI
import uvicorn

app = FastAPI(title="Agentic Accessibility Auditor API")

@app.get("/")
def read_root():
    return {"status": "success", "message": "Backend container is running and connected!"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    # This ensures the app runs when the container executes this file
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)