import os
import choreo

p0_name = "\"Player 1\\n■□□□\""
p1_name = "\"Player 2\\n■■□□\""
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
