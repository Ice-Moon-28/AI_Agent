from fastapi import APIRouter, File, UploadFile, HTTPException
from blog_backend_gpt.web.api.upload.utils.s3 import upload_file_to_s3  # Assuming you have a utility function for S3 uploads
from PIL import Image
import io

router = APIRouter()

# TODO: Define extensions in a settings file or environment variable
ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}
# TODO: Define the max file size in a settings file or environment variable
MAX_FILE_SIZE_MB = 10  # 10 MB

@router.post("/upload-image")
async def upload_image(image: UploadFile = File(...)):
    """
    Endpoint to upload an image file.
    """
    
    # 1. validate file type
    ext = image.filename.split(".")[-1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Unsupported image format.")

    # 2. validate file size
    image.file.seek(0, io.SEEK_END)
    size_in_mb = image.file.tell() / (1024 * 1024)
    if size_in_mb > MAX_FILE_SIZE_MB:
        raise HTTPException(status_code=400, detail="Image too large (max 10MB).")
    image.file.seek(0)

    # 3. validate image content
    try:
        img_data = await image.read()
        Image.open(io.BytesIO(img_data)).verify()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid image file.")
    
    image.file = io.BytesIO(img_data)

    # 4. Save the image on AWS S3 Bucket
    url = upload_file_to_s3(image)

    return {"url": url, "filename": image.filename, "size": size_in_mb}