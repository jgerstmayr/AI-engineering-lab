# -*- coding: utf-8 -*- 
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# This is an EXUDYN example
#
# Details:  Create a reference solution for LLM-code evaluation
#
# Model:    A planar four-bar mechanism modelled with 2 points masses
#
# Author:   Johannes Gerstmayr
# Date:     2025-03-12
#
# Copyright:This file is part of Exudyn. Exudyn is free software. You can redistribute it and/or modify it under the terms of the Exudyn license. See 'LICENSE.txt' for more details.
#
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

# "description": "A planar four-bar mechanism modelled with 2 points masses and the 4 bars modeled as 
# massless distance constraints. The origin point of the mechanism fixed to ground is located at [0,0,0], 
# mass 1 with m1 = {mass1} kg is located at [0,{a},0], mass 2 with m2 = {mass2} kg is located at [{b},{a},0] 
# and the final point is located at [{b},-{c},0]. Gravity acts in negative y-direction and a 
# mass 1 has an initial velocity of [{vx},0,0]. There is no friction or other resistance.",

#%%parametersstart%%
#parameters which can be varied
mass1=0.5
mass2=1
a=0.1
b=0.8
c=0.1
vx=1.25
gravity=9.81

#%%samplecodestart%%

import exudyn as exu
from exudyn.utilities import *
import exudyn.graphics as graphics 

import numpy as np

SC = exu.SystemContainer()
mbs = SC.AddSystem()

oGround = mbs.CreateGround()

oMass1 = mbs.CreateMassPoint(referencePosition=[0,a,0],
                        physicsMass=mass1,
                        initialVelocity=[vx,0,0],
                        gravity=[0,-gravity,0])

mbs.CreateDistanceConstraint(bodyNumbers=[oGround,oMass1])

oMass2 = mbs.CreateMassPoint(referencePosition=[b,a,0],
                        physicsMass=mass2,
                        gravity=[0,-gravity,0])

mbs.CreateDistanceConstraint(bodyNumbers=[oMass1,oMass2])

oGround2 = mbs.CreateGround(referencePosition=[b,-c,0])
mbs.CreateDistanceConstraint(bodyNumbers=[oMass2,oGround2])

#add sensors:
sPos = mbs.AddSensor(SensorBody(bodyNumber=oMass1, storeInternal=True,
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

