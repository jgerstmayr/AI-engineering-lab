# ** given model description: **
# A planar four-bar mechanism modelled with 2 points masses and the 3 moving
# bars modeled as massless distance constraints. The origin point of the mechanism
# on ground is located at [0,0,0], mass 1 with m1 = 0.6 kg is located at [0,0.1,0],
# mass 2 with m2 = 1.25 kg is located at [1.5,0.1,0] and the final additional
# ground point is at [1.5,-0.1,0]. Gravity g = 3.73 m/s^2 acts in negative y-direction
# and mass 1 has an initial velocity of [0.4,0,0]. There is no friction or other
# resistance.
#import Exudyn library and utilities
import exudyn as exu
from exudyn.utilities import *
import numpy as np

#set up new multibody system to work with
SC = exu.SystemContainer()
mbs = SC.AddSystem()

#Create a ground object as an inertial reference frame for the multibody system.
#Create a ground object at given (optional) referencePosition.  Even several ground objects at specific positions can be added.
oGround = mbs.CreateGround(referencePosition=[0,0,0])
oGround2 = mbs.CreateGround(referencePosition=[1.5,-0.1,0])

#Create a point mass object with specified mass at reference position with optional initial conditions
#physicsMass: the mass in kg
#referencePosition: initial/reference position at which mechanism is defined; 
#initialDisplacement: additional initial deviations from referencePosition; usually this is [0,0,0]
#initialVelocity: initial velocities of mass point
#all vectors always have 3 components, no matter if 2D or 3D problem
oMass1 = mbs.CreateMassPoint(physicsMass=0.6, referencePosition=[0,0.1,0], 
                            initialDisplacement=[0,0,0],  #optional, relative to reference position
                            initialVelocity=[0.4,0,0],    #optional
                            gravity=[0,-3.73,0])          #optional

oMass2 = mbs.CreateMassPoint(physicsMass=1.25, referencePosition=[1.5,0.1,0], 
                            initialDisplacement=[0,0,0],  #optional, relative to reference position
                            initialVelocity=[0,0,0],    #optional
                            gravity=[0,-3.73,0])          #optional

#Create a rigid distance constraint between two points on different bodies or between a body and the ground.
#NOTE: localPosition0 resp. localPosition1 are the positions relativ to body0 resp. 1 (or ground); localPosition is always [0,0,0] for point masses; on ground, localPosition depends on position where the distance constraint should be anchored; use distance=None as it is computed automatically (safer)
oDistance1 = mbs.CreateDistanceConstraint(bodyNumbers=[oGround, oMass1], #[body0,body1]
                                         localPosition0 = [0,0,0], #locally on body0
                                         localPosition1 = [0,0,0], #locally on body1
                                         distance=None)

oDistance2 = mbs.CreateDistanceConstraint(bodyNumbers=[oMass1, oMass2], #[body0,body1]
                                         localPosition0 = [0,0,0], #locally on body0
                                         localPosition1 = [0,0,0], #locally on body1
                                         distance=None)

oDistance3 = mbs.CreateDistanceConstraint(bodyNumbers=[oMass2, oGround2], #[body0,body1]
                                         localPosition0 = [0,0,0], #locally on body0
                                         localPosition1 = [0,0,0], #locally on body1
                                         distance=None)

#Assemble has to be called just before solving or system analysis (after AddSensor!).
mbs.Assemble()

tEnd = 2
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


