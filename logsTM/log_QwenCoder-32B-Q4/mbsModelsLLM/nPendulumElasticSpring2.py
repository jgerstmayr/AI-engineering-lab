# ** given model description: **
# Multibody n-pendulum system consisting of 4 point masses connected with
# spring-dampers with the following properties: masses m = 0.5 kg, lengths of single elastic
# strings l_single = 0.25 m, stiffness k = 10000 and damping d = 100 of strings,
# and gravity g = 9.81 m/s^2 which acts in negative y-direction. The pendulum
# starts from horizontal configuration, where all masses are aligned with the x-axis,
# the first mass located at x=0.25, with a spring-damper connected to ground.
#import Exudyn library and utilities
import exudyn as exu
from exudyn.utilities import *
import numpy as np

#set up new multibody system to work with
SC = exu.SystemContainer()
mbs = SC.AddSystem()

#Create a ground object as an inertial reference frame for the multibody system.
oGround = mbs.CreateGround(referencePosition=[0,0,0])

#Properties of the pendulum
m = 0.5  # mass in kg
l_single = 0.25  # length of single elastic string in m
k = 10000  # stiffness in N/m
d = 100  # damping in Ns/m
g = 9.81  # gravity in m/s^2

#Create point masses and spring-dampers
oMasses = []
for i in range(4):
    #Create a point mass object
    oMass = mbs.CreateMassPoint(physicsMass=m, referencePosition=[0.25 + i * l_single, 0, 0], 
                                initialDisplacement=[0,0,0], 
                                initialVelocity=[0,0,0], 
                                gravity=[0,-g,0])
    oMasses.append(oMass)

    #Create a spring-damper system between the current mass and the previous one or ground
    if i == 0:
        oSpringDamper = mbs.CreateSpringDamper(bodyNumbers=[oGround, oMass], 
                                              localPosition0=[0,0,0], 
                                              localPosition1=[0,0,0], 
                                              referenceLength=l_single, 
                                              stiffness=k, damping=d)
    else:
        oSpringDamper = mbs.CreateSpringDamper(bodyNumbers=[oMasses[i-1], oMass], 
                                              localPosition0=[0,0,0], 
                                              localPosition1=[0,0,0], 
                                              referenceLength=l_single, 
                                              stiffness=k, damping=d)

#Assemble has to be called just before solving or system analysis (after AddSensor!).
mbs.Assemble()

tEnd = 0.5
stepSize = 0.001

simulationSettings = exu.SimulationSettings()
simulationSettings.solutionSettings.solutionWritePeriod = 5e-2
simulationSettings.solutionSettings.sensorsWritePeriod = 1e-2
simulationSettings.timeIntegration.numberOfSteps = int(tEnd/stepSize) #must be integer
simulationSettings.timeIntegration.endTime = tEnd

SC.visualizationSettings.nodes.drawNodesAsPoint=False
SC.visualizationSettings.nodes.defaultSize=0.06
SC.visualizationSettings.nodes.tiling = 16
SC.visualizationSettings.connectors.defaultSize = 0.02 #spring


#start solver:
mbs.SolveDynamic(simulationSettings)


