from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from pymongo import MongoClient
from bson import ObjectId
from typing import List

# Initialize the FastAPI app
app = FastAPI()

# MongoDB connection setup
client = MongoClient("mongodb://localhost:27017")
db = client.contentdb
collection = db.contents

# Pydantic models for request and response validation
class Content(BaseModel):
    title: str
    body: str
    author: str
    tags: List[str] = []

class ContentInDB(Content):
    id: str

# Utility function to convert MongoDB documents to Pydantic models
def content_helper(content) -> ContentInDB:
    return ContentInDB(
        id=str(content["_id"]),
        title=content["title"],
        body=content["body"],
        author=content["author"],
        tags=content.get("tags", [])
    )

# Create a new content item
@app.post("/contents/", response_model=ContentInDB)
async def create_content(content: Content):
    result = collection.insert_one(content.dict())
    new_content = collection.find_one({"_id": result.inserted_id})
    return content_helper(new_content)

# Retrieve all content items
@app.get("/contents/", response_model=List[ContentInDB])
async def get_all_contents():
    contents = []
    for content in collection.find():
        contents.append(content_helper(content))
    return contents

# Retrieve a single content item by ID
@app.get("/contents/{content_id}", response_model=ContentInDB)
async def get_content(content_id: str):
    content = collection.find_one({"_id": ObjectId(content_id)})
    if content is None:
        raise HTTPException(status_code=404, detail="Content not found")
    return content_helper(content)

# Update a content item by ID
@app.put("/contents/{content_id}", response_model=ContentInDB)
async def update_content(content_id: str, content: Content):
    result = collection.update_one({"_id": ObjectId(content_id)}, {"$set": content.dict()})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Content not found")
    updated_content = collection.find_one({"_id": ObjectId(content_id)})
    return content_helper(updated_content)

# Delete a content item by ID
@app.delete("/contents/{content_id}", response_model=dict)
async def delete_content(content_id: str):
    result = collection.delete_one({"_id": ObjectId(content_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Content not found")
    return {"message": "Content deleted successfully"}
