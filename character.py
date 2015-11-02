import pygame, copy
from pygame.locals import *

##########################################################################
## Character                                                            ##
## -------------------------------------------------------------------- ##
## Class that defines an instance of an on-screen character sprite. Has ##
## various attributes that help optimize drawing routines.              ##
##########################################################################
            
class Character(object):
    #################
    ## Constructor ##
    #################
    def __init__(self, image, em, pos, name, index, num):
        self.image = image.copy().convert_alpha() ## Copy the source image
        self.em    = em     ## Identifier for current "emotion"
        self.pos   = pos    ## Top-left anchoring position
        self.name  = name   ## Character's name
        self.index = index  ## Character's index into the image bank
        self.alpha = 0      ## Character's current alpha channel
        self.num = num      ## Character's unique identifier
        self.rect = self.image.get_rect(midbottom=self.pos)

    ######################################
    ## Method to draw to target surface ##
    ######################################
    def draw(self, surface):
        ## If the current alpha channel is at all transparent, fade in
        if self.alpha < 255:
            image = copy.copy(self.image)
            image.fill((255,255,255,self.alpha), None, pygame.BLEND_RGBA_MULT)
            surface.blit(image, self.rect)
            self.alpha += 12
            if self.alpha > 255:
                self.alpha = 255
        ## If we are opaque, no need to update alpha channel
        else:
            surface.blit(self.image, self.rect)
