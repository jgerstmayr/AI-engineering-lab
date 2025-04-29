# ** given model description: **
# Straight elastic chain modelled with 8 mass points connected with spring-dampers
# with the following properties: masses m = 5 kg, lengths of each chain element
# l_single = 2 m, stiffness k = 2000 and damping d = 125 of chain elements, and gravity
# g = 11.15 m/s^2 which acts in negative y-direction. The chain starts from
# horizontal configuration, where all masses are aligned with the x-axis, the first
# mass located at x=0. The left-most and right-most spring-dampers are fixed to
# ground using spherical joints.
#import Exudyn library and utilities
import exudyn as exu
from exudyn.utilities import *
import numpy as np

#set up new multibody system to work with
SC = exu.SystemContainer()
mbs = SC.AddSystem()

#Create a ground object as an inertial reference frame for the multibody system.
oGround = mbs.CreateGround(referencePosition=[0,0,0])

#Parameters
m = 5  # mass in kg
l_single = 2  # length of each chain element in m
k = 2000  # stiffness in N/m
d = 125  # damping in Ns/m
g = 11.15  # gravity in m/s^2

#Create 8 mass points
mass_points = []
for i in range(8):
    oMass = mbs.CreateMassPoint(physicsMass=m, referencePosition=[i*l_single,0,0], 
                                initialDisplacement=[0,0,0],  
                                initialVelocity=[0,0,0],    
                                gravity=[0,-g,0])          
    mass_points.append(oMass)

#Create spring-dampers between mass points
for i in range(7):
    oSpringDamper = mbs.CreateSpringDamper(bodyNumbers=[mass_points[i], mass_points[i+1]], 
                                          localPosition0=[0,0,0], 
                                          localPosition1=[0,0,0], 
                                          referenceLength=None, 
                                          stiffness=k, damping=d)

#Create spherical joints for the left-most and right-most mass points
mbs.CreateSphericalJoint(bodyNumbers=[oGround, mass_points[0]],
                         position=[0,0,0], 
                         constrainedAxes=[1,1,1])

mbs.CreateSphericalJoint(bodyNumbers=[oGround, mass_points[7]],
                         position=[7*l_single,0,0], 
                         constrainedAxes=[1,1,1])

#Assemble has to be called just before solving or system analysis (after AddSensor!).
mbs.Assemble()

tEnd = 2
stepSize = 0.005

simulationSettings = exu.SimulationSettings()
simulationSettings.solutionSettings.solutionWritePeriod = 0.5
simulationSettings.solutionSettings.sensorsWritePeriod = 1e-2
simulationSettings.timeIntegration.numberOfSteps = int(tEnd/stepSize) #must be integer
simulationSettings.timeIntegration.endTime = tEnd

SC.visualizationSettings.nodes.drawNodesAsPoint=False
SC.visualizationSettings.nodes.defaultSize=0.5
SC.visualizationSettings.nodes.tiling = 16
SC.visualizationSettings.connectors.defaultSize = 0.05 #spring


#start solver:
mbs.SolveDynamic(simulationSettings)


