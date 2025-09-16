import pyaudio
import numpy as np
import pygame #Add Flappy bird
import matplotlib.pyplot as plt
import random
import math
import scipy.fftpack as fftpack
import librosa

'''
POSSIBLE OVERSIGHT: 
    - Lower notes have greater margin for error so 
    certain notes like eb to d is iffy
REMEMBER:
    - Close program through pygame window

To do:
    -tuning is buggy and innacurate
    -Add Flappy Bird
'''

#Constants -------------------------------------
CHUNK = 1024*6
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 1000
WHITE = (255,255,255)
BLACK = (0,0,0)
DARK_GREEN = (100,255,150)
PLOT_RANGE = 20000
SIDE_NOTE_INERVALS = SCREEN_HEIGHT/12
WIDTH_OF_OBSTACLE = 70
AMOUNT_PER_PASS = 15
AMOUNT_OF_OBSTACLES = 3
BALL_X_CORD = 80


#CONDITIONS ----------------
graphM = False #Matlab
checkCollision = True #Check Collisions


# Methods ------------------------------------------------
A4 = 440.0
#HZ to Note Chain
NOTES = ['A', 'A♯', 'B', 'C', 'C♯', 'D', 'D♯', 'E', 'F', 'F♯', 'G', 'G♯']

def get_note_name(freq):
    
    note_number = 12 * math.log2(freq / 440) + 49  
    note_number = round(note_number)
        
    nearest_note_index = (note_number - 1 ) % len(NOTES)
    note = NOTES[nearest_note_index]
    
    octave = (note_number + 8 ) // len(NOTES)
    return f"{note}{octave}", nearest_note_index



def get_frequencies(np_data, RATE):
    """
    # Perform FFT on the audio data
    fft_data = scipy.fftpack.fft(np_data)
    freqs = np.fft.fftfreq(len(fft_data))

    # Get the magnitude of the FFT results
    magnitude = np.abs(fft_data)

    # Get the positive frequencies
    pos_freqs = freqs[:len(freqs) // 2] * RATE
    pos_magnitude = magnitude[:len(magnitude) // 2]
    """
    fft_data = fftpack.fft(np_data)
    freqs = fftpack.fftfreq(len(fft_data)) * RATE
    # Get dominant frequency
    dominant_freq = freqs[np.argmax(np.abs(fft_data))]
    return dominant_freq



def volume_meter(amplitude):
    if amplitude < PLOT_RANGE:
        volume = "-"*int(amplitude/1000)
        return f"[{volume}]"
    return "TOO LOUD"

def drawCircle(screen, color, cords, rad):
    pygame.draw.circle(screen,color,cords,rad)



#Obstacle --------------------------------------------------
class Obstacle:
    '''
    Obstacle -
    X Coordinate
    Gap Size
    Y Cordinate of Gap
    
    All created on initialization of Obstacle
    '''
    def __init__(self, x, gp):
        self.xCord = x
        self.gapSize = gp
        self.gapY = random.randint(0, 11) * SIDE_NOTE_INERVALS

    def drawOb(self):
        #Draw Pipe to be filled
        rect = pygame.Rect(self.xCord,0,WIDTH_OF_OBSTACLE,SCREEN_HEIGHT)
        pygame.draw.rect(screen, BLACK, rect)

        #print(f"{self.xCord} : {self.gapY}")
        #Draw Gap over Pipe
        rect = pygame.Rect(
            self.xCord, #X
            self.gapY-10, #Y
            WIDTH_OF_OBSTACLE, #Wid
            self.gapSize #Len
        )
        pygame.draw.rect(screen, WHITE, rect)

    def moveOb(self,amount):
        self.xCord = self.xCord - amount


#SET UP --------------------------------------------------
p = pyaudio.PyAudio()
stream = p.open(
    format=FORMAT,
    channels=CHANNELS,
    rate=RATE,
    input=True,
    frames_per_buffer=CHUNK
)



