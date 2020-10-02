# coding: utf-8
"""
Created on Fri Oct  2 14:11:22 2020

@author: 
    - Julivius Prawira
    - Kasper Hartveld
    - Rico Herzog
    - Tess Kim
    
"""
# %% Package

import salabim as sim
#import numpy as np
import pandas as pd
import random, os
#import time, sys

# %% Global Setting

dir_path = os.path.dirname(os.path.realpath(__file__))
CAR_NUMBERS = pd.read_csv(dir_path+"\\TimeTable.csv", sep=";")
#CAR_NUMBERS = pd.read_csv("TimeTable.csv", sep=";")

# Time unit in minutes
SAILING_TIME = sim.Triangular(10,18,13)
NUMBER_OF_CARS = sim.Triangular(70,80,75)
PAYMENT_TIME = sim.Triangular(1,4,2)
PAYMENT_HICCUP_TIME = 0.25 + sim.Uniform(0.5,0.75) + 0.25 # Walk elsewhere + Meet supervisor + Return
PAYMENT_HICCUP_CHANCE = 0.05
LOADING_TIME = sim.Exponential(1/6) # 10 seconds per car
UNLOADING_TIME = sim.Exponential(5/60) # 5 seconds per car
WAITING_TIME_PREPAID = sim.Exponential(0.5) # minutes
PERCENTAGE_PREPAID = 0.2 

SIM_TIME = 60*24 # Time in minutes
REPLICATIONS = 10 # Number of experiment replications
ANIMATION = False
ANIMATION_TIME_CAR = 5
TRACE = True

# %% Car Component

class Car(sim.Component):
    def setup(self, cartype, paid, location):
        self.cartype = cartype # either tourist or employee
        self.paid = paid # true for prepaid, false for not prepaid
        self.location = location # either mainland or island
        self.inittime = env.now() # get the time the car was instantiated

    def process(self):  
        # Go to the assigned booth and line depending on the cartype, prepaid and locations
        ## Employee type
        if self.cartype == "employee":
            if self.location == "mainland":
                if ANIMATION:
                        sim.Animate(image="employee_car_mainland.png", t1=env.now()+ANIMATION_TIME_CAR, x0=50, y0=400, x1=75, alpha1=0)
                self.enter(mainland_line1)
                
            else: 
                if ANIMATION:
                        sim.Animate(image="employee_car_island.png", t1=env.now()+ANIMATION_TIME_CAR, x0=900, y0=400, x1=875, alpha1=0)
                self.enter(island_line1)
                
        ## Tourists
        else: 
            # In case the tourist has prepaid 
            if self.paid:
                if self.location == "mainland":

                    # Animate
                    if ANIMATION:
                        sim.Animate(image="tourist_car_mainland.png", t1=env.now()+ANIMATION_TIME_CAR, x0=50, y0=250, x1=75, alpha1=0)

                    # Wait until the prepaid booth is free
                    yield self.request(prepaid_booth_mainland)

                    # Do the 
                    yield self.hold(WAITING_TIME_PREPAID.sample())

                    # Free up the prepaid booth
                    self.release(prepaid_booth_mainland) 

                    # Enter the assigned waiting line
                    self.enter(mainland_line2)

                # Same for the island
                else: 
                    if ANIMATION:
                        sim.Animate(image="tourist_car_island.png", t1=env.now()+ANIMATION_TIME_CAR, x0=900, y0=250, x1=875, alpha1=0)
                    yield self.request(prepaid_booth_island)
                    yield self.hold(WAITING_TIME_PREPAID.sample())
                    self.release(prepaid_booth_island) 
                    self.enter(island_line2)

            # In case the tourist still has to pay
            else: 
                if self.location == "mainland":
                    if ANIMATION:
                        sim.Animate(image="tourist_car_mainland.png", t1=env.now()+ANIMATION_TIME_CAR, x0=50, y0=100, x1=75, alpha1=0)
                    yield self.request(payment_booth_mainland)
                    yield self.hold(PAYMENT_TIME.sample())
                    if random.random < PAYMENT_HICCUP_CHANCE:
                        yield self.hold(PAYMENT_HICCUP_TIME.sample())
                    self.release(payment_booth_mainland)
                    self.enter(mainland_line3)
                    
                    
                else: 
                    if ANIMATION:
                        sim.Animate(image="tourist_car_island.png", t1=env.now()+ANIMATION_TIME_CAR, x0=900, y0=100, x1=875, alpha1=0)
                    yield self.request(payment_booth_island)
                    yield self.hold(PAYMENT_TIME.sample())
                    self.release(payment_booth_island)
                    self.enter(island_line3)
                    
        # Passivate the component
        yield self.passivate()

    # Set waiting time tallies whenever a car enters the ferry
    def setTally(self):
        total_waiting_time = env.now() - self.inittime

        if self.cartype == "employee":
            Waitingtime_employee.tally(total_waiting_time)
        elif self.paid:
            Waitingtime_tourist_prepaid.tally(total_waiting_time)
        else:
            Waitingtime_tourist_unpaid.tally(total_waiting_time)

        yield self.passivate()

