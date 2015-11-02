import pygame
from pygame.locals import *

##########################################################################
## Slider                                                               ##
## -------------------------------------------------------------------- ##
## Class that defines a sliding bar, for use in the configuration menu. ##
## Players will be able to drag the member button left and right to     ##
## modify a floating point variable.                                    ##
##########################################################################
    
class Slider(object):
    #################
    ## Constructor ##
    #################
    def __init__(self, image, pos, button, value, fadein=False):
        self.pos = pos                            ## Top-left anchoring position
        self.focus = False                        ## Whether or not this slider has focus
        self.image = image.copy().convert_alpha() ## Slider graphic to draw
        ## Slider's rectangular data
        self.rect = pygame.Rect(self.pos[0],self.pos[1],image.get_width(),image.get_height())
        self.button = button               ## Slider's draggable button
        self.value = value                 ## Unique identifier for the slider
        self.alpha = 0 if fadein else 255  ## Starting alpha transparency value

    ######################################
    ## Method to draw to target surface ##
    ######################################  
    def draw(self, surface):
        ## If the current alpha channel is at all transparent, fade in
        if self.alpha < 255:
            image = self.image.copy()
            image.fill((255,255,255,self.alpha), None, pygame.BLEND_RGBA_MULT)
            surface.blit(image, self.rect)
            self.button.draw(surface)
            self.alpha += 12
            if self.alpha > 255:
                self.alpha = 255
        ## If we are already opaque, no need to update alpha channel
        else:
            surface.blit(self.image, self.rect)
            self.button.draw(surface)
