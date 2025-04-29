# -*- coding: utf-8 -*- 
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# This is an EXUDYN example
#
# Details:  Create a reference solution for LLM-code evaluation
#
# Model:    two mass points connected by spring or distance constraint
#
# Author:   Johannes Gerstmayr
# Date:     2025-04-07
#
# Copyright:This file is part of Exudyn. Exudyn is free software. You can redistribute it and/or modify it under the terms of the Exudyn license. See 'LICENSE.txt' for more details.
#
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

# "description": "Two mass points connected by springs. The mass points both have mass m1 = m2 = {mass} kg, 
# are initially located at p1 = [-{ax},0,0] and p2 = [{ax},0,0], positions given in m. Mass m1 has initial 
# velocity {velStr} = {vel} m/s and m2 has initial velocity {velStr} = -{vel} m/s while all other initial 
# velocity components are zero. The spring between the two mass points is initially relaxed and has stiffness 
# k = {stiffness} N/m. No gravity nor forces are present.",

#default values for rigid mode:
stiffness = -1

#%%parametersstart%%
#parameters which can be varied

mass=1
ax=0.5
vel=4
velStr="vy"
stiffness=2000

#%%samplecodestart%%

import exudyn as exu
from exudyn.utilities import *
import exudyn.graphics as graphics 

import numpy as np

SC = exu.SystemContainer()
mbs = SC.AddSystem()

if velStr == "vy": 
    vInit = np.array([0,vel,0])
else:
    vInit = np.array([0,0,vel])

oMassPoint1 = mbs.CreateMassPoint(referencePosition=[-ax, 0, 0],
                                 initialVelocity=vInit,
                                 physicsMass=mass)

oMassPoint2 = mbs.CreateMassPoint(referencePosition=[ax, 0, 0],
                                 initialVelocity=-vInit,
                                 physicsMass=mass)

if stiffness == -1:
    mbs.CreateDistanceConstraint(bodyNumbers=[oMassPoint1,oMassPoint2])
else:
    mbs.CreateSpringDamper(bodyNumbers=[oMassPoint1,oMassPoint2],
                           stiffness=stiffness)
    
#add sensors:
sPos = mbs.AddSensor(SensorBody(bodyNumber=oMassPoint1, storeInternal=True,
                                outputVariableType=exu.OutputVariableType.Position))

#%%
mbs.Assemble()

tEnd = 2
stepSize = 0.001

simulationSettings = exu.SimulationSettings()
simulationSettings.solutionSettings.solutionWritePeriod = 1e-1
simulationSettings.solutionSettings.sensorsWritePeriod = 1e-2
simulationSettings.timeIntegration.numberOfSteps = int(tEnd/stepSize) #must be integer
simulationSettings.timeIntegration.endTime = tEnd

SC.visualizationSettings.nodes.drawNodesAsPoint=False
SC.visualizationSettings.nodes.defaultSize=0.05
SC.visualizationSettings.nodes.tiling = 32

#start solver:
mbs.SolveDynamic(simulationSettings)

#%%samplecodestop%%
mbs.PlotSensor(sPos,components=[2])
mbs.SolutionViewer()


