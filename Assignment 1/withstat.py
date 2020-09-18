import salabim as sim
import numpy as np
import pandas as pd
import time, sys, random, os

CAR_NUMBERS = pd.read_csv("TimeTable.csv", sep=";")

SAILING_TIME = sim.Triangular(10,18,13)
NUMBER_OF_CARS = sim.Triangular(70,80,75)
PAYMENT_TIME = sim.Triangular(1,4,2)
LOADING_TIME = sim.Exponential(1/6) # 10 seconds per car
UNLOADING_TIME = sim.Exponential(5/60) # 5 seconds per time
WAITING_TIME_PREPAID = sim.Exponential(0.5) # minutes
PERCENTAGE_PREPAID = 0.2 

SIM_TIME = 60*24 # Time in minutes
REPLICATIONS = 10 # Number of experiment replications

class Car(sim.Component):
    def setup(self, cartype, paid, location):
        self.cartype = cartype # either tourist or employee
        self.paid = paid # true for prepaid, false for not prepaid
        self.location = location # either mainland or island

    def process(self):  
        # Go to the assigned booth and line depending on the cartype, prepaid and locations
        ## Employee type
        if self.cartype == "employee":
            if self.location == "mainland":
                self.enter(mainland_line1)
                
            else: 
                self.enter(island_line1)
                
        ## Tourists
        else: 
            # In case the tourist has prepaid 
            if self.paid:
                if self.location == "mainland":
                    self.enter(mainland_line2_1)
                    if prePaidBooth_mainland.ispassive():
                        prePaidBooth_mainland.activate()

                    self.enter(mainland_line2)

                    
                    
                else: 
                    self.enter(island_line2_1)
                    
                    if prePaidBooth_island.ispassive():
                        prePaidBooth_island.activate()

                    self.enter(island_line2)

            # In case the tourist still has to pay
            else: 
                if self.location == "mainland":
                    self.enter(mainland_line3_1)
                    if payingBooth_mainland.ispassive():
                        payingBooth_mainland.activate()

                    self.enter(mainland_line3)
                    
                    
                else: 
                    self.enter(island_line3_1)
                    
                    if payingBooth_island.ispassive():
                        payingBooth_island.activate()

                    self.enter(island_line3)
                    
            # Passivate the component
        yield self.passivate()
        
class CarGenerator(sim.Component):
    def setup(self, location, cartype):
        self.cartype = cartype # either tourist or employee
        self.location = location # either mainland or island

    def process(self):
        while True:
            #Get current time
            CurrentCarNumbers = CAR_NUMBERS[CAR_NUMBERS["time"]<= (env.now()/60)].tail(1)

            # Generate a car
            Car(cartype = self.cartype, paid = (random.random() < 0.2), location= self.location)

            # Wait for the correct amount of time until creating the next car
            ## Get the number of cars
            number_cars = int(CurrentCarNumbers[str(self.cartype) + "_" + str(self.location)])

            ## Calculate the time span the cars arrive in 
            time_span = int(CAR_NUMBERS["time"].iloc[CurrentCarNumbers.index + 1]) - int(CAR_NUMBERS["time"].iloc[CurrentCarNumbers.index])

            ## Check if number of cars is greater than zero, then wait the correct amount of time, otherwise wait for the time interval
            if number_cars > 0:
                # Interarrival times are based on an exponential equation
                yield self.hold(sim.Exponential(60*time_span / number_cars))
            else:
                yield self.hold(60*time_span)

class Ferry(sim.Component):
    def setup(self, capacity, carsonferry, ferryrides, location):
        self.capacity = capacity # indicates how much space there is on the ferry
        self.carsonferry = carsonferry # indicates how many cars there are currently on the ferry 
        self.ferryrides = ferryrides # counts the amount of ferryrides done
        self.location = location # the location of the ferry (either mainland or island)

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
                elif len(mainland_line2) > 0:
                    self.car = mainland_line2.pop()
                    self.carsonferry += 1
                    yield self.hold(LOADING_TIME.sample())
                elif len(mainland_line3) > 0:
                    self.car = mainland_line3.pop()
                    self.carsonferry += 1
                    yield self.hold(LOADING_TIME.sample())

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
                elif len(island_line2) > 0:
                    self.car = island_line2.pop()
                    self.carsonferry += 1
                    yield self.hold(LOADING_TIME.sample())
                elif len(island_line3) > 0:
                    self.car = island_line3.pop()
                    self.carsonferry += 1
                    yield self.hold(LOADING_TIME.sample())
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

            
class FerryOperator(sim.Component):
    def process(self):
        while True:
            # Load the ferry       
            CanadianFerry.activate()

            # Wait for 30 mins
            yield self.hold(30)

            # Give the go for departure
            departuretime.set(True)

               
            
            
