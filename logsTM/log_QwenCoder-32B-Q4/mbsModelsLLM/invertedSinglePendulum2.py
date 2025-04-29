# ** given model description: **
# An inverted pendulum on a cart modelled with two mass points, where the
# cart is attached to ground with a spherical joint where the x-coordinate is
# not constrained, such that it can move along the x-direction. The pendulum
# is modelled with a distance constraint between cart and pendulum mass: cart
# mass m1 = 2 kg, pendulum mass m2 = 2 kg, pendulum length = 1.2 m, and gravity
# g = 11.15 m/s^2 which acts in negative y-direction. The pendulum starts from
# the upright position, where m2 is located at the positive y-axis. A disturbance
# force f = 0.0125 N acts in x-direction at the pendulum and no control is applied
# on the cart.
#import Exudyn library and utilities
import exudyn as exu
from exudyn.utilities import *
import numpy as np

#set up new multibody system to work with
SC = exu.SystemContainer()
mbs = SC.AddSystem()

#Create a ground object as an inertial reference frame for the multibody system.
oGround = mbs.CreateGround(referencePosition=[0,0,0])

#Create a point mass object for the cart with specified mass at reference position
oCart = mbs.CreateMassPoint(physicsMass=2, referencePosition=[0,0,0], 
                            initialDisplacement=[0,0,0],  
                            initialVelocity=[0,0,0],    
                            gravity=[0,-11.15,0])

#Create a point mass object for the pendulum with specified mass at reference position
oPendulum = mbs.CreateMassPoint(physicsMass=2, referencePosition=[0,1.2,0], 
                                 initialDisplacement=[0,0,0],  
                                 initialVelocity=[0,0,0],    
                                 gravity=[0,-11.15,0])

#Create a spherical joint between ground and cart; x-coordinate is not constrained
mbs.CreateSphericalJoint(bodyNumbers=[oGround, oCart],
                         position=[0,0,0], 
                         constrainedAxes=[0,1,1])

#Create a distance constraint between cart and pendulum mass
oDistance = mbs.CreateDistanceConstraint(bodyNumbers=[oCart, oPendulum], 
                                         localPosition0 = [0,0,0], 
                                         localPosition1 = [0,0,0], 
                                         distance=1.2)

#Applies a force in x-direction on the pendulum
loadPendulum = mbs.CreateForce(bodyNumber=oPendulum, loadVector=[0.0125,0,0])

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
SC.visualizationSettings.openGL.lineWidth = 3


#start solver:
mbs.SolveDynamic(simulationSettings)


