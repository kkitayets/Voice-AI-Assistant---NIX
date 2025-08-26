# vision_processor.py
import cv2
import time
import logging
from threading import Thread, Lock
from utils import capture_frame, detect_objects, format_detection_results, draw_detections
class VisionProcessor:
    def __init__(self, camera_index=0, model_path="yolov8n.pt", update_interval=0.5):
        self.camera_index = camera_index
        self.model_path = model_path
        self.update_interval = update_interval
        self.latest_frame = None
        self.latest_detections = []
        self.latest_description = ""
        self.running = False
        self.lock = Lock()
        self.thread = None
        self.cap = None

    def start(self):
        if self.running:
            return

        # Инициализируем камеру только один раз
        try:
            self.cap = cv2.VideoCapture(self.camera_index)
            if not self.cap.isOpened():
                logging.error(f"Cannot open camera at index {self.camera_index}")
                return
        except Exception as e:
            logging.error(f"Camera init error: {e}")
            return

        self.running = True
        self.thread = Thread(target=self._process_loop, daemon=True)
        self.thread.start()
        logging.info("Vision processor started")

    def stop(self):
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1.0)

        # Важно: освобождаем ресурсы камеры
        if self.cap and self.cap.isOpened():
            self.cap.release()
        logging.info("Vision processor stopped")

    def _process_loop(self):
        while self.running:
            try:
                # Используем уже открытую камеру
                if self.cap and self.cap.isOpened():
                    ret, frame = self.cap.read()
                    if not ret:
                        logging.warning("Failed to capture frame")
                        time.sleep(0.5)
                        continue

                    # Обнаружение объектов
                    detections = detect_objects(frame, self.model_path)

                    # Форматируем описание
                    description = format_detection_results(detections)

                    # Отрисовываем объекты на кадре
                    annotated_frame = draw_detections(frame.copy(), detections)

                    # Обновляем данные
                    with self.lock:
                        self.latest_frame = annotated_frame
                        self.latest_detections = detections
                        self.latest_description = description
                else:
                    time.sleep(1)
            except Exception as e:
                logging.error(f"Vision processing error: {e}")
                time.sleep(1)

        if self.cap and self.cap.isOpened():
            self.cap.release()

    def get_current_frame(self):
        with self.lock:
            return self.latest_frame

    def get_detection_description(self):
        with self.lock:
            return self.latest_description

    def get_detections(self):
        with self.lock:
            return self.latest_detections