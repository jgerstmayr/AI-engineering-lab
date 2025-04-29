# ** given model description: **
# Mass-spring-damper with the following properties: The mass point with mass
# m = 10 kg lies at [12 cm,0,0], stiffness k = 1500 N/m, and damping d = 40
# Ns/m. The force applied to the mass in x-direction is f = 15 N. The spring-damper
# between mass point and ground at [0,0,0] is aligned with the x-axis, the spring
# has a length of 12 cm and is initially relaxed. The system is subject to gravity
# g = 11.15 m/s^2 in positive x-direction.
import exudyn as exu
from exudyn.utilities import *
import numpy as np

SC = exu.SystemContainer()
mbs = SC.AddSystem()

oGround = mbs.CreateGround(referencePosition=[0,0,0])

oMass = mbs.CreateMassPoint(physicsMass=10, referencePosition=[0.12,0,0], 
                            initialDisplacement=[0,0,0],  
                            initialVelocity=[0,0,0],    
                            gravity=[11.15,0,0])

oSpringDamper = mbs.CreateSpringDamper(bodyNumbers=[oGround, oMass], 
                                      localPosition0=[0,0,0], 
                                      localPosition1=[0,0,0], 
                                      referenceLength=0.12, 
                                      stiffness=1500, damping=40)

loadMassPoint = mbs.CreateForce(bodyNumber=oMass, loadVector=[15,0,0])

sMassPos = mbs.AddSensor(SensorBody(bodyNumber=oMass, storeInternal=True,
                                    outputVariableType=exu.OutputVariableType.Position))
sMassVel = mbs.AddSensor(SensorBody(bodyNumber=oMass, storeInternal=True,
                                    outputVariableType=exu.OutputVariableType.Velocity))

mbs.Assemble()

output = mbs.ComputeODE2Eigenvalues()