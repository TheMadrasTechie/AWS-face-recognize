import boto3
import os
from typing import List

def upload_files_to_s3(folder_path: str, bucket_name: str) -> List[str]:
    """
    Upload image files in the specified folder to an S3 bucket.

    Parameters:
    folder_path (str): The path of the folder containing the images.
    bucket_name (str): The name of the S3 bucket.

    Returns:
    List[str]: A list of the file names that were successfully uploaded.
    """
    # Initialize the S3 resource
    s3 = boto3.resource('s3')

    # The list that will hold the names of the successfully processed files
    processed_files = []

    # Iterate through each file in the folder
    for file_name in os.listdir(folder_path):
        # Ensure only image files are uploaded
        if file_name.endswith(('.png', '.jpg', '.jpeg', '.gif')):
            try:
                # Construct the full file path
                file_path = os.path.join(folder_path, file_name)

                # Open and read the file in binary mode
                with open(file_path, 'rb') as file:
                    # Create an object for the file on S3
                    object = s3.Object(bucket_name, 'index/' + file_name.replace(".jpeg", "")
                                                .replace(".jpg", "")
                                                .replace(".png", "")
                                                .replace(".gif", ""))

                    # Upload the file
                    object.put(
                        Body=file,
                        Metadata={
                            'FullName': file_name.replace(".jpeg", "")
                                                .replace(".jpg", "")
                                                .replace(".png", "")
                                                .replace(".gif", "")
                        }
                    )

                # If the upload was successful, add the file name to the processed files list
                processed_files.append(file_name)

            except Exception as e:
                print(f"Something went wrong while uploading {file_name}: {e}")

    # Return the list of successfully processed files
    return processed_files
