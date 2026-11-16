
import os
from pathlib import Path
from dotenv import load_dotenv
from azure.storage.blob import BlobServiceClient

# Load environment variables
base_folder = Path(__file__).resolve().parent

load_dotenv(base_folder / ".env")

# Azure configuration
connection_string = os.getenv(
    "AZURE_STORAGE_CONNECTION_STRING"
)

container_name = os.getenv(
    "AZURE_CONTAINER_NAME"
)

if not connection_string:
    raise ValueError("Azure connection string not found")

if not container_name:
    raise ValueError("Azure container name not found")

# Connect to Azure
blob_service_client = (
    BlobServiceClient.from_connection_string(
        connection_string
    )
)

container_client = (
    blob_service_client.get_container_client(
        container_name
    )
)


# Upload a file to Azure
def upload_file(local_file, blob_name):

    local_file = Path(local_file)

    if not local_file.exists():
        raise FileNotFoundError(local_file)

    blob_client = container_client.get_blob_client(
        blob_name
    )

    with open(local_file, "rb") as file:

        blob_client.upload_blob(
            file,
            overwrite=True
        )

    print(f"Uploaded successfully: {blob_name}")

    return blob_client.url


# Test the Azure connection
if __name__ == "__main__":

    print("Connecting to Azure...")

    sample_image = (
        base_folder
        / "sample_images"
        / "scratch_0h.png"
    )

    upload_file(
        sample_image,
        "test/scratch_0h.png"
    )

    print("Azure upload test completed.")
