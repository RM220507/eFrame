const socket = io("http://192.168.1.144:8080");

function cycle_image(direction) {
    socket.emit("cycle_image", direction);
}

function pause() {
    socket.emit("pause", null);
}

function get_album_list() {
    socket.emit("get_album_list", null, callback=function(response) {
        albums = response["albums"];
        albums.forEach(album => {
            var option = document.createElement("option");
            option.text = album[1];
            album_select.add(option);
        });
        album_select.value = response["active"];
    });
}

function update_album() {
    socket.emit("set_album", album_select.value);
}