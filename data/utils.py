import eventlet
from flask_socketio import SocketIO

# eventlet.monkey_patch(socket=True)


class EventletSender(SocketIO): pass
