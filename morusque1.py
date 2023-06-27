import pygame
import sys
from pygame.locals import Color, KEYUP, K_ESCAPE, K_RETURN
import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522
import time
import random


pygame.init()
random.seed()
reader = SimpleMFRC522()

size_list = pygame.display.list_modes()
myscreen_size = size_list[0]

mywidth = 768
myheight = 1024

#mywidth = myscreen_size[0]
#myheight = myscreen_size[1]
#surface = pygame.display.set_mode((mywidth, myheight))
surface = pygame.display.set_mode((mywidth, myheight), pygame.FULLSCREEN)
pygame.mouse.set_visible(0)


# set up music and sound effect files
petiteFile = "song1.mp3"
lonelyFile = "song2.mp3"
untitledFile = "song3.mp3"
cooldownFile = "song6.mp3"
computeFile = "song4.mp3"
tomorrowsFile = "song5.mp3"
mildlyFile = "song7.mp3"
unreadableFile = "song8.mp3"
musiclist = ["PetiteValse","LonelyRobot","Untitled","Compute",
             "Tomorrows","CoolDown","Mildly","Unreadable"]
musicfilelist = ["song1.mp3","song2.mp3","song3.mp3","song4.mp3",
                 "song5.mp3","song6.mp3","song7.mp3","song8.mp3"]

lovefile = "heartreaction.mp3"
talkfilelist = ["morusqueSound1.mp3", "morusqueSound2.mp3"]
pygame.mixer.init()

#GPIO configuration. Meow = white, Music = green, Cancel = blue, Quit = red

meow_pin = 7
music_pin = 37
cancel_pin = 29
quit_pin = 13

GPIO.setup(meow_pin, GPIO.IN)
GPIO.setup(music_pin, GPIO.IN)
GPIO.setup(cancel_pin, GPIO.IN)
GPIO.setup(quit_pin, GPIO.IN)



# these classes were retrieved from the Pygame Wiki at:
# https://www.pygame.org/wiki/Spritesheet
# helpful classes for animating sprite sheets.
class spritesheet(object):
    def __init__(self, filename):
        try:
            self.sheet = pygame.image.load(filename).convert()
        except (pygame.error, message):
            print ('Unable to load spritesheet image:', filename)
            raise (SystemExit, message)
    # Load a specific image from a specific rectangle
    def image_at(self, rectangle, colorkey = None):
        "Loads image from x,y,x+offset,y+offset"
        rect = pygame.Rect(rectangle)
        #rect = pygame.Rect(0,0,mywidth, myheight)
        image = pygame.Surface(rect.size).convert()
        #rect2 = pygame.Rect(0,0,mywidth,myheight)
        image.blit(self.sheet, (0, 0), rect)
        if colorkey != None:
            if colorkey == -1:
                colorkey = image.get_at((0,0))
            image.set_colorkey(colorkey, pygame.RLEACCEL)

        image = pygame.transform.scale(image, (mywidth, myheight))
        image_rect = image.get_rect()
        image_surface = pygame.Surface((image_rect.width, image_rect.height))
        image_surface.blit(image, image_rect)
        return image_surface
    # Load a whole bunch of images and return them as a list
    def images_at(self, rects, colorkey = None):
        "Loads multiple images, supply a list of coordinates" 
        return [self.image_at(rect, colorkey) for rect in rects]
    # Load a whole strip of images
    def load_strip(self, rect, image_count, colorkey = None):
        "Loads a strip of images and returns them as a list"
        tups = [(rect[0]+rect[2]*x, rect[1], rect[2], rect[3])
                for x in range(image_count)]
        return self.images_at(tups, colorkey)


class SpriteStripAnim(object):
    """sprite strip animator
    
    This class provides an iterator (iter() and next() methods), and a
    __add__() method for joining strips which comes in handy when a
    strip wraps to the next row.
    """
    def __init__(self, filename, rect, count, colorkey=None, loop=False, frames=1):
        """construct a SpriteStripAnim
        
        filename, rect, count, and colorkey are the same arguments used
        by spritesheet.load_strip.
        
        loop is a boolean that, when True, causes the next() method to
        loop. If False, the terminal case raises StopIteration.
        
        frames is the number of ticks to return the same image before
        the iterator advances to the next image.
        """
        self.filename = filename
        ss = spritesheet(filename)
        self.images = ss.load_strip(rect, count, colorkey)
        self.i = 0
        self.loop = loop
        self.frames = frames
        self.f = frames
    def iter(self):
        self.i = 0
        self.f = self.frames
        return self
    def next(self):
        if self.i >= len(self.images):
            if not self.loop:
                raise StopIteration
            else:
                self.i = 0
        image = self.images[self.i]
        self.f -= 1
        if self.f == 0:
            self.i += 1
            self.f = self.frames
        return image
    def __add__(self, ss):
        self.images.extend(ss.images)
        return self


