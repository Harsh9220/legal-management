from fastapi import FastAPI, Depends
from routes import auth, staff
app = FastAPI(title="Legal Management System")

@app.get("/")
def read():
    return {"message": "Welcome to the Legal Management System"}

app.include_router(auth.router)
app.include_router(staff.router)