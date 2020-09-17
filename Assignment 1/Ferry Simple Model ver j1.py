# -*- coding: utf-8 -*-
"""
Created on Mon Sep 14 20:06:07 2020

@author: julivius

SEN9110 Simulation Packages
Assignment 1 - Building a small model
"""

import salabim as sim

class CarGenerator(sim.Component):
    def process(self):
        while True:
            Car()
            yield self.hold(1)
            
class Car(sim.Component):
    def process(self):
        # if trip.available_quantity() < 5:
            # Ferry()
        # yield self.get((trip,1))
        self.enter(carLane)
        if ferry.ispassive():
            ferry.activate()
        yield self.passivate()
        
        # self.unload()
        
    # def unload(self):
        # yield self.hold(5)

# class Vehicle(sim.Component):
    # def __init__(self,*args,**kwargs):
        # super().__init__(*args,**kwargs)
        # self.capacity = 75

class Ferry(sim.Component):
    def process(self):
        self.ismoving = False
        while True:
            while self.ismoving == False:    
                while len(carLane) < 40: #& self.ismoving == False:
                    yield self.passivate()
                if len(carLane) == 40:
                    self.ismoving = True
                    yield self.hold(15)
                if len(carLane) == 0:
                    self.ismoving = False
            self.car = carLane.pop()
            yield self.hold(5)
            self.car.activate()
        # yield self.hold(10)
        # yield self.put((trip,10))
            
env = sim.Environment(trace=True)
count = 0
CarGenerator()
ferry = Ferry()
carLane = sim.Queue("carLane")
# trip = sim.Resource("trip",capacity=15,anonymous=True)


env.run(till=60)
print()
carLane.print_statistics()
# trip.print_statistics()