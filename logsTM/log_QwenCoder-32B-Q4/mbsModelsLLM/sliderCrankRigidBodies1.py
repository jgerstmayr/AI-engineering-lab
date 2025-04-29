# ** given model description: **
# A slider-crank mechanism is given with a crank rotating about the z-axis.
# The crank is modelled as rigid body with cylinder shape (axis=z) with mass
# m = 2 kg, radius r = 0.25 m, and width = 0.08 m, and it is initially located
# at [0,0,-0.08]. The brick-shaped conrod and piston have identical parameters:
# density = 7850 kg/m^3, and xyz-dimensions lx=0.5 m, wy=0.075 m, hz=0.1 m, initially
# not rotated (straight configuration of slider-crank). The conrod's center is
# located initially at [r+0.5*lx,0,0] and the piston is initially located at [r+1.5*lx,0,0].
# A torque [0,0,T] shall act on the crank, employing a user-function with T=1.5
# Nm until 1 s and 0 thereafter. The revolute joint between ground and crank
# is located at [0,0,0] (global coordinates), the revolute joint between crank
# and conrod is located at [r,0,0] (global coordinates), and the revolute joint
# between conrod and piston is located at [r+lx,0,0] (global coordinates). The prismatic
# joint (axis=x) between ground and piston is located at [r+1.5*lx,0,0] (global
# coordinates). No gravity acts on the system. Simulate the system for 2 s.
#import Exudyn library and utilities
import exudyn as exu
from exudyn.utilities import *
import numpy as np

#set up new multibody system to work with
SC = exu.SystemContainer()
mbs = SC.AddSystem()

#Create a ground object as an inertial reference frame for the multibody system.
oGround = mbs.CreateGround(referencePosition=[0,0,0])

#Crank parameters
massCrank = 2
radiusCrank = 0.25
widthCrank = 0.08
volumeCrank = np.pi * radiusCrank**2 * widthCrank
inertiaCrank = InertiaCylinder(density=massCrank/volumeCrank, length=widthCrank, outerRadius=radiusCrank, axis=2)

#Create crank rigid body
oCrank = mbs.CreateRigidBody(inertia=inertiaCrank,
                            referencePosition=[0,0,-0.08], 
                            initialVelocity=[0,0,0],   
                            initialAngularVelocity=[0,0,0], 
                            gravity=[0,0,0])

#Conrod and piston parameters
density = 7850
lx = 0.5
wy = 0.075
hz = 0.1
volumeConrod = lx * wy * hz
volumePiston = lx * wy * hz
massConrod = density * volumeConrod
massPiston = density * volumePiston
inertiaConrod = InertiaCuboid(density=density, sideLengths=[lx, wy, hz])
inertiaPiston = InertiaCuboid(density=density, sideLengths=[lx, wy, hz])

#Create conrod rigid body
oConrod = mbs.CreateRigidBody(inertia=inertiaConrod,
                             referencePosition=[radiusCrank+0.5*lx,0,0], 
                             initialVelocity=[0,0,0],   
                             initialAngularVelocity=[0,0,0], 
                             gravity=[0,0,0])

#Create piston rigid body
oPiston = mbs.CreateRigidBody(inertia=inertiaPiston,
                             referencePosition=[radiusCrank+1.5*lx,0,0], 
                             initialVelocity=[0,0,0],   
                             initialAngularVelocity=[0,0,0], 
                             gravity=[0,0,0])

#Torque user function
def UserFunctionTorque(mbs, t, loadVector):
    if t <= 1:
        return np.array(loadVector)
    else:
        return np.array([0,0,0])

#Add torque with user function
mbs.CreateTorque(bodyNumber=oCrank, loadVector=[0,0,1.5], 
                 loadVectorUserFunction=UserFunctionTorque)

#Revolute joint between ground and crank
mbs.CreateRevoluteJoint(bodyNumbers=[oGround, oCrank], 
                        position=[0,0,0], 
                        axis=[0,0,1], 
                        useGlobalFrame=True)

#Revolute joint between crank and conrod
mbs.CreateRevoluteJoint(bodyNumbers=[oCrank, oConrod], 
                        position=[radiusCrank,0,0], 
                        axis=[0,0,1], 
                        useGlobalFrame=True)

#Revolute joint between conrod and piston
mbs.CreateRevoluteJoint(bodyNumbers=[oConrod, oPiston], 
                        position=[radiusCrank+lx,0,0], 
                        axis=[0,0,1], 
                        useGlobalFrame=True)

#Prismatic joint between ground and piston
mbs.CreatePrismaticJoint(bodyNumbers=[oGround, oPiston], 
                         position=[radiusCrank+1.5*lx,0,0], 
                         axis=[1,0,0], 
                         useGlobalFrame=True)

#Assemble has to be called just before solving or system analysis (after AddSensor!).
mbs.Assemble()

tEnd = 2
stepSize = 0.001

simulationSettings = exu.SimulationSettings()
simulationSettings.solutionSettings.solutionWritePeriod = 1e-1
simulationSettings.solutionSettings.sensorsWritePeriod = 5e-3
simulationSettings.timeIntegration.numberOfSteps = int(tEnd/stepSize) #must be integer
simulationSettings.timeIntegration.endTime = tEnd
# simulationSettings.timeIntegration.verboseMode = 1

simulationSettings.linearSolverSettings.ignoreSingularJacobian = True
simulationSettings.linearSolverType = exu.LinearSolverType.EigenDense

SC.visualizationSettings.nodes.drawNodesAsPoint=False
SC.visualizationSettings.nodes.defaultSize=1
SC.visualizationSettings.openGL.lineWidth = 3
SC.visualizationSettings.openGL.shadow = 0.25


#start solver:
mbs.SolveDynamic(simulationSettings)


