import socketio

with socketio.SimpleClient() as sio:
    sio.connect("http://localhost:8080")
