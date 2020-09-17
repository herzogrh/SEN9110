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
        if trip.available_quantity() < 5:
            Ferry()
        yield self.get((trip,1))
        yield self.hold(1)
        self.unload()
        
    def unload(self):
        yield self.hold(5)

class Ferry(sim.Component):
    def process(self):
        yield self.hold(10)
        yield self.put((trip,10))
        
            
env = sim.Environment(trace=True)
count = 0
CarGenerator()
#carLane = sim.Queue("carLane")
trip = sim.Resource("trip",capacity=15,anonymous=True)


env.run(till=60)
print()
trip.print_statistics()