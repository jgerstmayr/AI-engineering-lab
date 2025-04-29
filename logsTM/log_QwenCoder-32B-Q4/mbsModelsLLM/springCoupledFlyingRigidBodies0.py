# ** given model description: **
# Two free flying rigid elements, each modeled as a rigid body with brick-shape
# (density = 1500 kg/m^3, lx=0.6 m, wy=0.125 m, hz=0.05 m). Rigid body 1 is globally
# placed at [lx/2,0,0] and rigid body 2 at [3*lx/2,0,0], both bodies' COMs being
# at their origin. A Cartesian spring-damper with stiffness [20000,20000,20000]
# N/m and damping [150,150,150] Ns/m is attached between rigid body 1 at [lx/2,0,0]
# (local position) and rigid body 2 at [-lx/2,0,0] (also local position). Body1
# has initial velocity [0,3,0] and body2 has initial velocity [0,-3,0] and gravity
# is zero.
#import Exudyn library and utilities
import exudyn as exu
from exudyn.utilities import *
import numpy as np

#set up new multibody system to work with
SC = exu.SystemContainer()
mbs = SC.AddSystem()

#Create a ground object as an inertial reference frame for the multibody system.
oGround = mbs.CreateGround(referencePosition=[0,0,0])

#Create a rigid body with a brick (cuboid) shape; uses rotated reference configuration.
lx = 0.6
wy = 0.125
hz = 0.05

#create inertia instance for cuboid (brick) shape
density = 1500 #kg/m^3
volume = lx * wy * hz
inertiaCube1 = InertiaCuboid(density=density, sideLengths=[lx, wy, hz])
inertiaCube2 = InertiaCuboid(density=density, sideLengths=[lx, wy, hz])

#create a free rigid body with defined inertia and applies an initial rotation and velocity.
oBody1 = mbs.CreateRigidBody(inertia = inertiaCube1,
                             referencePosition = [lx/2,0,0], #reference position, not COM
                             initialVelocity = [0,3,0],
                             gravity = [0,0,0])

oBody2 = mbs.CreateRigidBody(inertia = inertiaCube2,
                             referencePosition = [3*lx/2,0,0], #reference position, not COM
                             initialVelocity = [0,-3,0],
                             gravity = [0,0,0])

#Create a special spring-damper which acts on translations in global x, y, and z-direction, with possibility to connect rigid bodies, mass points together or on ground.
mbs.CreateCartesianSpringDamper(
    bodyNumbers=[oBody1, oBody2], #[body0,body1]
    localPosition0=[lx/2,0,0], #for body0
    localPosition1=[-lx/2,0,0],        #for body1
    stiffness = [20000,20000,20000], #x,y,z stiffness
    damping = [150,150,150], #x,y,z damping
)

#Assemble has to be called just before solving or system analysis (after AddSensor!).
mbs.Assemble()

tEnd = 2
stepSize = 0.001

simulationSettings = exu.SimulationSettings()
simulationSettings.solutionSettings.solutionWritePeriod = 1e-1
simulationSettings.solutionSettings.sensorsWritePeriod = 5e-3
simulationSettings.timeIntegration.numberOfSteps = int(tEnd/stepSize) #must be integer
simulationSettings.timeIntegration.endTime = tEnd

SC.visualizationSettings.nodes.drawNodesAsPoint=False
SC.visualizationSettings.nodes.defaultSize=1
SC.visualizationSettings.openGL.lineWidth = 3


#start solver:
mbs.SolveDynamic(simulationSettings)


