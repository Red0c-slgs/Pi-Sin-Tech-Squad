# import os
# import json
# import tempfile
# import logging
# import signal
# import threading
# from concurrent.futures import ThreadPoolExecutor, as_completed
#
# from kafka import KafkaConsumer, KafkaProducer
# import boto3
# from ultralytics import YOLO
#
# logging.basicConfig(
#     format='%(asctime)s %(levelname)s %(message)s',
#     level=logging.INFO
# )
# logger = logging.getLogger(__name__)
#
# # Environment/configuration
# KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
# INPUT_TOPIC = os.getenv('INPUT_TOPIC', 'image_requests')
# OUTPUT_TOPIC = os.getenv('OUTPUT_TOPIC', 'image_responses')
# CONSUMER_GROUP = os.getenv('CONSUMER_GROUP', 'yolo-processor-group')
# AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
# YOLO_S3_MODEL_URL = os.getenv('YOLO_S3_MODEL_URL', 's3://my-bucket/models/yolov8n.pt')
# MAX_WORKERS = int(os.getenv('MAX_WORKERS', '8'))
#
# # AWS clients
# s3 = boto3.client('s3', region_name=AWS_REGION)
#
# # Shutdown flag
# shutdown_event = threading.Event()
#
# def download_from_s3(s3_url: str, dest_path: str):
#     """
#     Download a file from S3 (s3://bucket/key) to dest_path.
#     """
#     _, _, path = s3_url.partition('s3://')
#     bucket, _, key = path.partition('/')
#     s3.download_file(bucket, key, dest_path)
#     logger.info(f"Downloaded s3://{bucket}/{key} to {dest_path}")
#
#
# def download_model():
#     """
#     Download YOLO weights from S3 to a temporary file and return its path.
#     """
#     tmp_model = tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(YOLO_S3_MODEL_URL)[1])
#     tmp_model.close()
#     download_from_s3(YOLO_S3_MODEL_URL, tmp_model.name)
#     return tmp_model.name
#
#
# def download_image(s3_url: str) -> str:
#     """
#     Download an image from S3 to a temp file and return its local path.
#     """
#     tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(s3_url)[1])
#     tmp_file.close()
#     download_from_s3(s3_url, tmp_file.name)
#     return tmp_file.name
#
#
# def process_message(message: str, model: YOLO) -> dict:
#     data = json.loads(message)
#     image_id = data['id']
#     s3_url = data['s3_url']
#     try:
#         img_path = download_image(s3_url)
#         results = model.predict(source=img_path, save=False)
#         detections = []
#         for res in results:
#             for box in res.boxes:
#                 detections.append({
#                     'class': int(box.cls),
#                     'confidence': float(box.conf),
#                     'bbox': [float(x) for x in box.xyxy.tolist()]
#                 })
#         output = {'id': image_id, 's3_url': s3_url, 'detections': detections}
#         logger.info(f"Processed id={image_id}, found {len(detections)} detections")
#         return output
#     except Exception as e:
#         logger.error(f"Error id={image_id}: {e}")
#         return {'id': image_id, 'error': str(e)}
#     finally:
#         # Cleanup downloaded image
#         try:
#             os.remove(img_path)
#             logger.debug(f"Removed temp file {img_path}")
#         except Exception:
#             pass
#
#
# def main():
#     # Download and load YOLO model
#     model_path = download_model()
#     model = YOLO(model_path)
#
#     # Handle shutdown signals
#     def _shutdown(signum, frame):
#         logger.info(f"Received shutdown signal {signum}, no longer consuming new messages.")
#         shutdown_event.set()
#     signal.signal(signal.SIGINT, _shutdown)
#     signal.signal(signal.SIGTERM, _shutdown)
#
#     consumer = KafkaConsumer(
#         INPUT_TOPIC,
#         bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS.split(','),
#         group_id=CONSUMER_GROUP,
#         enable_auto_commit=False,
#         auto_offset_reset='earliest',
#         value_deserializer=lambda m: m.decode('utf-8')
#     )
#     producer = KafkaProducer(
#         bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS.split(','),
#         value_serializer=lambda v: json.dumps(v).encode('utf-8')
#     )
#
#     executor = ThreadPoolExecutor(max_workers=MAX_WORKERS)
#     futures = []
#
#     try:
#         for msg in consumer:
#             if shutdown_event.is_set():
#                 logger.info("Shutdown requested, breaking consume loop.")
#                 break
#             futures.append(executor.submit(process_message, msg.value, model))
#
#         # After breaking, wait remaining tasks
#         for future in as_completed(futures):
#             result = future.result()
#             producer.send(OUTPUT_TOPIC, result)
#             producer.flush()
#             consumer.commit()
#
#     finally:
#         consumer.close()
#         producer.close()
#         executor.shutdown(wait=True)
#         # Remove model file
#         try:
#             os.remove(model_path)
#             logger.debug(f"Removed model file {model_path}")
#         except Exception:
#             pass
#         logger.info("Processor shutdown complete.")
#
