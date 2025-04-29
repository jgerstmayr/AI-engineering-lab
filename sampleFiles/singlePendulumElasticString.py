# -*- coding: utf-8 -*- 
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# This is an EXUDYN example
#
# Details:  Create a reference solution for LLM-code evaluation
#
# Model:    single pendulum
#
# Author:   Johannes Gerstmayr
# Date:     2025-03-11
#
# Copyright:This file is part of Exudyn. Exudyn is free software. You can redistribute it and/or modify it under the terms of the Exudyn license. See 'LICENSE.txt' for more details.
#
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

# Simple mathematical pendulum with the following properties: point mass m = {mass} kg, length of the elastic 
# string L = {length} m, string stiffness k = {stiffness} N/m, and gravity g = {gravity} m/s^2 which is applied
#  in negative y-direction. The pendulum is initialized with an angle of {angle} degrees from vertical (negative
# y-axis) equilibrium position, thus the mass being displaced in x-direction. The initial velocities of the 
# mass point are v_x = {vx} m/s and v_y = {vy} m/s, applied in x resp. y direction.

#%%parametersstart%%
#parameters which can be varied
mass=2
length=1
gravity=9.81
angle=60 #degree
stiffness=2000
vx=0
vy=1

#%%samplecodestart%%

import exudyn as exu
from exudyn.utilities import *
import exudyn.graphics as graphics 

import numpy as np

SC = exu.SystemContainer()
mbs = SC.AddSystem()

oGround = mbs.CreateGround()

angleRad = angle*np.pi/180
oMassPoint = mbs.CreateMassPoint(referencePosition=[ length * sin(angleRad), 
                                                    -length * cos(angleRad),0],
                                 initialVelocity=[vx,vy,0],
                                 physicsMass=mass,
                                 gravity=[0,-gravity,0])

mbs.CreateSpringDamper(bodyNumbers=[oGround,oMassPoint],stiffness=stiffness)

#add sensors:
sPos = mbs.AddSensor(SensorBody(bodyNumber=oMassPoint, storeInternal=True,
                                outputVariableType=exu.OutputVariableType.Position))

#%%
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

exu.StartRenderer()
mbs.WaitForUserToContinue()

#start solver:
mbs.SolveDynamic(simulationSettings)

SC.WaitForRenderEngineStopFlag()
exu.StopRenderer()

#%%samplecodestop%%
mbs.PlotSensor(sPos)
mbs.SolutionViewer()


