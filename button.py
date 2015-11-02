import pygame
from pygame.locals import *
from text import Text

##########################################################################
## Button                                                               ##
## -------------------------------------------------------------------- ##
## Class that defines a button, which can either be clickable or non-   ##
## clickable. Has various attributes to allow for buttons that make     ##
## sound or change color to signal interaction.                         ##
##########################################################################
            
class Button(object):
    #################
    ## Constructor ##
    #################
    def __init__(self, string, name, antialias, size, image, pos, value, sfx=None,
                 ping=None, color=(255,255,255), shadow=(0,0,0), hover=(128,128,128),
                 fadein=False, scrollable=False, speed=20, anchor="center", shadow_type=1):

        ## Button's instance of text
        self.text = Text(string, name, antialias, size=size, color=color, shadow=shadow,
                         hover=hover, scrollable=scrollable, scroll_speed=speed, loop=True,
                         shadow_type=shadow_type)
        
        self.pos = pos        ## Top-left anchoring position
        self.anchor = anchor  ## Internal anchoring position for the text
        self.value = value    ## Unique identifier for the button
        self.image = image.copy().convert_alpha() ## Button graphic to draw
        ## Button's rectangular data
        self.rect = pygame.Rect(self.pos[0],self.pos[1],image.get_width(),image.get_height())
        self.sound = sfx      ## Sound to play when hovered over
        self.ping = ping      ## Sound to play when clicked
        self.has_sound_played = False ## Whether or not the sound has played already

        self.alpha = 0 if fadein else 255 ## Starting alpha transparency value

    ######################################
    ## Method to draw to target surface ##
    ######################################
    def draw(self, surface):
        ## If the current alpha channel is at all transparent, fade in
        if self.alpha < 255:
            image = self.image.copy()
            self.text.draw(image, anchor=self.anchor)
            image.fill((255,255,255,self.alpha), None, pygame.BLEND_RGBA_MULT)
            surface.blit(image, self.rect)
            self.alpha += 12
            if self.alpha > 255:
                self.alpha = 255
        ## If we are already opaque, no need to update alpha channel
        else:
            image = self.image.copy()
            self.text.draw(image, anchor=self.anchor)
            surface.blit(image, self.rect)

    #################################################
    ## Method to update the text within the button ##
    #################################################
    def update(self, color=None, string=None, speed=None):
        ## Only update if necessary
        if string != None:
            self.text.update(string, self.text.color)
        elif color != None:
            self.text.update(self.text.string, color)            
        elif speed != None:
            self.text.scroll_speed = speed
