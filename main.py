# -*- coding: utf-8 -*-
#!usr/bin/env python
#
# Joey Navarro
#
# This is a game engine designed to specifically facilitate the creation
# of visual novels through an easy scripting language system, as well as
# a simple resource management system.
#
# Licensed under the MIT License.

import pygame, os, glob, datetime, random, codecs, sys
from pygame.locals import *
from string import ascii_lowercase
from slider import Slider
from button import Button
from text import Text
from choice import Choice
from character import Character

## Center the display on-screen
os.environ["SDL_VIDEO_CENTERED"] = "1"

#########################################################################
## STATE                                                               ##
## ------------------------------------------------------------------- ##
## Static structure for the finite state machine that defines what the ##
## engine's parser should be doing at the current point in time.       ##
#########################################################################

class STATE:
    ####################
    ## In-game states ##
    ####################
    
    READ       = 1    ## Default idle state; player can pause to read dialogue
    CHOOSE     = 2    ## Option selection state; player can pick a response
    OPT_BRANCH = 3    ## Option branching state; wait until target line is found
    VAR_BRANCH = 4    ## Variable branching state; wait until target line is found
    
    #########################
    ## Title screen states ##
    #########################
    
    TITLE      = 5    ## Currently in the main menu
    LOAD       = 6    ## Currently selecting a file from which data will be loaded
    SAVE       = 7    ## Currently selecting a file into which data will be saved
    CONFIG     = 8    ## Currently setting configuration options

##########################################################################
## CONST                                                                ##
## -------------------------------------------------------------------- ##
## Static structure for the various defined constants that need not be  ##
## member variables of any class or instantiated object.                ##
##########################################################################
    
class CONST:
    SPEED_RANGE = 30  ## Range of text scrolling speeds in pixels per frame
    FADE        = 5   ## Fade rate in alpha per second

##########################################################################
## Main                                                                 ##
## -------------------------------------------------------------------- ##
## Wrapper class for the main method, main game loop, and various other ##
## helper methods to handle game logic.                                 ##
##########################################################################

