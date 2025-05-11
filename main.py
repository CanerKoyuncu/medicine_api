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

from starlette.websockets import WebSocket

load_dotenv()

app = FastAPI()

# MongoDB bağlantısı
MONGO_URI = os.getenv("127.0.0.1:27018")
client = MongoClient(MONGO_URI)
db = client["Hospital"]  # Veritabanı adınızı yazın

class Address(BaseModel):
    street: str
    city: str
    postal_code: str
    country: str

class Patient(BaseModel):
    name: str
    surname: str
    age: int
    address: Address
    description: Optional[str] = None

class User(BaseModel):
    username: str
    password: str

def patient_helper(patient) -> dict:
    return {
        "id": str(patient["_id"]),
        "name": patient["name"],
        "surname": patient["surname"],
        "age": patient["age"],
        "address": patient["address"],
        "description": patient.get("description", "")
    }

@app.websocket("/socket")
async def root(websocket: WebSocket):
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        data_dict = json.loads(data)
        data_dict['_id'] = uuid.uuid4().__str__()
        db.product.insert_one(data_dict)

@app.post("/patient/", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_patient(patient: Patient):
    patient_data = patient.dict()
    new_patient = db.patients.insert_one(patient_data)
    created_patient = db.patients.find_one({"_id": new_patient.inserted_id})
    return patient_helper(created_patient)

@app.get("/patients/", response_model=list[dict])
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


@app.post("/auth/login")
async def login_user(user: User):
    username = user.username
    password = user.password
    if username and password:
        user_result = db.users.find_one({"username": username, "password": password})
        if user_result is None:
            raise HTTPException(status_code=401, detail="Invalid username or password")

        else:
            raise HTTPException(status_code=200, detail="Login successful")


if __name__ == '__main__':
    uvicorn.run("main:app", reload=True,  server_header=False, host="0.0.0.0", port=8001)