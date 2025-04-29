# -*- coding: utf-8 -*- 
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# This is an EXUDYN example
#
# Details:  Create a reference solution for LLM-code evaluation
#
# Model:    Free falling mass
#
# Author:   Johannes Gerstmayr
# Date:     2025-03-11
#
# Copyright:This file is part of Exudyn. Exudyn is free software. You can redistribute it and/or modify it under the terms of the Exudyn license. See 'LICENSE.txt' for more details.
#
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

# "Free-fall motion of an object with the following properties: point mass m = {mass} kg, gravity g = {gravity} m/s^2 (in negative z-direction). "
# "The object starts from rest and is dropped from a height hz = {height} m. The free fall shall be analyzed for 1 s. Air resistance is neglected. ",

#%%parametersstart%%
#parameters which can be varied
mass=1.5
gravity=9.81
height=20

#%%samplecodestart%%

import exudyn as exu
from exudyn.utilities import *
import exudyn.graphics as graphics 

import numpy as np

SC = exu.SystemContainer()
mbs = SC.AddSystem()

oGround = mbs.CreateGround(graphicsDataList=[graphics.CheckerBoard(point=[0,-1,0], normal=[0,1,0],size=50)])

oMass = mbs.CreateMassPoint(referencePosition = [0,0,height],
                            physicsMass = mass,
                            gravity = [0,0,-gravity])

#add sensors:
sPos = mbs.AddSensor(SensorBody(bodyNumber=oMass, storeInternal=True,
                                outputVariableType=exu.OutputVariableType.Position))

#%%
mbs.Assemble()

tEnd = 2
stepSize = 0.001

simulationSettings = exu.SimulationSettings()
simulationSettings.solutionSettings.solutionWritePeriod = 1e-2
simulationSettings.solutionSettings.sensorsWritePeriod = 5e-3
simulationSettings.timeIntegration.numberOfSteps = int(tEnd/stepSize) #must be integer
simulationSettings.timeIntegration.endTime = tEnd

SC.visualizationSettings.nodes.drawNodesAsPoint=False
SC.visualizationSettings.nodes.defaultSize=1

exu.StartRenderer()
mbs.WaitForUserToContinue()

#start solver:
mbs.SolveDynamic(simulationSettings)

SC.WaitForRenderEngineStopFlag()
exu.StopRenderer()

#%%samplecodestop%%
mbs.PlotSensor(sPos,components=[2])
mbs.SolutionViewer()

