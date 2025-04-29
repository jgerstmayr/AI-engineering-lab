# ** given model description: **
# Rolling motion of a solid disc rolling on a x/y plane with the following
# properties: mass m = 2 kg, radius r = 0.4 m, width w = 0.04 m, and gravity g = 9.81
# m/s^2 (in negative z-direction). The disc's axis is initially aligned with the
# x-axis. The COM of the disc has an initial position of p0 = [0.1,0.125,0.4], translational
# velocity of v_y = 0.8 m/s and an initial angular velocity omega_x=-v_y/radius. Rolling
# shall be modelled ideal and without slipping.
#import Exudyn library and utilities
import exudyn as exu
from exudyn.utilities import *
import numpy as np

#set up new multibody system to work with
SC = exu.SystemContainer()
mbs = SC.AddSystem()

#Create a ground object as an inertial reference frame for the multibody system.
oGround = mbs.CreateGround(referencePosition=[0,0,0])

#Create a rigid body with a cylindrical shape.
mass = 2 
rDisc = 0.4
length = 0.04
volume = np.pi * rDisc**2 * length
inertiaCylinder = InertiaCylinder(density=mass/volume, length=length, outerRadius=rDisc, axis=0)

#create a free rigid body using the defined inertia properties and applies gravity (y-direction).
oDisc = mbs.CreateRigidBody(inertia=inertiaCylinder,
                            referencePosition=[0.1,0.125,0.4], #reference position x/y/z of COM
                            initialVelocity=[0,0.8,0],   
                            initialAngularVelocity=[-0.8/rDisc,0,0],
                            gravity=[0,0,-9.81])

#create a 'rolling' joint between flat ground defined by plane, lying on oGround, and rigid body given as oDisc:
mbs.CreateRollingDisc(bodyNumbers=[oGround, oDisc], discRadius = rDisc, 
                      axisPosition=[0,0,0], axisVector=[1,0,0], #relative to oDisc
                      planePosition = [0,0,0], planeNormal = [0,0,1], #defines plane
                      constrainedAxes=[1,1,1] #constrain 3 axes: lateral motion, forward motion and normal contact
                      )

#Assemble has to be called just before solving or system analysis (after AddSensor!).
mbs.Assemble()

tEnd = 1
stepSize = 0.001

simulationSettings = exu.SimulationSettings()
simulationSettings.solutionSettings.solutionWritePeriod = 5e-2
simulationSettings.solutionSettings.sensorsWritePeriod = 5e-3
simulationSettings.timeIntegration.numberOfSteps = int(tEnd/stepSize) #must be integer
simulationSettings.timeIntegration.endTime = tEnd

SC.visualizationSettings.nodes.drawNodesAsPoint=False
SC.visualizationSettings.nodes.defaultSize=1
SC.visualizationSettings.openGL.lineWidth = 2


#start solver:
mbs.SolveDynamic(simulationSettings)


