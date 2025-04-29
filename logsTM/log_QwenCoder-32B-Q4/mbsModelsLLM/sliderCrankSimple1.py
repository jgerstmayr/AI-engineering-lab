# ** given model description: **
# Simple slider-crank mechanism modelled with two mass points that are connected
# with distance constraints. The crank is modelled with a point mass m1 = 0.75
# kg, located at radius r = 0.8 m (initially located at x=0, y=r) and constrained
# to ground with a distance r; the slider is a point mass m2 = 0.5 kg, initially
# located at xSlider = 2 m and ySlider = 0. The connecting rod is only represented
# as distance constraint between crank mass and slider mass. Add a spherical
# joint between mass 1 and ground and only constrain the z-axis motion and a second
# spherical joint to constrain the y- and z-axes motion of mass 2. A force fx = 15
# acts on the slider in positive x-direction. The system is initially at rest,
# and no gravity is applied.
#import Exudyn library and utilities
import exudyn as exu
from exudyn.utilities import *
import numpy as np

#set up new multibody system to work with
SC = exu.SystemContainer()
mbs = SC.AddSystem()

#Create a ground object as an inertial reference frame for the multibody system.
oGround = mbs.CreateGround(referencePosition=[0,0,0])

#Create a point mass object for the crank with specified mass at reference position
oMass1 = mbs.CreateMassPoint(physicsMass=0.75, referencePosition=[0,0.8,0], 
                            initialDisplacement=[0,0,0],  
                            initialVelocity=[0,0,0],    
                            gravity=[0,0,0])

#Create a point mass object for the slider with specified mass at reference position
oMass2 = mbs.CreateMassPoint(physicsMass=0.5, referencePosition=[2,0,0], 
                            initialDisplacement=[0,0,0],  
                            initialVelocity=[0,0,0],    
                            gravity=[0,0,0])

#Create a distance constraint between the crank and the slider
oDistance = mbs.CreateDistanceConstraint(bodyNumbers=[oMass1, oMass2], 
                                         localPosition0 = [0,0,0], 
                                         localPosition1 = [0,0,0], 
                                         distance=None)

#Applies a force in the x-direction to the slider
loadMassPoint = mbs.CreateForce(bodyNumber=oMass2, loadVector=[15,0,0])

#Create a spherical joint between the ground and the crank, constraining only the z-axis
mbs.CreateSphericalJoint(bodyNumbers=[oGround, oMass1],
                         position=[0,0.8,0], 
                         constrainedAxes=[0,0,1])

#Create a spherical joint between the ground and the slider, constraining the y- and z-axes
mbs.CreateSphericalJoint(bodyNumbers=[oGround, oMass2],
                         position=[2,0,0], 
                         constrainedAxes=[0,1,1])

#Assemble has to be called just before solving or system analysis (after AddSensor!).
mbs.Assemble()

tEnd = 1
stepSize = 0.001

simulationSettings = exu.SimulationSettings()
simulationSettings.solutionSettings.solutionWritePeriod = 5e-2
simulationSettings.solutionSettings.sensorsWritePeriod = 1e-2
simulationSettings.timeIntegration.numberOfSteps = int(tEnd/stepSize) #must be integer
simulationSettings.timeIntegration.endTime = tEnd

SC.visualizationSettings.nodes.drawNodesAsPoint=False
SC.visualizationSettings.nodes.defaultSize=0.05
SC.visualizationSettings.nodes.tiling = 32


#start solver:
mbs.SolveDynamic(simulationSettings)


