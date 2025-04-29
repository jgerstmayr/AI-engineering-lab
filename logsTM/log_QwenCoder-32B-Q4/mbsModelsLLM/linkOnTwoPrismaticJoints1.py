# ** given model description: **
# A system consisting of two mass points connected by a distance constraint.
# The first mass m1 = 12.5 kg is initially located at x0 = 1 m (other coordinates
# are 0) and can freely move only along the x-axis, while y-axis and z-axis are
# constrained by a spherical joint. The second mass m2 = 2.5 kg is initially located
# at z0 = 0.5 m (other coordinates are 0) and can move only freely along the
# z-axis, while the other two axes are constrained by a spherical joint. Furthermore,
# a distance constraint is added between the two mass points and the length
# shall be computed automatically. A spring with stiffness = 750 N/m is used to
# connect mass m1 and ground at [0,0,0]. Gravity g = 11.15 m/s^2 acts in positive
# x-direction, and no further forces or damping are applied.
#import Exudyn library and utilities
import exudyn as exu
from exudyn.utilities import *
import numpy as np

#set up new multibody system to work with
SC = exu.SystemContainer()
mbs = SC.AddSystem()

#Create a ground object as an inertial reference frame for the multibody system.
oGround = mbs.CreateGround(referencePosition=[0,0,0])

#Create the first mass point m1 with specified mass at reference position with optional initial conditions
oMass1 = mbs.CreateMassPoint(physicsMass=12.5, referencePosition=[1,0,0], 
                             initialDisplacement=[0,0,0],  
                             initialVelocity=[0,0,0],    
                             gravity=[11.15,0,0])          

#Create the second mass point m2 with specified mass at reference position with optional initial conditions
oMass2 = mbs.CreateMassPoint(physicsMass=2.5, referencePosition=[0,0,0.5], 
                             initialDisplacement=[0,0,0],  
                             initialVelocity=[0,0,0],    
                             gravity=[11.15,0,0])          

#Create a linear spring system between the first mass point and the ground.
oSpring = mbs.CreateSpringDamper(bodyNumbers=[oGround, oMass1], 
                                  localPosition0=[0,0,0], 
                                  localPosition1=[0,0,0], 
                                  referenceLength=None, 
                                  stiffness=750, damping=0)

#Create a spherical joint between the ground and the first mass point, constraining y and z axes.
mbs.CreateSphericalJoint(bodyNumbers=[oGround, oMass1],
                         position=[1,0,0], 
                         constrainedAxes=[0,1,1])

#Create a spherical joint between the ground and the second mass point, constraining x and y axes.
mbs.CreateSphericalJoint(bodyNumbers=[oGround, oMass2],
                         position=[0,0,0.5], 
                         constrainedAxes=[1,1,0])

#Create a distance constraint between the two mass points.
oDistance = mbs.CreateDistanceConstraint(bodyNumbers=[oMass1, oMass2], 
                                         localPosition0 = [0,0,0], 
                                         localPosition1 = [0,0,0], 
                                         distance=None)

#Assemble has to be called just before solving or system analysis (after AddSensor!).
mbs.Assemble()

tEnd = 2
stepSize = 0.001

simulationSettings = exu.SimulationSettings()
simulationSettings.solutionSettings.solutionWritePeriod = 1e-1
simulationSettings.solutionSettings.sensorsWritePeriod = 1e-2
simulationSettings.timeIntegration.numberOfSteps = int(tEnd/stepSize) #must be integer
simulationSettings.timeIntegration.endTime = tEnd

SC.visualizationSettings.nodes.drawNodesAsPoint=False
SC.visualizationSettings.nodes.defaultSize=0.05
SC.visualizationSettings.nodes.tiling = 32

#start solver:
mbs.SolveDynamic(simulationSettings)