# a function that will play a song from the SD card.

def music(name):
    foundSong = False
    for songindex in range(0,8,1):
        if musiclist[songindex] in name:
            pygame.mixer.music.load(musicfilelist[songindex])
            print("playing " + musiclist[songindex])
            foundSong = True
            break
    if foundSong:
        pygame.mixer.music.play()
    
# Meows at you. Choose a random meow (there are 3 to choose from)     
def meow():
    rmeow = random.randint(1,4)
    meowfile = "meow" + str(rmeow) + ".wav"
    meowsound = pygame.mixer.Sound(meowfile)
    pygame.mixer.Sound.play(meowsound)

# plays the love sound effect
def love():
    pygame.mixer.music.load(lovefile)
    pygame.mixer.music.play()
    
    

# main program starts here!!

#surface = pygame.display.set_mode((mywidth,myheight))
# these lines load the face animations from sprite strips.
sleeptime = -1
FPS = 12
frames = FPS / 12
strips = [SpriteStripAnim('droidblink.png', (0,0,64,64), 32, 1, True, frames),
             SpriteStripAnim('droidheart.png', (0,0,64,64), 4, 1, True, frames),
             SpriteStripAnim('droidnotes0.png', (0,0,64,64), 8, 1, True, frames),
             SpriteStripAnim('happytalk.png', (0,0,64,64), 8, 1, True, frames)]
    
black = Color('black')
clock = pygame.time.Clock()
n = 0
strips[n].iter()
image = strips[n].next()
done = False
newAnim = False
talkAnim = False
songname = random.choice(musiclist)

# main loop looks for key presses (if keyboard attached), button presses, or RFID scans.
while not done:
    for e in pygame.event.get():
        if e.type == KEYUP:
            if e.key == K_ESCAPE:
                pygame.quit()
                sys.exit()
            elif e.key == K_RETURN:
                n += 1
                if n >= len(strips):
                    n = 0
                strips[n].iter()
                image = strips[n].next()

    # read from the RFID scanner
    id,text = reader.read_no_block()
    # GPIO pin for meow (pulled low if you press it)
    if GPIO.input(meow_pin) == 0:
        n = 1
        strips[n].iter()
        image = strips[n].next()
        FPS = 4
        sleeptime = 0.05
        meow()
        love()
        newAnim = True

    # if you're pressing the music pin and you're not currently talking,
    # start talking.
    elif GPIO.input(music_pin) == 0 and talkAnim == False:
        talkAnim = True
        rtalk = random.randint(0,1)
        talkfilename = talkfilelist[rtalk]
        pygame.mixer.music.load(talkfilename)
        pygame.mixer.music.play()
        songname = random.choice(musiclist)
        n = 3
        strips[n].iter()
        image = strips[n].next()
        FPS = 8

    # if you're done talking, now it's time to play music
    elif talkAnim == True and pygame.mixer.music.get_busy() == False:
        music(songname)
        n = 2
        strips[n].iter()
        image = strips[n].next()
        FPS = 4
        sleeptime = 0.05
        newAnim = True
        talkAnim = False
    # if you're currently playing music and you hit the cancel button, stop.
    elif GPIO.input(cancel_pin) == 0:
        pygame.mixer.music.stop()
        n = 0
        strips[n].iter()
        image = strips[n].next()
        FPS = 48
        sleeptime = -1
        newAnim = False
    
    # if we scanned a card, identify which one and set the music variable
    # to that song. This code starts talking. When talking is done
    # the song will play. 
    elif id != None:
        talkAnim = True
        rtalk = random.randint(0,1)
        talkfilename = talkfilelist[rtalk]
        pygame.mixer.music.load(talkfilename)
        pygame.mixer.music.play()
        songname = text
        n = 3
        strips[n].iter()
        image = strips[n].next()
        FPS = 8

    # if you're done making sound effects and animations, go back to the
    # default animation.
    elif pygame.mixer.music.get_busy() == False and newAnim == True:
        n = 0
        strips[n].iter()
        image = strips[n].next()
        FPS = 25
        sleeptime = -1
        newAnim = False

    # if you hit the quit button then quit.
    elif GPIO.input(quit_pin) == 0:
        pygame.quit()
        sys.exit()


    # if no input was detected, just refresh the screen with the next
    # frame in the animation.    
    surface.fill(black)
    surface.blit(image, (0,0))
    pygame.display.update()
    #pygame.display.flip()
    image = strips[n].next()
    #if sleeptime > 0:
    #    time.sleep(sleeptime)
    clock.tick(FPS)

