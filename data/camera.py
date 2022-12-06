from multiprocessing.managers import SyncManager
from threading import Thread
from multiprocessing import Process, Manager, Queue, Value, Pipe
import subprocess
import queue
import multiprocessing

import ctypes
import cv2
from flask_socketio import SocketIO
import eventlet
import time
import numpy as np
from datetime import datetime
from PIL import ImageFont, ImageDraw, Image

from models import db_session
from models.users import User
from models.photos import Photo
from models.videos import Video

from .detectors import MotionDetector

PHOTO_EVENT = 1
VIDEO_EVENT = 2
ADD_FACE_EVENT = 3
TRAIN_EVENT = 4
RECOGNITION_EVENT = 5

FONTPATH = "FreeSans.ttf"
FONT = ImageFont.load_default()


class VideoCamera(Process):
    def __init__(self, device_id):
        self.sender = SocketIO(message_queue='redis://127.0.0.1:6379')
        self.db = db_session.create_session()

        self.cam = cv2.VideoCapture(device_id)

        self.detector = MotionDetector()
        self.last_motion = None

        self.fourcc = cv2.VideoWriter_fourcc(*"MJPG")
        # self.fourcc = 0x00000000
        self.out = None
        self.video_enabled = False

        self.img = None

        # self.p = subprocess.Popen(command, stdin=subprocess.PIPE)


        # self.video_recognition = VideoRecognition(
        #     self, self.sender, recognition=recognition)
        # self.video_recognition.start()

        self.events = Queue()

        self.faces_to_train = []

        super().__init__(daemon=True)

    def run(self):
        print("Camera started")
        prev_time = time.time()
        c = 0
        while True:
            if not self.events.empty():
                event, params = self.events.get()
            else:
                event, params = None, None

            if event == PHOTO_EVENT:
                self.screenshot(*params, in_loop=True)
            elif event == VIDEO_EVENT:
                self.video(*params, in_loop=True)
            elif event == ADD_FACE_EVENT:
                self.add_face(*params, in_loop=True)
            elif event == TRAIN_EVENT:
                self.train(*params, in_loop=True)

            img = self.get_frame()
            movement = self.detector.add_frame(img)

            if movement:
                self.last_motion = time.time()

            # if self.last_motion is not None:
            #     self.video(enable=time.time() - self.last_motion < 10, in_loop=True)

            ret, jpeg = cv2.imencode('.jpg', img)
            cur_time = time.time()
            fps = (cur_time - prev_time) ** -1
            prev_time = cur_time

            bts = jpeg.tobytes()
            self.sender.emit("frame", {"img": bts, "fps": fps})
            # self.p.stdin.write(bts)
            eventlet.sleep()
            # time.sleep(.01)

    def get_frame(self):
        success, img = self.cam.read()

        self.img = img
        if success:
            if self.video_enabled:
                # print("svd")
                self.out.write(img)

        return img

    def screenshot(self, in_loop=False):
        if not in_loop:
            self.events.put((PHOTO_EVENT, tuple()))
            return

        db = db_session.create_session()

        photo = Photo()
        photo.generate()
        db.add(photo)
        db.commit()

        cv2.imwrite("media/screenshots/{}".format(photo.file), self.img)
        self.sender.emit("state", {"type": "saved"})

    def video(self, enable=None, in_loop=False):
        if not in_loop:
            self.events.put((VIDEO_EVENT, tuple()))
            return

        if enable is None:
            if self.video_enabled:
                # self.out.close()
                self.out.release()
                self.video_enabled = False
            else:
                db = db_session.create_session()

                video = Video()
                video.generate()
                db.add(video)
                db.commit()

                self.out = cv2.VideoWriter("media/videos/{}".format(video.file), self.fourcc, 10, (640, 480))
                # self.out = FFmpegWriter("media/videos/{}".format(video.file), outputdict={'-vcodec': 'libx264'})
                cv2.imwrite("media/videos/{}".format(video.preview), self.img)
                self.video_enabled = True
        else:
            if enable and not self.video_enabled:
                db = db_session.create_session()

                video = Video()
                video.generate()
                db.add(video)
                db.commit()

                self.out = cv2.VideoWriter("media/videos/{}".format(video.file), self.fourcc, 10, (640, 480))
                # self.out = FFmpegWriter("media/videos/{}".format(video.file), outputdict={'-vcodec': 'libx264'})
                cv2.imwrite("media/videos/{}".format(video.preview), self.img)
                self.video_enabled = True
            elif not enable and self.video_enabled:
                # self.out.close()
                self.out.release()
                self.video_enabled = False

        self.sender.emit("state", {"type": "video", "state": self.video_enabled})

    def start_video(self, filename, preview):
        self.video_enabled = True
        self.params = {"filename": filename, "preview": preview}
        self.event = VIDEO_START_EVENT

    def stop_video(self):
        self.video_enabled = False
        self.event = VIDEO_STOP_EVENT

    def add_face(self, face_id, in_loop=False):
        if not in_loop:
            self.params = [face_id]
            self.event = ADD_FACE_EVENT
            return

        gray = cv2.cvtColor(self.clear_img, cv2.COLOR_BGR2GRAY)
        faces = self.video_recognition.faceCascade.detectMultiScale(
            gray,
            scaleFactor=1.2,
            minNeighbors=2,
            minSize=(int(self.video_recognition.minW),
                     int(self.video_recognition.minH)),
        )

        if not len(faces):
            self.sender.emit("faces_notfound")

        for (x, y, w, h) in faces:
            face_img = gray[y:y + h, x:x + w]

            self.faces_to_train.append(face_img)
            ret, jpeg = cv2.imencode('.jpg', face_img)
            self.sender.emit("added_face", jpeg.tobytes())

    def train(self, face_id, in_loop=False):
        if not in_loop:
            self.params = [face_id]
            self.event = TRAIN_EVENT
            return

        ids = [int(face_id) for _ in range(len(self.faces_to_train))]

        self.sender.emit("train_started")
        self.video_recognition.recognizer.update(
            self.faces_to_train, np.array(ids))
        self.sender.emit("train_finished")

        self.video_recognition.recognizer.write("trainer/trainer.yml")


