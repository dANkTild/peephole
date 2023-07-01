import cv2
import numpy

font = cv2.FONT_HERSHEY_DUPLEX


class BaseDetector:
    def __init__(self):
        pass

    def tick(self, source: numpy.ndarray) -> numpy.ndarray:
        return source


class FaceDetector(BaseDetector):
    face_classifier = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    recognizer = cv2.face.LBPHFaceRecognizer_create(threshold=4000)

    def __init__(self):
        self.last_frame = None

        self.faces_to_train = []
        self.recognizer.setThreshold(200)

        try:
            self.recognizer.read('media/trainer.yml')
        except cv2.error:
            self.recognizer.write('media/trainer.yml')

    def tick(self, source: numpy.ndarray) -> numpy.ndarray:
        self.last_frame = source
        # if not self.recognizer.empty():
        gray = cv2.cvtColor(source, cv2.COLOR_BGR2GRAY)
        face = self.face_classifier.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(40, 40))

        for (x, y, w, h) in face:
            if not self.recognizer.empty():
                face_id, confidence = self.recognizer.predict(gray[y:y + h, x:x + w])
                # face_name

                # Check if confidence is less them 100 ==> "0" is perfect match
                # if confidence < 100:
                confidence = "{0}%".format(round(100 - confidence, 4))
                face_name = face_id
                # else:
                #     face_name = "unknown"
                #     confidence = "  "

                source = cv2.putText(source, str(face_name), (5, 30), font, 1, (0, 0, 0), 4, cv2.LINE_AA)
                source = cv2.putText(source, str(confidence), (5, 60), font, 1, (0, 0, 0), 2, cv2.LINE_AA)
                source = cv2.putText(source, str(self.recognizer.getThreshold()),
                                     (5, 90), font, 1, (0, 0, 0), 2, cv2.LINE_AA)

            cv2.rectangle(source, (x, y), (x + w, y + h), (0, 255, 0), 4)

        return source

    def add_face(self):
        gray = cv2.cvtColor(self.last_frame, cv2.COLOR_BGR2GRAY)
        face = self.face_classifier.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(40, 40))
        if len(face):
            x, y, w, h = face[0]
            self.faces_to_train.append(gray[y:y+h, x:x+w])
            ret, jpeg = cv2.imencode('.jpg', self.faces_to_train[-1])
            return jpeg.tobytes()

        return None

    def train(self, face_id):
        self.recognizer.update(self.faces_to_train, numpy.array([face_id] * len(self.faces_to_train)))
        self.recognizer.write("media/trainer.yml")
        self.faces_to_train.clear()
