import pygame
import sys

# Initialize Pygame
pygame.init()

# Set up the display
width, height = 800, 600
screen = pygame.display.set_mode((width, height))
pygame.display.set_caption("Text in Pygame")

def render_and_display_text(text, font_size, text_color, max_width):
    # Define the font
    font = pygame.font.Font(None, font_size)

    # Split the text into lines
    lines = text.split("\n")

    # Calculate the total height required for the text
    total_height = len(lines) * font_size

    # Calculate the starting position to center the text vertically
    y = (height - total_height) // 2

    # Main game loop
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Clear the screen
        screen.fill((0, 0, 0))

        # Render and blit each line onto the screen
        for line in lines:
            text_surface = font.render(line, True, text_color)
            text_rect = text_surface.get_rect()
            text_rect.centerx = width // 2
            text_rect.y = y
            screen.blit(text_surface, text_rect)
            y += font_size  # Move to the next line

        # Update the display
        pygame.display.flip()

# Example usage of the function
if __name__ == '__main__':
    text_to_display = "This is an example of a long text that will be displayed\nwith line breaks in Pygame. It's a great way to\nadd multiple lines of text to your game."
    font_size = 24
    text_color = (255, 255, 255)
    max_width = 400

    render_and_display_text(text_to_display, font_size, text_color, max_width)

# Clean up and exit
pygame.quit()
sys.exit()