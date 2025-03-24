from fastapi import FastAPI, Depends
from routes import auth, admin, lawyer, staff, client, case
app = FastAPI(title="Legal Management System")

@app.get("/")
def read():
    return {"message": "Welcome to the Legal Management System"}

app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(lawyer.router)
app.include_router(staff.router)
app.include_router(client.router)
app.include_router(case.router)