# -*- coding: utf-8 -*-
#%%+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# This is part of the AI engineering lab project
#
# Filename: evalHelper.py
#
# Details:  this file serves as a documented example that shall be used by 
#           LLMs to update information on their internal knowledge of Exudyn; this file specifically addresses evaluation; 
#           the text is split by #%% comments, including tags for respective functionality
#
# Author:   Johannes Gerstmayr, Tobias Möltner
# Date:     2025-13-01
#
# License:  BSD-3 license
#
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

#just some model to check implementation
import exudyn as exu
from exudyn.utilities import *
import numpy as np

SC = exu.SystemContainer()
mbs = SC.AddSystem()

oGround = mbs.CreateGround()
oMass = mbs.CreateMassPoint(physicsMass=5, referencePosition=[0,0,0], #position at which mechanism is defined
                            initialDisplacement=[0,0,0], initialVelocity=[0,0.5,0], #initial conditions for simulation, if we want deviation from reference configuration
                            gravity=[0,-9.81,0])
oBody = mbs.CreateRigidBody(referencePosition=[1,0,0], 
                            inertia=InertiaCuboid(1000, [1,0.5,0.2]),
                            gravity=[0,0,-9.81])

oDistance = mbs.CreateDistanceConstraint(bodyNumbers=[oGround, oBody])

oSpringDamper = mbs.CreateSpringDamper(bodyOrNodeList=[oGround, oBody], 
                                      localPosition0=[1,1,0], 
                                      localPosition1=[0,0,0], 
                                      stiffness=1e3, damping=1, drawSize=0.1)
oSpringDamper = mbs.CreateSpringDamper(bodyOrNodeList=[oGround, oBody], 
                                      localPosition0=[1,0,1], 
                                      localPosition1=[0,0,0], 
                                      stiffness=1e3, damping=1, drawSize=0.1)

mbs.Assemble()

#%%
#TAG: sensor for point mass
#DIFFICULTY: 5
#REQUIRES: point mass, dynamic solver
#INFO: Create a sensor attached to a point mass to measure various physical quantities such as position, velocity, or acceleration
from exudyn.utilities import SensorBody
#NOTE sensors have to be added before mbs.Assemble() !
#Example 1: add position sensor to measure the 3D position of a point (defined by localPosition relative to the body, here at x=0.5) on a rigid body with index oBody; insert sensor before mbs.Assemble(); returns sensorNumber sMassPos
sMassPos = mbs.AddSensor(SensorBody(bodyNumber=oMass, storeInternal=True,
                                    outputVariableType=exu.OutputVariableType.Position))
#Example 2: velocity sensor 
sMassVel = mbs.AddSensor(SensorBody(bodyNumber=oMass, storeInternal=True,
                                    outputVariableType=exu.OutputVariableType.Velocity))
#Other OutputVariableType types: Acceleration (global acceleration), Displacement (relative to reference configuration)

#%%
#TAG: sensor for rigid body
#DIFFICULTY: 10
#REQUIRES: rigid body omniform, dynamic solver
#INFO: Create a sensor attached to a rigid body to measure various physical quantities such as position, velocity, acceleration, etc.
from exudyn.utilities import SensorBody
#Add a position sensor to measure the 3D position of a point (defined by localPosition relative to the body, here at x=0.5) on a rigid body with index oBody; insert sensor before mbs.Assemble(); returns sensorNumber sBodyPos
sBodyPos = mbs.AddSensor(SensorBody(name='sensor on rigid body', bodyNumber=oBody, storeInternal=True, localPosition=[0.5,0,0],
                                    outputVariableType=exu.OutputVariableType.Position))
#Likewise, add a velocity sensor 
sBodyVel = mbs.AddSensor(SensorBody(name='sensor on mass point',bodyNumber=oBody, storeInternal=True, localPosition=[0.5,0,0],
                                    outputVariableType=exu.OutputVariableType.Velocity))
#Other OutputVariableType types: Acceleration (global acceleration), Displacement (relative to reference configuration), AngularVelocity, AngularAcceleration
#There are also local quantities, such as AccelerationLocal, VelocityLocal or AngularVelocityLocal, which return body-fixed coordinates
#OutputVariableType.Rotation returns the Tait-Bryan angles, being consecutive rotations around X, Y and Z axes
#NOTE: rotations resp. angular velocities are only available for rigid bodies, NOT for mass points

