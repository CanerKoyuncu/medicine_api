from typing import Optional

import uvicorn
from bson import ObjectId
from fastapi import FastAPI, status,HTTPException
from pydantic import BaseModel
from pymongo import MongoClient
from dotenv import load_dotenv
import os
import json
import uuid

from starlette.middleware.cors import CORSMiddleware
from starlette.websockets import WebSocket
from time import time

load_dotenv()

app = FastAPI()

MONGO_URI = "mongodb://mongo"
client = MongoClient(MONGO_URI)
db = client["Hospital"]

class Patient(BaseModel):
    name: str
    surname: str
    age: int
    address: str
    description: Optional[str] = None
    deviceId: str

class User(BaseModel):
    username: str
    password: str

class HealthData(BaseModel):
    _id: Optional[uuid.UUID]
    spo2: float
    bpm: float
    device_id: str
    is_falled: bool
    timestamp: Optional[float]

def patient_helper(patient) -> dict:
    return {
        "id": str(patient["_id"]),
        "name": patient["name"],
        "surname": patient["surname"],
        "age": patient["age"],
        "address": patient["address"],
        "description": patient.get("description", ""),
        "deviceId": patient["deviceId"]
}



app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Gerekirse spesifik domainleri yazın
    allow_credentials=True,
    allow_methods=["*"],  # OPTIONS dahil tüm yöntemlere izin verir
    allow_headers=["*"],
)

@app.post("/data")
async def data(data:HealthData):
    data._id = uuid.uuid4()
    data.timestamp= time()
    print(data)
    db.product.insert_one(data.model_dump())


@app.post("/patient", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_patient(patient: Patient):
    patient_data = patient.dict()
    print(patient_data)
    new_patient = db.patients.insert_one(patient_data)
    created_patient = db.patients.find_one({"_id": new_patient.inserted_id})
    return patient_helper(created_patient)

@app.get("/health_data/{product_id}")
async def get_health_data(product_id:str):
    health_data = []
    for data in db.product.find({"device_id":product_id}):
        health_data.append(data)
    return health_data

@app.get("/patients", response_model=list[dict])
async def read_patients():
    patients = []
    for patient in db.patients.find():
        patients.append(patient_helper(patient))
    return patients

@app.get("/patients/{patient_id}", response_model=dict)
async def read_patient(patient_id: str):
    if (patient := db.patients.find_one({"_id": ObjectId(patient_id)})) is not None:
        return patient_helper(patient)
    raise HTTPException(status_code=404, detail="Hasta bulunamadı")

@app.put("/patients/{patient_id}", response_model=dict)
async def update_patient(patient_id: str, patient: Patient):
    patient_data = patient.dict()
    result = db.patients.update_one(
        {"_id": ObjectId(patient_id)},
        {"$set": patient_data})
    if result.modified_count == 1:
        if (updated_patient := db.patients.find_one({"_id": ObjectId(patient_id)})) is not None:
            return patient_helper(updated_patient)
    raise HTTPException(status_code=404, detail="Hasta bulunamadı")

@app.delete("/patients/{patient_id}")
async def delete_patient(patient_id: str):
    result = db.paitents.delete_one({"_id": ObjectId(patient_id)})
    if result.deleted_count == 1:
        return {"message": "Hasta başarıyla silindi"}
    raise HTTPException(status_code=404, detail="Hasta bulunamadı")


if __name__ == '__main__':
    uvicorn.run("main:app", reload=True,  server_header=False, host="0.0.0.0", port=8001)