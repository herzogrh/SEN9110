# Imports
import salabim as sim, numpy as np, pandas as pd
import time, sys

#Time data
CAR_NUMBERS = pd.read_csv("TimeTable.csv", sep=";")
CAR_NUMBERS[CAR_NUMBERS["Time"]< 15].tail(1)

# Variables
SAILING_TIME = sim.Triangular(10,18,13)
NUMBER_OF_CARS = sim.Triangular(70,80,75)
PAYMENT_TIME = sim.Triangular(1,4,2)
SIM_TIME = 60*24 # Time in minutes
LOADING_TIME = 1/6 # 10 seconds per car
UNLOADING_TIME = 5/60 # 5 seconds per time
WAITING_TIME_PREPAID = 0.5 # minutes
PERCENTAGE_PREPAID = 0.2 

REPLICATIONS = 10 # Number of experiment replications

# Components
class Car(sim.Component):
    def __init__(self, cartype, paid, location, *args, **kwargs):
        sim.Component.__init__(self, *args, **kwargs)
        self.cartype = cartype # either tourist or employee
        self.paid = paid # true for prepaid, false for not prepaid
        self.location = location # either mainland or island

    def process(self):  
        # Assign itself to the correct queue

        #
        yield self.hold(1)


class CarGenerator(sim.Component):
    def process(self):
        while True:
            #Get current time
            CurrentCarNumbers = CAR_NUMBERS[CAR_NUMBERS["Time"]< (env.now()/60)].tail(1)

            # Mainland ----------------------
            ## Generate Cars based on time


            #Generate 

            Car(cartype = "tourist", paid = False, location="mainland")


            yield self.hold(60)


# Create the Environment
env = sim.Environment(time_unit='minutes', trace= True)
env.modelname("Canadian Ferries Simulation")
CarGenerator()
env.run(duration=SIM_TIME)
print()


#Comp