#%%
#TAG: distance constraint force sensor
#DIFFICULTY: 10000
#REQUIRES: distance constraint, dynamic solver
#INFO: Create a sensor to monitor forces in distance constraint
from exudyn.utilities import SensorObject
# Add a sensor to measure the scalar force of the distance constraint
sDistance = mbs.AddSensor(SensorObject(name='distance sensor',objectNumber=oDistance, storeInternal=True, 
                          outputVariableType=exu.OutputVariableType.Force))

#%% 
#TAG: assemble
#DIFFICULTY: 0
#INFO: Assemble has to be called just before solving or system analysis (after AddSensor!).
mbs.Assemble()

#%%
#TAG: compute system degree of freedom
#DIFFICULTY: 10000
#INFO: Computes the system degrees of freedom numerically, considering the Grubler-Kutzbach formula and redundant constraints.
# Returns a dictionary with:
#  - 'degreeOfFreedom': total system degrees of freedom,
#  - 'redundantConstraints': number of redundant constraints,
#  - 'nODE2': number of second-order differential equation (ODE2) coordinates,
#  - 'nODE1': number of first-order differential equation (ODE1) coordinates,
#  - 'nAE': total number of algebraic constraints,
#  - 'nPureAE': number of constraints on algebraic variables that are not coupled to ODE2 coordinates.
# Insert this command after mbs.Assemble(...)
dof = mbs.ComputeSystemDegreeOfFreedom()['degreeOfFreedom']
#%%
#TAG: compute eigenfrequencies
#DIFFICULTY: 10000
#INFO: Computes the eigenfrequencies of the multibody system and returns a numpy array of frequencies in Hz.
# The number of eigenfrequencies corresponds to the number of system coordinates.
# Insert this command after mbs.Assemble(...)
eigenfrequencies = np.sqrt(mbs.ComputeODE2Eigenvalues()[0])/(2*np.pi)
#%%
#TAG: compute linearized system
#DIFFICULTY: 10000
#INFO: Computes the linearized system matrices (mass, stiffness, damping) for the second-order differential equations in the multibody system.
# Insert this command after mbs.Assemble(...)
[M,K,D] = mbs.ComputeLinearizedSystem()

#%% 
#TAG: visualization
#DIFFICULTY: 10000
print('dof=',dof)
print('eigenfrequencies=',eigenfrequencies)
print('[M,K,D]=',[M,K,D])

#%%
#TAG: dynamic solver
#DIFFICULTY: 1
#INFO: define simulation settings and solve system with dynamic solver (time integration)
#simulation time and step size given in seconds ; please adjust endTime to investigated problem:
endTime = 2
stepSize = endTime/5000

#get default simulation settings:
simulationSettings = exu.SimulationSettings()
simulationSettings.timeIntegration.numberOfSteps = int(endTime/stepSize)
simulationSettings.timeIntegration.endTime = endTime

#in case of redundant constraints, add the following two settings:
simulationSettings.linearSolverSettings.ignoreSingularJacobian = True
simulationSettings.linearSolverType = exu.LinearSolverType.EigenDense

#call the Exudyn solver for dynamic simulation (this is the important last step):
mbs.SolveDynamic(simulationSettings)
#=>sensor values are now available

#%% 
#TAG: visualization
#DIFFICULTY: 10000
mbs.SolutionViewer()

#%%
#TAG: static solver
#DIFFICULTY: 10000
#INFO: solve multibody system with static solver; adjust simulation settings; only works if system has no kinematic DOF

simulationSettings = exu.SimulationSettings()
simulationSettings.staticSolver.verboseMode = 1

#for redundant constraints, use these two settings
simulationSettings.linearSolverSettings.ignoreSingularJacobian = True
simulationSettings.linearSolverType = exu.LinearSolverType.EigenDense

#call the Exudyn solver for static simulation using simulationSettings; this automatically stores solution in sensors:
mbs.SolveStatic(simulationSettings)
#%% #this is not used any more!
#TAG: retrieve sensor data 
#DIFFICULTY: 10000
#REQUIRES: body sensor
#INFO: Retrieves and processes sensor data after simulation.
# The first column contains time, while further columns store measured values (e.g., x, y, z position data).
dataBody = mbs.GetSensorStoredData(sBody)

# Evaluate the minimum and maximum y-position after solving
minPos = np.min(dataBody[:,2])
maxPos = np.max(dataBody[:,2])

# Extract the final position of the body
finalPos = mbs.GetSensorStoredData(sBody)[-1,1:4]

#%% 
#TAG: visualization
#DIFFICULTY: 10000
mbs.SolutionViewer()
