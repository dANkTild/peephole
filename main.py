import time
from multiprocessing import Queue
import logging
import eventlet
from flask import Flask, render_template, send_from_directory, request, redirect
from flask_socketio import SocketIO
from werkzeug.utils import secure_filename
from werkzeug.security import safe_join
from multiprocessing import Process, Manager
from multiprocessing.managers import BaseManager

from data.camera import VideoCamera
from models import db_session
from models.cameras import Camera
from models.users import User
from models.photos import Photo
from models.videos import Video

from models.user_forms import AddUserForm
from models.cams_forms import AddCameraForm

# app.logger.disabled = True
log = logging.getLogger('werkzeug')
log.disabled = True

eventlet.monkey_patch(socket=True)
# utils = eventlet.import_patched("data.utils")

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret_key'
socketio = SocketIO(app, async_mode="eventlet",
                    message_queue='redis://127.0.0.1:6379')


@app.route('/', methods=["GET", "POST"])
def index():
    db = db_session.create_session()
    photos = db.query(Photo).order_by(Photo.date.desc()).all()
    videos = db.query(Video).order_by(Video.date.desc()).all()

    form = AddCameraForm()
    if form.validate_on_submit():
        print("asdfasdasd")
        cam = Camera(device_id=form.device_id.data)
        db.add(cam)
        db.commit()

    print(cameras)

    return render_template('index.html', title="FRPE", cams=cameras, photos=photos, videos=videos, form=form)


@app.route('/add_face')
def add_face():
    db = db_session.create_session()

    all_users = db.query(User).all()
    return render_template('add_face.html', title="FRPE - Добавить лица", users=all_users)


@app.route('/users', methods=["GET", "POST"])
def users():
    db = db_session.create_session()
    form = AddUserForm()

    if form.validate_on_submit():
        if form.preview.data is not None:
            img_name = secure_filename(form.preview.data.filename)
            img_path = safe_join("media/users/", img_name)
            form.preview.data.save(img_path)
        else:
            img_name = None

        email = form.email.data if form.email.data else None

        user = User(name=form.name.data, email=email, preview=img_name)
        db.add(user)
        db.commit()

    all_users = db.query(User).all()

    return render_template('users.html', title="FRPE - Пользователи",
                           form=form, users=all_users)


@app.route('/photo_file/<int:photo_id>')
def photo_file(photo_id):
    db = db_session.create_session()
    filename = db.query(Photo).get(photo_id).file
    return send_from_directory("media/screenshots", filename)


@app.route('/video_file/<int:video_id>')
def video_file(video_id):
    db = db_session.create_session()
    filename = db.query(Video).get(video_id).file
    return send_from_directory("media/videos", filename)


@app.route('/video_preview/<int:video_id>')
def video_preview(video_id):
    db = db_session.create_session()
    filename = db.query(Video).get(video_id).preview
    return send_from_directory("media/videos", filename)


@app.route('/user_photo/<int:user_id>')
def user_photo(user_id):
    db = db_session.create_session()
    filename = db.query(User).get(user_id).preview
    return send_from_directory("media/users", filename)


@app.route('/photo/<int:photo_id>', methods=["GET", "POST"])
def photo_view(photo_id):
    db = db_session.create_session()
    photo = db.query(Photo).get(photo_id)
    if request.method == "POST":
        if "delete_btn" in request.form:
            db.delete(photo)
            db.commit()
            return redirect("/")
        if "accept_btn" in request.form:
            photo.name = request.form["name"]
            db.commit()
            return redirect("/")

    photo_dict = photo.to_dict()
    return render_template('photo.html', title="FRPE", photo=photo_dict)


@app.route('/video/<int:video_id>', methods=["GET", "POST"])
def video_view(video_id):
    db = db_session.create_session()
    video = db.query(Video).get(video_id)
    if request.method == "POST":
        if "delete_btn" in request.form:
            db.delete(video)
            db.commit()
            return redirect("/")
        if "accept_btn" in request.form:
            video.name = request.form["name"]
            db.commit()
            return redirect("/")

    video_dict = video.to_dict()
    return render_template('video.html', title="FRPE", video=video_dict)


# @socketio.on('connect')
# def handle_json():
#     join_room("video_room")
#     socketio.emit("frame", "test123", to="video_room")


@socketio.on('trigger')
def trigger(data):
    db = db_session.create_session()
    if data["type"] == "recognition":
        frame_gen.video_recognition.toggle()
    elif data["type"] == "screenshot":
        frame_gen.screenshot()
    elif data["type"] == "video":
        frame_gen.video()


@socketio.on('frame')
def frm(data):
    print("rcv")


@socketio.on('add_face')
def add_face(data):
    frame_gen.add_face(data["user_id"])


@socketio.on('train')
def train(data):
    frame_gen.train(data["user_id"])


@socketio.on('test')
def test(data):
    print("test", data)
    socketio.emit("tested", data)


if __name__ == '__main__':
    db_session.global_init("database/data.db")
    db = db_session.create_session()

    cameras = db.query(Camera).all()

    # for cam in cameras:
    #     frame_gen = VideoCamera(cam.device_id)
    #     frame_gen.start()

    frame_gen = VideoCamera(-1)
    frame_gen.start()

    socketio.run(app, host='0.0.0.0', debug=False, use_reloader=False)
    # print("dfsdf")
    # eventlet.sleep(50000)
