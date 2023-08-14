import cv2
import time
from aiortc import VideoStreamTrack
from aiortc.contrib.media import MediaRecorder, MediaRelay, MediaBlackhole
from av import VideoFrame
import asyncio

import numpy

from models import db_session
from models.users import User
from models.photos import Photo
from models.videos import Video

from data import detectors

font = cv2.FONT_HERSHEY_DUPLEX


class VideoCamera:
    def __init__(self, device_id) -> None:
        super().__init__()
        self.main_stream = VideoStream(self)
        self.media_relay = MediaRelay()

        self.cap = cv2.VideoCapture(device_id)
        self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        self.cur_frame = None

        self.is_started = True

        self.prev_time = time.time()
        self.counted_frames = 0
        self.fps = 0

        self.recorder = None

        self.detector = detectors.FaceDetector()

    def get_stream(self):
        return self.media_relay.subscribe(self.main_stream)

    def updater(self):
        while self.is_started:
            ret, img = self.cap.read()

            # img = self.detector.tick(img)

            self.counted_frames += 1

            if self.counted_frames > 10:
                cur_time = time.time()
                self.fps = int(self.counted_frames / (cur_time - self.prev_time))
                self.prev_time = cur_time
                self.counted_frames = 0

            meta = "{} / {}".format(time.strftime("%d.%m.%Y %H:%M:%S", time.localtime()),
                                    self.fps)

            if ret:
                img = cv2.putText(img, meta, (5, self.height - 10), font, 1, (255, 255, 255), 4, cv2.LINE_AA)
                img = cv2.putText(img, meta, (5, self.height - 10), font, 1, (0, 0, 0), 2, cv2.LINE_AA)

                self.cur_frame = img

    async def screenshot(self):
        async with db_session.create_session() as db:
            photo = Photo()
            photo.generate()

            await asyncio.to_thread(cv2.imwrite, "media/screenshots/{}".format(photo.file), self.cur_frame)

            db.add(photo)
            await db.commit()

    async def record(self):
        if self.recorder is None:
            async with db_session.create_session() as db:
                video = Video()
                video.generate()
                db.add(video)

                self.recorder = MediaRecorder("media/videos/{}".format(video.file))
                self.recorder.addTrack(VideoStream(self))
                await self.recorder.start()
                await asyncio.to_thread(cv2.imwrite, "media/videos/{}".format(video.preview), self.cur_frame)

                await db.commit()
        else:
            await self.recorder.stop()
            self.recorder = None

        return self.recorder is not None


class VideoStream(VideoStreamTrack):
    def __init__(self, camera):
        super().__init__()

        self.camera = camera

    async def recv(self):
        pts, time_base = await self.next_timestamp()

        frame = await asyncio.to_thread(VideoFrame.from_ndarray, self.camera.cur_frame, format="bgr24")

        frame.pts = pts
        frame.time_base = time_base
        return frame
