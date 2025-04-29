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

# "description": "Simple mathematical pendulum with the following properties: mass m = {mass} kg, 
# length of the inextensible string L = {length} m, and gravity g = {gravity} m/s² which acts in 
# negative y-direction, while the pendulum moves in the x-y plane. The pendulum from vertical 
# equilibrium position with an angle of {angle} degrees (positive rotation sense). Air resistance
#  is neglected.",

#%%parametersstart%%
#parameters which can be varied
mass=2
length=1
gravity=9.81
angle=15 #degree

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
                        physicsMass=mass,
                        gravity=[0,-gravity,0])

mbs.CreateDistanceConstraint(bodyNumbers=[oGround,oMassPoint])

#add sensors:
sPos = mbs.AddSensor(SensorBody(bodyNumber=oMassPoint, storeInternal=True,
                                outputVariableType=exu.OutputVariableType.Position))

#%%
mbs.Assemble()

tEnd = 2
stepSize = 0.001

simulationSettings = exu.SimulationSettings()
simulationSettings.solutionSettings.solutionWritePeriod = 1e-2
simulationSettings.solutionSettings.sensorsWritePeriod = 1e-2
simulationSettings.timeIntegration.numberOfSteps = int(tEnd/stepSize) #must be integer
simulationSettings.timeIntegration.endTime = tEnd

SC.visualizationSettings.nodes.drawNodesAsPoint=False
SC.visualizationSettings.nodes.defaultSize=0.05
SC.visualizationSettings.nodes.tiling = 32

exu.StartRenderer()
mbs.WaitForUserToContinue()

#start solver:
mbs.SolveDynamic(simulationSettings)

SC.WaitForRenderEngineStopFlag()
exu.StopRenderer()

#%%samplecodestop%%
mbs.PlotSensor(sPos)
mbs.SolutionViewer()


