import boto3
import io
from PIL import Image



def upload_to_s3(image_content: bytes, image_name: str, aws_code: str) -> None:
    s3 = boto3.resource('s3')
    
    # Define the object's path in the S3 bucket
    object_path = 'index/' + image_name

    # Prepare the object to be uploaded to S3
    object = s3.Object('facerecognition-images-crz', object_path)
    ret = object.put(Body=image_content, Metadata={'FullName': aws_code})

def recognize_person_from_image(image: Image) -> dict:
    rekognition = boto3.client('rekognition', region_name='us-east-1')
    dynamodb = boto3.client('dynamodb', region_name='us-east-1')
    
    stream = io.BytesIO()
    image.save(stream, format="JPEG")
    image_binary = stream.getvalue()

    response = rekognition.search_faces_by_image(
        CollectionId='facerecognition_collection',
        Image={'Bytes': image_binary}                                       
    )

    results = []

    for match in response['FaceMatches']:
        data = {
            "FaceId": match['Face']['FaceId'],
            "Confidence": match['Face']['Confidence']
        }

        face = dynamodb.get_item(
            TableName='facerecognition',
            Key={'RekognitionId': {'S': match['Face']['FaceId']}}
        )

        if 'Item' in face:
            data["FullName"] = face['Item']['FullName']['S']
            results.append(data)

    if not results:
        return {"message": "Person cannot be recognized"}

    return {"matches": results}

# Usage example:
# image_obj = Image.open("path/to/image.jpg")
# json_data = recognize_person_from_image(image_obj)
# print(json_data)