#%% Car Generator Component

class CarGenerator(sim.Component):
    def setup(self, location, cartype):
        self.cartype = cartype # either tourist or employee
        self.location = location # either mainland or island

    def process(self):
        while True:
            #Get current time
            CurrentCarNumbers = CAR_NUMBERS[CAR_NUMBERS["time"]<= (env.now()/60)].tail(1)

            ## Get the number of cars
            number_cars = int(CurrentCarNumbers[str(self.cartype) + "_" + str(self.location)])

            ## Calculate the time span the cars arrive in 
            time_span = int(CAR_NUMBERS["time"].iloc[CurrentCarNumbers.index + 1]) - int(CAR_NUMBERS["time"].iloc[CurrentCarNumbers.index])

            ## Check if number of cars is greater than zero, then wait the correct amount of time, otherwise wait for the time interval
            if number_cars > 0:
                # Generate a car
                Car(cartype = self.cartype, paid = (random.random() < 0.2), location= self.location)

                # Wait for the correct amount of time until creating the next car
                # Interarrival times are based on an exponential equation
                yield self.hold(sim.Exponential(60*time_span / number_cars))
            else:
                yield self.hold(60*time_span)

#%% Ferry Component
class Ferry(sim.Component):
    def setup(self, capacity, carsonferry, ferryrides, location):
        self.capacity = capacity # indicates how much space there is on the ferry
        self.carsonferry = carsonferry # indicates how many cars there are currently on the ferry 
        self.ferryrides = ferryrides # counts the amount of ferryrides done
        self.location = location # the location of the ferry (either mainland or island)
    
    #Repetetive task of the ferry
    def process(self):
        while True: 
            yield from self.load()

            yield self.wait(departuretime, ferryloaded, all=True)

            yield from self.cruise()

            yield from self.unload()


    # Cruising process of the ferry
    def cruise(self):
        # Set the departure time to False
        departuretime.set(False)

        # Tally the Ferrydelay
        Ferrydelay.tally(env.now()-self.ferryrides*30+60*7)

        # Add one more ride to the ferry ride attribute
        self.ferryrides += 1

        # Cruise
        yield self.hold(SAILING_TIME.sample())

        # Change the location of the ferry
        if self.location == "mainland":
            self.location = "island"
        else:
            self.location = "mainland"
        

    # Loading process of the ferry
    def load(self):  
        # Determine the capacity
        self.capacity = NUMBER_OF_CARS.sample()

        # As long as there is space left, check the waiting lines and fill up the space
        while self.capacity > self.carsonferry:            
            # Check for departure 
            if departuretime.get():
                break
            
            # Check location
            if self.location == "mainland":
                # Check if there are any cars left in the queues 
                if len(mainland_line1) > 0:
                    self.car = mainland_line1.pop()
                    self.carsonferry += 1
                    yield self.hold(LOADING_TIME.sample())
                    self.car.activate(process='setTally')
                elif len(mainland_line2) > 0:
                    self.car = mainland_line2.pop()
                    self.carsonferry += 1
                    yield self.hold(LOADING_TIME.sample())
                    self.car.activate(process='setTally')
                elif len(mainland_line3) > 0:
                    self.car = mainland_line3.pop()
                    self.carsonferry += 1
                    yield self.hold(LOADING_TIME.sample())
                    self.car.activate(process='setTally')

                # If no cars are left, set the ferryloaded state to true and check again in 5 mins
                else:
                    ferryloaded.set(True)
                    yield self.hold(5)


            # Same goes for the Island
            if self.location == "island":
                if len(island_line1) > 0:
                    self.car = island_line1.pop()
                    self.carsonferry += 1
                    yield self.hold(LOADING_TIME.sample())
                    self.car.activate(process='setTally')
                elif len(island_line2) > 0:
                    self.car = island_line2.pop()
                    self.carsonferry += 1
                    yield self.hold(LOADING_TIME.sample())
                    self.car.activate(process='setTally')
                elif len(island_line3) > 0:
                    self.car = island_line3.pop()
                    self.carsonferry += 1
                    yield self.hold(LOADING_TIME.sample())
                    self.car.activate(process='setTally')
                else:
                    ferryloaded.set(True)
                    yield self.hold(5)

        # When the maximum capacity is reached, set the ferry to loaded
        ferryloaded.set(True)

    # Unloading of the ferry
    def unload(self):
        for i in range(self.carsonferry):
            yield self.hold(UNLOADING_TIME.sample())
        self.carsonferry = 0
        ferryloaded.set(False)