class Server(sim.Component):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.activeTime = 0
        self.activeTimeManual = 0
        self.startProcessTime = -1

    def startUtilTime(self):
        self.startProcessTime = env.now()

    def endUtilTime(self):
        if self.startProcessTime >= 0:
            endNow = env.now()
            self.activeTime += endNow - self.startProcessTime
            self.startProcessTime = -1

    def getUtilization(self):
        return self.activeTime / (env.now() - self._creation_time)

    def getUtilizationManual(self):
        return self.activeTimeManual / (env.now() - self._creation_time)

class PrePaidBooth(Server):
    
    def setup(self, location):
        self.location = location # either mainland or island

    
    def process(self):
        while True:
            if self.location == "mainland":
                while len(mainland_line2_1) == 0:
                    yield self.passivate()

                self.startUtilTime()
                self.car = mainland_line2_1.pop()

                yield self.hold(WAITING_TIME_PREPAID.sample())

                self.car.activate()
                
            elif self.location == "island":
                while len(island_line2_1) == 0:
                    yield self.passivate()

                self.startUtilTime()
                self.car = island_line2_1.pop()

                yield self.hold(WAITING_TIME_PREPAID.sample())

                self.car.activate()

                
class PayingBooth(Server):
    
    def setup(self, location):
        self.location = location # either mainland or island

    
    def process(self):
        while True:
            if self.location == "mainland":
                while len(mainland_line3_1) == 0:
                    yield self.passivate()

                self.startUtilTime()
                self.car = mainland_line3_1.pop()

                yield self.hold(PAYMENT_TIME.sample())

                self.car.activate()
                
            elif self.location == "island":
                while len(island_line3_1) == 0:
                    yield self.passivate()

                self.startUtilTime()
                self.car = island_line3_1.pop()

                yield self.hold(PAYMENT_TIME.sample())

                self.car.activate()
                

def max(lst):
    cleanedlst = [x for x in lst if str(x) != 'nan']
    if len(cleanedlst)==0:
        return 0

    max = np.max(cleanedlst)
    return np.max(cleanedlst)

def avg(lst):
    cleanedlst = [x for x in lst if str(x) != 'nan']
    if len(cleanedlst)==0:
        return 0
    return sum(cleanedlst)/len(cleanedlst)

   

#queue statistics
employee_length = []
prepaid_length = []
paying_length = []

employee_95 = []
prepaid_95 = []
paying_95 = []

employee_queue = []
prepaid_queue = []
paying_queue = []

employee_queue_max = []
prepaid_queue_max = []
paying_queue_max = []


replications = 10
if len(sys.argv) > 1:
    replications = int(sys.argv[1])

if replications == 1:
    trace = True

