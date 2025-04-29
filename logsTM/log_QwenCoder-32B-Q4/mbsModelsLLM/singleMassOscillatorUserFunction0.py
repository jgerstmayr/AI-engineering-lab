# ** given model description: **
# Mass-spring-damper with the following properties: mass m = 10 kg, stiffness
# k = 1000 N/m, and damping d = 50 Ns/m. The force applied to the mass only
# in x-direction is given by the time-dependent function f(t) = 400.*math.sin(math.pi*t).
# The spring-damper is aligned with the x-axis and the spring has a length of
# 0.75 m and is relaxed in the initial position. Gravity is neglected.
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
oMass = mbs.CreateMassPoint(physicsMass=10, referencePosition=[0.75,0,0], 
                            initialDisplacement=[0,0,0],  
                            initialVelocity=[0,0,0],    
                            gravity=[0,0,0])          

#Create a linear spring-damper system between two bodies or between a body and the ground.
oSpringDamper = mbs.CreateSpringDamper(bodyNumbers=[oGround, oMass], 
                                      localPosition0=[0,0,0], 
                                      localPosition1=[0,0,0], 
                                      referenceLength=0.75, 
                                      stiffness=1000, damping=50)

#Defines a time-dependent force function and applies it to a rigid body or mass point at a specific local position.
def UFforce(mbs, t, loadVector):
    return 400.*np.sin(np.pi*t)*np.array([1,0,0])

mbs.CreateForce(bodyNumber=oMass,
                localPosition=[0,0,0], 
                loadVectorUserFunction=UFforce)

#Assemble has to be called just before solving or system analysis (after AddSensor!).
mbs.Assemble()

tEnd = 1.2
stepSize = 0.002

simulationSettings = exu.SimulationSettings()
simulationSettings.solutionSettings.solutionWritePeriod = 1e-2
simulationSettings.solutionSettings.sensorsWritePeriod = 5e-3
simulationSettings.timeIntegration.numberOfSteps = int(tEnd/stepSize) #must be integer
simulationSettings.timeIntegration.endTime = tEnd

SC.visualizationSettings.nodes.drawNodesAsPoint=False
SC.visualizationSettings.openGL.lineWidth = 3
SC.visualizationSettings.nodes.defaultSize=0.05
SC.visualizationSettings.nodes.tiling = 16
SC.visualizationSettings.connectors.defaultSize = 0.005 #spring


#start solver:
mbs.SolveDynamic(simulationSettings)


