from fastapi import FastAPI

from scai.api.inventory import router as inventory_router
from scai.api.shipment import router as shipment_router
from scai.api.supplier import router as supplier_router

app = FastAPI(
    title="Supply Chain AI API",
    version="1.0.0",
    description="Asynchronous Supply Chain AI platform powered by FastAPI and SQLAlchemy.",
)

app.include_router(inventory_router)
app.include_router(shipment_router)
app.include_router(supplier_router)


@app.get("/")
async def root() -> dict[str, str]:
    return {"status": "online", "message": "Supply Chain AI API is running."}
