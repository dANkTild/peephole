import numpy as np
import cv2


class MotionDetector:
    def __init__(self, buffer=25):
        self.buffer = buffer
        self.imgs = None

    def add_frame(self, img):
        if self.imgs is not None:
            diff = cv2.absdiff(self.imgs, img)
            rsd = cv2.resize(diff, (100, 100))

            self.imgs = img
            return len(rsd[rsd > 100]) > 1

        self.imgs = img