screen = pygame.display.set_mode((SCREEN_WIDTH,SCREEN_HEIGHT))
Clock =  pygame.time.Clock()
pygame.font.init() # For text
my_font = pygame.font.SysFont('Comic Sans MS', 30)



# Run Vars ---------------------------------------

run = True
screen.fill(WHITE)

note = ""
indexOfNote = -1

if(graphM):
    fig = plt.gcf()
    fig.show()
    fig.canvas.draw()

obs = [] #Obstacles
obs.append(Obstacle(SCREEN_WIDTH,SIDE_NOTE_INERVALS))
notSpawnedObs = AMOUNT_OF_OBSTACLES-1 #Account for first spawn

yvalue = None

#Loop
while run:

    #Check Collision ----------
    if checkCollision and yvalue is not None:
        if obs[0].xCord <= BALL_X_CORD and obs[0].xCord+WIDTH_OF_OBSTACLE >= BALL_X_CORD:
            if yvalue < obs[0].gapY or yvalue > (obs[0].gapY+obs[0].gapSize):
                run = False

    #READ CHUNK
    data = stream.read(CHUNK)
    #print(data)
    #Convert from base 16
    np_data = np.frombuffer(data, dtype=np.int16)
    #print(np_data)
    #process data
    
    #Find hz
    dominant_freq = get_frequencies(np_data, RATE)
    
    #Map to note
    amplitude = max(np_data)
    if amplitude < 500 or dominant_freq is 0.0:
        note = "No Audio"
    else:
        #print(dominant_freq)
        note = librosa.hz_to_note(dominant_freq)
        #print(note[0:len(note)-1])
        indexOfNote = NOTES.index(note[0:len(note)-1])
        # note,indexOfNote = get_note_name(dominant_freq)

    #Pygame --------------------------------
    screen.fill(WHITE)
    distanceBetweenObs = SCREEN_WIDTH/AMOUNT_OF_OBSTACLES
    
    #Obstacles
    obToRemove = None
    for ob in obs:
        ob.drawOb()
        ob.moveOb(AMOUNT_PER_PASS)
        if(ob.xCord < 0-WIDTH_OF_OBSTACLE):
            obToRemove = ob
    if obToRemove is not None:
        obs.remove(obToRemove)
        obs.append(Obstacle(SCREEN_WIDTH,SIDE_NOTE_INERVALS))
    
    #Spawn in new obs, check most recently added ob
    if notSpawnedObs > 0 and obs[len(obs)-1].xCord < SCREEN_WIDTH-distanceBetweenObs:
        obs.append(Obstacle(SCREEN_WIDTH,SIDE_NOTE_INERVALS))
        notSpawnedObs -= 1


    #Display curr note
    text_surface = my_font.render(note, False, DARK_GREEN)
    screen.blit(text_surface, (SCREEN_WIDTH/2,SCREEN_HEIGHT/2))
    #Display notes on left
    for i in range(0,len(NOTES)):
        text_surface = my_font.render(NOTES[i], False, DARK_GREEN)
        yvalue = SIDE_NOTE_INERVALS*i + 10
        screen.blit(text_surface, (0,yvalue))
    #Display ball on note
    if indexOfNote != -1:
        yvalue = (SIDE_NOTE_INERVALS*indexOfNote) + 30
        drawCircle(screen,BLACK,[BALL_X_CORD,yvalue],20)
    
    
    #Matplotlib ---------------
    if(graphM):
        volume = volume_meter(amplitude)
        plt.title(f"VOLUME : {volume}")
        plt.xlim([0,CHUNK])
        plt.ylim([-PLOT_RANGE,PLOT_RANGE])
        plt.plot(np_data)
        fig.canvas.draw()
        fig.canvas.flush_events()
        fig.clear()
    
    pygame.display.update()
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False

print("Game Over! --------------------------")
    
plt.close()
exit()