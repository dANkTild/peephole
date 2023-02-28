import quart.flask_patch

import time
import os
import logging
import asyncio
import json
from quart import Quart, render_template, send_from_directory, request, redirect, websocket
from werkzeug.utils import secure_filename
from werkzeug.security import safe_join

from aiortc import RTCPeerConnection, RTCSessionDescription
from aiortc.contrib.media import MediaRelay

from data.camera import VideoCamera

from sqlalchemy import select
from models import db_session
from models.cameras import Camera
from models.users import User
from models.photos import Photo
from models.videos import Video

from models.user_forms import AddUserForm
from models.cams_forms import AddCameraForm

app = Quart(__name__)
app.config['SECRET_KEY'] = 'secret_key'

camera = VideoCamera(1)


@app.route('/', methods=["GET", "POST"])
async def index():
    async with db_session.create_session() as db:
        photos = await db.scalars(select(Photo).order_by(Photo.date.desc()))
        videos = await db.scalars(select(Video).order_by(Video.date.desc()))

        return await render_template('index.html', title="FRPE", photos=photos.all(), videos=videos.all())


@app.route('/offer', methods=["POST"])
async def offer_handler():
    params = await request.get_json()
    offer = RTCSessionDescription(sdp=params["sdp"], type=params["type"])

    pc = RTCPeerConnection()

    @pc.on("connectionstatechange")
    async def on_connectionstatechange():
        print("Connection state is %s" % pc.connectionState)
        if pc.connectionState == "failed":
            await pc.close()

    pc.addTrack(camera.get_stream())

    await pc.setRemoteDescription(offer)
    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)

    return {"sdp": pc.localDescription.sdp, "type": pc.localDescription.type}


@app.route('/add_face')
async def add_face():
    async with db_session.create_session() as db:
        for i in range(5):
            new_user = User(name=f"asd{i}")
            db.add(new_user)
        await db.commit()

        return "200"
    # db = db_session.create_session()

    # all_users = db.query(User).all()
    # return render_template('add_face.html', title="FRPE - Добавить лица", users=all_users)


@app.route('/users', methods=["GET", "POST"])
async def users():
    async with db_session.create_session() as db:
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
            await db.commit()

        all_users = await db.scalars(select(User))
        return await render_template('users.html', title="FRPE - Пользователи",
                                     form=form, users=all_users)


@app.route('/photo_file/<int:photo_id>')
async def photo_file(photo_id):
    async with db_session.create_session() as db:
        photo = await db.get(Photo, photo_id)
        return await send_from_directory("media/screenshots", photo.file)


@app.route('/video_file/<int:video_id>')
async def video_file(video_id):
    async with db_session.create_session() as db:
        video = await db.get(Video, video_id)
        return await send_from_directory("media/videos", video.file)


@app.route('/video_preview/<int:video_id>')
async def video_preview(video_id):
    async with db_session.create_session() as db:
        video = await db.get(Video, video_id)
        return await send_from_directory("media/videos", video.preview)


@app.route('/user_photo/<int:user_id>')
def user_photo(user_id):
    db = db_session.create_session()
    filename = db.query(User).get(user_id).preview
    return send_from_directory("media/users", filename)


@app.route('/photo/<int:photo_id>', methods=["GET", "POST"])
async def photo_view(photo_id):
    async with db_session.create_session() as db:
        photo = await db.get(Photo, photo_id)
        if request.method == "POST":
            if "delete_btn" in await request.form:
                os.remove("media/screenshots/{}".format(photo.file))
                await db.delete(photo)
                await db.commit()
                return redirect("/")
            if "accept_btn" in await request.form:
                photo.name = (await request.form)["name"]
                await db.commit()
                return redirect("/")

        return await render_template('photo.html', title="FRPE", photo=photo)


@app.route('/video/<int:video_id>', methods=["GET", "POST"])
async def video_view(video_id):
    async with db_session.create_session() as db:
        video = await db.get(Video, video_id)
        if request.method == "POST":
            if "delete_btn" in await request.form:
                os.remove("media/videos/{}".format(video.file))
                os.remove("media/videos/{}".format(video.preview))
                await db.delete(video)
                await db.commit()
                return redirect("/")
            if "accept_btn" in await request.form:
                video.name = (await request.form)["name"]
                await db.commit()
                return redirect("/")

        return await render_template('video.html', title="FRPE", video=video)


@app.websocket('/ws')
async def ws():
    while True:
        try:
            data = await websocket.receive_json()

            if data["trigger"] == "screenshot":
                await camera.screenshot()
                await websocket.send_json({"trigger": "saved"})
            elif data["trigger"] == "record":
                res = await camera.record()
                await websocket.send_json({"trigger": "video", "is_recording": res})
                if not res:
                    await websocket.send_json({"trigger": "saved"})

        except json.decoder.JSONDecodeError:
            logging.error("Can`t decode JSON")


@app.before_serving
async def inter():
    app.add_background_task(asyncio.to_thread, camera.updater)
    # await camera.run()


# @socketio.on('connect')
# def handle_json():
#     join_room("video_room")
#     socketio.emit("frame", "test123", to="video_room")


# @socketio.on('trigger')
# def trigger(data):
#     db = db_session.create_session()
#     if data["type"] == "recognition":
#         frame_gen.video_recognition.toggle()
#     elif data["type"] == "screenshot":
#         frame_gen.screenshot()
#     elif data["type"] == "video":
#         frame_gen.video()


# @socketio.on('frame')
# def frm(data):
#     print("rcv")


# @socketio.on('add_face')
# def add_face(data):
#     frame_gen.add_face(data["user_id"])


# @socketio.on('train')
# def train(data):
#     frame_gen.train(data["user_id"])


# @socketio.on('test')
# def test(data):
#     print("test", data)
#     socketio.emit("tested", data)


if __name__ == '__main__':
    db_session.global_init("database/data.db")

    app.run("0.0.0.0", port=5555, use_reloader=False)
