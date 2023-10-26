const socket = io("http://192.168.1.144:8080");

let albums = [];
const images_per_page = 30;
let current_page = 1;
let images = [];

let selected_image_id = null;
let selected_image_div = null;

let multiselect = false;
let multiselect_target_divs = [];
let multiselect_target_ids = [];

let number_of_pages = 0;

const album_select = document.getElementById("album_select");

const new_album_name = document.getElementById("new-album-name");
const delete_album_button = document.getElementById("delete-album-button");
const upload_button = document.getElementById("upload-button");

const multiselect_activation_button = document.getElementById("activate-multiselect");
const multiselect_toolbar = document.getElementById("multiselect-toolbar");
const basic_toolbar = document.getElementById("basic-toolbar")
const multiselect_album_dropdown = document.getElementById("multiselect-album-dropdown");
const multiselect_counter = document.getElementById("multiselect-counter")

const image_container = document.getElementById("image-container");

const pagination_status = document.getElementById("pagination-status");
const prev_page_button = document.getElementById("prev-page");
const next_page_button = document.getElementById("next-page");
const first_page_button = document.getElementById("first-page");
const last_page_button = document.getElementById("last-page");

const image_pane = document.getElementById("image-pane");
const selected_image = document.getElementById("selected-image");
const selected_image_name = document.getElementById("selected-image-name");
const selected_image_rotation = document.getElementById("selected-image-rotation");
const selected_image_desc = document.getElementById("selected-image-desc");
const selected_album_dropdown = document.getElementById("selected-album-dropdown")

function fetch_images(album_name) {
    socket.emit("lookup_album_images", album_name, callback=function(response) {
        hide_pane();
        
        if (!response["success"]) {return}

        current_page = 1;
        images = response["data"];

        if (album_name == "All") {
            upload_button.style.display = "block";
            delete_album_button.style.display = "none";
        } else {
            delete_album_button.style.display = "block";
            upload_button.style.display = "none";
        }

        show_images(current_page);
    });
}

document.getElementById("album_select").onchange = function() {
    fetch_images(this.value);
}

function activate_multiselect() {
    multiselect = true;
    multiselect_target_divs = [];
    multiselect_target_ids = [];

    multiselect_toolbar.style.display = "flex";
    basic_toolbar.style.display = "none";
    multiselect_activation_button.disabled = true;

    multiselect_counter.innerText = "0 selected";

    hide_pane();
}

function deactivate_multiselect() {
    multiselect = false;
    multiselect_target_ids = [];

    multiselect_target_divs.forEach(element => {
        element.style.backgroundColor = "#555"
    });
    multiselect_target_divs = [];

    multiselect_toolbar.style.display = "none";
    basic_toolbar.style.display = "flex";
    multiselect_activation_button.disabled = false;
}

function show_images(page) {
    hide_pane();
    deactivate_multiselect();
    image_container.innerHTML = "";

    const start_index = (page - 1) * images_per_page;
    const end_index = start_index + images_per_page;

    number_of_pages = Math.ceil(images.length / images_per_page);
    pagination_status.innerText = `Page ${page} of ${number_of_pages} (${images.length} images)`;

    for (let i = start_index; i < end_index && i < images.length; i++) {
        const image_wrapper = document.createElement("div");
        image_wrapper.classList.add("image-wrapper");
        image_wrapper.onclick = function() {
            if (multiselect) {
                index = multiselect_target_divs.indexOf(this);
                if (index != -1) {
                    // unselect
                    multiselect_target_divs.splice(index, 1);
                    this.style.backgroundColor = "#555";

                    multiselect_target_ids.splice(multiselect_target_ids.indexOf(images[i][0]), 1);
                
                    if (multiselect_target_ids.length == 0) {
                        deactivate_multiselect();
                    }

                } else {
                    // select
                    multiselect_target_divs.push(this);
                    this.style.backgroundColor = "#5F5";

                    multiselect_target_ids.push(images[i][0]);
                }
                multiselect_counter.innerText = `${multiselect_target_ids.length} selected`;
            } else {
                select_image(i);

                this.style.backgroundColor = "#5F5";
                if (selected_image_div) {
                    selected_image_div.style.backgroundColor = "#555";
                }
                selected_image_div = this;
                
            }
        }
        
        const image = document.createElement("img");
        image.src = `get_image/${image_path(i)}`;
        image.classList.add("image");
        image_wrapper.appendChild(image);

        const image_name = document.createElement("p");
        image_name.innerText = image_path(i);
        image_name.classList.add("image-name");
        image_wrapper.appendChild(image_name);

        image_container.appendChild(image_wrapper);
    }

    update_pagination_buttons(page);
}

