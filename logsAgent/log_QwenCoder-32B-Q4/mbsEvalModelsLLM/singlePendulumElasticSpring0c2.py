# ** given model description: **
# Simple mathematical pendulum with the following properties: point mass
# m = 2 kg, elastic string length = 0.6 m, string stiffness k = 600 N/m, and
# gravity g = 9.81 m/s^2 which is applied in negative y-direction. The pendulum's
# reference configuration is such that the string has an angle 25 degrees from the
# vertical (negative y-axis), thus the mass being on a positive x-coordinate for positive
# angles. The initial velocities of the mass point are v_x = -0.02 m/s and v_y =
# 0.04 m/s, applied in x resp. y direction.
import exudyn as exu
from exudyn.utilities import *
import numpy as np

SC = exu.SystemContainer()
mbs = SC.AddSystem()

oGround = mbs.CreateGround(referencePosition=[0,0,0])

oMass = mbs.CreateMassPoint(physicsMass=2, referencePosition=[0.6*np.sin(np.radians(25)), -0.6*np.cos(np.radians(25)), 0], 
                            initialDisplacement=[0,0,0],  
                            initialVelocity=[-0.02,0.04,0],    
                            gravity=[0,-9.81,0])

oSpringDamper = mbs.CreateSpringDamper(bodyNumbers=[oGround, oMass], 
                                      localPosition0=[0,0,0], 
                                      localPosition1=[0,0,0], 
                                      referenceLength=0.6, 
                                      stiffness=600, damping=0)

sMassPos = mbs.AddSensor(SensorBody(bodyNumber=oMass, storeInternal=True,
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

data = GetSensorData(mbs, sMassPos)
output = CheckPlanarTrajectory(data)