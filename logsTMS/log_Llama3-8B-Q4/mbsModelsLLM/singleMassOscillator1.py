# ** given model description: **
# Mass-spring-damper with the following properties: The mass  point with
# mass m = 1 kg lies at [5 cm,0,0], stiffness k = 2000 N/m, and damping d = 20
# Ns/m. The force applied to the mass in x-direction is f = 10 N. The spring-damper
# between mass point and ground at [0,0,0] is aligned with the x-axis, the spring
# has a length of 5 cm and is initially relaxed. Gravity is neglected.
import exudyn as exu
from exudyn.utilities import *
import numpy as np

SC = exu.SystemContainer()
mbs = SC.AddSystem()

oGround = mbs.CreateGround(referencePosition=[0,0,0])

oMass = mbs.CreateMassPoint(physicsMass=1, referencePosition=[0.05,0,0], 
                            initialDisplacement=[0,0,0], 
                            initialVelocity=[0,0,0], 
                            gravity=[0,0,0])

oSpringDamper = mbs.CreateSpringDamper(bodyNumbers=[oGround, oMass], 
                                      localPosition0=[0,0,0], 
                                      localPosition1=[0,0,0], 
                                      referenceLength=0.05, 
                                      stiffness=2000, 
                                      damping=20)

loadMassPoint = mbs.CreateForce(bodyNumber=oMass, loadVector=[10,0,0])

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


