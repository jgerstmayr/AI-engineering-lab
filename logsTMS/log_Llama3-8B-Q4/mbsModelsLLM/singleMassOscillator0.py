# ** given model description: **
# Mass-spring-damper with the following properties: The mass point with mass
# m = 1 kg lies at [5 cm,0,0], stiffness k = 2000 N/m, and damping d = 20 Ns/m.
# The force applied to the mass in x-direction is f = 10 N. The spring-damper
# between mass point and ground at [0,0,0] is aligned with the x-axis, the spring
# has a length of 5 cm and is initially relaxed. Gravity is neglected.
#import Exudyn library and utilities
import exudyn as exu
from exudyn.utilities import  *
import numpy as np

#set up new multibody system to work with
SC  = exu.SystemContainer()
mbs = SC.AddSystem()

#Create a ground object as an inertial reference frame for the multibody system.
#Create a ground object at given (optional) referencePosition.  Even several ground objects at specific positions can be added.
oGround = mbs.CreateGround(referencePosition=[0,0,0])

#Create a point mass object with specified mass at reference position with optional initial conditions
#physicsMass: the mass in kg
#referencePosition: initial/reference position at which mechanism is defined; 
#initialDisplacement: additional initial deviations from referencePosition; usually this is [0,0,0]
#initialVelocity: initial velocities of mass point
#all vectors always have 3 components, no matter if 2D or 3D problem
oMass = mbs.CreateMassPoint(physicsMass=1, referencePosition=[0.05,0,0], 
                            initialDisplacement=[0,0,0],   #optional, relative to reference position
                            initialVelocity=[0,0,0],     #optional
                            gravity=[0,0,0])           #optional

#Create a linear spring-damper system between two bodies or between a body and the ground.
#NOTE: localPosition0 resp. localPosition1 are the positions relativ to body0 resp. 1 (or ground); localPosition is always [0,0,0] for point masses; on ground, localPosition depends on position where the spring-damper should be anchored
oSpringDamper = mbs.CreateSpringDamper(bodyNumbers=[oGround, oMass],  #[body0,body1]
                                      localPosition0=[0,0,0],  #locally on body0
                                      localPosition1=[0,0,0],  #locally on body1
                                      referenceLength=0.05,  #usually set to None (default) => takes the (relaxed) length in reference configuration
                                      stiffness=2000, damping=20)

#Applies a force in a specific direction to a point mass.
#apply 10N in x-direction on point mass with index oMass
loadMassPoint = mbs.CreateForce(bodyNumber=oMass, loadVector=[10,0,0])

#Assemble has to be called just before solving or system analysis (after AddSensor!).
mbs.Assemble()

tEnd = 1
stepSize = 0.001

simulationSettings = exu.SimulationSettings()
simulationSettings.solutionSettings.solutionWritePeriod = 1e-2
simulationSettings.solutionSettings.sensorsWritePeriod = 5e-3
simulationSettings.timeIntegration.numberOfSteps = int(tEnd/stepSize) #must be integer
simulationSettings.timeIntegration.endTime = tEnd

SC.visualizationSettings.nodes.drawNodesAsPoint=False
SC.visualizationSettings.nodes.defaultSize=0.01
SC.visualizationSettings.openGL.lineWidth = 3


#start solver:
mbs.SolveDynamic(simulationSettings)


