import os
from pydub import AudioSegment
from pydub.playback import play
import random
import choreo

p0_name = "\"■□□□\""
p1_name = "\"■■□□\""
p_names = [p0_name, p1_name]

def make_chart(name:str, chor:choreo.Choreography):
    # open file
    chart = open(f"{name}.txt", "w")
    # write "@startuml\n" into it
    chart.write("@startuml\n")
    # for each arrow, write p0/p1 name, " -> ", matching name
    for arrow in chor.arrows:
        chart.write(f"{p_names[arrow.recv.target]} -> {p_names[arrow.send.target]}\n")
    # write @enduml into it
    chart.write("@enduml")
    # close file
    chart.close()

def view_chart(name:str):
    os.system(f"java -jar plantuml.jar {name}.txt")
    os.system(f"eog {name}.png &")

def delete_chart_raw(name:str):
    os.system(f"rm {name}.txt")

def chart_choreography(name:str, chor:choreo.Choreography):
    make_chart(name, chor)
    view_chart(name)
    delete_chart_raw(name)


# given a directory, play a random sound
# TODO: current issue: python file cant seem to find/access audio driver (?) despite being sudo'd.
def play_random_sound(directory:str):
    # src: https://stackoverflow.com/questions/2152898/filtering-a-list-of-strings-based-on-contents
    # but also adrian brasoveanu's code
    files = [file for file in os.listdir(directory) if '.ogg' in file]
    #os.system(f"play -q {random.choice(files)}")
    os.environ['SDL_AUDIODRIVER'] = 'pipewire'
    sfx = AudioSegment.from_ogg(f"{directory}/{random.choice(files)}")
    play(sfx)
