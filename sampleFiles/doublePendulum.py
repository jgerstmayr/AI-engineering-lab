# -*- coding: utf-8 -*- 
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# This is an EXUDYN example
#
# Details:  Create a reference solution for LLM-code evaluation
#
# Model:    double pendulum
#
# Author:   Johannes Gerstmayr
# Date:     2025-03-11
#
# Copyright:This file is part of Exudyn. Exudyn is free software. You can redistribute it and/or modify it under the terms of the Exudyn license. See 'LICENSE.txt' for more details.
#
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

# "doublePendulum": {
#     "description": "Double pendulum system consisting of two mass points which are connected 
# with inextensible strings with the following properties: mass m1 = {mass1} 
# kg, mass m2 = {mass2} kg, length of the strings L1 = {length1} m, L2 = {length2} m, and gravity 
# g = {gravity} m/s² which acts in negative y-direction. The first arm of the pendulum points in 
# positive x direction and the second arm in positive y-direction. Air resistance is neglected.",

#%%parametersstart%%
#parameters which can be varied
mass1=2
mass2=3
length1=0.8
length2=0.5
gravity=9.81

#%%samplecodestart%%

import exudyn as exu
from exudyn.utilities import *
import exudyn.graphics as graphics 

import numpy as np

SC = exu.SystemContainer()
mbs = SC.AddSystem()

oGround = mbs.CreateGround()

oMassPoint1 = mbs.CreateMassPoint(referencePosition=[length1,0,0],
                        physicsMass=mass1,
                        gravity=[0,-gravity,0])

mbs.CreateDistanceConstraint(bodyNumbers=[oGround,oMassPoint1])
oMassPoint2 = mbs.CreateMassPoint(referencePosition=[length1,length2,0],
                        physicsMass=mass2,
                        gravity=[0,-gravity,0])

mbs.CreateDistanceConstraint(bodyNumbers=[oMassPoint1,oMassPoint2])

#add sensors:
sPos = mbs.AddSensor(SensorBody(bodyNumber=oMassPoint2, storeInternal=True,
                                outputVariableType=exu.OutputVariableType.Position))

#%%
mbs.Assemble()

tEnd = 1
stepSize = 0.001

simulationSettings = exu.SimulationSettings()
simulationSettings.solutionSettings.solutionWritePeriod = 1e-1
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
mbs.SolutionViewer()
mbs.PlotSensor(sPos)


