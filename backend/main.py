from fastapi import FastAPI
from routes import auth, income, balance
from db.database import engine, Base

# Crear tablas en SQLite en el arranque (MVP Local)
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Incomia API",
    description="Backend MVP para Incomia - Estabilización de Ingresos (Income Smoothing)",
    version="1.0.0"
)

# Incluir los routers
app.include_router(auth.router)
app.include_router(income.router)
app.include_router(balance.router)

@app.get("/", tags=["Health"])
def health_check():
    return {"status": "ok", "message": "Incomia API is running locally!"}

if __name__ == "__main__":
    import uvicorn
    # Para poder ejecutarlo directamente con `python main.py`
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
