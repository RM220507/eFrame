import pygame
import time
import os
import json

pygame.init()

display_width = 1920
display_height = 1080

max_image_width = display_width - 100
max_image_height = display_height - 100

time_delay = 5

display = pygame.display.set_mode((display_width, display_height)) # make screen width/height

picture_dir = "Pictures"
data_file = "image_data.json"

BLACK = (0, 0, 0)

def scale_image(original):
    original_width = original.get_width()
    original_height = original.get_height()
    
    if original_width > original_height:
        scale = max_image_width // original_width
    else:
        scale = max_image_height // original_height    
    
    scaled_width = original_width * scale
    scaled_height = original_height * scale
    
    scaled = pygame.transform.smoothscale(original, (scaled_width, scaled_height))
    return scaled

def get_centered_pos(image):
    x = (display_width - image.get_width()) // 2
    y = (display_height - image.get_height()) // 2
    
    return (x, y)

def load_image_from_file(image_file):
    print(image_file)
    image = pygame.image.load(f"{picture_dir}/{image_file}")
    
    with open(data_file, "r") as f:
        data_dict = json.load(f)
        
    image_data = data_dict.get(image_file)
    if image_data:
        if image_data[1] % 4 != 0:
            print("Rotating...")
            image = pygame.transform.rotate(image, (image_data[1] * 90) % 360)
            
    scaled_image = scale_image(image)
    
    image_pos = get_centered_pos(scaled_image)
    
    return scaled_image, image_pos

def previous_image(image_file):
    image_files = os.listdir(picture_dir)
    
    if image_file == "":
        image_file = image_files[0]
    else:
        index = image_files.index(image_file) - 1
        
        if index < 0:
            index = len(image_files) - 1
            
    scaled_image, image_pos = load_image_from_file(image_file)
    
    return image_file, scaled_image, image_pos

def next_image(image_file):
    image_files = os.listdir(picture_dir)
    
    if image_file == "":
        image_file = image_files[0]
    else:
        image_file = image_files[(image_files.index(image_file) + 1) % len(image_files)]
        
    scaled_image, image_pos = load_image_from_file(image_file)
    
    return image_file, scaled_image, image_pos

def main():
    running = True
    
    last_update = 0
    image_file = ""

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
            
        current_time = time.time()    
        if current_time - last_update >= time_delay:
            last_update = current_time
            
            image_file, image, image_pos = next_image(image_file)
                
        display.fill(BLACK)
        
        display.blit(image, image_pos)
        pygame.display.update()
        
main()