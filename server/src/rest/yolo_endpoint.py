from fastapi import APIRouter, Depends

from rest.models.panda_data import LabelData
from service.file_service import set_service_url
from service.panda_service import YoloResultService
from utils.logger import get_logger

log = get_logger("FileEndpoint")

router = APIRouter(prefix="/yolo", tags=["YOLO"])


@router.post("", response_model=LabelData)
async def upload_yolo_label(project_id: int, file_id: int, label: str, service: YoloResultService = Depends()) -> LabelData:
    """Загрузить разметку YOLO и сохранить в s3"""
    log.info(f"Received request to save YOLO label as .txt for file {file_id} from project {project_id}")
    result = await service.analysis_yolo_txt(file_id=file_id, txt=label)
    log.info(f"Saved YOLO label as .txt for file {file_id} from project {project_id}")
    return result

@router.post("/server", response_model=LabelData)
async def set_server(url: str, service: YoloResultService = Depends()):
    set_service_url(url)
