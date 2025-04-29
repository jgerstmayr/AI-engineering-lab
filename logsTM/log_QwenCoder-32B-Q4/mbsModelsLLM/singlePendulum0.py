# ** given model description: **
# Simple mathematical pendulum with the following properties: point mass
# m = 1.25 kg, inelastic string length = 1.2 m (fixed distance between ground
# and mass point), and gravity g = 9.81 m/s^2 which acts in negative y-direction,
# while the pendulum moves in the x-y plane. The reference configuration of the
# pendulum is such that the string has an angle (positive rotation sense) of 12 degrees
# relative to the negative y-axis. Air resistance is neglected.
#import Exudyn library and utilities
import exudyn as exu
from exudyn.utilities import *
import numpy as np

#set up new multibody system to work with
SC = exu.SystemContainer()
mbs = SC.AddSystem()

#Create a ground object as an inertial reference frame for the multibody system.
oGround = mbs.CreateGround(referencePosition=[0,0,0])

#Create a point mass object with specified mass at reference position with optional initial conditions
oMass = mbs.CreateMassPoint(physicsMass=1.25, referencePosition=[1.2*np.sin(np.radians(12)), -1.2*np.cos(np.radians(12)), 0], 
                            initialDisplacement=[0,0,0],  
                            initialVelocity=[0,0,0],    
                            gravity=[0,-9.81,0])          

#Create a rigid distance constraint between two points on different bodies or between a body and the ground.
oDistance = mbs.CreateDistanceConstraint(bodyNumbers=[oGround, oMass], 
                                         localPosition0 = [0,0,0], 
                                         localPosition1 = [0,0,0], 
                                         distance=1.2)

#Assemble has to be called just before solving or system analysis (after AddSensor!).
mbs.Assemble()

tEnd = 2
stepSize = 0.001

simulationSettings = exu.SimulationSettings()
simulationSettings.solutionSettings.solutionWritePeriod = 1e-2
simulationSettings.solutionSettings.sensorsWritePeriod = 1e-2
simulationSettings.timeIntegration.numberOfSteps = int(tEnd/stepSize) #must be integer
simulationSettings.timeIntegration.endTime = tEnd

SC.visualizationSettings.nodes.drawNodesAsPoint=False
SC.visualizationSettings.nodes.defaultSize=0.05
SC.visualizationSettings.nodes.tiling = 32


#start solver:
mbs.SolveDynamic(simulationSettings)


