# ** given model description: **
# A rigid body is suspended by 4 Cartesian spring-dampers. The rigid body
# has a brick-shape with density = 400 kg/m^3, and xyz-dimensions lx=3m, ly=1.2m,
# lz=2m. The reference point of the body, which is equal to the COM, is located
# initially at [0,1.2/2,0]. The Cartesian spring-dampers are located at the x/z positions
# of the vertices of the body. The y-local-position of the spring-dampers at
# the body is -1.2/2 and the local position for ground is y=0. All spring-dampers
# have equal parameters: stiffness = [10000,150000,20000] N/m and damping = [400,4000,250]
# Ns/m. Gravity g = 9.81 m/s^2 acts in negative y-direction, and no further forces
# or damping are applied and contact with ground is ignored.
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
lx = 3
ly = 1.2
lz = 2

#create inertia instance for cuboid (brick) shape
density = 400 #kg/m^3
volume = lx * ly * lz
inertiaCube = InertiaCuboid(density=density, sideLengths=[lx, ly, lz])

#create a free rigid body with defined inertia and applies an initial rotation and velocity.
oBody = mbs.CreateRigidBody(inertia = inertiaCube,
                             referencePosition = [0, ly/2, 0], #reference position, not COM
                             referenceRotationMatrix = RotationVector2RotationMatrix([0,0,0]),
                             initialAngularVelocity = [0,0,0],
                             initialVelocity = [0,0,0],
                             gravity = [0,-9.81,0])

#Create a special spring-damper which acts on translations in global x, y, and z-direction, with possibility to connect rigid bodies, mass points together or on ground.
spring_damper_params = {
    'stiffness': [10000, 150000, 20000],
    'damping': [400, 4000, 250]
}

# Define the positions of the spring-dampers
positions = [
    [-lx/2, -ly/2, -lz/2],
    [lx/2, -ly/2, -lz/2],
    [-lx/2, -ly/2, lz/2],
    [lx/2, -ly/2, lz/2]
]

for pos in positions:
    mbs.CreateCartesianSpringDamper(
        bodyNumbers=[oGround, oBody], #[body0,body1]
        localPosition0=[pos[0], 0, pos[2]], #for body0
        localPosition1=[pos[0], pos[1], pos[2]],        #for body1
        stiffness = spring_damper_params['stiffness'],
        damping = spring_damper_params['damping'],
    )

#Assemble has to be called just before solving or system analysis (after AddSensor!).
mbs.Assemble()

tEnd = 2
stepSize = 0.001

simulationSettings = exu.SimulationSettings()
simulationSettings.solutionSettings.solutionWritePeriod = 5e-2
simulationSettings.solutionSettings.sensorsWritePeriod = 5e-3
simulationSettings.timeIntegration.numberOfSteps = int(tEnd/stepSize) #must be integer
simulationSettings.timeIntegration.endTime = tEnd

SC.visualizationSettings.nodes.drawNodesAsPoint=False
SC.visualizationSettings.nodes.defaultSize=1
SC.visualizationSettings.openGL.lineWidth = 3

#start solver:
mbs.SolveDynamic(simulationSettings)

