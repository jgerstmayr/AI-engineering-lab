# ** given model description: **
# Free-fall motion of an object with the following properties: point mass
# m = 2 kg, gravity g = 3.73 m/s^2 (in negative z-direction). The object starts
# from rest and is dropped from a height hz = 30 m. The free fall shall be analyzed
# for 1 s. Air resistance is neglected and except the action of gravity, no forces
# act on the point mass..
import exudyn as exu
from exudyn.utilities import *
import numpy as np

SC = exu.SystemContainer()
mbs = SC.AddSystem()

oGround = mbs.CreateGround(referencePosition=[0,0,0])

oMass = mbs.CreateMassPoint(physicsMass=2, referencePosition=[0,0,30], 
                            initialDisplacement=[0,0,0],  
                            initialVelocity=[0,0,0],    
                            gravity=[0,0,-3.73])          

loadMassPoint = mbs.CreateForce(bodyNumber=oMass, loadVector=[0,0,0])

sMassVel = mbs.AddSensor(SensorBody(bodyNumber=oMass, storeInternal=True,
                                    outputVariableType=exu.OutputVariableType.Velocity))

mbs.Assemble()

endTime = 1
stepSize = endTime/5000

simulationSettings = exu.SimulationSettings()
simulationSettings.timeIntegration.numberOfSteps = int(endTime/stepSize)
simulationSettings.timeIntegration.endTime = endTime

simulationSettings.linearSolverSettings.ignoreSingularJacobian = True
simulationSettings.linearSolverType = exu.LinearSolverType.EigenDense

mbs.SolveDynamic(simulationSettings)