class Main:
    def __init__(self):
        #################
        ## Constructor ##
        #################
        pygame.mixer.pre_init(44100, -16, 2, 4096) ## Initialize the sound
        pygame.init() ## Initialize pygame

        config = open("data/data/config.nec", "r").readlines() ## Open config

        ## Default values to fall back on if the config file is corrupt
        self.caption = ""
        self.screen_dimension = (1280,720)
        self.fade_color = (0,0,0)
        self.fullscreen = False
        self.volume = 0.5

        ## Read in values from configuration file
        for line in config:
            ## Set up the caption
            if line.startswith("caption:"):
                self.caption = line.lstrip("caption:").lstrip().rstrip()
            ## Set up the window dimensions
            elif line.startswith("window_size:"):
                temp = line.split(":")[1].split(",")
                self.screen_dimension = (int(temp[0]), int(temp[1]))
            ## Toggle fullscreen mode
            elif line.startswith("is_fullscreen:"):
                temp = line.split(":")[1].lstrip().rstrip()
                if int(temp):
                    self.fullscreen = True
            ## Set up the fade color
            elif line.startswith("fade_color:"):
                temp = line.split(":")[1].split(",")
                self.fade_color = (int(temp[0]),int(temp[1]),int(temp[2]))
            ## Establish background music volume
            elif line.startswith("volume:"):
                temp = line.split(":")[1]
                self.volume = float(temp)
                pygame.mixer.music.set_volume(self.volume)

        ## Set caption for windowed mode
        pygame.display.set_caption(self.caption)

        ## Create the display surface
        if self.fullscreen:
            self.screen = pygame.display.set_mode(self.screen_dimension, SWSURFACE|FULLSCREEN)
        else:
            self.screen = pygame.display.set_mode(self.screen_dimension, SWSURFACE)

        self.screen.fill((0,0,0))

        ## Set up the game clock to poll events with
        self.clock = pygame.time.Clock()

        self.load_images()   ## Load all images
        self.set_constants() ## Set anchoring constants

    def _quit(self):
        ###########################################
        ## Method for safe and easy game exiting ##
        ###########################################
        pygame.quit()
        raise SystemExit
    
    def init_title(self):
        ###################################################
        ## External game loop that handles the main menu ##
        ###################################################
        while True:
            pygame.mixer.stop()
            self.init_defaults()
            self.init_config()
            self.save_changes()
            self.draw_splash()
            self.draw_title()

    def get_mouse_pos(self):
        ########################################
        ## Returns the current mouse position ##
        ########################################
        return pygame.mouse.get_pos()

    def set_constants(self):
        ############################################################
        ## Creates a dictionary of anchoring positions to be used ##
        ## by the engine's scripting language.                    ##
        ############################################################
        topleft      = (0,0)
        midtop       = (self.screen_dimension[0]/2,0)
        topright     = (self.screen_dimension[0],0)
        midleft      = (0,self.screen_dimension[1]/2)
        center       = (self.screen_dimension[0]/2,self.screen_dimension[1]/2)
        midright     = (self.screen_dimension[0],self.screen_dimension[1]/2)
        bottomleft   = (0,self.screen_dimension[1])
        midbottom    = (self.screen_dimension[0]/2,self.screen_dimension[1])
        bottomright  = (self.screen_dimension[0],self.screen_dimension[1])

        self.anchors = {"topleft":topleft, "midtop":midtop, "topright":topright,
                        "midleft":midleft, "center":center, "midright":midright,
                        "bottomleft":bottomleft, "midbottom":midbottom, "bottomright":bottomright}

    def save_changes(self):
        ########################################################
        ## Writes a default-formatted configuration string to ##
        ## the configuration file, according to the current   ##
        ## user specifications.                               ##
        ########################################################
        
        string = ""

        string += "#######################\n"
        string += "## CONFIGURATION     ##\n"
        string += "#######################\n"
        string += "## TEXT PARAMETERS   ##\n"
        string += "#######################\n"
        string += "font_antialias:      %d\n" %(int(self.font_antialias))
        string += "button_font:         %s\n" %(self.button_font)
        string += "button_foreground:   %d, %d, %d\n" %(self.button_font_color[0], self.button_font_color[1], self.button_font_color[2])
        string += "button_hover:        %d, %d, %d\n" %(self.button_hover_color[0], self.button_hover_color[1], self.button_hover_color[2])
        string += "button_shadow:       %d, %d, %d\n" %(self.button_shadow_color[0], self.button_shadow_color[1], self.button_shadow_color[2])
        string += "text_font:           %s\n" %(self.dialogue_font)        
        string += "text_foreground:     %d, %d, %d\n" %(self.dialogue_font_color[0], self.dialogue_font_color[1], self.dialogue_font_color[2])
        string += "backlog_foreground:  %d, %d, %d\n" %(self.dialogue_prev_color[0], self.dialogue_prev_color[1], self.dialogue_prev_color[2])
        string += "text_shadow:         %d, %d, %d\n" %(self.dialogue_shadow_color[0], self.dialogue_shadow_color[1], self.dialogue_shadow_color[2])
        string += "textbox_padding:     %d\n" %(self.textbox_margin)
        string += "choice_padding:      %d\n" %(self.option_margin)
        string += "text_fontsize:       %d\n" %(self.dialogue_fontsize)
        string += "button_fontsize_1:   %d\n" %(self.button0_fontsize)
        string += "button_fontsize_2:   %d\n" %(self.button1_fontsize)
        string += "button_fontsize_3:   %d\n" %(self.button2_fontsize)
        string += "widget_fontsize:     %d\n" %(self.datetime_fontsize)
        string += "savebox_fontsize:    %d\n\n" %(self.savebox_fontsize)
        string += "#######################\n"
        string += "## GRAPHIC HANDLING  ##\n"
        string += "#######################\n"
        string += "caption:             %s\n" %(self.caption)
        string += "is_fullscreen:       %d\n" %(int(self.fullscreen))
        string += "fade_color:          %d, %d, %d\n" %(self.fade_color[0], self.fade_color[1], self.fade_color[2])
        string += "window_size:         %d, %d\n" %(self.screen_dimension[0], self.screen_dimension[1])
        string += "logo_anchor:         %d, %d\n" %(self.title_pos[0], self.title_pos[1])
        string += "savebox_anchor:      %d, %d\n" %(self.save_list_pos[0], self.save_list_pos[1])
        string += "save_grid_dimension: %d, %d\n" %(self.grid_size[0], self.grid_size[1])
        string += "back_anchor:         %d, %d\n\n" %(self.to_title_pos[0], self.to_title_pos[1])
        string += "#######################\n"
        string += "## SOUND HANDLING    ##\n"
        string += "#######################\n"
        string += "hover_sound:         %s\n" %(self.button_sound_file)
        string += "select_sound:        %s\n" %(self.select_sound_file)
        string += "title_music:         %s\n" %(self.main_music)
        string += "volume:              %.3f\n\n" %(self.volume)
        string += "#######################\n"
        string += "## BUTTON HANDLING   ##\n"
        string += "#######################\n"
        string += "title_newgame:       %s, %d, %d\n" %(self.title_button_data[0][0], self.title_button_data[0][1], self.title_button_data[0][2])
        string += "title_load:          %s, %d, %d\n" %(self.title_button_data[1][0], self.title_button_data[1][1], self.title_button_data[1][2])
        string += "title_config:        %s, %d, %d\n" %(self.title_button_data[2][0], self.title_button_data[2][1], self.title_button_data[2][2])
        string += "title_quit:          %s, %d, %d\n\n" %(self.title_button_data[3][0], self.title_button_data[3][1], self.title_button_data[3][2])
        string += "volume_control:      %d, %d, %.3f\n" %(self.slider_pos[0][0], self.slider_pos[0][1], self.slider_values[0])
        string += "sound_control:       %d, %d, %.3f\n" %(self.slider_pos[1][0], self.slider_pos[1][1], self.slider_values[1])
        string += "speed_control:       %d, %d, %.3f\n\n" %(self.slider_pos[2][0], self.slider_pos[2][1], self.slider_values[2])
        string += "volume_label:        %s\n" %(self.config_button_data[4][0])
        string += "sound_label:         %s\n" %(self.config_button_data[5][0])
        string += "speed_label:         %s\n\n" %(self.config_button_data[6][0])
        string += "volume_label_anchor: %d, %d\n" %(self.config_button_data[4][1], self.config_button_data[4][2])
        string += "sound_label_anchor:  %d, %d\n" %(self.config_button_data[5][1], self.config_button_data[5][2])
        string += "speed_label_anchor:  %d, %d\n\n" %(self.config_button_data[6][1], self.config_button_data[6][2])
        string += "demo_text_anchor:    %d, %d\n" %(self.config_button_data[0][1], self.config_button_data[0][2])
        string += "demo_text:           %s\n\n" %(self.config_button_data[0][0])
        string += "fullscreen:          %s, %d, %d\n" %(self.config_button_data[1][0], self.config_button_data[1][1], self.config_button_data[1][2])
        string += "window:              %s, %d, %d\n" %(self.config_button_data[2][0], self.config_button_data[2][1], self.config_button_data[2][2])
        string += "save_config:         %s, %d, %d\n\n" %(self.config_button_data[3][0], self.config_button_data[3][1], self.config_button_data[3][2])
        string += "ingame_save:         %s, %d, %d\n" %(self.ingame_button_data[0][0], self.ingame_button_data[0][1], self.ingame_button_data[0][2])
        string += "ingame_load:         %s, %d, %d\n" %(self.ingame_button_data[1][0], self.ingame_button_data[1][1], self.ingame_button_data[1][2])
        string += "ingame_return:       %s, %d, %d\n" %(self.ingame_button_data[2][0], self.ingame_button_data[2][1], self.ingame_button_data[2][2])
        string += "ingame_quit:         %s, %d, %d\n" %(self.ingame_button_data[3][0], self.ingame_button_data[3][1], self.ingame_button_data[3][2])
        string += "ingame_back:         %s, %d, %d\n" %(self.ingame_button_data[4][0], self.ingame_button_data[4][1], self.ingame_button_data[4][2])
        string += "ingame_next:         %s, %d, %d\n" %(self.ingame_button_data[5][0], self.ingame_button_data[5][1], self.ingame_button_data[5][2])
        string += "ingame_skip:         %s, %d, %d\n" %(self.ingame_button_data[6][0], self.ingame_button_data[6][1], self.ingame_button_data[6][2])
        string += "ingame_auto:         %s, %d, %d\n\n" %(self.ingame_button_data[7][0], self.ingame_button_data[7][1], self.ingame_button_data[7][2])
        string += "#######################\n"
        string += "## GUI HANDLING      ##\n"
        string += "#######################\n"
        string += "textbox_anchor:      %d, %d\n" %(self.textbox_topleft[0], self.textbox_topleft[1])
        string += "widget_anchor:       %d, %d\n\n" %(self.datetime_topleft[0], self.datetime_topleft[1])
        string += "#######################\n"
        string += "## INITIAL SCRIPT    ##\n"
        string += "#######################\n"
        string += "root_scene:          %s\n" %(self.starting_scene)

        fi = open("data/data/config.nec", "w")
        fi.write(string)
        fi.close()
        
    def draw_splash(self):
        ######################################################
        ## Draws the splash screen when booting up the game ##
        ######################################################
        logo_alpha = 0

        ## Fade in the logo
        while logo_alpha < 255:
            logo_alpha += CONST.FADE
            self.clock.tick(60)
            self.screen.fill((255,255,255))
            self.logo.set_alpha(logo_alpha)
            self.screen.blit(self.logo, (0,0))
            pygame.display.flip()

            ## Allow the user to exit while fading in
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    self._quit()
                elif e.type == pygame.KEYDOWN:
                    if e.key == pygame.K_ESCAPE:
                        self._quit()

        ## Fade out the logo
        while logo_alpha > 0:
            logo_alpha -= CONST.FADE
            self.clock.tick(60)
            self.screen.fill((255,255,255))
            self.logo.set_alpha(logo_alpha)
            self.screen.blit(self.logo, (0,0))
            pygame.display.flip()

            ## Allow the user to exit while fading out
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    self._quit()
                elif e.type == pygame.KEYDOWN:
                    if e.key == pygame.K_ESCAPE:
                        self._quit()
            
        return

    def draw_title(self):
        ###################################################
        ## Draws the title and handles the game loop for ##
        ## the title screen itself.                      ##
        ###################################################
        
        self.title.set_alpha(255)
        self.title_alpha = 0
        new_game = False
        continue_game = False

        ## Loop as long as we haven't requested a new game or
        ## loaded a save file.
        
        while not new_game and not continue_game:
            self.clock.tick(60) ## 60 frames per second
            
            self.state = STATE.TITLE ## Establish state for FSM
            self.screen.blit(self.title, (0,0))

            ## Fade in title logo
            if self.title_alpha < 255:
                self.title_alpha += 15
                image = self.splash.copy()
                image.fill((255,255,255,self.title_alpha), None, pygame.BLEND_RGBA_MULT)
                self.screen.blit(image, (self.title_pos[0],self.title_pos[1]))
            else:
                self.screen.blit(self.splash, (self.title_pos[0],self.title_pos[1]))

            ## Draw the buttons
            self.draw_buttons()
            pygame.display.flip()

            ## Poll for user input
            for e in pygame.event.get():
                ## Safe quit method
                if e.type == pygame.QUIT:
                    self._quit()
                ## Same thing as above
                elif e.type == pygame.KEYDOWN:
                    if e.key == pygame.K_ESCAPE:
                        self._quit()
                elif e.type == pygame.MOUSEBUTTONDOWN:
                    ## Handle button logic
                    if self.handle_buttons():
                        return True

        return True

    def load_images(self):
        #########################
        ## Load all GUI images ##
        #########################
        
        self.button0 = pygame.image.load("data/images/gui/button_1.png").convert_alpha()
        self.button1 = pygame.image.load("data/images/gui/button_2.png").convert_alpha()
        self.button2 = pygame.image.load("data/images/gui/button_3.png").convert_alpha()
        self.savebox = pygame.image.load("data/images/gui/savebox.png").convert_alpha()
        self.datetime = pygame.image.load("data/images/gui/widget.png").convert_alpha()
        self.textbox = pygame.image.load("data/images/gui/textbox.png").convert_alpha()
        self.choicebox = pygame.image.load("data/images/gui/choicebox.png").convert_alpha()
        self.slidebar = pygame.image.load("data/images/gui/slidebar.png").convert_alpha()
        self.slider = pygame.image.load("data/images/gui/slider.png").convert_alpha()
        self.speedbox = pygame.image.load("data/images/gui/demobox.png").convert_alpha()

        self.logo = pygame.image.load("data/images/screen/logo.png").convert()
        self.title = pygame.image.load("data/images/screen/title_back.png").convert_alpha()
        self.config_screen = pygame.image.load("data/images/screen/config_back.png").convert_alpha()
        self.splash = pygame.image.load("data/images/screen/splash.png").convert_alpha()
            
        self.fade_mask = pygame.Surface(self.screen_dimension)
        self.fade_mask = self.fade_mask.convert()
        self.fade_mask.fill(self.fade_color)
        
    def init_defaults(self):
        ################################
        ## Default in-game parameters ##
        ################################
        
        self.is_skip = False        ## Whether we are skipping dialogue
        self.is_auto = False        ## Whether we are auto-advancing
        self.font_antialias = True  ## Whether the font is antialiased
        self.dialogue_font = "None" ## Name of the font for dialogue
        self.scroll_speed = 12      ## Text scrolling speed
        self.auto_pause = 60        ## Pause time in frames for auto mode
        self.button_font = "None"   ## Name of the font for buttons
        self.button_sound_file = "None" ## Sound effect when buttons are hovered
        self.button_sound = None        ## Sound object instance
        self.select_sound_file = "None" ## Sound effect when buttons are pressed
        self.select_sound = None        ## Sound object instance
        
        self.button_font_color = (128,128,128)  ## Button font color
        self.button_hover_color = (255,255,255) ## Button hover color
        self.button_shadow_color = (0,0,0)      ## Button shadow color
        
        self.dialogue_font_color = (255,255,255) ## Dialogue font color
        self.dialogue_prev_color = (128,128,128) ## Dialogue backlog color
        self.dialogue_shadow_color = (0,0,0)     ## Dialogue shadow color
        self.textbox_topleft = (0,0) ## Textbox topleft anchor position
        self.textbox_margin = 8      ## Margin from topleft corner
        self.option_margin = 8       ## Margin from topleft corner
        self.dialogue_fontsize = 16  ## Font size for dialogue
        self.button0_fontsize = 16   ## Font size for large button
        self.button1_fontsize = 16   ## Font size for medium button
        self.button2_fontsize = 16   ## Font size for small button
        self.datetime_fontsize = 16  ## Date-time indicator widget fontsize
        self.savebox_fontsize = 16   ## Save box fontsize
        self.title_pos = (0,0)       ## Topleft anchor for title image
        self.save_list_pos = (0,0)   ## Topleft anchor for savebox grid
        self.to_title_pos = (0,0)    ## Return to title button position
        self.datetime_topleft = (0,0) ## Topleft anchor for date-time widget
        self.ingame_buttons = []     ## List of in-game buttons
        self.title_buttons = []      ## List of title buttons
        self.config_buttons = []     ## List of configuration buttons
        self.config_sliders = []     ## List of configuration sliders
        self.slider_values = [0.5, 0.5, 0.5]  ## Default values for sliders
        self.slider_pos = [(0,0),(0,0),(0,0)] ## Positions for sliders
        self.grid_size = (2,7) ## Savebox grid dimensions

        ## Lists of buttons containing name and topleft positions
        self.title_button_data = [["New Game",0,0],["Continue",0,0],["Option",0,0],["Exit Game",0,0]]
        self.ingame_button_data = [["Save",0,0],["Load",0,0],["Title",0,0],["Quit",0,0],
                                   ["Back",0,0],["Next",0,0],["Skip",0,0],["Auto",0,0]]
        self.config_button_data = [["",0,0],["Fullscreen",0,0],["Windowed",0,0],["Save",0,0],
                                   ["Volume",0,0], ["Sound",0,0], ["Speed",0,0]]

        self.starting_scene = "000" ## Filename for starting scene
        self.main_music = "None"    ## Filename for title screen BGM

        ## Generate variables named "$aa" to "$zz"
        self.variable_strings = []
        for c in ascii_lowercase:
            for d in ascii_lowercase:
                self.variable_strings.append("$%s%s" %(c,d))

    def init_config(self):
        #############################
        ## Load configuration file ##
        #############################
        config = open("data/data/config.nec", "r").readlines()

        for line in config:
            ## Skip any and all comments
            if line.startswith("#"):
                continue

            ## Dialogue font
            elif line.startswith("text_font:"):
                temp = line.split(":")[1].lstrip().rstrip()
                self.dialogue_font = temp

            ## Button font
            elif line.startswith("button_font:"):
                temp = line.split(":")[1].lstrip().rstrip()
                self.button_font = temp

            ## Button hover sound effect
            elif line.startswith("hover_sound:"):
                temp = line.split(":")[1].lstrip().rstrip()
                self.button_sound_file = temp
                if self.button_sound_file != "None":
                    self.button_sound = pygame.mixer.Sound("data/sound/" + self.button_sound_file + ".wav")

            ## Button press sound effect
            elif line.startswith("select_sound:"):
                temp = line.split(":")[1].lstrip().rstrip()
                self.select_sound_file = temp
                if self.select_sound_file != "None":
                    self.select_sound = pygame.mixer.Sound("data/sound/" + self.select_sound_file + ".wav")

            ## Button text font color
            elif line.startswith("button_foreground:"):
                temp = line.split(":")[1].split(",")
                self.button_font_color = [int(temp[0]),int(temp[1]),int(temp[2])]

            ## Button text shadow color
            elif line.startswith("button_shadow:"):
                temp = line.split(":")[1].split(",")
                self.button_shadow_color = [int(temp[0]),int(temp[1]),int(temp[2])]

            ## Button text hover color
            elif line.startswith("button_hover:"):
                temp = line.split(":")[1].split(",")
                self.button_hover_color = [int(temp[0]),int(temp[1]),int(temp[2])]

            ## Dialogue font color
            elif line.startswith("text_foreground:"):
                temp = line.split(":")[1].split(",")
                self.dialogue_font_color = [int(temp[0]),int(temp[1]),int(temp[2])]

            ## Dialogue backlog color
            elif line.startswith("backlog_foreground:"):
                temp = line.split(":")[1].split(",")
                self.dialogue_prev_color = [int(temp[0]),int(temp[1]),int(temp[2])]

            ## Dialogue shadow color
            elif line.startswith("text_shadow:"):
                temp = line.split(":")[1].split(",")
                self.dialogue_shadow_color = [int(temp[0]),int(temp[1]),int(temp[2])]

            ## Textbox anchoring position
            elif line.startswith("textbox_anchor:"):
                temp = line.split(":")[1].split(",")
                self.textbox_topleft = [int(temp[0]),int(temp[1])]

            ## Textbox margin from topleft
            elif line.startswith("textbox_padding:"):
                temp = line.split(":")[1]
                self.textbox_margin = int(temp)

            ## Choice box topleft padding
            elif line.startswith("choice_padding:"):
                temp = line.split(":")[1]
                self.option_margin = int(temp)

            ## Dialogue fontsize
            elif line.startswith("text_fontsize:"):
                temp = line.split(":")[1]
                self.dialogue_fontsize = int(temp)

            ## Button fontsize for large buttons
            elif line.startswith("button_fontsize_1:"):
                temp = line.split(":")[1]
                self.button0_fontsize = int(temp)

            ## Button fontsize for medium buttons
            elif line.startswith("button_fontsize_2:"):
                temp = line.split(":")[1]
                self.button1_fontsize = int(temp)

            ## Button fontsize for small buttons
            elif line.startswith("button_fontsize_3:"):
                temp = line.split(":")[1]
                self.button2_fontsize = int(temp)

            ## Date-time widget fontsize
            elif line.startswith("widget_fontsize:"):
                temp = line.split(":")[1]
                self.datetime_fontsize = int(temp)

            ## Savebox fontsize
            elif line.startswith("savebox_fontsize:"):
                temp = line.split(":")[1]
                self.savebox_fontsize = int(temp)

            ## Date-time widget anchor topleft
            elif line.startswith("widget_anchor:"):
                temp = line.split(":")[1].split(",")
                self.datetime_topleft = (int(temp[0]), int(temp[1]))

            ## Title screen logo anchor topleft
            elif line.startswith("logo_anchor:"):
                temp = line.split(":")[1].split(",")
                self.title_pos = (int(temp[0]), int(temp[1]))

            ## Savebox anchoring position
            elif line.startswith("savebox_anchor:"):
                temp = line.split(":")[1].split(",")
                self.save_list_pos = (int(temp[0]), int(temp[1]))

            ## Back button anchoring position
            elif line.startswith("back_anchor:"):
                temp = line.split(":")[1].split(",")
                self.to_title_pos = (int(temp[0]), int(temp[1]))

            ## Label for volume controller
            elif line.startswith("volume_label:"):
                temp = line.split(":")[1].lstrip().rstrip()
                self.config_button_data[4][0] = temp

            ## Label for sound controller
            elif line.startswith("sound_label:"):
                temp = line.split(":")[1].lstrip().rstrip()
                self.config_button_data[5][0] = temp

            ## Label for text scroll controller
            elif line.startswith("speed_label:"):
                temp = line.split(":")[1].lstrip().rstrip()
                self.config_button_data[6][0] = temp

            ## Label anchoring position for volume controller
            elif line.startswith("volume_label_anchor:"):
                temp = line.split(":")[1].split(",")
                self.config_button_data[4][1] = int(temp[0])
                self.config_button_data[4][2] = int(temp[1])

            ## Label anchoring position for sound controller
            elif line.startswith("sound_label_anchor:"):
                temp = line.split(":")[1].split(",")
                self.config_button_data[5][1] = int(temp[0])
                self.config_button_data[5][2] = int(temp[1])

            ## Label anchoring position for text scroll controller
            elif line.startswith("speed_label_anchor:"):
                temp = line.split(":")[1].split(",")
                self.config_button_data[6][1] = int(temp[0])
                self.config_button_data[6][2] = int(temp[1])

            ## BGM volume control button and slider setup
            elif line.startswith("volume_control:"):
                temp = line.split(":")[1].split(",")
                pos1 = [int(temp[0]),int(temp[1])]
                pos2 = [int(float(temp[2]) * self.slidebar.get_width()), int(temp[1])-self.slider.get_height()/4]
                new_button = Button("", self.button_font, self.font_antialias, self.button2_fontsize, self.slider, pos2, -999, fadein=True, anchor="topleft")
                new_slider = Slider(self.slidebar, pos1, new_button, 0, True)
                self.config_sliders.append(new_slider)
                self.slider_values[0] = float(temp[2])
                pygame.mixer.music.set_volume(float(temp[2]))
                self.volume = float(temp[2])
                self.slider_pos[0] = pos1

            ## SFX volume control button and slider setup
            elif line.startswith("sound_control:"):
                temp = line.split(":")[1].split(",")
                pos1 = [int(temp[0]),int(temp[1])]
                pos2 = [int(float(temp[2]) * self.slidebar.get_width()), int(temp[1])-self.slider.get_height()/4]
                new_button = Button("", self.button_font, self.font_antialias, self.button2_fontsize, self.slider, pos2, -999, True, anchor="topleft")
                new_slider = Slider(self.slidebar, pos1, new_button, 1, True)
                self.config_sliders.append(new_slider)
                self.slider_values[1] = float(temp[2])
                self.slider_pos[1] = pos1

            ## Text scroll control button and slider setup
            elif line.startswith("speed_control:"):
                temp = line.split(":")[1].split(",")
                pos1 = [int(temp[0]),int(temp[1])]
                pos2 = [int(float(temp[2]) * self.slidebar.get_width()), int(temp[1])-self.slider.get_height()/4]
                new_button = Button("", self.button_font, self.font_antialias, self.button2_fontsize, self.slider, pos2, -999, True, anchor="topleft")
                new_slider = Slider(self.slidebar, pos1, new_button, 2, True)
                self.config_sliders.append(new_slider)
                self.slider_values[2] = float(temp[2])
                self.scroll_speed = float(temp[2])*CONST.SPEED_RANGE
                self.slider_pos[2] = pos1

            ## Scroll speed demo text anchoring position
            elif line.startswith("demo_text_anchor:"):
                temp = line.split(":")[1].split(",")
                pos = [int(temp[0]),int(temp[1])]
                self.config_button_data[0] = ["" if len(self.config_button_data[0][0]) == 0 else self.config_button_data[0][0], pos[0], pos[1]]

            ## Scroll speed demo text string
            elif line.startswith("demo_text:"):
                temp = line.split(":")[1].lstrip().rstrip()
                self.config_button_data[0][0] = temp

            ## Fullscreen toggle button
            elif line.startswith("fullscreen:"):
                temp = line.split(":")[1].split(",")
                pos = [int(temp[1]),int(temp[2])]
                label = temp[0].lstrip().rstrip()
                new_button = Button(label, self.button_font, self.font_antialias, self.button0_fontsize, self.button0, pos, 0,
                                    sfx=self.button_sound, ping=self.select_sound, color=self.button_font_color, shadow=self.button_shadow_color,
                                    hover=self.button_hover_color, fadein=True, anchor="center")
                self.config_button_data[1] = [label, pos[0], pos[1]]
                self.config_buttons.append(new_button)

            ## Windowed mode toggle button
            elif line.startswith("window:"):
                temp = line.split(":")[1].split(",")
                pos = [int(temp[1]),int(temp[2])]
                label = temp[0].lstrip().rstrip()
                new_button = Button(label, self.button_font, self.font_antialias, self.button0_fontsize, self.button0, pos, 1, sfx=self.button_sound,
                                    ping=self.select_sound, color=self.button_font_color, shadow=self.button_shadow_color, hover=self.button_hover_color,
                                    fadein=True, anchor="center")
                self.config_button_data[2] = [label, pos[0], pos[1]]
                self.config_buttons.append(new_button)

            ## Save configuration changes button
            elif line.startswith("save_config:"):
                temp = line.split(":")[1].split(",")
                pos = [int(temp[1]),int(temp[2])]
                label = temp[0].lstrip().rstrip()
                new_button = Button(label, self.button_font, self.font_antialias, self.button0_fontsize, self.button0, pos, 2, sfx=self.button_sound,
                                    ping=self.select_sound, color=self.button_font_color, shadow=self.button_shadow_color, hover=self.button_hover_color,
                                    fadein=True, anchor="center")
                self.config_button_data[3] = [label, pos[0], pos[1]]
                self.config_buttons.append(new_button)

            ## In-game save button
            elif line.startswith("ingame_save:"):
                temp = line.split(":")[1].split(",")
                pos = [int(temp[1]),int(temp[2])]
                label = temp[0].lstrip().rstrip()
                new_button = Button(label, self.button_font, self.font_antialias, self.button2_fontsize, self.button2, pos, 0, sfx=self.button_sound,
                                    ping=self.select_sound, color=self.button_font_color, shadow=self.button_shadow_color, hover=self.button_hover_color)
                self.ingame_buttons.append(new_button)
                self.ingame_button_data[0] = [label, int(temp[1]), int(temp[2])]

            ## In-game load button
            elif line.startswith("ingame_load:"):
                temp = line.split(":")[1].split(",")
                pos = [int(temp[1]),int(temp[2])]
                label = temp[0].lstrip().rstrip()
                new_button = Button(label, self.button_font, self.font_antialias, self.button2_fontsize, self.button2, pos, 1, sfx=self.button_sound,
                                    ping=self.select_sound, color=self.button_font_color, shadow=self.button_shadow_color, hover=self.button_hover_color)
                self.ingame_buttons.append(new_button)
                self.ingame_button_data[1] = [label, int(temp[1]), int(temp[2])]

            ## In-game return to title button
            elif line.startswith("ingame_return:"):
                temp = line.split(":")[1].split(",")
                pos = [int(temp[1]),int(temp[2])]
                label = temp[0].lstrip().rstrip()
                new_button = Button(label, self.button_font, self.font_antialias, self.button2_fontsize, self.button2, pos, 2, sfx=self.button_sound,
                                    ping=self.select_sound, color=self.button_font_color, shadow=self.button_shadow_color, hover=self.button_hover_color)
                self.ingame_buttons.append(new_button)
                self.ingame_button_data[2] = [label, int(temp[1]), int(temp[2])]

            ## In-game force quit button
            elif line.startswith("ingame_quit:"):
                temp = line.split(":")[1].split(",")
                pos = [int(temp[1]),int(temp[2])]
                label = temp[0].lstrip().rstrip()
                new_button = Button(label, self.button_font, self.font_antialias, self.button2_fontsize, self.button2, pos, 3, sfx=self.button_sound,
                                    ping=self.select_sound, color=self.button_font_color, shadow=self.button_shadow_color, hover=self.button_hover_color)
                self.ingame_buttons.append(new_button)
                self.ingame_button_data[3] = [label, int(temp[1]), int(temp[2])]

            ## In-game view backlog button
            elif line.startswith("ingame_back:"):
                temp = line.split(":")[1].split(",")
                pos = [int(temp[1]),int(temp[2])]
                label = temp[0].lstrip().rstrip()
                new_button = Button(label, self.button_font, self.font_antialias, self.button2_fontsize, self.button2, pos, 4, sfx=self.button_sound,
                                    ping=self.select_sound, color=self.button_font_color, shadow=self.button_shadow_color, hover=self.button_hover_color)
                self.ingame_buttons.append(new_button)
                self.ingame_button_data[4] = [label, int(temp[1]), int(temp[2])]

            ## In-game dialogue advance button
            elif line.startswith("ingame_next:"):
                temp = line.split(":")[1].split(",")
                pos = [int(temp[1]),int(temp[2])]
                label = temp[0].lstrip().rstrip()
                new_button = Button(label, self.button_font, self.font_antialias, self.button2_fontsize, self.button2, pos, 5, sfx=self.button_sound,
                                    ping=self.select_sound, color=self.button_font_color, shadow=self.button_shadow_color, hover=self.button_hover_color)
                self.ingame_buttons.append(new_button)
                self.ingame_button_data[5] = [label, int(temp[1]), int(temp[2])]

            ## In-game dialogue skip button
            elif line.startswith("ingame_skip:"):
                temp = line.split(":")[1].split(",")
                pos = [int(temp[1]),int(temp[2])]
                label = temp[0].lstrip().rstrip()
                new_button = Button(label, self.button_font, self.font_antialias, self.button2_fontsize, self.button2, pos, 6, sfx=self.button_sound,
                                    ping=self.select_sound, color=self.button_font_color, shadow=self.button_shadow_color, hover=self.button_hover_color)
                self.ingame_buttons.append(new_button)
                self.ingame_button_data[6] = [label, int(temp[1]), int(temp[2])]

            ## In-game dialogue auto-advance button
            elif line.startswith("ingame_auto:"):
                temp = line.split(":")[1].split(",")
                pos = [int(temp[1]),int(temp[2])]
                label = temp[0].lstrip().rstrip()
                new_button = Button(label, self.button_font, self.font_antialias, self.button2_fontsize, self.button2, pos, 7, sfx=self.button_sound,
                                    ping=self.select_sound, color=self.button_font_color, shadow=self.button_shadow_color, hover=self.button_hover_color)
                self.ingame_buttons.append(new_button)
                self.ingame_button_data[7] = [label, int(temp[1]), int(temp[2])]

            ## Savebox grid dimensions
            elif line.startswith("save_grid_dimension:"):
                temp = line.split(":")[1].split(",")
                self.grid_size = [int(temp[0]),int(temp[1])]

            ## Title screen newgame button
            elif line.startswith("title_newgame:"):
                temp = line.split(":")[1].split(",")
                pos = [int(temp[1]),int(temp[2])]
                label = temp[0].lstrip().rstrip()
                new_button = Button(label, self.button_font, self.font_antialias, self.button0_fontsize, self.button0, pos, 0, sfx=self.button_sound,
                                    ping=self.select_sound, color=self.button_font_color, shadow=self.button_shadow_color, hover=self.button_hover_color,
                                    fadein=True)
                self.title_buttons.append(new_button)
                self.title_button_data[0] = [label, int(temp[1]), int(temp[2])]

            ## Title screen load button
            elif line.startswith("title_load:"):
                temp = line.split(":")[1].split(",")
                pos = [int(temp[1]),int(temp[2])]
                label = temp[0].lstrip().rstrip()
                new_button = Button(label, self.button_font, self.font_antialias, self.button0_fontsize, self.button0, pos, 1, sfx=self.button_sound,
                                    ping=self.select_sound, color=self.button_font_color, shadow=self.button_shadow_color, hover=self.button_hover_color,
                                    fadein=True)
                self.title_buttons.append(new_button)
                self.title_button_data[1] = [label, int(temp[1]), int(temp[2])]

            ## Title screen configuration button
            elif line.startswith("title_config:"):
                temp = line.split(":")[1].split(",")
                pos = [int(temp[1]),int(temp[2])]
                label = temp[0].lstrip().rstrip()
                new_button = Button(label, self.button_font, self.font_antialias, self.button0_fontsize, self.button0, pos, 2, sfx=self.button_sound,
                                    ping=self.select_sound, color=self.button_font_color, shadow=self.button_shadow_color, hover=self.button_hover_color,
                                    fadein=True)
                self.title_buttons.append(new_button)
                self.title_button_data[2] = [label, int(temp[1]), int(temp[2])]

            ## Title screen quit button
            elif line.startswith("title_quit:"):
                temp = line.split(":")[1].split(",")
                pos = [int(temp[1]),int(temp[2])]
                label = temp[0].lstrip().rstrip()
                new_button = Button(label, self.button_font, self.font_antialias, self.button0_fontsize, self.button0, pos, 3, sfx=self.button_sound,
                                    ping=self.select_sound, color=self.button_font_color, shadow=self.button_shadow_color, hover=self.button_hover_color,
                                    fadein=True)
                self.title_buttons.append(new_button)
                self.title_button_data[3] = [label, int(temp[1]), int(temp[2])]

            ## Title screen BGM loading
            elif line.startswith("title_music:"):
                temp = line.split(":")[1].lstrip().rstrip()
                try:
                    pygame.mixer.music.load("data/music/" + temp + ".wav")
                    pygame.mixer.music.set_volume(self.volume)
                    pygame.mixer.music.play(-1)
                    self.main_music = temp
                except Exception as e:
                    pass

            ## Scene filename to begin playback from
            elif line.startswith("root_scene:"):
                temp = line.split(":")[1].lstrip().rstrip()
                self.starting_scene = temp

        ## Create BGM volume control label
        new_button = Button(self.config_button_data[0][0], self.dialogue_font, self.font_antialias, self.dialogue_fontsize, self.speedbox,
                            (self.config_button_data[0][1], self.config_button_data[0][2]), -1024, color=self.dialogue_font_color,
                            shadow=self.dialogue_shadow_color, fadein=True, scrollable=True, speed=self.scroll_speed, anchor="topleft", shadow_type=2)
        self.config_buttons.append(new_button)

        ## Create SFX volume control label
        new_button = Button(self.config_button_data[4][0], self.button_font, self.font_antialias, self.button0_fontsize, self.button0,
                            (self.config_button_data[4][1], self.config_button_data[4][2]), -999, color=self.dialogue_font_color,
                            shadow=self.button_shadow_color, fadein=True, anchor="center")
        self.config_buttons.append(new_button)

        ## Create text scroll volume conrol label
        new_button = Button(self.config_button_data[5][0], self.button_font, self.font_antialias, self.button0_fontsize, self.button0,
                            (self.config_button_data[5][1], self.config_button_data[5][2]), -999, color=self.dialogue_font_color,
                            shadow=self.button_shadow_color, fadein=True, anchor="center")
        self.config_buttons.append(new_button)

        ## Create demo text scroll label
        new_button = Button(self.config_button_data[6][0], self.button_font, self.font_antialias, self.button0_fontsize, self.button0,
                            (self.config_button_data[6][1], self.config_button_data[6][2]), -999, color=self.dialogue_font_color,
                            shadow=self.button_shadow_color, fadein=True, anchor="center")
        self.config_buttons.append(new_button)

    def init_members(self):
        ##########################################################
        ## Member variable initialization for in-game variables ##
        ##########################################################
        
        self.char_im           = [[] for i in range(8)] ## List of character images
        self.cur_chars         = [] ## List of character objects currently on-screen
        self.cur_char_pos      = 0  ## Character position
        self.index             = 0  ## Current index into the scene file
        self.new_anchor        = self.anchors["center"] ## Current anchoring position
        self.old_anchor        = self.anchors["center"] ## Old anchoring position
        self.new_anchor_string = "center" ## Current anchor string label
        self.old_anchor_string = "center" ## Old anchor string label

        self.cur_dialogue    = []     ## List of strings in current dialogue
        self.cur_text_index  = 0      ## Index into the current dialogue string
        self.cur_name_text   = None   ## Text object for current name
        self.datetime_display = None  ## Date-time widget object
        self.ingame_date     = "null" ## Date-time widget string

        self.prev_dialogue   = []     ## List of previous dialogue strings
        self.prev_text_index = -1     ## Index into the previous dialogue string
        self.max_prev_index  = -1     ## Maximum index at which previous dialogue occurs
        self.prev_name_text  = []     ## List of previous name entries
        self.cur_scene       = None   ## Current scene file
        self.old_scene       = None   ## Old scene file
        self.is_process_text = False  ## Whether or not we are processing scene text
        self.cur_scene_file  = ["null", "null"] ## Strings for the current scene filename

        self.cur_options  = [] ## List of dialogue options
        self.cur_choice   = -1 ## Current choice index

        self.state = STATE.READ ## Finite state machine state
        self.advance = False    ## Whether or not we allow advancement into the scene file
        self.finished_scene = False ## Whether or not we've finished the scene
        
        self.hide_alpha = 255        ## Alpha channel value for hiding GUI
        self.target_hide_alpha = 255 ## Target alpha channel value
        self.has_set_hide = False    ## Whether or not we've requested a hide operation

        self.fade_alpha = 0              ## Alpha channel value for fading in and out
        self.fade_rate = 5               ## Fade rate in alpha channel units per frame
        self.zoom_scale = 1.0            ## Current scale at which background image is rendered
        self.target_scale = 1.0          ## Target scale at which backgroudn image should end up
        self.zoom_rate = 0.1             ## Rate to interpolate between target_scale and zoom_scale
        self.temp_scene = None           ## Temporary scene object holder
        self.has_loaded_scene = False    ## Whether or not we've requested a load scene operation
        self.has_unloaded_scene = False  ## Whether or not we've requested a delete scene operation

        self.wait_count = 0       ## How long to wait
        self.has_set_wait = False ## Whether or not we've requested a wait operation

        self.is_shake = False ## Whether or not we're shaking the screen

        self.auto_count = 0       ## How long to wait in auto-advance mode
        self.has_set_auto = False ## Whether or not we've toggled auto-advance mode

        self.variables = {key:0 for key in self.variable_strings} ## Dictionary of all in-game variables
        self.shake_range = [0,0] ## Shake magnitude in X and Y direction

        self.is_fade_in = False  ## Whether we're fading in a scene
        self.is_fade_out = False ## Whether we're fading out a scene
        self.is_zoom_in = False  ## Whether we're zooming into a scene
        self.is_zoom_out = False ## Whether we're zooming out of a scene

        pygame.mixer.music.stop() ## Force stop any accidental music playing 
        self.sound = None ## Current sound effect object

        self.is_comment = False ## Whether or not we've parsed a comment
        self.is_process_choice = False ## Whether or not we're processing a dialogue branch choice
        
    def interpret_line(self, line):
        ###########################################################
        ## Meat of the engine that parses the scripting language ##
        ###########################################################

        ## Get rid of all comments, which can begin with a # anywhere in the lien
        line = line.lstrip().split("#")[0].rstrip()
        self.is_comment = False

        ## Get rid of all comments like above
        if len(line) == 0 and not self.is_process_text:
            self.is_comment = True
            return True

        ## Quit the game
        elif line.startswith(".forcequit"):
            self.running = False
            return True

        ## Load a character into memory
        elif line.startswith(".load"):
            ## Parse out the parentheses
            temp = line.replace(")","").split("(")[1].split(",")
            ## If we have no parameters passed
            if len(temp) < 2:
                try:
                    temp = temp[0].lstrip().rstrip()
                    ## Clear all characters from current scene
                    if (temp.isdigit() or temp == '-1') and int(temp) < len(self.cur_chars):
                        clear = True
                        ## Fade them out, then remove them from memory
                        for char in self.cur_chars:
                            if int(temp) == char.index or int(temp) == -1:
                                char.alpha -= 24
                                if char.alpha < 0:
                                    self.cur_chars.remove(char)
                                    char.alpha = 0
                                else:
                                    clear = False
                        if clear:
                            if int(temp) == -1:
                                self.cur_chars = []
                            return True
                        return False
                    return True
                except:
                    ## Raise custom exception into terminal
                    self.raise_exception(200)

            ## If we have at least one parameter passed
            path = "data/images/char/%s/" %(temp[0].lstrip().rstrip())

            ## Attempt to load the images from the expected directory
            for filename in glob.glob(os.path.join(path, "*.png")):
                try:
                    im = pygame.image.load(filename).convert_alpha()
                    self.char_im[int(temp[1])].append(im)
                except:
                    ## Raise custom exception into terminal
                    self.raise_exception(50, arg=filename)

            return True

        ## Start a line of dialogue text
        elif line.startswith(".text"):
            ## If we are currently processing commands, not raw text strings...
            if not self.is_process_text:
                ## Reset dialogue box
                self.cur_dialogue    = []
                self.cur_text_index  = 0
                self.advance = False

                ## Parse out the parentheses
                temp = line.replace(")","").split("(")[1].split(",")
                cur_char  = 0
                cur_em    = 0
                cur_pos   = 0
                cur_name  = ""
                ignore    = True
                skip      = False

                for phrase in temp:
                    ## Parse out the parameters
                    keywords = phrase.lstrip().rstrip().split("=")
                    param = keywords[0].lstrip().rstrip()
                    value = keywords[1].lstrip().rstrip()

                    ## Character image bank detected
                    if param == "char":
                        ignore = False
                        try:
                            cur_char = int(value)
                        except:
                            ## Raise custom exception
                            self.raise_exception(101)

                    ## Specific character image detected
                    elif param == "sub":
                        try:
                            cur_em = int(value)
                        except:
                            ## Raise custom exception
                            self.raise_exception(102)

                    ## Character horizontal pos detected
                    elif param == "pos":
                        try:
                            cur_pos = int(value)
                        except:
                            ## Raise custom exception
                            self.raise_exception(103)

                    ## Character name detected
                    elif param == "name":
                        cur_name = value

                    ## No character detected
                    elif param == "skip":
                        skip = True

                ## If any of the above parameters were supplied...
                if not ignore:
                    try:
                        ## Load character image
                        temp = self.char_im[cur_char][cur_em]
                    except:
                        ## Raise exception if character image not found
                        if not self.char_im[cur_char] or cur_char > len(self.char_im) - 1:
                            self.raise_exception(51, str(cur_char))
                        elif cur_em > len(self.char_im[cur_char]) - 1:
                            self.raise_exception(52, str(cur_em))

                    ## Calculate x-pos
                    pos  = [cur_pos * self.screen_dimension[0]/16, self.screen_dimension[1]]

                    ## Don't draw a new character if he/she is currently in the scene
                    if len(self.cur_chars) == 0:
                        add_new = True
                    elif self.cur_chars[-1].em != cur_em or self.cur_chars[-1].name != cur_name or self.cur_chars[-1].pos != pos:
                        add_new = True
                    else:
                        add_new = False

                    ## Don't draw a new character if he/she is currently in the scene
                    if add_new:
                        new_char = Character(temp, cur_em, pos, cur_name, cur_char, cur_pos)
                        self.cur_chars.append(new_char)
                        if len(self.cur_chars) > 8:
                            self.cur_chars = self.cur_chars[1:]

                ## If we have new text to put into the buffer...
                if not skip:
                    ## Add the current text into the previous text buffer
                    self.prev_dialogue.append([])
                    self.prev_text_index += 1
                    self.max_prev_index += 1

                    ## Set up the text objects to be displayed on-screen
                    pos = [self.textbox_margin, self.textbox_margin + self.cur_text_index * self.dialogue_fontsize]
                    name_text = Text(cur_name, self.dialogue_font, self.font_antialias, pos, self.dialogue_fontsize, self.dialogue_font_color,
                                     self.dialogue_shadow_color, False, shadow_type=2)

                    self.cur_name_text = name_text
                    self.prev_name_text.append(name_text)

                ## Start processing raw strings
                self.is_process_text = True
            
            else:
                ## If we encountered a terminator command...
                if not self.is_skip and not self.is_auto:
                    self.state = STATE.READ ## Allow player to pause and read
                self.cur_text_index = 0
                if not self.advance:
                    return False
                self.advance = False
                self.is_process_text = False
                
            return True

        ## Wait a few frames before proceeding with game
        elif line.startswith(".wait"):
            ## Parse out parameters
            temp = line.replace(")","").split("(")[1]
            if not self.has_set_wait:
                try:
                    self.wait_count = int(temp)
                except:
                    self.raise_exception(104)
                self.has_set_wait = True

            ## Tick down the counter
            self.wait_count -= 1
            if self.wait_count <= 0:
                self.wait_count = 0
                self.has_set_wait = False
                return True
            return False

        ## Shake screen in either X or Y axis
        elif line.startswith(".shake"):
            ## parse Out parameters
            temp = line.replace(")","").split("(")
            ## Turn off shaking if empty parameters supplied
            if len(temp) < 2:
                self.is_shake = False
                self.shake_range = [0,0]
                return True

            ## Continue shaking otherwise
            self.is_shake = True
            try:
                temp = temp[1].split(",")
                self.shake_range = [int(temp[0]), int(temp[1])]
            except:
                self.raise_exception(105)
                
            return True

        ## Start a branching dialogue options section
        elif line.startswith(".choice"):
            ## If we're not processing choices currently
            if not self.is_process_choice:
                self.state = STATE.READ
                self.advance = False
                self.cur_options = []
                self.cur_choice = -1
                self.is_process_choice = True
            else:
                ## Processing choices until we jump to the correct branch
                self.state = STATE.CHOOSE
                if self.cur_choice == -1:
                    return False
                self.is_process_choice = False
                self.state = STATE.READ
                self.advance = False
            return True

        ## If we are processing choices, seek until the correct branch is found
        elif len(line) >= 2 and line[0].isdigit() and self.is_process_choice:
            temp = line.split(":")
            text = temp[1].lstrip().rstrip()
            pos = [self.screen_dimension[0]/2, (len(self.cur_options)+1)*int(self.choicebox.get_height()*1.2) + self.screen_dimension[1]/8]
            choice = Choice(text, self.dialogue_font, self.font_antialias, self.choicebox, int(temp[0]), pos)
            self.cur_options.append(choice)
            return True

        ## Choice branch conditional statement
        elif line.startswith(".branch"):

            ## Parse out the parameters before the colon
            temp = line.replace(":","").lstrip().rstrip().split(" ")
            if len(temp) > 1:
                try:
                    if int(temp[1]) == self.cur_choice:
                        self.cur_choice = -1
                        return True
                    self.state = STATE.OPT_BRANCH
                except:
                    ## Raise custom exception
                    self.raise_exception(106)
            else:
                self.state = STATE.READ
                
            return True

        ## Set anchoring position for zooming in and out
        elif line.startswith(".setanchor"):
            temp = line.replace(")","").split("(")[1].lstrip().rstrip()
            self.new_anchor = self.anchors[temp]
            self.new_anchor_string = temp
            return True

        ## Transition into a scene image
        elif line.startswith(".scenein"):
            if not self.has_loaded_scene:
                ## Parse out parameters
                temp = line.replace(")","").split("(")[1].split(",")
                if len(temp) < 2:
                    ## Raise exception
                    self.raise_exception(200)
                folder = temp[0].lstrip().rstrip()
                file   = temp[1].lstrip().rstrip()

                ## If we have at least as many parameters as required
                if len(temp) > 2:
                    type = temp[2].lstrip().rstrip()
                    ## Fade in the image
                    if type == "fade":
                        self.is_fade_in = True
                    ## Zoom in the image
                    elif type == "zoomin":
                        self.is_zoom_in = True
                        ## Allow for zoom scale, target scale, and zoom rate
                        ## to be supplied as optional parameters
                        if len(temp) > 3:
                            scale = temp[3].lstrip().rstrip() 
                            try:
                                self.zoom_scale = float(scale)
                            except:
                                self.raise_exception(100)
                        if len(temp) > 4:
                            scale = temp[4].lstrip().rstrip() 
                            try:
                                self.target_scale = float(scale)
                            except:
                                self.raise_exception(100)
                        if len(temp) > 5:
                            rate = temp[5].lstrip().rstrip() 
                            try:
                                self.zoom_rate = float(rate)
                            except:
                                self.raise_exception(100)
                    ## Zoom out the image
                    elif type == "zoomout":
                        self.is_zoom_out = True
                        ## Allow zoom scale, zoom rate, and target scale
                        ## to be supplied as optional parameters
                        if len(temp) > 3:
                            scale = temp[3].lstrip().rstrip() 
                            try:
                                self.zoom_scale = float(scale)
                            except:
                                self.raise_exception(100)
                        if len(temp) > 4:
                            scale = temp[4].lstrip().rstrip() 
                            try:
                                self.target_scale = float(scale)
                            except:
                                self.raise_exception(100)
                        if len(temp) > 5:
                            rate = temp[5].lstrip().rstrip() 
                            try:
                                self.zoom_rate = float(rate)
                            except:
                                self.raise_exception(100)
                    ## Combination fade and zoom in
                    elif type == "fadezoomin":
                        self.is_fade_in = True
                        self.is_zoom_in = True
                        if len(temp) > 3:
                            scale = temp[3].lstrip().rstrip() 
                            try:
                                self.zoom_scale = float(scale)
                            except:
                                self.raise_exception(100)
                        if len(temp) > 4:
                            scale = temp[4].lstrip().rstrip() 
                            try:
                                self.target_scale = float(scale)
                            except:
                                self.raise_exception(100)
                        if len(temp) > 5:
                            rate = temp[5].lstrip().rstrip() 
                            try:
                                self.zoom_rate = float(rate)
                            except:
                                self.raise_exception(100)
                    ## Combination fade and zoom out
                    elif type == "fadezoomout":
                        self.is_fade_in = True
                        self.is_zoom_out = True
                        if len(temp) > 3:
                            scale = temp[3].lstrip().rstrip() 
                            try:
                                self.zoom_scale = float(scale)
                            except:
                                self.raise_exception(100)
                        if len(temp) > 4:
                            scale = temp[4].lstrip().rstrip() 
                            try:
                                self.target_scale = float(scale)
                            except:
                                self.raise_exception(100)
                        if len(temp) > 5:
                            rate = temp[5].lstrip().rstrip() 
                            try:
                                self.zoom_rate = float(rate)
                            except:
                                self.raise_exception(100)
                try:
                    ## Fade scenes over one another
                    if self.cur_scene != None:
                        self.old_scene = self.cur_scene.copy().convert()
                    self.cur_scene = pygame.image.load("data/images/%s/%s.png" %(folder,file)).convert()
                    self.cur_scene_file = [folder, file]
                    self.has_loaded_scene = True

                    self.temp_scene = self.cur_scene.copy().convert()
                    
                except:
                    ## Raise custom exception
                    self.raise_exception(50)

            pre_done = False ## Variable to manage zooming and fading states
            if self.is_fade_in:
                ## Fade in the scene for real
                if self.fade_alpha < 255:
                    self.fade_alpha += self.fade_rate
                    self.temp_scene.set_alpha(self.fade_alpha)
                    self.cur_scene = self.temp_scene
                    pre_done = True
                if not pre_done:
                    self.is_fade_in = False
                    self.fade_alpha = 0
            if self.is_zoom_in:
                ## Zoom in the scene for real
                if self.zoom_scale < self.target_scale:
                    dim = (self.temp_scene.get_width(), self.temp_scene.get_height())
                    self.zoom_scale = min(self.target_scale, self.zoom_scale + self.zoom_rate)
                    try:
                        self.cur_scene = pygame.transform.scale(self.temp_scene, (int(dim[0]*self.zoom_scale), int(dim[1]*self.zoom_scale)))
                    except:
                        self.raise_exception(90)
                    pre_done = True
                if not pre_done:
                    self.is_zoom_in = False
                    self.zoom_scale = 1.0
                    self.target_scale = 1.0
                    self.zoom_rate = 0.1
            elif self.is_zoom_out:
                ## Zoom out the scene for real
                if self.zoom_scale > self.target_scale:
                    dim = (self.temp_scene.get_width(), self.temp_scene.get_height())
                    self.zoom_scale = max(self.target_scale, self.zoom_scale - self.zoom_rate)
                    try:
                        self.cur_scene = pygame.transform.scale(self.temp_scene, (int(dim[0]*self.zoom_scale), int(dim[1]*self.zoom_scale)))
                    except:
                        self.raise_exception(90)
                    pre_done = True
                if not pre_done:
                    self.is_zoom_out = False
                    self.zoom_scale = 1.0
                    self.target_scale = 1.0
                    self.zoom_rate = 0.1

            if pre_done:
                ## If we aren't done zooming in or fading in, don't change the scene
                return False

            ## We're done loading the scene, change it in memory
            self.has_loaded_scene = False
            if self.old_scene != None:
                self.old_scene.set_alpha(0)
            
            self.has_set_auto = False
            return True

        ## Transition out of a scene
        elif line.startswith(".sceneout"):
            if not self.has_unloaded_scene:
                ## Parse out parentheses
                temp = line.replace(")","").split("(")[1].split(",")
                if len(temp) > 0:
                    ## If we have enough parameters...
                    type = temp[0].lstrip().rstrip()
                    ## Fade out a scene
                    if type == "fade":
                        self.is_fade_out = True
                    ## Zoom in to transition out
                    elif type == "zoomin":
                        self.is_zoom_in = True
                        if len(temp) > 1:
                            scale = temp[1].lstrip().rstrip() 
                            try:
                                self.zoom_scale = float(scale)
                            except:
                                self.raise_exception(100)
                        if len(temp) > 2:
                            scale = temp[2].lstrip().rstrip() 
                            try:
                                self.target_scale = float(scale)
                            except:
                                self.raise_exception(100)
                        if len(temp) > 3:
                            rate = temp[3].lstrip().rstrip() 
                            try:
                                self.zoom_rate = float(rate)
                            except:
                                self.raise_exception(100)
                    ## Zoom out to transition out
                    elif type == "zoomout":
                        self.is_zoom_out = True
                        if len(temp) > 1:
                            scale = temp[1].lstrip().rstrip() 
                            try:
                                self.zoom_scale = float(scale)
                            except:
                                self.raise_exception(100)
                        if len(temp) > 2:
                            scale = temp[2].lstrip().rstrip() 
                            try:
                                self.target_scale = float(scale)
                            except:
                                self.raise_exception(100)
                        if len(temp) > 3:
                            rate = temp[3].lstrip().rstrip() 
                            try:
                                self.zoom_rate = float(rate)
                            except:
                                self.raise_exception(100)
                    ## Combination fade and zoom in
                    elif type == "fadezoomin":
                        self.is_fade_out = True
                        self.is_zoom_in = True
                        if len(temp) > 1:
                            scale = temp[1].lstrip().rstrip() 
                            try:
                                self.zoom_scale = float(scale)
                            except:
                                self.raise_exception(100)
                        if len(temp) > 2:
                            scale = temp[2].lstrip().rstrip() 
                            try:
                                self.target_scale = float(scale)
                            except:
                                self.raise_exception(100)
                        if len(temp) > 3:
                            rate = temp[3].lstrip().rstrip() 
                            try:
                                self.zoom_rate = float(rate)
                            except:
                                self.raise_exception(100)
                    ## Combination fade and zoom out
                    elif type == "fadezoomout":
                        self.is_fade_out = True
                        self.is_zoom_out = True
                        if len(temp) > 1:
                            scale = temp[1].lstrip().rstrip() 
                            try:
                                self.zoom_scale = float(scale)
                            except:
                                self.raise_exception(100)
                        if len(temp) > 2:
                            scale = temp[2].lstrip().rstrip() 
                            try:
                                self.target_scale = float(scale)
                            except:
                                self.raise_exception(100)
                        if len(temp) > 3:
                            rate = temp[3].lstrip().rstrip() 
                            try:
                                self.zoom_rate = float(rate)
                            except:
                                self.raise_exception(100)
                    
                self.temp_scene = self.cur_scene.copy().convert()
                self.has_unloaded_scene = True
            
            pre_done = False ## Don't delete scene if we're not done transitioning out
            if self.is_fade_out:
                ## Fade out for real
                if self.fade_alpha < 255:
                    self.fade_alpha += self.fade_rate
                    self.temp_scene.set_alpha(255-self.fade_alpha)
                    self.cur_scene = self.temp_scene
                    pre_done = True
                if not pre_done:
                    self.is_fade_out = False
                    self.fade_alpha = 0
            if self.is_zoom_in:
                ## Zoom in for real
                if self.zoom_scale < self.target_scale:
                    dim = (self.temp_scene.get_width(), self.temp_scene.get_height())
                    self.zoom_scale = min(self.target_scale, self.zoom_scale + self.zoom_rate)
                    try:
                        self.cur_scene = pygame.transform.scale(self.temp_scene, (int(dim[0]*self.zoom_scale), int(dim[1]*self.zoom_scale)))
                    except:
                        self.raise_exception(90)
                    pre_done = True
                if not pre_done:
                    self.is_zoom_in = False
                    self.zoom_scale = 1.0
                    self.target_scale = 1.0
                    self.zoom_rate = 0.1
            elif self.is_zoom_out:
                ## ZOom out for real
                if self.zoom_scale > self.target_scale:
                    dim = (self.temp_scene.get_width(), self.temp_scene.get_height())
                    self.zoom_scale = max(self.target_scale, self.zoom_scale - self.zoom_rate)
                    try:
                        self.cur_scene = pygame.transform.scale(self.temp_scene, (int(dim[0]*self.zoom_scale), int(dim[1]*self.zoom_scale)))
                    except:
                        self.raise_exception(90)
                    pre_done = True
                if not pre_done:
                    self.is_zoom_out = False
                    self.zoom_scale = 1.0
                    self.target_scale = 1.0
                    self.zoom_rate = 0.1

            if pre_done:
                ## Not done transitioning, don't continue
                return False

            ## Continue with scene file processing
            self.has_unloaded_scene = False
            self.has_set_auto = False
            return True

        ## Load or stop a piece of background music
        elif line.startswith(".music"):
            ## Parse out the parentheses
            temp = line.replace(")","").split("(")[1].lstrip().rstrip()
            if len(temp) == 0:
                ## Empty parameters means stop music
                pygame.mixer.music.stop()
            else:
                ## Attempt to load a wav file
                try:
                    pygame.mixer.music.load("data/music/" + temp + ".wav")
                    pygame.mixer.music.set_volume(self.volume)
                    pygame.mixer.music.play(-1)
                except:
                    ## Raise custom exception
                    self.raise_exception(55, temp)
            return True

        ## Load or stop a sound effect wav
        elif line.startswith(".sound") and not self.is_skip:
            ## Parse out parentheses
            temp = line.replace(")","").split("(")[1].lstrip().rstrip()
            if len(temp) > 0:
                ## Full parameters means attempt to load wav
                try:
                    self.sound = pygame.mixer.Sound("data/sound/" + temp + ".wav")
                    self.sound.set_volume(self.slider_values[1])
                    self.sound.play()
                except:
                    ## raise custom exception
                    self.raise_exception(56, temp)
            else:
                ## Empty parameters means stop sound effect
                self.sound.stop()
                self.sound = None
            return True

        ## Set fade rate
        elif line.startswith(".setfade"):
            temp = line.replace(")","").split("(")[1].lstrip().rstrip()
            self.fade_rate = int(temp)
            return True

        ## Hide GUI buttons and text box
        elif line.startswith(".hide"):
            if not self.has_set_hide:
                self.has_set_hide = True
                self.target_hide_alpha = 0
            if self.hide_alpha > self.target_hide_alpha:
                self.hide_alpha -= 15
                if self.hide_alpha < 0:
                    self.hide_alpha = 0
                return False
            self.has_set_hide = False
            return True

        ## Show GUI buttons and text box
        elif line.startswith(".show"):
            if not self.has_set_hide:
                self.has_set_hide = True
                self.target_hide_alpha = 255
            if self.hide_alpha < self.target_hide_alpha:
                self.hide_alpha += 15
                if self.hide_alpha > 255:
                    self.hide_alpha = 255
                return False
            self.has_set_hide = False
            return True

        ## Swap the current scene file with a new one
        elif line.startswith(".swap"):
            temp = line.replace(")","").split("(")[1].lstrip().rstrip()
            self.run_scene(temp, False)
            return True

        ## Create a date-time indicator widget
        elif line.startswith(".widget"):
            temp = line.replace(")","").split("(")[1].split(",")
            if len(temp) < 2:
                self.raise_exception(200)
            self.ingame_date = temp[0].lstrip().rstrip()
            anchor = temp[1].lstrip().rstrip()
            if anchor not in ("topleft","midtop","topright","midleft","center","midright","bottomleft","midbottom","bottomright"):
                self.raise_exception(250)
            self.datetime_display = Button(self.ingame_date, self.button_font, self.font_antialias, self.datetime_fontsize, self.datetime,
                                           self.datetime_topleft, -1, True, anchor=anchor, shadow_type=2)
            return True

        ## Do a variable manipulation command
        elif line.startswith("$"):
            try:
                if "+" in line:
                    ## Increment a variable via +=
                    temp = line.split("+=")
                    var   = temp[0].lstrip().rstrip()
                    value = temp[1].lstrip().rstrip()
                    if value.isdigit():
                        value = int(value)
                        self.variables[var] += value
                    else:
                        self.variables[var] += self.variables[value]
                elif "-" in line:
                    ## Decrement a variable via -=
                    temp = line.split("-=")
                    var   = temp[0].lstrip().rstrip()
                    value = temp[1].lstrip().rstrip()
                    if value.isdigit():
                        value = int(value)
                        self.variables[var] -= value
                    else:
                        self.variables[var] -= self.variables[value]
                elif "=" in line:
                    ## Assign to a variable via =
                    temp = line.split("=")
                    var   = temp[0].lstrip().rstrip()
                    value = temp[1].lstrip().rstrip()
                    if value.isdigit():
                        value = int(value)
                        self.variables[var] = value
                    else:
                        self.variables[var] = self.variables[value]
            except:
                ## Raise custom exception
                self.raise_exception(150)
            return True

        ## Compare variables for boolean result
        elif line.startswith(".if"):
            temp = line.split(" ")
            if len(temp) > 1:
                try:
                    var  = self.variables[temp[1].lstrip().rstrip()]
                    comp = temp[3].replace(":","").rstrip()
                    ## Allow for intervariable and variable-constant comparisons
                    if comp.isdigit():
                        comparison = int(comp)
                    else:
                        comparison = self.variables[comp]
                except:
                    self.raise_exception(150)
            else:
                self.state = STATE.READ
                return True

            ## Less than
            op = temp[2].lstrip().rstrip()
            if op == "<":
                if var < comparison:
                    return True

            ## Less than or equals
            elif op == "<=":
                if var <= comparison:
                    return True

            ## Greater than
            elif op == ">":
                if var > comparison:
                    return True

            ## Greater than or equals
            elif op == ">=":
                if var >= comparison:
                    return True

            ## Equals
            elif op == "==":
                if var == comparison:
                    return True

            ## Does not equal
            elif op == "!=":
                if var != comparison:
                    return True
                
            self.state = STATE.VAR_BRANCH
            return True

        ## Read in and scroll out a piece of dialogue
        elif self.state == STATE.READ and self.is_process_text:
            pos = [self.textbox_margin * 8, self.textbox_margin + (self.cur_text_index + 1) * self.dialogue_fontsize]
            text = line.lstrip().rstrip()
            text = Text(text, self.dialogue_font, self.font_antialias, pos, self.dialogue_fontsize, self.dialogue_font_color,
                        self.dialogue_shadow_color, scrollable=True, scroll_speed=self.scroll_speed, shadow_type=2)
            self.cur_dialogue.append(text)
            self.cur_text_index += 1

            text = line.lstrip().rstrip()
            text = Text(text, self.dialogue_font, self.font_antialias, pos, self.dialogue_fontsize, self.dialogue_prev_color, self.dialogue_shadow_color, False,
                        shadow_type=2)
            self.prev_dialogue[self.prev_text_index].append(text)
            return True

        return True

    def raise_exception(self, num, arg=None):
        ######################################################
        ## Raise a custom exception to handle engine errors ##
        ######################################################

        ## Remove Python's stack trace
        sys.tracebacklimit = 0
        ## List of exceptions, which are self-explanatory
        if num == 0:
            raise Exception("VNError: Scene file '%s.nes' does not exist!\n\tPlease check the scenes folder!" %(arg))
        elif num == 50:
            raise Exception("VNError (Line %d in %s.nes): Attempted to load nonexistent '%s.png'!\n\tPlease check the images folder!" %(self.index+1, self.cur_file, arg))
        elif num == 51:
            raise Exception("VNError (Line %d in %s.nes): Referenced a nonexistent character %s!\n\tPerhaps an integer is out of range?" %(self.index+1, self.cur_file, arg))
        elif num == 52:
            raise Exception("VNError (Line %d in %s.nes): Referenced a nonexistent sub-image %s!\n\tPerhaps an integer is out of range?" %(self.index+1, self.cur_file, arg))
        elif num == 55:
            raise Exception("VNError (Line %d in %s.nes): Attempted to load nonexistent 'music/%s.wav'!\n\tPlease check the music folder!" %(self.index+1, self.cur_file, arg))
        elif num == 56:
            raise Exception("VNError (Line %d in %s.nes): Attempted to load nonexistent 'sound/%s.wav'!\n\tPlease check the sound folder!" %(self.index+1, self.cur_file, arg))
        elif num == 90:
            raise Exception("VNError (Line %d in %s.nes): Attempted scaling to negative size!\n\tPerhaps a scaling factor was 0 or less?" %(self.index+1, self.cur_file))
        elif num == 100:
            raise Exception("VNError (Line %d in %s.nes): Scaling factor was not a float!" %(self.index+1, self.cur_file))
        elif num == 101:
            raise Exception("VNError (Line %d in %s.nes): Parameter 'char' was not an integer!" %(self.index+1, self.cur_file))
        elif num == 102:
            raise Exception("VNError (Line %d in %s.nes): Parameter 'sub' was not an integer!" %(self.index+1, self.cur_file))
        elif num == 103:
            raise Exception("VNError (Line %d in %s.nes): Parameter 'pos' was not an integer!" %(self.index+1, self.cur_file))
        elif num == 104:
            raise Exception("VNError (Line %d in %s.nes): Waiting time was not an integer!" %(self.index+1, self.cur_file))
        elif num == 105:
            raise Exception("VNError (Line %d in %s.nes): Shake magnitude was not an integer pair!" %(self.index+1, self.cur_file))
        elif num == 106:
            raise Exception("VNError (Line %d in %s.nes): Branch label was not an integer!" %(self.index+1, self.cur_file))
        elif num == 150:
            raise Exception("VNError (Line %d in %s.nes): Referenced a nonexistent variable!" %(self.index+1, self.cur_file))
        elif num == 200:
            raise Exception("VNError (Line %d in %s.nes): Not enough arguments supplied for the function!" %(self.index+1, self.cur_file))
        elif num == 250:
            raise Exception("VNError (Line %d in %s.nes): Anchor position was not recognized!" %(self.index+1, self.cur_file))
        

    def draw_buttons(self):
        ####################################################
        ## Draw the buttons in various states of the game ##
        ####################################################

        ## Title screen
        if self.state == STATE.TITLE:
            for button in self.title_buttons:
                ## Check for collision and update color / play sound accordingly
                if button.rect.collidepoint(self.get_mouse_pos()):
                    button.update(color=self.button_hover_color)
                    if button.sound != None and not button.has_sound_played:
                        button.sound.set_volume(self.slider_values[1])
                        button.sound.play()
                        button.has_sound_played = True
                else:
                    button.update(color=self.button_font_color)
                    button.has_sound_played = False
                button.draw(self.screen)

        ## Load save screen
        elif self.state == STATE.LOAD:
            for button in self.load_buttons:
                ## Check for collision and update color / play sound accordingly
                if button.rect.collidepoint(self.get_mouse_pos()):
                    button.update(color=self.button_hover_color)
                    if button.sound != None and not button.has_sound_played:
                        button.sound.set_volume(self.slider_values[1])
                        button.sound.play()
                        button.has_sound_played = True
                else:
                    button.update(color=self.button_font_color)
                    button.has_sound_played = False
                button.draw(self.screen)

        ## Write save screen
        elif self.state == STATE.SAVE:
            for button in self.save_buttons:
                ## Check for collision and update color / play sound accordingly
                if button.rect.collidepoint(self.get_mouse_pos()):
                    button.update(color=self.button_hover_color)
                    if button.sound != None and not button.has_sound_played:
                        button.sound.set_volume(self.slider_values[1])
                        button.sound.play()
                        button.has_sound_played = True
                else:
                    button.update(color=self.button_font_color)
                    button.has_sound_played = False
                button.draw(self.screen)

        ## Configuration screen
        elif self.state == STATE.CONFIG:
            ## Draw sliders and buttons
            for slider in self.config_sliders:
                slider.draw(self.screen)
            for button in self.config_buttons:
                ## Check for collision and update color / play sound accordingly
                if button.value == -1024:
                    button.update(speed=self.scroll_speed)
                elif button.rect.collidepoint(self.get_mouse_pos()):
                    if button.value != -999:
                        button.update(color=self.button_hover_color)
                    if button.sound != None and not button.has_sound_played:
                        button.sound.set_volume(self.slider_values[1])
                        button.sound.play()
                        button.has_sound_played = True
                elif button.value != -999:
                    button.update(color=self.button_font_color)
                    button.has_sound_played = False
                button.draw(self.screen)

        ## Show in-game buttons only if not hiding them
        elif self.hide_alpha == 255:
            for button in self.ingame_buttons:
                if button.rect.collidepoint(self.get_mouse_pos()):
                    button.update(color=self.button_hover_color)
                    if button.sound != None and not button.has_sound_played:
                        button.sound.set_volume(self.slider_values[1])
                        button.sound.play()
                        button.has_sound_played = True
                else:
                    button.update(color=self.button_font_color)
                    button.has_sound_played = False
                button.draw(self.screen)

    def run_save(self):
        #################################
        ## Write data into a save file ##
        #################################
        
        temp_index = self.index
        found_text = 0
        ## Iterate backwards into the scene file until the beginning of a dialogue is found 
        while temp_index > 0:
            if self.lines[temp_index].lstrip().startswith(".text"):
                found_text += 1
                if found_text == 2:
                    break
            temp_index -= 1

        ## Create the save string to write to the save file
        save_string = u"begin\n"
        ## Concatenate relevant information
        for i in range(len(self.prev_dialogue)):
            ## Concatenate speaker's name
            save_string += "name: %s\n" %(self.prev_name_text[i].string.rstrip())
            ## Concatenate dialogue strings
            for j in range(len(self.prev_dialogue[i])):
                save_string += "%s\n" %(self.prev_dialogue[i][j].string)
        ## Concatenate scene index, background indices, text indices, et cetera
        save_string += "end\n\nscene: %s\nindex: %03d\n" %(self.cur_file, temp_index)
        save_string += "background: %s, %s\n" %(self.cur_scene_file[0], self.cur_scene_file[1])
        save_string += "text_index: %d, %d\n" %(self.max_prev_index, self.max_prev_index)

        ## Allow for Unicode recording
        date = self.ingame_date.decode('utf-8')
        ## Concatenate what the date-time widget says
        save_string += u"widget: {}\n".format(date)

        for var in self.variable_strings:
            ## Record all nonzero variables
            if self.variables[var] != 0:
                save_string += "nonzero_var: %s, %d\n" %(var, self.variables[var])

        ## Record music filename
        music_index = self.index
        while not (self.lines[music_index].lstrip().startswith(".music")) and music_index > 0:
            music_index -= 1
        if self.lines[music_index].lstrip().startswith(".music"):
            temp = self.lines[music_index].lstrip().split("#")[0].rstrip()
            temp = temp.split("(")[1].rstrip(")").lstrip().rstrip()
            if len(temp) > 0:
                save_string += "music: %s\n" %(temp)

        ## Record whether we were shaking the screen at the time
        anim_index = self.index
        while not(self.lines[anim_index].lstrip().startswith(".shake")) and anim_index > 0:
            anim_index -= 1
        if self.lines[anim_index].lstrip().startswith(".shake"):
            temp = self.lines[anim_index].lstrip().split("#")[0].rstrip()
            temp = temp.replace(")","").split("(")[1].split(",")
            if len(temp) > 1:
                save_string += "shake: %d, %d\n" %(int(temp[0]), int(temp[1]))

        ## Record characters as they are found (max 4)
        char_index = self.index
        char_exist_count = 0
        char_found_count = 0
        for i in range(4):
            if len(self.char_im[i]) > 0:
                char_exist_count += 1

        ## Record characters
        while char_found_count < char_exist_count:
            char_index -= 1
            if char_index < 0:
                break
            elif self.lines[char_index].lstrip().startswith(".load"):
                temp = self.lines[char_index].lstrip().split("#")[0].rstrip()
                temp = temp.replace(")","").split("(")[1].split(",")
                if len(temp) > 1:
                    save_string += "load: %s, %d\n" %(temp[0], int(temp[1]))
                    char_found_count += 1

        for char in self.cur_chars:
            save_string += "draw: %d, %d, %d, %s\n" %(char.index, char.em, char.num, char.name)

        ## Calculate the save directory and actually write to the file
        path = "data/data/"
        self.save_buttons = []
        save_positions = []
        ## Generate a list of save files already in the directory
        for filename in glob.glob(os.path.join(path, "*.jsav")):
            x, y = 0, 0
            save_file = open(filename, "r").readlines()
            total = self.grid_size[1] * x + y
            label = "Empty File"
            for line in save_file:
                if line.startswith("xy"):
                    temp = line.split(":")[1].split(",")
                    x, y = int(temp[0]), int(temp[1])
                elif line.startswith("datetime"):
                    total = self.grid_size[1] * x + y
                    label = "Save %02d: " %(total+1) + line.split(":")[1].lstrip().rstrip() + ":" + line.split(":")[2].lstrip().rstrip()
            pos = [self.save_list_pos[0] + int(self.savebox.get_width() * 1.05) * x,
                   self.save_list_pos[1] + self.savebox.get_height() * y]
            button = Button(label, self.button_font, self.font_antialias, self.button0_fontsize, self.savebox, pos, total, sfx=self.button_sound, ping=self.select_sound,
                                    color=self.button_font_color, shadow=self.button_shadow_color, hover=self.button_hover_color, fadein=True)
            self.save_buttons.append(button)
            save_positions.append((x,y))

        ## Draw the save files as buttons on-screen
        for i in range(self.grid_size[0]):
            for j in range(self.grid_size[1]):
                if (i,j) not in save_positions:
                    pos = [self.save_list_pos[0] + int(self.savebox.get_width() * 1.05) * i,
                           self.save_list_pos[1] + self.savebox.get_height() * j]
                    total = self.grid_size[1] * i + j
                    label = "Empty File"
                    button = Button(label, self.button_font,  self.font_antialias, self.button0_fontsize, self.savebox, pos, total, sfx=self.button_sound, ping=self.select_sound,
                                    color=self.button_font_color, shadow=self.button_shadow_color, hover=self.button_hover_color, fadein=True)
                    self.save_buttons.append(button)
                    save_positions.append((i,j))

        button = Button("Back", self.button_font, self.font_antialias, self.button0_fontsize, self.button0, self.to_title_pos, -1, sfx=self.button_sound, ping=self.select_sound,
                                    color=self.button_font_color, shadow=self.button_shadow_color, hover=self.button_hover_color, fadein=True)
        self.save_buttons.append(button)

        old_state = self.state
        self.state = STATE.SAVE
        self.save_index = 0
        done = False

        ## Sub game loop to allow players to choose a save slot to save into
        while not done:
            self.clock.tick(60) ## 60 FPS
            
            self.screen.blit(self.title, (0,0)) ## Blit title background image

            self.draw_buttons() ## Draw relevant buttons
                
            pygame.display.flip() ## Refresh screen buffer

            ## Poll for input
            for e in pygame.event.get():
                ## Allow for easy exiting
                if e.type == pygame.QUIT:
                    self._quit()
                elif e.type == pygame.KEYDOWN:
                    ## Return to where you came from
                    if e.key == pygame.K_ESCAPE:
                        done = True
                elif e.type == pygame.MOUSEBUTTONDOWN:
                    ## Handle buttons and concatenate relevant save data information
                    if self.handle_buttons():
                        save_string += "xy: %d, %d\n" %(save_positions[self.save_index])
                        dt = datetime.datetime.today()
                        year = dt.year
                        month = dt.month
                        day = dt.day
                        hour = dt.hour
                        minute = dt.minute
                        ## Date-time will be used as the label for the save button
                        save_string += "datetime: %d-%d-%d, %02d:%02d\n" %(year,month,day,hour,minute)

                        total = save_positions[self.save_index][0] * self.grid_size[1] + save_positions[self.save_index][1]
                        ## Write to a utf-8 encoded file
                        savefile = codecs.open("data/data/%03d.jsav" %(total), "w+", "utf-8")
                        savefile.write(save_string)
                        savefile.close()

                        pos = [self.save_list_pos[0] + int(self.savebox.get_width() * 1.05) * save_positions[self.save_index][0],
                               self.save_list_pos[1] + self.savebox.get_height() * save_positions[self.save_index][1]]
                        ## Date-time will be used as the label for the save button
                        label = "Save %02d: %d-%d-%d, %02d:%02d" %(total+1,year,month,day,hour,minute)
                        self.save_buttons[self.save_index] = Button(label, self.button_font, self.font_antialias, self.button0_fontsize,
                                                                    self.savebox, pos, total, sfx=self.button_sound, ping=self.select_sound,
                                                                    color=self.button_font_color, shadow=self.button_shadow_color,
                                                                    hover=self.button_hover_color, fadein=True)
                    else:
                        done = True

        self.state = old_state
        return True

    def run_load(self):
        ##################################
        ## Read data out of a save file ##
        ##################################
        path = "data/data/"
        self.load_buttons = []
        load_positions = []
        for filename in glob.glob(os.path.join(path, "*.jsav")):
            x, y = 0, 0
            load_file = open(filename, "r").readlines()
            total = self.grid_size[1] * x + y
            label = "Empty File"
            for line in load_file:
                if line.startswith("xy:"):
                    temp = line.split(":")[1].split(",")
                    x, y = int(temp[0]), int(temp[1])
                elif line.startswith("datetime"):
                    total = self.grid_size[1] * x + y
                    label = "Save %02d: " %(total+1) + line.split(":")[1].lstrip().rstrip() + ":" + line.split(":")[2].lstrip().rstrip()
            pos = [self.save_list_pos[0] + int(self.savebox.get_width() * 1.05) * x,
                   self.save_list_pos[1] + self.savebox.get_height() * y]
            button = Button(label, self.button_font, self.font_antialias, self.button0_fontsize, self.savebox, pos, total, sfx=self.button_sound, ping=self.select_sound,
                                color=self.button_font_color, shadow=self.button_shadow_color, hover=self.button_hover_color, fadein=True)
            self.load_buttons.append(button)
            load_positions.append((x,y))

        for i in range(self.grid_size[0]):
            for j in range(self.grid_size[1]):
                if (i,j) not in load_positions:
                    pos = [self.save_list_pos[0] + int(self.savebox.get_width() * 1.05) * i,
                           self.save_list_pos[1] + self.savebox.get_height() * j]
                    total = self.grid_size[1] * i + j
                    label = "Empty File"
                    button = Button(label, self.button_font, self.font_antialias, self.button0_fontsize, self.savebox, pos, -1, sfx=self.button_sound, ping=self.select_sound,
                                    color=self.button_font_color, shadow=self.button_shadow_color, hover=self.button_hover_color, fadein=True)
                    self.load_buttons.append(button)
                    load_positions.append((i,j))

        button = Button("Back", self.button_font, self.font_antialias, self.button0_fontsize, self.button0, self.to_title_pos, -1, sfx=self.button_sound, ping=self.select_sound,
                                    color=self.button_font_color, shadow=self.button_shadow_color, hover=self.button_hover_color, fadein=True)
        self.load_buttons.append(button)

        old_state = self.state
        self.state = STATE.LOAD

        while True:
            self.clock.tick(60)

            self.screen.blit(self.title, (0,0))
                        
            self.draw_buttons()
                
            pygame.display.flip()

            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    self._quit()
                elif e.type == pygame.KEYDOWN:
                    if e.key == pygame.K_ESCAPE:
                        self.state = old_state
                        return False
                elif e.type == pygame.MOUSEBUTTONDOWN:
                    if self.handle_buttons():
                        return True
                    self.state = old_state
                    return False

        self.state = old_state
        return False

    def load_save(self, num):
        self.init_members()
        save_file = open("data/data/%03d.jsav" %(num)).readlines()
        scene = 0
        for i in range(len(save_file)):
            if save_file[i].startswith("begin"):
                while not save_file[i].startswith("end"):
                    i += 1
                    if save_file[i].startswith("name"):
                        self.cur_text_index = 0
                        temp = save_file[i].split(":")[1].lstrip().rstrip()
                        pos = [self.textbox_margin, self.textbox_margin + self.cur_text_index * self.dialogue_fontsize]
                        temp = Text(temp, self.dialogue_font, self.font_antialias, pos, self.dialogue_fontsize,
                                    self.dialogue_font_color, self.dialogue_shadow_color, False, shadow_type=2)
                        self.prev_name_text.append(temp)
                        self.prev_dialogue.append([])
                    elif save_file[i].startswith("end"):
                        self.prev_name_text.remove(self.prev_name_text[-1])
                        self.prev_dialogue.remove(self.prev_dialogue[-1])
                        break
                    else:
                        temp = save_file[i].lstrip().rstrip()
                        pos = [self.textbox_margin * 8, self.textbox_margin + (self.cur_text_index + 1) * self.dialogue_fontsize]
                        temp = Text(temp, self.dialogue_font, self.font_antialias, pos, self.dialogue_fontsize,
                                    self.dialogue_prev_color, self.dialogue_shadow_color, False, shadow_type=2)
                        self.prev_dialogue[-1].append(temp)
                        self.cur_text_index += 1

            elif save_file[i].startswith("scene"):
                temp = save_file[i].split(":")[1].lstrip().rstrip()
                scene = temp
            elif save_file[i].startswith("shake"):
                temp = save_file[i].split(":")[1].split(",")
                self.shake_range = [int(temp[0]), int(temp[1])]
                if int(temp[0]) != 0 or int(temp[1]) != 0:
                    self.is_shake = True
            elif save_file[i].startswith("music"):
                temp = save_file[i].split(":")[1].lstrip().rstrip()
                if temp != "None":
                    pygame.mixer.music.load("data/music/" + temp + ".wav")
                    pygame.mixer.music.set_volume(self.volume)
                    pygame.mixer.music.play(-1)
            elif save_file[i].startswith("background"):
                temp = save_file[i].split(":")[1].split(",")
                if temp[0].lstrip().rstrip() == "null" and temp[1].lstrip().rstrip() == "null":
                    self.cur_scene = None
                    self.old_scene = None
                else:
                    self.old_scene = None
                    self.cur_scene = pygame.image.load("data/images/%s/%s.png" %(temp[0].lstrip().rstrip(), temp[1].lstrip().rstrip())).convert()
                    self.cur_scene_file = [temp[0], temp[1]]
            elif save_file[i].startswith("index"):
                temp = save_file[i].split(":")[1].lstrip().rstrip()
                self.index = int(temp)
            elif save_file[i].startswith("text_index"):
                temp = save_file[i].split(":")[1].split(",")
                self.prev_text_index = int(temp[0]) - 1
                self.max_prev_index  = int(temp[1]) - 1
            elif save_file[i].startswith("widget"):
                temp = save_file[i].split(":")[1].lstrip().rstrip()
                date = temp
                if date != "null":
                    self.ingame_date = date
                    text = "%s" %(temp)
                    self.datetime_display = Button(text, self.button_font, self.font_antialias, self.datetime_fontsize, self.datetime, self.datetime_topleft, -1,
                                                   True, shadow_type=2)
                else:
                    self.ingame_date = date
                    self.datetime_display = None
                    
            elif save_file[i].startswith("load"):
                temp = save_file[i].split(":")[1].split(",")
                path = "data/images/char/%s/" %(temp[0].lstrip().rstrip())

                for filename in glob.glob(os.path.join(path, "*.png")):
                    im = pygame.image.load(filename).convert_alpha()
                    self.char_im[int(temp[1])].append(im)
                    
            elif save_file[i].startswith("draw"):
                temp = save_file[i].split(":")[1].split(",")
                im = self.char_im[int(temp[0])][int(temp[1])]
                pos  = [int(temp[2]) * self.screen_dimension[0]/16, self.screen_dimension[1]]
                new_char = Character(im, int(temp[1]), pos, temp[3].rstrip(), int(temp[0]), int(temp[2]))
                self.cur_chars.append(new_char)
                if len(self.cur_chars) > 8:
                    self.cur_chars = self.cur_chars[1:]
                    
            elif save_file[i].startswith("nonzero_var"):
                temp = save_file[i].split(":")[1].split(",")
                self.variables[temp[0].lstrip().rstrip()] = int(temp[1])

        self.fade_alpha = 0
        self.run_scene(scene, True)
        return True

    def run_config(self):
        old_state = self.state
        self.state = STATE.CONFIG
        for slider in self.config_sliders:
            percent = self.slider_values[slider.value]
            diff = percent * slider.rect.width
            slider.button.rect.centerx = slider.rect.x + diff
            slider.alpha = 0

        for button in self.config_buttons:
            button.alpha = 0

        running = True
        while running:
            self.clock.tick(60)
            self.screen.blit(self.title, (0,0))
                        
            self.screen.blit(self.config_screen, (0,0))

            self.handle_sliders()
            self.draw_buttons()
                
            pygame.display.flip()

            if pygame.event.get_grab():
                pygame.event.set_grab(False)

            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    self._quit()
                elif e.type == pygame.KEYDOWN:
                    if e.key == pygame.K_ESCAPE:
                        self.state = old_state
                        running = False
                elif e.type == pygame.MOUSEBUTTONDOWN:
                    if self.handle_buttons():
                        self.state = old_state
                        running = False

        self.save_changes()
        self.state = old_state
        return False

    def run_title(self):
        self.running = False
        return True

    def run_back(self):
        self.prev_text_index -= 1
        if self.prev_text_index < 0:
            self.prev_text_index = 0

    def run_auto(self):
        if self.prev_text_index == self.max_prev_index:
            complete = True
            for i in range(len(self.cur_dialogue)):
                if self.cur_dialogue[i].cur_width < self.cur_dialogue[i].width:
                    complete = False

            if complete:
                if not self.has_set_auto:
                    self.auto_count = self.auto_pause
                    self.has_set_auto = True
                
                self.auto_count -= 1
                if self.auto_count <= 0:
                    self.auto_count = 0
                    self.has_set_auto = False
                    self.advance = True
                else:
                    self.advance = False

    def run_next(self):
        if self.prev_text_index == self.max_prev_index:
            complete = True
            for i in range(len(self.cur_dialogue)):
                if self.cur_dialogue[i].cur_width < self.cur_dialogue[i].width:
                    self.cur_dialogue[i].cur_width = self.cur_dialogue[i].width
                    complete = False
            if complete:
                self.advance = True
        else:
            self.prev_text_index += 1
            if self.prev_text_index > self.max_prev_index:
                self.prev_text_index = self.max_prev_index

    def new_game(self):
        temp_fade_alpha = 0
        self.fade_mask.set_alpha(temp_fade_alpha)
        done = False
        
        pygame.mixer.music.stop()
        
        while not done:
            self.clock.tick(60)
            self.screen.blit(self.title, (0,0))
            self.screen.blit(self.splash, (self.title_pos[0],self.title_pos[1]))
            self.state = STATE.TITLE
                    
            self.draw_buttons()
            self.screen.blit(self.fade_mask, (0,0))
            self.fade_mask.set_alpha(temp_fade_alpha)
            temp_fade_alpha += CONST.FADE
            if temp_fade_alpha > 255:
                temp_fade_alpha = 255
                done = True
            pygame.display.flip()

            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    self._quit()
                elif e.type == pygame.KEYDOWN:
                    if e.key == pygame.K_ESCAPE:
                        self._quit()
                
        self.run_scene(self.starting_scene, False)
        return True

    def continue_game(self):
        self.load_value = -1
        if self.run_load():
            temp_fade_alpha = 0
            self.fade_mask.set_alpha(temp_fade_alpha)
            done = False
            
            while not done:
                self.clock.tick(60)
                self.screen.blit(self.title, (0,0))
                self.state = STATE.TITLE
                
                self.draw_buttons()
                self.screen.blit(self.fade_mask, (0,0))
                pygame.display.flip()
                
                self.fade_mask.set_alpha(temp_fade_alpha)
                temp_fade_alpha += CONST.FADE
                if temp_fade_alpha > 255:
                    temp_fade_alpha = 255
                    done = True

                for e in pygame.event.get():
                    if e.type == pygame.QUIT:
                        self._quit()
                    elif e.type == pygame.KEYDOWN:
                        if e.key == pygame.K_ESCAPE:
                            self._quit()
                    
            self.load_save(self.load_value)
            return True
        return False

    def handle_sliders(self):
        is_focused = False
        for slider in self.config_sliders:
            if pygame.mouse.get_pressed()[0] and not is_focused:
                if slider.button.rect.collidepoint(self.get_mouse_pos()):
                    slider.focus = True
            else:
                slider.focus = False
                
            if slider.focus:
                is_focused = True
                slider.button.rect.centerx = max(slider.rect.x+slider.button.rect.width/2,
                                                 min(slider.rect.right-slider.button.rect.width/2, self.get_mouse_pos()[0]))
                if slider.value == 0:
                    diff = slider.button.rect.centerx - slider.rect.x
                    percent = float(diff) / slider.rect.width
                    self.slider_values[0] = percent
                    self.volume = percent
                    pygame.mixer.music.set_volume(percent)
                elif slider.value == 1:
                    diff = slider.button.rect.centerx - slider.rect.x
                    percent = float(diff) / slider.rect.width
                    self.slider_values[1] = percent
                elif slider.value == 2:
                    diff = slider.button.rect.centerx - slider.rect.x
                    percent = float(diff) / slider.rect.width
                    self.slider_values[2] = percent
                    self.scroll_speed = int(percent * CONST.SPEED_RANGE) + 1

    def handle_buttons(self):
        if self.state == STATE.TITLE:
            for button in self.title_buttons:
                if button.rect.collidepoint(self.get_mouse_pos()):
                    if button.ping != None:
                        button.ping.set_volume(self.slider_values[1])
                        button.ping.play()
                    if button.value == 0:
                        self.new_game()
                        return True
                    elif button.value == 1:
                        return self.continue_game()
                    elif button.value == 2:
                        return self.run_config()
                    elif button.value == 3:
                        self._quit()

        elif self.state == STATE.LOAD:
            for button in self.load_buttons:
                if button.rect.collidepoint(self.get_mouse_pos()):
                    if button.ping != None:
                        button.ping.set_volume(self.slider_values[1])
                        button.ping.play()
                    if button.value == -1:
                        return False
                    else:
                        self.load_value = button.value
                        return True

        elif self.state == STATE.SAVE:
            for button in self.save_buttons:
                if button.rect.collidepoint(self.get_mouse_pos()):
                    if button.ping != None:
                        button.ping.set_volume(self.slider_values[1])
                        button.ping.play()
                    if button.value == -1:
                        return False
                    else:
                        self.save_index = self.save_buttons.index(button)
                        return True

        elif self.state == STATE.CONFIG:
            for button in self.config_buttons:
                if button.rect.collidepoint(self.get_mouse_pos()):
                    if button.ping != None:
                        button.ping.set_volume(self.slider_values[1])
                        button.ping.play()
                    if button.value == 0:
                        if not self.fullscreen:
                            self.display = pygame.display.set_mode(self.screen_dimension, SWSURFACE|FULLSCREEN)
                            self.fullscreen = True
                        return False
                    elif button.value == 1:
                        if self.fullscreen:
                            self.display = pygame.display.set_mode(self.screen_dimension, SWSURFACE)
                            self.fullscreen = False
                        return False
                    elif button.value == 2:
                        self.save_changes()
                        return True

        elif self.target_hide_alpha == 255:
            for button in self.ingame_buttons:
                if button.rect.collidepoint(self.get_mouse_pos()):
                    if button.ping != None:
                        button.ping.set_volume(self.slider_values[1])
                        button.ping.play()
                    if button.value == 0:
                        self.run_save()
                    elif button.value == 1:
                        self.continue_game()
                    elif button.value == 2:
                        self.run_title()
                    elif button.value == 3:
                        self._quit()
                    elif button.value == 4:
                        self.run_back()
                    elif button.value == 5:
                        self.run_next()
                    elif button.value == 6:
                        self.is_skip = True if not self.is_skip and not self.is_auto else False
                    elif button.value == 7:
                        self.is_auto = True if not self.is_auto and not self.is_skip else False
                            
                    return True
        return False

    def draw_dialogue(self):
        for i in range(len(self.cur_chars)):
            self.cur_chars[i].draw(self.screen)

        if self.hide_alpha > 0:
            if self.datetime_display != None:
                self.datetime_display.alpha = self.hide_alpha
                self.datetime_display.draw(self.screen)
            if self.hide_alpha < 255:
                image = self.textbox.copy()
                if self.prev_text_index == self.max_prev_index:
                    if self.cur_name_text != None:
                        self.cur_name_text.draw(image)
                else:
                    if self.prev_name_text[self.prev_text_index] != None:
                        self.prev_name_text[self.prev_text_index].draw(image)
                if self.prev_text_index == self.max_prev_index:
                    display_text_index = 0
                    for i in range(len(self.cur_dialogue)):
                        if i <= display_text_index:
                            self.cur_dialogue[i].draw(image)
                        if self.cur_dialogue[i].width == self.cur_dialogue[i].cur_width:
                            display_text_index += 1
                else:
                    for i in range(len(self.prev_dialogue[self.prev_text_index])):
                        self.prev_dialogue[self.prev_text_index][i].draw(image)
                image.fill((255,255,255,self.hide_alpha), None, pygame.BLEND_RGBA_MULT)
                self.screen.blit(image, self.textbox_topleft)
            else:
                image = self.textbox.copy()
                if self.prev_text_index == self.max_prev_index:
                    if self.cur_name_text != None:
                        self.cur_name_text.draw(image)
                else:
                    if self.prev_name_text[self.prev_text_index] != None:
                        self.prev_name_text[self.prev_text_index].draw(image)
                if self.prev_text_index == self.max_prev_index:
                    display_text_index = 0
                    for i in range(len(self.cur_dialogue)):
                        if i <= display_text_index:
                            self.cur_dialogue[i].draw(image)
                        if self.cur_dialogue[i].width == self.cur_dialogue[i].cur_width:
                            display_text_index += 1
                else:
                    for i in range(len(self.prev_dialogue[self.prev_text_index])):
                        self.prev_dialogue[self.prev_text_index][i].draw(image)
                self.screen.blit(image, self.textbox_topleft)

    def run_scene(self, filename, is_continue):
        if not is_continue:
            self.init_members()
        try:
            self.lines = open("data/scenes/%s.nes" %(filename), "r").readlines()
        except:
            self.raise_exception(0, filename)
        self.cur_file = filename
        self.running = True

        while self.running:
            self.clock.tick(60)
            
            if not self.finished_scene and self.interpret_line(self.lines[self.index]):
                self.index += 1
                if self.index >= len(self.lines):
                    self.index = len(self.lines) - 1
                    self.finished_scene = True
            
            if self.is_shake:
                old = (self.old_anchor[0] + random.randint(-self.shake_range[0], self.shake_range[0]),
                       self.old_anchor[1] + random.randint(-self.shake_range[1], self.shake_range[1]))
                new = (self.new_anchor[0] + random.randint(-self.shake_range[0], self.shake_range[0]),
                       self.new_anchor[1] + random.randint(-self.shake_range[1], self.shake_range[1]))
            else:
                old = self.old_anchor
                new = self.new_anchor

            if self.old_scene != None:
                if self.old_anchor_string == "topleft":
                    old_anchor_rect = self.old_scene.get_rect(topleft=old)
                elif self.old_anchor_string == "midtop":
                    old_anchor_rect = self.old_scene.get_rect(midtop=old)
                elif self.old_anchor_string == "topright":
                    old_anchor_rect = self.old_scene.get_rect(topright=old)
                elif self.old_anchor_string == "midleft":
                    old_anchor_rect = self.old_scene.get_rect(midleft=old)
                elif self.old_anchor_string == "center":
                    old_anchor_rect = self.old_scene.get_rect(center=old)
                elif self.old_anchor_string == "midright":
                    old_anchor_rect = self.old_scene.get_rect(midright=old)
                elif self.old_anchor_string == "bottomleft":
                    old_anchor_rect = self.old_scene.get_rect(bottomleft=old)
                elif self.old_anchor_string == "midbottom":
                    old_anchor_rect = self.old_scene.get_rect(midbottom=old)
                elif self.old_anchor_string == "bottomright":
                    old_anchor_rect = self.old_scene.get_rect(bottomright=old)

            if self.cur_scene != None:
                if self.new_anchor_string == "topleft":
                    new_anchor_rect = self.cur_scene.get_rect(topleft=new)
                elif self.new_anchor_string == "midtop":
                    new_anchor_rect = self.cur_scene.get_rect(midtop=new)
                elif self.new_anchor_string == "topright":
                    new_anchor_rect = self.cur_scene.get_rect(topright=new)
                elif self.new_anchor_string == "midleft":
                    new_anchor_rect = self.cur_scene.get_rect(midleft=new)
                elif self.new_anchor_string == "center":
                    new_anchor_rect = self.cur_scene.get_rect(center=new)
                elif self.new_anchor_string == "midright":
                    new_anchor_rect = self.cur_scene.get_rect(midright=new)
                elif self.new_anchor_string == "bottomleft":
                    new_anchor_rect = self.cur_scene.get_rect(bottomleft=new)
                elif self.new_anchor_string == "midbottom":
                    new_anchor_rect = self.cur_scene.get_rect(midbottom=new)
                elif self.new_anchor_string == "bottomright":
                    new_anchor_rect = self.cur_scene.get_rect(bottomright=new)

            if not self.is_comment:
                self.screen.fill((0,0,0))
                if self.old_scene != None:                      
                    self.screen.blit(self.old_scene, old_anchor_rect)
                if self.cur_scene != None:
                    self.screen.blit(self.cur_scene, new_anchor_rect)

                if self.state == STATE.READ:
                    self.draw_dialogue()

                elif self.state == STATE.CHOOSE:
                    self.draw_dialogue()
                    for option in self.cur_options:
                        if option.rect.collidepoint(self.get_mouse_pos()):                        
                            option.update(color=self.button_hover_color)
                        else:
                            option.update(color=self.button_font_color)
                        option.draw(self.screen)

                elif self.state == STATE.OPT_BRANCH:
                    self.draw_dialogue()
                    if not self.finished_scene:
                        while not (self.lines[self.index].lstrip().startswith(".branch") and\
                                   len(self.lines[self.index].replace(":","").lstrip().rstrip().split(" ")) == 1):
                            self.index += 1
                            if self.index >= len(self.lines):
                                self.index = len(self.lines) - 1
                                self.finished_scene = True

                elif self.state == STATE.VAR_BRANCH:
                    self.draw_dialogue()
                    if not self.finished_scene:
                        while not self.lines[self.index].lstrip().startswith(".if"):
                            self.index += 1
                            if self.index >= len(self.lines):
                                self.index = len(self.lines) - 1
                                self.finished_scene = True

            if self.is_skip:
                self.run_next()
            elif self.is_auto:
                self.run_auto()

            if not self.is_comment:
                if self.target_hide_alpha == 255:
                    self.draw_buttons()

            ## Allow character images to fade in over each other
            for i in range(len(self.cur_chars)):
                for j in range(i+1, len(self.cur_chars)):
                    if self.cur_chars[i].pos == self.cur_chars[j].pos and self.cur_chars[j].alpha == 255:
                        self.cur_chars.remove(self.cur_chars[i])

            pygame.display.flip()

            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    self._quit()
                elif e.type == pygame.KEYDOWN:
                    if e.key == pygame.K_ESCAPE:
                        self._quit()
                elif e.type == pygame.MOUSEBUTTONDOWN:
                    if not self.handle_buttons():
                        if self.state == STATE.READ:
                            self.run_next()
                        elif self.state == STATE.CHOOSE:
                            for option in self.cur_options:
                                if option.rect.collidepoint(self.get_mouse_pos()):
                                    self.cur_choice = option.value
                                    self.prev_text_index = self.max_prev_index
                                    self.advance = True
                        
        return True

if __name__ == "__main__":
    main = Main()
    main.init_title()
