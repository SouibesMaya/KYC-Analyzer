from fastapi import APIRouter, File, UploadFile

from app.services.document_service import (
    analyze_document_mock,
    save_uploaded_document,
)

router = APIRouter(
    prefix="/api/documents",
    tags=["Documents"]
)


@router.get("/test")
def test_documents_router():
    return {
        "message": "Documents router is working"
    }


@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    document = await save_uploaded_document(file)

    return {
        "message": "Document uploadé avec succès",
        "document": document
    }


@router.post("/upload-and-analyze")
async def upload_and_analyze_document(file: UploadFile = File(...)):
    document = await save_uploaded_document(file)
    analysis = analyze_document_mock(document["path"])

    return {
        "message": "Document uploadé et analysé avec succès",
        "document": document,
        "analysis": analysis
    }