function update_pagination_buttons(page) {
    first_page_button.disabled = (page === 1);
    prev_page_button.disabled = (page === 1);
    next_page_button.disabled = (page * images_per_page >= images.length);
    last_page_button.disabled = (page == number_of_pages);
}

function image_path(i) {
    return `${images[i][1]}/${images[i][2]}`;
}

function select_image(i) {
    selected_image_id = images[i][0];
    selected_image.src = `get_image/${image_path(i)}`;
    selected_image_name.innerText = image_path(i);

    selected_image_rotation.value = images[i][3];
    selected_image_desc.value = images[i][4];

    image_pane.style.display = "block";
}

function hide_pane() {
    selected_image_id = null;

    if (selected_image_div) {
        selected_image_div.style.backgroundColor = "#555";
        selected_image_div = null;
    }

    image_pane.style.display = "none";
}

function update_image_data() {
    socket.emit("update_image_data", {"id" : selected_image_id, "rotation" : selected_image_rotation.value, "desc" : selected_image_desc.value}, callback=function(response) {
        fetch_images(album_select.value);
    });
}

function get_album_list() {
    socket.emit("get_album_list", null, callback=function(response) {
        albums = response["albums"];

        album_select.innerHTML = "";
        selected_album_dropdown.innerHTML = "";
        multiselect_album_dropdown.innerHTML = "";

        var option = document.createElement("option");
        option.text = "All";
        album_select.add(option);

        albums.forEach(album => {

            option = document.createElement("option");
            option.text = album[1];
            album_select.add(option);

            option = document.createElement("option");
            option.text = album[1];
            selected_album_dropdown.add(option);

            option = document.createElement("option");
            option.text = album[1];
            multiselect_album_dropdown.add(option);
        });
    });
}

function new_album() {
    socket.emit("new_album", new_album_name.value, callback=function(response) {
        new_album_name.value = "";
        get_album_list();
    });
}

function delete_album() {
    socket.emit("delete_album", album_select.value, callback=function(response) {
        get_album_list();
        fetch_images("All");
    });
}

function single_add_to_album() {
    socket.emit("add_to_album", {"album" : selected_album_dropdown.value, "photos" : [selected_image_id]})
}

function multi_add_to_album() {
    socket.emit("add_to_album", {"album" : multiselect_album_dropdown.value, "photos" : multiselect_target_ids})
    deactivate_multiselect();
}

function single_delete () {
    socket.emit("remove_from_album", {"album" : album_select.value, "photos" : [selected_image_id]}, callback=function(response) {
        fetch_images(album_select.value);
    });
}

function multi_delete () {
    socket.emit("remove_from_album", {"album" : album_select.value, "photos" : multiselect_target_ids}, callback=function(response) {
        fetch_images(album_select.value);
    });
    deactivate_multiselect();
}

prev_page_button.addEventListener('click', () => {
    if (current_page > 1) {
        current_page--;
        show_images(current_page);
    }
});

next_page_button.addEventListener('click', () => {
    if (current_page * images_per_page < images.length) {
        current_page++;
        show_images(current_page);
    }
});

get_album_list();
fetch_images("All");
