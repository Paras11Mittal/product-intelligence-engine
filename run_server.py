import os
import uvicorn

if __name__ == "__main__":
    # Render assigns a dynamic port, so we must read it from the environment.
    # We fall back to 8000 for local development.
    port = int(os.environ.get("PORT", 8000))
    
    uvicorn.run(
        "app.main:app", 
        host="0.0.0.0", 
        port=port, 
        reload=False  # Turn off reload in production!
    )