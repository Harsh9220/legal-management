from fastapi import FastAPI, Depends
app = FastAPI(title="Legal Management System")

@app.get("/")
def read():
    return {"message": "Welcome to the Legal Management System"}
