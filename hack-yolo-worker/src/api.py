import logging
import queue
import threading
from fastapi import FastAPI

from config import CONFIG
from dto import RecognizeRequest
from worker import WORKER

logger = logging.getLogger(__name__)

app = FastAPI()

task_queue = queue.Queue()
semaphore = threading.Semaphore(CONFIG.YOLO_MAX_WORKERS)



def queue_worker():
    while True:
        payload = task_queue.get()
        semaphore.acquire()
        def process_task(data):
            try:
                logger.info(f"Starting to process task: {data}")
                WORKER.worker_start(data)
            except Exception as e:
                logger.error(f"Error in queue worker: {e}")
            finally:
                semaphore.release()  # Освобождаем слот
                task_queue.task_done()

        threading.Thread(target=process_task, args=(payload,), daemon=True).start()


worker_thread = threading.Thread(target=queue_worker, daemon=True)
worker_thread.start()


@app.post("/recognize", status_code=200)
async def recognize_image(request: RecognizeRequest):
    payload = {
        "image_url": request.image_url,
        "image_id": request.image_id,
        "project_id": request.project_id,
    }

    task_queue.put(payload)
    
    logger.info(f"Recognition request accepted and added to queue: {payload}")
    return {}