#%% Ferry Operator Component
class FerryOperator(sim.Component):
    def process(self):
        while True:
            # Load the ferry       
            CanadianFerry.activate()

            # Wait for 30 mins
            yield self.hold(30)

            # Give the go for departure
            departuretime.set(True)

#%% Booth Operator
            
class BoothOperator(sim.Component):
    def process(self):
        # Add an additional booth to the Mainland when initiated on 9:00
        payment_booth_mainland.set_capacity(2)

        # Remove the additional booth again on 12:00
        yield self.hold(3*60)
        payment_booth_mainland.set_capacity(1)

        # Add an additional booth on the island on 15:00
        yield self.hold(3*60)
        payment_booth_island.set_capacity(2)

        # Remove the additional booth on 17:00
        yield self.hold(2*60)
        payment_booth_island.set_capacity(1)

        # Passivate
        yield self.passivate()

#%%Animation Code
def do_animation():
    if ANIMATION: 
        # Enable animation
        env.animate(True)
        env.background_color('20%gray')

        # Mainland queues
        qm1 = sim.AnimateQueue(mainland_line1, x=100, y=400, title='Mainland line 1 - Employees', direction='e', id='green')
        qm2 = sim.AnimateQueue(mainland_line2, x=100, y=250, title='Mainland line 2 - Tourists prepaid', direction='e', id='green')
        qm3 = sim.AnimateQueue(mainland_line3, x=100, y=100, title='Mainland line 3 - Tourists', direction='e', id='green')

        # Mainland queues
        qm1 = sim.AnimateQueue(island_line1, x=800, y=400, title='Island line 1 - Employees', direction='w', id='blue')
        qm2 = sim.AnimateQueue(island_line2, x=800, y=250, title='Island line 2 - Tourists prepaid', direction='w', id='blue')
        qm3 = sim.AnimateQueue(island_line3, x=800, y=100, title='Island line 3 - Tourists', direction='w', id='blue')

        # Monitors
        m1 = sim.AnimateMonitor(mainland_line1.length, x=100, y=1000, width=200, height=80, horizontal_scale=5, vertical_scale=5)
        m2 = sim.AnimateMonitor(island_line1.length, x=800, y=1000, width=200, height=80, horizontal_scale=5, vertical_scale=5)
        m3 = sim.AnimateMonitor(Ferrydelay, x=500, y=1000, width=200, height=80, horizontal_scale=5, vertical_scale=5)

        #Ferry in the middle
        sim.Animate(image="ferry.png", x0=500, y0=400)

    else:
        env.animate(False)
        
#%% Run Environment

# Create the Environment
env = sim.Environment(time_unit='minutes', trace= TRACE)
env.modelname("Canadian Ferries Simulation")

# States
departuretime = sim.State('departuretime', value=False)
ferryloaded = sim.State('ferryloaded', value=False)

# Queues
mainland_line1, mainland_line2, mainland_line3 = sim.Queue('mainland_line1'), sim.Queue('mainland_line2'), sim.Queue('mainland_line3')
island_line1, island_line2, island_line3 = sim.Queue('island_line1'), sim.Queue('island_line2'), sim.Queue('island_line3')
mainland_line2_1, mainland_line3_1 = sim.Queue('mainland_line2_1'), sim.Queue('mainland_line3_1')
island_line2_1, island_line3_1 = sim.Queue('island_line2_1'), sim.Queue('island_line3_1')

# Create a ferry at the beginning of the simulation
CanadianFerry = Ferry(capacity = NUMBER_OF_CARS.sample(), carsonferry = 0, ferryrides = 0, location = "mainland")

# Activate the Ferry operators on 6:30
FerryOperator(at=6.5*60)

# Activate the Booth operator on 9:00
BoothOperator(at=9*60)

# Initiate the Car Generators
CarGenerator(cartype="employee", location="island")
CarGenerator(cartype="employee", location="mainland")
CarGenerator(cartype="tourist", location="island")
CarGenerator(cartype="tourist", location="mainland")

# Resources
payment_booth_mainland = sim.Resource('payment_booth_mainland', capacity=1)
payment_booth_island = sim.Resource('payment_booth_island', capacity=1)
prepaid_booth_mainland = sim.Resource('prepaid_booth_mainland', capacity=1)
prepaid_booth_island = sim.Resource('prepaid_booth_island', capacity=1)

# Monitors
Waitingtime_tourist_prepaid = sim.Monitor('Waitingtime_tourist_prepaid') #tally
Waitingtime_tourist_unpaid = sim.Monitor('Waitingtime_tourist_unpaid') #tally
Waitingtime_employee = sim.Monitor('Waitingtime_employee') #tally

Ferrydelay = sim.Monitor(name='Ferrydelay', level=True, initial_tally=0)

# Calls the function which has all the animation code in
do_animation()

# Run the experiments
env.run(duration=SIM_TIME)
#%% Sandbox