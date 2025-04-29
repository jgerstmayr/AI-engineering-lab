# ** given model description: **
# Two mass points connected by distance constraint. The mass points both
# have mass m1 = m2 = 1.25 kg, are initially located at p1 = [-0.5,0,0] and p2
# = [0.5,0,0], positions given in m. Mass m1 has initial velocity vy = 2 m/s
# and m2 has initial velocity vy = -2 m/s while all other initial velocity components
# are zero. No gravity nor forces are present.
import exudyn as exu
from exudyn.utilities import *
import numpy as np

SC = exu.SystemContainer()
mbs = SC.AddSystem()

oGround = mbs.CreateGround(referencePosition=[0,0,0])

oMass1 = mbs.CreateMassPoint(physicsMass=1.25, referencePosition=[-0.5,0,0], 
                            initialDisplacement=[0,0,0],  
                            initialVelocity=[0,2,0],    
                            gravity=[0,0,0])

oMass2 = mbs.CreateMassPoint(physicsMass=1.25, referencePosition=[0.5,0,0], 
                            initialDisplacement=[0,0,0],  
                            initialVelocity=[0,-2,0],    
                            gravity=[0,0,0])

oDistance = mbs.CreateDistanceConstraint(bodyNumbers=[oMass1, oMass2], 
                                         localPosition0 = [0,0,0], 
                                         localPosition1 = [0,0,0], 
                                         distance=None)

sMass1Pos = mbs.AddSensor(SensorBody(bodyNumber=oMass1, storeInternal=True,
                                    outputVariableType=exu.OutputVariableType.Position))

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

data1 = GetSensorData(mbs, sMass1Pos)
output1 = CheckPlanarTrajectory(data1)

data2 = GetSensorData(mbs, sMass2Pos)
output2 = CheckPlanarTrajectory(data2)