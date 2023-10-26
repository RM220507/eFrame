import pygame

def wrap_text(text, font_size, max_width):
    words = text.split()
    lines = []
    current_line = []
    current_line_width = 0
    
    font = pygame.font.Font(None, font_size)

    for word in words:
        word_surface = font.render(word, True, (255, 255, 255))
        word_width, word_height = word_surface.get_size()

        if current_line_width + word_width <= max_width:
            current_line.append(word)
            current_line_width += word_width
        else:
            lines.append(" ".join(current_line))
            current_line = [word]
            current_line_width = word_width

    if current_line:
        lines.append(" ".join(current_line))

    return lines

def render_text(text, font_size, text_color, text_position, align="center"):
    font = pygame.font.Font(None, font_size)

    text_surface = font.render(text, True, text_color)

    text_rect = text_surface.get_rect()

    if align == "center":
        text_rect.center = text_position
    elif align == "left":
        text_rect.left = text_position[0]
        text_rect.centery = text_position[1]
        
    elif align == "right":
        text_rect.right = text_position[0]
        text_rect.centery = text_position[1]
    
    return text_surface, text_rect

def display_text(display, text, font_size, text_color, text_position, align="center"):
    text_surface, text_rect = render_text(text, font_size, text_color, text_position, align)
    
    display.blit(text_surface, text_rect)
    
def display_text_wrapped(display, text, font_size, text_color, text_position, max_width, align="center"):
    lines = wrap_text(text, font_size, max_width)
    
    total_height = len(lines) * font_size
    y = text_position[1] - (total_height // 4)
    
    for line in lines:
        display_text(display, line, font_size, text_color, (text_position[0], y), align)
        y += font_size