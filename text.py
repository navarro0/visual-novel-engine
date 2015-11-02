import pygame
from pygame.locals import *

##########################################################################
## Text                                                                 ##
## -------------------------------------------------------------------- ##
## Class that defines an instance of renderable text. Text associates   ##
## itself with a target rectangular surface, and aligns itself within   ##
## that rectangle according to given parameters.                        ##
##########################################################################
class Text(object):
    #################
    ## Constructor ##
    #################
    def __init__(self, string, fontname, antialias, pos=[0,0], size=24, color=(128,128,128), shadow=(0,0,0), hover=(255,255,255),
                 scrollable=False, scroll_speed=20, loop=False, shadow_type=1):

        ## Decode the parameter string to allow for unicode inputs
        string = string.decode('utf-8')
        self.string = u"{}".format(string)

        try:
            self.font   = pygame.font.Font("data/fonts/%s.ttf" %(fontname), size)
        except Exception as e:
            self.font   = pygame.font.SysFont("Arial", size)
        self.pos    = pos
        self.color  = color
        self.hover  = hover
        self.shadow = shadow
        self.antialias = antialias
        self.render = self.font.render(string, antialias, color)
        self.s_render = self.font.render(string, antialias, shadow)
        self.width  = self.render.get_width()
        self.height = self.font.get_height()

        self.shadow_type = shadow_type

        self.cur_width = 0
        self.delay = 0
        self.scrollable = scrollable
        self.scroll_speed = scroll_speed
        self.loop = loop

        self.has_target_surface = False

    def draw(self, surface, anchor="none"):        
        if self.scrollable and (self.loop or self.cur_width < self.width):
            surface.blit(self.s_render.subsurface(0,0,self.cur_width,self.height), (self.pos[0]+2,self.pos[1]+2))
            surface.blit(self.render.subsurface(0,0,self.cur_width,self.height), self.pos)
            self.cur_width += self.scroll_speed
            if self.cur_width >= self.width:
                if self.loop:
                    if self.delay < 60:
                        self.cur_width = self.width
                        self.delay += 1
                    else:
                        self.delay = 0
                        self.cur_width = 0
                else:
                    self.cur_width = self.width
        else:
            if not self.has_target_surface:
                w = surface.get_width()
                h = surface.get_height()
                self.topleft = (0,0)
                self.midtop = (w/2,0)
                self.topright = (w,0)
                self.midleft = (0,h/2)
                self.center = (w/2,h/2)
                self.midright = (w,h/2)
                self.bottomleft = (0,h)
                self.midbottom = (w/2,h)
                self.bottomright = (w,h)
                self.has_target_surface = True

            if anchor == "none":
                 surface.blit(self.s_render, (self.pos[0]+2,self.pos[1]+2))
                 surface.blit(self.render, self.pos)
                
            elif anchor == "topleft":
                surface.blit(self.s_render, self.s_render.get_rect(topleft=(self.topleft[0]+2,self.topleft[1]+2)))
                surface.blit(self.render, self.render.get_rect(topleft=(self.topleft[0], self.topleft[1])))
            elif anchor == "midtop":
                surface.blit(self.s_render, self.s_render.get_rect(midtop=(self.midtop[0]+2,self.midtop[1]+2)))
                surface.blit(self.render, self.render.get_rect(midtop=(self.midtop[0], self.midtop[1])))
            elif anchor == "topright":
                surface.blit(self.s_render, self.s_render.get_rect(topright=(self.topright[0]+2,self.topright[1]+2)))
                surface.blit(self.render, self.render.get_rect(topright=(self.topright[0], self.topright[1])))
            elif anchor == "midleft":
                surface.blit(self.s_render, self.s_render.get_rect(midleft=(self.midleft[0]+2,self.midleft[1]+2)))
                surface.blit(self.render, self.render.get_rect(midleft=(self.midleft[0], self.midleft[1])))
            elif anchor == "center":
                surface.blit(self.s_render, self.s_render.get_rect(center=(self.center[0]+2,self.center[1]+2)))
                surface.blit(self.render, self.render.get_rect(center=(self.center[0], self.center[1])))
            elif anchor == "midright":
                surface.blit(self.s_render, self.s_render.get_rect(midright=(self.midright[0]+2,self.midright[1]+2)))
                surface.blit(self.render, self.render.get_rect(midright=(self.midright[0], self.midright[1])))
            elif anchor == "bottomleft":
                surface.blit(self.s_render, self.s_render.get_rect(bottomleft=(self.bottomleft[0]+2,self.bottomleft[1]+2)))
                surface.blit(self.render, self.render.get_rect(bottomleft=(self.bottomleft[0], self.bottomleft[1])))
            elif anchor == "midbottom":
                surface.blit(self.s_render, self.s_render.get_rect(midbottom=(self.midbottom[0]+2,self.midbottom[1]+2)))
                surface.blit(self.render, self.render.get_rect(midbottom=(self.midbottom[0], self.midbottom[1])))
            elif anchor == "bottomright":
                surface.blit(self.s_render, self.s_render.get_rect(bottomright=(self.bottomright[0]+2,self.bottomright[1]+2)))
                surface.blit(self.render, self.render.get_rect(bottomright=(self.bottomright[0], self.bottomright[1])))

    def update(self, string, color):
        if color != self.color:
            self.color = color
            self.render = self.font.render(self.string, self.antialias, color)
            self.width  = self.render.get_width()
        elif string != self.string:
            self.string = string
            self.render = self.font.render(string, self.antialias, self.color)
            self.width  = self.render.get_width()

