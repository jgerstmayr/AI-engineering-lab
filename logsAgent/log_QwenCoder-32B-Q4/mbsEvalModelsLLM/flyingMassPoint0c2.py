# ** given model description: **
# Projectile motion of a point mass with the following properties: mass m
# = 12.5 kg, gravity g = 3.73 m/s^2, initial velocity in x/y/z-direction: vx
# = 0.125 m/s, vy = 12.5 m/s, vz = 0 m/s. The initial position is given as
# x=0 and y=0. Gravity acts along the negative y-axis, and there is no other
# external propulsion or resistance. The motion shall be evaluated for 1 s. Contact
# with ground is not modelled, so the projectile can go below y=0. Except the
# action of gravity, no forces act on the point mass.
import exudyn as exu
from exudyn.utilities import *
import numpy as np

SC = exu.SystemContainer()
mbs = SC.AddSystem()

oGround = mbs.CreateGround(referencePosition=[0,0,0])

oMass = mbs.CreateMassPoint(physicsMass=12.5, referencePosition=[0,0,0], 
                            initialDisplacement=[0,0,0],  
                            initialVelocity=[0.125,12.5,0],    
                            gravity=[0,-3.73,0])

loadMassPoint = mbs.CreateForce(bodyNumber=oMass, loadVector=[0,0,0])

sMassPos = mbs.AddSensor(SensorBody(bodyNumber=oMass, storeInternal=True,
                                    outputVariableType=exu.OutputVariableType.Position))

mbs.Assemble()

endTime = 1
stepSize = endTime/5000

simulationSettings = exu.SimulationSettings()
simulationSettings.timeIntegration.numberOfSteps = int(endTime/stepSize)
simulationSettings.timeIntegration.endTime = endTime

simulationSettings.linearSolverSettings.ignoreSingularJacobian = True
simulationSettings.linearSolverType = exu.LinearSolverType.EigenDense

mbs.SolveDynamic(simulationSettings)

data = GetSensorData(mbs, sMassPos)
output = CheckParabolicMotion(data)