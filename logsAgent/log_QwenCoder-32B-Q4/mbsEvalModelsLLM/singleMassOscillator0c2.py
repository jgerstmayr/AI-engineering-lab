# ** given model description: **
# Mass-spring-damper with the following properties: The mass point with mass
# m = 6 kg lies at [15 cm,0,0], stiffness k = 1250 N/m, and damping d = 30
# Ns/m. The force applied to the mass in x-direction is f = 30 N. The spring-damper
# between mass point and ground at [0,0,0] is aligned with the x-axis, the spring
# has a length of 15 cm and is initially relaxed. Gravity is neglected.
import exudyn as exu
from exudyn.utilities import *
import numpy as np

SC = exu.SystemContainer()
mbs = SC.AddSystem()

oGround = mbs.CreateGround(referencePosition=[0,0,0])

oMass = mbs.CreateMassPoint(physicsMass=6, referencePosition=[0.15,0,0], 
                            initialDisplacement=[0,0,0],  
                            initialVelocity=[0,0,0],    
                            gravity=[0,0,0])

oSpringDamper = mbs.CreateSpringDamper(bodyNumbers=[oGround, oMass], 
                                      localPosition0=[0,0,0], 
                                      localPosition1=[0,0,0], 
                                      referenceLength=0.15, 
                                      stiffness=1250, damping=30)

loadMassPoint = mbs.CreateForce(bodyNumber=oMass, loadVector=[30,0,0])

sMassPos = mbs.AddSensor(SensorBody(bodyNumber=oMass, storeInternal=True,
                                    outputVariableType=exu.OutputVariableType.Position))

mbs.Assemble()

endTime = 10
stepSize = endTime/5000

simulationSettings = exu.SimulationSettings()
simulationSettings.timeIntegration.numberOfSteps = int(endTime/stepSize)
simulationSettings.timeIntegration.endTime = endTime

simulationSettings.linearSolverSettings.ignoreSingularJacobian = True
simulationSettings.linearSolverType = exu.LinearSolverType.EigenDense

mbs.SolveDynamic(simulationSettings)