for exp in range(0,replications):


    # Create the Environment
    env = sim.Environment(time_unit='minutes', trace= False)
    env.modelname("Canadian Ferries Simulation")

    # Create a ferry at the beginning of the simulation
    CanadianFerry = Ferry(capacity = NUMBER_OF_CARS.sample(), carsonferry = 0, ferryrides = 0, location = "mainland")

    # States
    departuretime = sim.State('departuretime', value=False)
    ferryloaded = sim.State('ferryloaded', value=False)

    #Queues
    mainland_line1, mainland_line2, mainland_line3 = sim.Queue('mainland_line1'), sim.Queue('mainland_line2'), sim.Queue('mainland_line3')
    island_line1, island_line2, island_line3 = sim.Queue('island_line1'), sim.Queue('island_line2'), sim.Queue('island_line3')
    mainland_line2_1, mainland_line3_1 = sim.Queue('mainland_line2_1'), sim.Queue('mainland_line3_1')
    island_line2_1, island_line3_1 = sim.Queue('island_line2_1'), sim.Queue('island_line3_1')

    # Create a ferry at the beginning of the simulation
    CanadianFerry = Ferry(capacity = NUMBER_OF_CARS.sample(), carsonferry = 0, ferryrides = 0, location = "mainland")

    # Activate the Ferry operators on 6:30
    FerryOperator(at=6.5*60)

    # Initiate the Car Generators
    CarGenerator(cartype="employee", location="island")
    CarGenerator(cartype="employee", location="mainland")
    CarGenerator(cartype="tourist", location="island")
    CarGenerator(cartype="tourist", location="mainland")

    prePaidBooth_mainland = PrePaidBooth(location="mainland")
    prePaidBooth_island = PrePaidBooth(location="island")
    payingBooth_mainland = PayingBooth(location="mainland")
    payingBooth_island = PayingBooth(location="island")

    env.run(duration=SIM_TIME)

    #TODO why suspend only length monitoring? Does everything need to be suspended?
    # Warm-up - don't collect statistics
    mainland_line1.length.monitor(False)
    mainland_line2.length.monitor(False)
    mainland_line3.length.monitor(False)
    mainland_line2_1.length.monitor(False)
    mainland_line3_1.length.monitor(False)

    island_line1.length.monitor(False)
    island_line2.length.monitor(False)
    island_line3.length.monitor(False)
    island_line2_1.length.monitor(False)
    island_line3_1.length.monitor(False)




    employee_length += [mainland_line1.length.mean()]
    employee_length += [island_line1.length.mean()]
    prepaid_length += [mainland_line2.length.mean() + mainland_line2_1.length.mean()]
    prepaid_length += [island_line2.length.mean() + island_line2_1.length.mean()]
    paying_length += [mainland_line3.length.mean() + mainland_line3_1.length.mean()]
    paying_length += [island_line3.length.mean() + island_line3_1.length.mean()]

    employee_95 += [mainland_line1.length.percentile(95)]
    employee_95 += [island_line1.length.percentile(95)]
    prepaid_95 += [mainland_line2.length.percentile(95) + mainland_line2_1.length.percentile(95)]
    prepaid_95 += [island_line2.length.percentile(95) + island_line2_1.length.percentile(95)]
    paying_95 += [mainland_line3.length.percentile(95) + mainland_line3_1.length.percentile(95)]
    paying_95 += [island_line3.length.percentile(95) + island_line3_1.length.percentile(95)]


    employee_queue += [mainland_line1.length_of_stay.mean()]
    employee_queue += [island_line1.length_of_stay.mean()]
    prepaid_queue += [mainland_line2.length_of_stay.mean() + mainland_line2_1.length_of_stay.mean()]
    prepaid_queue += [island_line2.length_of_stay.mean() + island_line2_1.length_of_stay.mean()]
    paying_queue += [mainland_line3.length_of_stay.mean() + mainland_line3_1.length_of_stay.mean()]
    paying_queue += [island_line3.length_of_stay.mean() + island_line3_1.length_of_stay.mean()]

    employee_queue_max += [mainland_line1.length_of_stay.maximum()]
    employee_queue_max += [island_line1.length_of_stay.maximum()]
    prepaid_queue_max += [mainland_line2.length_of_stay.maximum() + mainland_line2_1.length_of_stay.maximum()]
    prepaid_queue_max += [island_line2.length_of_stay.maximum() + island_line2_1.length_of_stay.maximum()]
    paying_queue_max += [mainland_line3.length_of_stay.maximum() + mainland_line3_1.length_of_stay.maximum()]
    paying_queue_max += [island_line3.length_of_stay.maximum() + island_line3_1.length_of_stay.maximum()]

print()
print()
print("employee length of queue mean [cars]:", avg(employee_length))
print("prepaid length of queue mean [cars]:", avg(prepaid_length))
print("paying length of queue mean [cars]:", avg(paying_length))
print()
print("employee length of queue mean 95% [cars]:", avg(employee_95))
print("prepaid length of queue mean 95% [cars]:", avg(prepaid_95))
print("paying length of queue mean 95% [cars]:", avg(paying_95))
print()
print()
print("employee_queueing average time [mins]:", avg(employee_queue))
print("prepaid_queueing average time [mins]:", avg(prepaid_queue))
print("paying_queueing average time [mins]:", avg(paying_queue))
print()
print("employee_queueing maximum time [mins]:", max(employee_queue))
print("prepaid_queueing maximum time [mins]:", max(prepaid_queue))
print("paying_queueing  maximum time [mins]:", max(paying_queue))
print()