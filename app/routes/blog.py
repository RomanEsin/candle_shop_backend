from fastapi import APIRouter, Depends, HTTPException, Form, UploadFile, File

from app import schemas
from app.config import BACKEND_BASE
from app.db import DB, User
from app.users import current_active_user
import requests
from PIL import Image
from secrets import token_hex
from app.bot import status_updated

router = APIRouter(prefix="/api/blog", tags=["orders"])


@router.get("", response_model=list[schemas.BlogShort])
async def get_blog(db: DB = Depends(DB)):
    return await db.get_blog_posts()


@router.get("/{blog_id}", response_model=schemas.Blog)
async def get_blog_post(blog_id: int, db: DB = Depends(DB)):
    return await db.get_blog_by_id(blog_id)


@router.post("", response_model=schemas.Blog)
async def create_blog_post(
    title: str = Form(...),
    content: str = Form(...),
    image: UploadFile = File(...),
    db: DB = Depends(DB),
):
    # check if image is present and is of correct format
    if image:
        if image.content_type.startswith("image/"):
            try:
                # load image
                image_data = Image.open(image.file)

                # Compress image
                image_data = image_data.resize(
                    (image_data.width // 2, image_data.height // 2)
                )

                # create a unique image filename with the original image extension
                image.filename = f"{token_hex(8)}.{image.filename.split('.')[-1]}"

                # Save image
                image_path = f"app/static/{image.filename}"
                image_path_short = f"static/{image.filename}"
                image_data.save(image_path)
                image_path = f"{BACKEND_BASE}/api/{image_path_short}"

            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Invalid image file. {e}")

        else:
            raise HTTPException(status_code=400, detail="Invalid file type.")
    else:
        raise HTTPException(status_code=400, detail="Invalid file type.")

    # Create product instance
    blog = schemas.BlogCreate(
        title=title,
        content=content,
        image=image_path,
    )

    return await db.create_blog_post(blog)
