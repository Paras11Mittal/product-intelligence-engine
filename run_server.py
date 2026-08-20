import uvicorn

if __name__ == "__main__":
    print("Starting AI Product Intelligence Engine server on http://127.0.0.1:8000")
    print("Interactive Swagger UI Docs: http://127.0.0.1:8000/docs")
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
