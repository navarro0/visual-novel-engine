import pygame
from pygame.locals import *
from text import Text

##########################################################################
## Choice                                                               ##
## -------------------------------------------------------------------- ##
## Class that defines instances of on-screen clickable dialogue options ##
## which, when clicked, can alter the flow of the game.                 ##
##########################################################################
class Choice(object):
    #################
    ## Constructor ##
    #################
    def __init__(self, string, num, antialias, image, value, pos):
        self.pos = pos                            ## Topleft anchoring position
        self.text = Text(string, num, antialias)  ## Renderable text object
        self.value = value                        ## Unique identifier

        ## Copy the source image so we don't mutate the original
        self.image = image.copy().convert_alpha()
        self.alpha = 0  ## Alpha channel is transparent

        ## Rectangular box information for positioning purposes
        self.rect = pygame.Rect(0,self.pos[1],image.get_width(),image.get_height())
        self.rect.centerx = self.pos[0] ## Center the box on-screen

    ######################################
    ## Method to draw to target surface ##
    ######################################
    def draw(self, surface):
        ## If we are at all transparent, update the alpha channel
        if self.alpha < 255:
            image = self.image.copy()
            self.text.draw(image, anchor="center")
            image.fill((255,255,255,self.alpha), None, pygame.BLEND_RGBA_MULT)
            surface.blit(image, self.rect.topleft)
            self.alpha += 12
            if self.alpha > 255:
                self.alpha = 255
        ## If we are fully opaque, no need to update
        else:
            image = self.image.copy()
            self.text.draw(image, anchor="center")
            surface.blit(image, self.rect.topleft)

    #################################################
    ## Method to modify the current string's color ##
    #################################################
    def update(self, color):
        self.text.update(self.text.string, color)
