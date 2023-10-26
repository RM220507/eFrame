import pygame
import socketio
from aiohttp import web
import logging
import threading
import time
import mysql.connector
import json
import sys
import os.path
from datetime import datetime

import toasts
import text_display


timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
log_file = f"logs/{timestamp}.log"
logging.basicConfig(filename=log_file, format="%(name)s - %(levelname)s - %(asctime)s - %(message)s", level=logging.INFO)

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

pygame.init()

class eFrame(socketio.AsyncServer):
    def __init__(self):
        super().__init__(logger=False)
        
        self.callbacks()
        
        self.app = web.Application()
        self.attach(self.app)
        
        self.app.router.add_get('/', self.index)
        self.app.router.add_post('/upload', self.upload_files)
        self.app.router.add_get('/control_script.js', self.control_script)
        self.app.router.add_get('/get_image/{upload_time}/{filename}', self.serve_image)
        self.app.router.add_get('/gallery.html', self.album_view)
        self.app.router.add_get('/gallery.js', self.gallery_script)
        self.app.router.add_get('/gallery.css', self.gallery_styles)
        
        self.connect_sql()
        
        self.width = 1000
        self.height = 500
        
        self.canvas = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("eFrame")
        
        self.toast_controller = toasts.ToastController()
        self.toast_controller.add_toast(f"Log file: {log_file}", toasts.INFO)
        self.toast_controller.add_toast("eFrame Loaded Successfully!", toasts.SUCCESS)
        
        self.last_update = 0
        
        self.reset()
        
        self.load_config()
        
        self.paused = False
        
    def load_config(self):
        with open("config.json", "r") as f:
            self.config = json.load(f)
            
    def write_config(self):
        with open("config.json", "w") as f:
            json.dump(self.config, f)
    
    def connect_sql(self):
        with open("connection_data.json", "r") as f:
            db_credentials = json.load(f)
        
        self.db = mysql.connector.connect(**db_credentials)
        self.db_cur = self.db.cursor()
    
    async def index(self, request):
        with open("index.html") as f:
            return web.Response(text=f.read(), content_type='text/html')
        
    async def album_view(self, request):
        with open("gallery.html") as f:
            return web.Response(text=f.read(), content_type='text/html')

    async def gallery_styles(self, request):
        with open("gallery.css") as f:
            return web.Response(text=f.read(), content_type='text/css')
    
    async def control_script(self, request):
        with open("control_script.js") as f:
            return web.Response(text=f.read(), content_type='text/javascript')
        
    async def gallery_script(self, request):
        with open("gallery.js") as f:
            return web.Response(text=f.read(), content_type='text/javascript')
        
    async def serve_image(self, request):
        upload_time = request.match_info.get("upload_time")
        filename = request.match_info.get("filename")
        if upload_time and filename:
            image_path = os.path.join(self.config["photos_root_path"], upload_time, filename)
            if os.path.exists(image_path) and os.path.isfile(image_path):
                with open(image_path, 'rb') as f:
                    return web.Response(body=f.read(), content_type='image/jpeg')
        
        return web.Response(status=404, text='Image not found')
        
    async def upload_files(self, request):
        data = await request.post()
        files = data.getall("file")
        
        if not files:
            self.toast_controller.add_toast(f"Cannot upload files: no file part", toasts.ERROR)
            return web.Response(text="No file part", status=400)
        
        current_time = datetime.now().strftime("%d%m%Y%H%M%S")
        os.makedirs(os.path.join(self.config["photos_root_path"], current_time))
        
        self.toast_controller.add_toast(f"Uploading {len(files)} files to {current_time}", toasts.INFO)
        
        for file in files:
            if not file.filename:
                self.toast_controller.add_toast(f"Failed uploading {len(files)} files: no selected file", toasts.ERROR)
                return web.Response(text="One of more files have no selected file", status=400)
            
            filename = os.path.join(self.config["photos_root_path"], current_time, file.filename)
            
            with open(filename, "wb") as f:
                while True:
                    chunk = file.file.read(8192)
                    if not chunk:
                        break
                    f.write(chunk)
                    
            self.db_cur.execute("INSERT INTO photos (uploadTime, filename) VALUES (%s, %s);", (current_time, file.filename))
            self.db.commit()
                    
        self.toast_controller.add_toast(f"Uploading {len(files)} files", toasts.SUCCESS)
        return web.Response(text="Files uploaded successfully")
        
        
    def callbacks(self):
        @self.event
        async def connect(sid, environ, auth):
            print("Connection established:", sid)
            
        @self.on("cycle_image")
        async def cycle_image_command(sid, data):
            if data == 1:
                self.toast_controller.add_toast("Next Image", toasts.INFO, 1)
            elif data == -1:
                self.toast_controller.add_toast("Previous Image", toasts.INFO, 1)
                
            self.cycle_image(data)
            
        @self.event
        async def pause(sid, data):
            if self.paused:
                self.toast_controller.add_toast("Resume Slideshow", toasts.INFO, 1)
            else:
                self.toast_controller.add_toast("Pause Slideshow", toasts.INFO, 1)
            
            self.paused = not self.paused
            
        @self.event
        async def get_album_list(sid, data):
            self.db_cur.execute("SELECT * FROM albums")
            albums = self.db_cur.fetchall()
            
            self.db.commit()
            
            return {"albums" : albums, "active" : self.album}
        
        @self.event
        async def set_album(sid, data):
            if data == "All":
                self.toast_controller.add_toast(f"Showing Album: '{self.album}'", toasts.INFO, 1)
                self.reset()
                return
            
            album_data = self.get_album_data(data)
            if album_data:
                self.album_id = album_data
                self.album = data
                self.current_info = (0, )
                
                self.toast_controller.add_toast(f"Showing Album: '{self.album}'", toasts.INFO, 1)
            else:
                self.toast_controller.add_toast(f"Unknown Album: '{data}'", toasts.ERROR, 3)
            
        @self.event
        async def lookup_album_images(sid, data):
            try:
                if data == "All":
                    self.db_cur.execute("SELECT * FROM photos")
                else:
                    album_id = self.get_album_data(data)
                    if album_id:
                        self.db_cur.execute("SELECT photos.photoID, uploadTime, filename, rotation, description FROM photo_album_assignment, photos WHERE albumID = %s AND photos.photoID = photo_album_assignment.photoID;", (album_id,))
                    else:
                        return {"success" : False}
                return_data = self.db_cur.fetchall()
                
                self.db.commit()
                
                return {"success" : True, "data" : return_data}
            except:
                return {"success" : False}
            
        @self.event
        async def update_image_data(sid, data):
            rotation = data.get("rotation")
            if not rotation:
                rotation = 0
                
            self.db_cur.execute("UPDATE photos SET rotation = %s, description = %s WHERE photoID = %s;", (rotation, data.get("desc"), data.get("id")))
            self.db.commit()
            
            self.toast_controller.add_toast(f"Successfully updated data of image '{data.get('id')}'", toasts.SUCCESS, 1)
            
        @self.event
        async def add_to_album(sid, data):
            self.toast_controller.add_toast(f"Adding {len(data.get('photos'))} photos to '{data.get('album')}'", toasts.INFO, 1)
            album_id = self.get_album_data(data.get("album"))
            if not album_id:
                self.toast_controller.add_toast(f"Adding to album failed: no album '{data.get('album')}'", toasts.ERROR, 3)
                return
            
            for photo_id in data.get("photos"):
                self.db_cur.execute("INSERT INTO photo_album_assignment (photoID, albumID) VALUES (%s, %s);", (photo_id, album_id))
            self.db.commit()
            
            self.toast_controller.add_toast(f"Successfully added {len(data.get('photos'))} photos to '{data.get('album')}'", toasts.SUCCESS, 3)
            
        @self.event
        async def remove_from_album(sid, data):
            self.toast_controller.add_toast(f"Removing {len(data.get('photos'))} photos from '{data.get('album')}'", toasts.INFO, 1)
            if data.get("album") != "All":
                album_id = self.get_album_data(data.get("album"))
                if not album_id:
                    self.toast_controller.add_toast(f"Removing from album failed: no album '{data.get('album')}'", toasts.ERROR, 3)
                    return
            
            for photo_id in data.get("photos"):
                if data.get("album") == "All":
                    self.db_cur.execute("DELETE FROM photos WHERE photoID = %s;", (photo_id,))
                else:
                    self.db_cur.execute("DELETE FROM photo_album_assignment WHERE photoID = %s AND albumID = %s;", (photo_id, album_id))
            self.db.commit()
            
            self.toast_controller.add_toast(f"Successfully removed {len(data.get('photos'))} photos from '{data.get('album')}'", toasts.SUCCESS, 3)
            
        @self.event
        async def new_album(sid, data):
            if (not data) or data == "":
                self.toast_controller.add_toast(f"Album creation failed: name cannot be blank", toasts.ERROR, 3)
            
            self.db_cur.execute("SELECT 1 FROM albums WHERE albumName = %s;", (data,))
            if self.db_cur.fetchone():
                self.toast_controller.add_toast(f"Album creation failed: name already in use", toasts.ERROR, 3)
                return
                
            self.db_cur.execute("INSERT INTO albums (albumName) VALUES (%s);", (data,))
            self.db.commit()
            
            self.toast_controller.add_toast(f"Successfully created new album: '{data}'", toasts.SUCCESS, 3)
                
        @self.event
        async def delete_album(sid, data):
            if data == "All":
                self.toast_controller.add_toast(f"Album deletion failed: cannot delete root", toasts.ERROR, 3)
            
            self.db_cur.execute("DELETE FROM albums WHERE albumName = %s;", (data,))
            self.db.commit()
            
            self.toast_controller.add_toast(f"Successfully deleted album: '{data}'", toasts.SUCCESS, 3)
        
    def get_next_file_name_album(self, direction):
        if direction == 1:
            self.db_cur.execute("""(
                                        SELECT photos.photoID, uploadTime, filename, rotation, description
                                        FROM photo_album_assignment, photos
                                        WHERE photos.photoID > %s
                                        AND albumID = %s
                                        AND photo_album_assignment.photoID = photos.photoID
                                        ORDER BY photoID ASC
                                        LIMIT 1
                                    )
                                    UNION
                                    (
                                        SELECT photoID, uploadTime, filename, rotation, description
                                        FROM photos
                                        WHERE photoID = (
                                            SELECT MIN(photoID)
                                            FROM photo_album_assignment
                                            WHERE albumID = %s
                                        )
                                        LIMIT 1
                                    )
                                    LIMIT 1;
                                    """, (self.current_info[0], self.album_id, self.album_id))
        elif direction == -1:
            self.db_cur.execute("""(
                                        SELECT photos.photoID, uploadTime, filename, rotation, description
                                        FROM photo_album_assignment, photos
                                        WHERE photos.photoID < %s
                                        AND albumID = %s
                                        AND photo_album_assignment.photoID = photos.photoID
                                        ORDER BY photoID DESC
                                        LIMIT 1
                                    )
                                    UNION
                                    (
                                        SELECT photos.photoID, uploadTime, filename, rotation, description
                                        FROM photo_album_assignment, photos
                                        WHERE photoID = (
                                            SELECT MAX(photoID)
                                            FROM photo_album_assignment
                                            WHERE albumID = %s
                                        )
                                        LIMIT 1
                                    )
                                    LIMIT 1;
                                    """, (self.current_info[0], self.album_id, self.album_id))
        
        next_info = self.db_cur.fetchone()        
        self.db.commit()
        
        return next_info
            
    def get_next_file_name_all(self, direction):
        if direction == 1:
            self.db_cur.execute("""(
                                        SELECT *
                                        FROM photos
                                        WHERE photoID > %s
                                        ORDER BY photoID ASC
                                        LIMIT 1
                                    )
                                    UNION
                                    (
                                        SELECT *
                                        FROM photos
                                        WHERE photoID = (
                                            SELECT MIN(photoID)
                                            FROM photos
                                        )
                                        LIMIT 1
                                    )
                                    LIMIT 1;
                                    """, (self.current_info[0],))
        elif direction == -1:
            self.db_cur.execute("""(
                                        SELECT *
                                        FROM photos
                                        WHERE photoID < %s
                                        ORDER BY photoID DESC
                                        LIMIT 1
                                    )
                                    UNION
                                    (
                                        SELECT *
                                        FROM photos
                                        WHERE photoID = (
                                            SELECT MAX(photoID)
                                            FROM photos
                                        )
                                        LIMIT 1
                                    )
                                    LIMIT 1;
                                    """, (self.current_info[0],))
            
        next_info = self.db_cur.fetchone()
        
        self.db.commit()
        
        return next_info

    def get_album_data(self, name):
        self.db_cur.execute("SELECT albumID from albums WHERE albumName = %s LIMIT 1;", (name,))
                
        return_data = self.db_cur.fetchone()
        if return_data:
            return return_data[0]
        else:
            return None
    
    def reset(self):
        self.album = "All"
        self.album_id = 0
        self.current_info = (0,)
    
    def scale_image(self, original):
        original_width = original.get_width()
        original_height = original.get_height()
        
        #if original_width > original_height:
        #    scale = self.width / original_width
        #else:
        scale = self.height / original_height
        
        scaled_width = round(original_width * scale)
        scaled_height = round(original_height * scale)
        
        scaled = pygame.transform.smoothscale(original, (scaled_width, scaled_height))
        return scaled
    
    def get_centered_pos(self, image):
        x = (self.width - image.get_width()) // 2
        y = (self.height - image.get_height()) // 2
        
        return (x, y)
    
    def cycle_image(self, direction=1):
        if self.album == "All":
            next_info = self.get_next_file_name_all(direction)
        else:
            next_info = self.get_next_file_name_album(direction)
            
        if not next_info:
            self.toast_controller.add_toast("No photos available: defaulting to 'All'", toasts.ERROR, 3)
            self.reset()
            return
            
        next_image = pygame.image.load(os.path.join(self.config['photos_root_path'], next_info[1], next_info[2]))
        
        if next_info[3] != 0:
            next_image = pygame.transform.rotate(next_image, next_info[3])
        
        scaled_image = self.scale_image(next_image)
        next_blit_pos = self.get_centered_pos(scaled_image)
        
        self.current_info = next_info
        self.image = scaled_image
        self.blit_pos = next_blit_pos
        
    def mainloop(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
            
            current_time = time.time()
            if (current_time - self.last_update > self.config["update_interval"]) and not self.paused:
                self.last_update = current_time
                self.cycle_image()

            self.canvas.fill(self.config.get("background_color", WHITE))
            
            self.canvas.blit(self.image, self.blit_pos)
            
            if self.config.get("display_toasts"):
                toast_surface_size = (325, 400)          
                toast_surface = self.toast_controller.update_toasts(toast_surface_size)
                self.canvas.blit(toast_surface, (self.width - toast_surface_size[0], 25))
                
            if self.config.get("display_album"):
                text_display.display_text(self.canvas, self.album, 40, self.config.get("album_color", BLACK), (25, 25), "left")
                
            if self.config.get("display_desc"):
                if self.current_info[4]:
                    text_display.display_text_wrapped(self.canvas, self.current_info[4], 40, self.config.get("desc_color", BLACK), (25, self.height - 80), self.width // 2, "left")
                    
            pygame.display.flip()

eframe = eFrame()

if __name__ == "__main__":
    try:
        runner = web.AppRunner(eframe.app)
        t = threading.Thread(target=web.run_app, args=(eframe.app,))
        t.daemon = True
        t.start()
        eframe.mainloop()
    finally:
        eframe.write_config()