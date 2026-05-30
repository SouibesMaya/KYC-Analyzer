from fastapi import APIRouter

router = APIRouter(
    prefix="/api/documents",
    tags=["Documents"]
)


@router.get("/test")
def test_documents_router():
    return {
        "message": "Documents router is working"
    }