# Imports
import salabim as sim
import numpy as np
import pandas as pd

# Variables
SAILING_TIME = sim.Triangular(10,18,13)
NUMBER_OF_CARS = sim.Triangular(70,80,75)
PAYMENT_TIME = sim.Triangular(1,4,2)
SIM_TIME = 60*24 # Time in minutes


# Create the Environment
env = sim.Environment()

env.run(duration=SIM_TIME)