class VideoRecognition(Thread):
    def __init__(self, camera, sender, recognition=True):
        super().__init__(daemon=True)

        self.sender = sender

        self.camera = camera

        self.recognition_enabled = recognition

        self.recognizer = cv2.face.LBPHFaceRecognizer_create()
        try:
            self.recognizer.read('trainer/trainer.yml')
        except cv2.error:
            self.recognizer.write('trainer/trainer.yml')
        cascadePath = "haarcascade_frontalface_default.xml"
        self.faceCascade = cv2.CascadeClassifier(cascadePath)

        self.min_size = (48, 48)

        self.events = Queue()

    def run(self):
        db = db_session.create_session()
        while True:
            if not self.events.empty():
                event, params = self.events.get()
            else:
                event, params = None, None

            if event == RECOGNITION_EVENT:
                self.toggle(*params, in_loop=True)

            # try:
            #     while True:
            #         img = self.img.get_nowait()
            # except queue.Empty:
            #     pass

            if self.recognition_enabled:
                img = self.camera.img
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

                faces = self.faceCascade.detectMultiScale(
                    gray,
                    scaleFactor=1.2,
                    minNeighbors=3,
                    minSize=self.min_size,
                )

                for (x, y, w, h) in faces:
                    face_id, confidence = self.recognizer.predict(
                        gray[y:y + h, x:x + w])

                    # Check if confidence is less them 100 ==> "0" is perfect match
                    if confidence < 100:
                        user = db.query(User).get(face_id)
                        face_name = user.name
                        confidence = "{0}%".format(round(confidence))
                    else:
                        face_name = "unknown"
                        confidence = "  "

                    self.sender.emit("detected_face", {
                                     "name": face_name, "confidence": confidence})
            else:
                time.sleep(1)
            # eventlet.sleep()

    def toggle(self, in_loop=False):
        print(in_loop)
        if not in_loop:
            self.events.put((RECOGNITION_EVENT, tuple()))
            return

        self.recognition_enabled = not self.recognition_enabled
        self.sender.emit(
            "state", {"type": "recognition", "state": self.recognition_enabled})
