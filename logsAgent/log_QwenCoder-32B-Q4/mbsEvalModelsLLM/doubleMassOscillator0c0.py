# ** given model description: **
# Two-mass-spring-damper system consisting of two masses with the following
# properties: mass m1 = m2 = 8 kg, stiffness k1 = k2 = 6000 N/m, and damping d1 = d2
# = 25 Ns/m. The first mass is placed at [20 cm,0,0] and the second mass at
# [2*20 cm,0,0]. The first spring is connected to ground at [0,0,0], and the second
# spring connects the two masses. Each spring has a reference length of 20 cm and
# is relaxed in the initial configuration. A force 40 is applied in x-direction
# to mass 2. No gravity is applied to the system.
import exudyn as exu
from exudyn.utilities import *
import numpy as np

SC = exu.SystemContainer()
mbs = SC.AddSystem()

oGround = mbs.CreateGround(referencePosition=[0,0,0])

oMass1 = mbs.CreateMassPoint(physicsMass=8, referencePosition=[0.2,0,0], 
                            initialDisplacement=[0,0,0],  
                            initialVelocity=[0,0,0],    
                            gravity=[0,0,0])

oMass2 = mbs.CreateMassPoint(physicsMass=8, referencePosition=[0.4,0,0], 
                            initialDisplacement=[0,0,0],  
                            initialVelocity=[0,0,0],    
                            gravity=[0,0,0])

oSpringDamper1 = mbs.CreateSpringDamper(bodyNumbers=[oGround, oMass1], 
                                      localPosition0=[0,0,0], 
                                      localPosition1=[0,0,0], 
                                      referenceLength=0.2, 
                                      stiffness=6000, damping=25)

oSpringDamper2 = mbs.CreateSpringDamper(bodyNumbers=[oMass1, oMass2], 
                                      localPosition0=[0,0,0], 
                                      localPosition1=[0,0,0], 
                                      referenceLength=0.2, 
                                      stiffness=6000, damping=25)

loadMassPoint = mbs.CreateForce(bodyNumber=oMass2, loadVector=[40,0,0])

sMass2Pos = mbs.AddSensor(SensorBody(bodyNumber=oMass2, storeInternal=True,
                                    outputVariableType=exu.OutputVariableType.Position))

mbs.Assemble()

endTime = 5
stepSize = endTime/5000

simulationSettings = exu.SimulationSettings()
simulationSettings.timeIntegration.numberOfSteps = int(endTime/stepSize)
simulationSettings.timeIntegration.endTime = endTime

simulationSettings.linearSolverSettings.ignoreSingularJacobian = True
simulationSettings.linearSolverType = exu.LinearSolverType.EigenDense

mbs.SolveDynamic(simulationSettings)