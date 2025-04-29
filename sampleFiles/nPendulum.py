# -*- coding: utf-8 -*- 
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# This is an EXUDYN example
#
# Details:  Create a reference solution for LLM-code evaluation
#
# Model:    n-pendulum, representing a chain of mass points and distance constraints under gravity
#
# Author:   Johannes Gerstmayr
# Date:     2025-03-11
#
# Copyright:This file is part of Exudyn. Exudyn is free software. You can redistribute it and/or modify it under the terms of the Exudyn license. See 'LICENSE.txt' for more details.
#
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

# "description": "Multibody n-pendulum system consisting of {nMasses} masses with the following 
# properties: masses m = {mass} kg, length of inextensible strings L = {length} m, and gravity 
# g = {gravity} m/s². The pendulum starts from horizontal configuration, where all masses are 
# coaxially aligned along the x-axis and all masses have an initial velocity of {initialVelocity} m/s
#  in negative y-direction. Gravity acts in negative y-direction and air resistance is neglected.",

#%%parametersstart%%
#parameters which can be varied
nMasses=8
mass=0.5
length=0.25
gravity=9.81
initialVelocity=0.5

#%%samplecodestart%%

import exudyn as exu
from exudyn.utilities import *
import exudyn.graphics as graphics 

import numpy as np

SC = exu.SystemContainer()
mbs = SC.AddSystem()

oGround = mbs.CreateGround()

lastBody = oGround
for i in range(nMasses):
    oMass = mbs.CreateMassPoint(referencePosition=[length*(i+1),0,0],
                                initialVelocity=[0,-initialVelocity,0],
                                physicsMass=mass,
                                gravity=[0,-gravity,0])
    
    mbs.CreateDistanceConstraint(bodyNumbers=[lastBody,oMass])
    lastBody = oMass

#add sensors:
sPos = mbs.AddSensor(SensorBody(bodyNumber=lastBody, storeInternal=True,
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
SC.visualizationSettings.nodes.tiling = 16

exu.StartRenderer()
mbs.WaitForUserToContinue()

#start solver:
mbs.SolveDynamic(simulationSettings)

SC.WaitForRenderEngineStopFlag()
exu.StopRenderer()

#%%samplecodestop%%
mbs.SolutionViewer()
# mbs.PlotSensor(sPos)


