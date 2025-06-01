from pydantic import BaseModel


class RecognizeRequest(BaseModel):
    image_url: str
    image_id: int
    project_id: int
