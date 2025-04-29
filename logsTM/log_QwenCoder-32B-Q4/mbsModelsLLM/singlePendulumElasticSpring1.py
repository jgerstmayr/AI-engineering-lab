# ** given model description: **
# Simple mathematical pendulum with the following properties: point mass
# m = 4 kg, elastic string length = 1.25 m, string stiffness k = 1500 N/m,
# and gravity g = 3.73 m/s^2 which is applied in negative y-direction. The pendulum's
# reference configuration is such that the string has an angle 120 degrees from the
# vertical (negative y-axis), thus the mass being on a positive x-coordinate for positive
# angles. The initial velocities of the mass point are v_x = -0.02 m/s and v_y =
# -0.06 m/s, applied in x resp. y direction.
#import Exudyn library and utilities
import exudyn as exu
from exudyn.utilities import *
import numpy as np

#set up new multibody system to work with
SC = exu.SystemContainer()
mbs = SC.AddSystem()

#Create a ground object as an inertial reference frame for the multibody system.
oGround = mbs.CreateGround(referencePosition=[0,0,0])

#Create a point mass object with specified mass at reference position with optional initial conditions
oMass = mbs.CreateMassPoint(physicsMass=4, referencePosition=[1.25*np.cos(np.radians(120)), -1.25*np.sin(np.radians(120)), 0], 
                            initialDisplacement=[0,0,0],  
                            initialVelocity=[-0.02,-0.06,0],    
                            gravity=[0,-3.73,0])          

#Create a linear spring-damper system between two bodies or between a body and the ground.
oSpringDamper = mbs.CreateSpringDamper(bodyNumbers=[oGround, oMass], 
                                      localPosition0=[0,0,0], 
                                      localPosition1=[0,0,0], 
                                      referenceLength=1.25, 
                                      stiffness=1500, damping=0)

#Assemble has to be called just before solving or system analysis (after AddSensor!).
mbs.Assemble()

tEnd = 2
stepSize = 0.001

simulationSettings = exu.SimulationSettings()
simulationSettings.solutionSettings.solutionWritePeriod = 5e-2
simulationSettings.solutionSettings.sensorsWritePeriod = 1e-2
simulationSettings.timeIntegration.numberOfSteps = int(tEnd/stepSize) #must be integer
simulationSettings.timeIntegration.endTime = tEnd

SC.visualizationSettings.nodes.drawNodesAsPoint=False
SC.visualizationSettings.nodes.defaultSize=0.2
SC.visualizationSettings.nodes.tiling = 32
SC.visualizationSettings.connectors.defaultSize = 0.05 #spring


#start solver:
mbs.SolveDynamic(simulationSettings)


