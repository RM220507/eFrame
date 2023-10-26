import pygame
import text_display
import time

INFO = "info"
SUCCESS = "success"
ERROR = "error"

toast_colors = {
    "info" : (167, 199, 231),
    "success" : (218, 247, 166),
    "error" : (255, 105, 97)
}

BLACK = (0, 0, 0)

class ToastController:
    def __init__(self):
        self.__active_toasts = []
        
        self.__toast_spacing = 25
        
    def add_toast(self, message, level, cooldown=5):
        new_toast = Toast(message, level, cooldown)
        self.__active_toasts.append(new_toast)
    
    def update_toasts(self, size):
        surface = pygame.Surface(size, pygame.SRCALPHA)
        surface.fill((0, 0, 0, 0))
        
        expired_toasts = []
        for i, toast in enumerate(self.__active_toasts[::-1]):
            if toast.expired:
                expired_toasts.append(toast)
            
            toast_surface = toast.render((300, 75))
            
            y = i * (75 + self.__toast_spacing)            
            surface.blit(toast_surface, (0, y))
            
        for expired_toast in expired_toasts:
            self.__active_toasts.remove(expired_toast)
            
        return surface
        
class Toast:
    def __init__(self, message, level, cooldown=5):
        self.__message = message
        self.__level = level
        self.__cooldown = cooldown
        
        self.__creation_time = time.time()
        
        self.__color = toast_colors.get(self.__level)
        
    def render(self, size):
        surface = pygame.Surface(size, pygame.SRCALPHA)
        surface.fill((0, 0, 0, 0))
        
        pygame.draw.rect(surface, self.__color, [0, 0, *size], border_radius=10)
        
        text_display.display_text_wrapped(surface, self.__message, 25, BLACK, (size[0] // 2, size[1] // 2), size[0] - 25)
        
        return surface
    
    @property
    def expired(self):
        return (time.time() - self.__creation_time) >= self.__cooldown