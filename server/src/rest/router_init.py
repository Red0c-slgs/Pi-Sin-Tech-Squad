from fastapi import FastAPI
from rest.system_endpoint import router as SystemEndpoint
from rest.auth_endpoint import router as AuthEndpoint
from rest.project_endpoint import router as ProjectRouter
from rest.file_endpoint import router as FileRouter
from rest.yolo_endpoint import router as YOLORouter

app = FastAPI(
    title="HACK",
    description="HACK",
    version="0.0.1",
)

app.include_router(SystemEndpoint)
app.include_router(AuthEndpoint)
app.include_router(ProjectRouter)
app.include_router(FileRouter)
app.include_router(YOLORouter)