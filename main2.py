#This is for deploying on Lambda
from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from PIL import Image
from io import BytesIO
from aws_face_recognize import recognize_person_from_image,upload_to_s3
import boto3
from fastapi.responses import HTMLResponse
from typing import Optional
from pathlib import Path
import imghdr
import os
import shutil
import aws_face_store
from mangum import Mangum

app = FastAPI()
handler = Mangum(app)

BUCKET_NAME = "facerecognition-images-crz"

FACE_IMAGES_FOLDER = Path(__file__).parent / "face_images"
s3 = boto3.resource('s3')

def upload_to_s3(file_content, file_name, text, bucket_name='facerecognition-images-crz', prefix='index/'):
    if file_name.endswith(('.png', '.jpg', '.jpeg', '.gif')):
        object = s3.Object(bucket_name, prefix + file_name)
        ret = object.put(Body=file_content, Metadata={'FullName': text, 'UserText': text})
        return ret
    else:
        raise HTTPException(status_code=400, detail="File type not supported!")



@app.post("/recognize_V2/")
async def recognizes_all_possible_matches_and_gives_result_as_list(file: UploadFile = File(...)):
    try:
        # Convert the uploaded file into a PIL Image object
        image_content = await file.read()
        image = Image.open(BytesIO(image_content))
        
        # Use the AWS Rekognition function to recognize the face
        result = recognize_person_from_image(image)
        
        # Transform the result to match the desired output
        transformed_result = {
            "face_ID": [match["FullName"] for match in result.get("matches", [])]
        }
        
        return transformed_result
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")

@app.post("/recognize_V3/")
async def recognize_the_best_possible_face_from_image(file: UploadFile = File(...)):
    try:
        # Convert the uploaded file into a PIL Image object
        image_content = await file.read()
        image = Image.open(BytesIO(image_content))
        
        # Use the AWS Rekognition function to recognize the face
        result = recognize_person_from_image(image)
        
        matches = result.get("matches", [])
        if not matches:
            return {"message": "No face recognized"}
        
        # Sort the matches by confidence and get the one with the highest confidence
        highest_confidence_match = sorted(matches, key=lambda x: x["Confidence"], reverse=True)[0]
        
        # Return the FullName of the match with the highest confidence
        return {"face_ID": highest_confidence_match["FullName"]}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

@app.post("/aws_store_with_ID/")
async def upload_image(file: UploadFile = File(...), name: str = Form(...)):
    # Ensure the folder for face images exists
    FACE_IMAGES_FOLDER.mkdir(parents=True, exist_ok=True)

    # Check if the uploaded file is an image
    if file.content_type not in ["image/png", "image/jpeg"]:
        raise HTTPException(status_code=400, detail="Invalid file type")

    # Delete any existing files in the directory
    for existing_file in FACE_IMAGES_FOLDER.glob("*"):
        if existing_file.is_file():
            existing_file.unlink()

    # Save the uploaded image with the provided name
    try:
        contents = await file.read()
        image_path = FACE_IMAGES_FOLDER / f"{name}.jpeg"  # Set the file path
        with open(image_path, "wb") as image_file:
            image_file.write(contents)

        # If you want to save another image (e.g., a copy) with the same name, uncomment the following lines:
        # copy_image_path = FACE_IMAGES_FOLDER / f"{name}_copy.jpeg"
        # shutil.copy(image_path, copy_image_path)
        successful_uploads = aws_face_store.upload_files_to_s3("face_images", "facerecognition-images-crz")

        return {"filename": f"{name}.jpeg", "message": "Image has been uploaded","result":successful_uploads}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File save error: {e}")

@app.post("/aws_store_without_id/")
async def upload_image_with_original_name(file: UploadFile = File(...)):
    # Ensure the folder for face images exists
    FACE_IMAGES_FOLDER.mkdir(parents=True, exist_ok=True)

    # Check if the uploaded file is an image
    if file.content_type not in ["image/png", "image/jpeg"]:
        raise HTTPException(status_code=400, detail="Invalid file type")

    # Delete any existing files in the directory
    for existing_file in FACE_IMAGES_FOLDER.glob("*"):
        if existing_file.is_file():
            existing_file.unlink()

    # Save the uploaded image with its original name
    try:
        contents = await file.read()
        original_name = file.filename  # Extract the original filename

        # Ensure the file has a proper extension
        if not original_name.lower().endswith((".jpg", ".jpeg", ".png")):
            raise HTTPException(status_code=400, detail="Invalid file extension")

        # If you want to save it specifically as a ".jpeg", you can modify the filename
        name_without_ext = original_name.rsplit('.', 1)[0]
        final_name = f"{name_without_ext}.jpeg"

        image_path = FACE_IMAGES_FOLDER / final_name  # Set the file path

        with open(image_path, "wb") as image_file:
            image_file.write(contents)
        successful_uploads = aws_face_store.upload_files_to_s3("face_images", "facerecognition-images-crz")
        return {"filename": final_name, "message": "Image has been uploaded with original name","result":successful_uploads}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File save error: {e}")
