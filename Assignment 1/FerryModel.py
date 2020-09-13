# Imports
import salabim as sim
import numpy as np
import pandas as pd

# Variables
SAILING_TIME = sim.Triangular(10,18,13)
NUMBER_OF_CARS = sim.Triangular(70,80,75)
PAYMENT_TIME = sim.Triangular(1,4,2)
SIM_TIME = 60*24 # Time in minutes
LOADING_TIME = 1/6 # 10 seconds per car
UNLOADING_TIME = 5/60 # 5 seconds per time
WAITING_TIME_PREPAID = 0.5 # minutes

# Components
class Car(sim.Component):
    def __init__(self, length, *args, **kwargs):
        sim.Component.__init__(self, *args, **kwargs)
        self.cartype = cartype
        self.paid = paid
    def process(self):  



# Create the Environment
env = sim.Environment()

env.run(duration=SIM_TIME, time_unit='minutes')
env.animate(True)
env.modelname("Canadian Ferries Simulation")