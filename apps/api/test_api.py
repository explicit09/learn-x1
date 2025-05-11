import uvicorn

if __name__ == "__main__":
    print("Starting LEARN-X API server for testing...")
    uvicorn.run("app.main:app", host="127.0.0.1", port=8080, reload=True)
