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

#"description": "A 3D mass point with mass m = {mass} kg is attached to a string with length {length} m, 
# with overall motion in x-y plane and gravity g = {gravity} m/s^2 applied in negative z-direction. The mass 
# point is placed initially at [{length},0,0] and the initial velocity is [{0,{vy},0] given in m/s. 
# The string shall be modelled as rigid distance between the mass point and the ground position at [0,0,0].",

#default values for rigid mode:
stiffness = -1
damping = 0

#%%parametersstart%%
#parameters which can be varied

mass=2
length=0.5
vy=5
gravity=9.81
stiffness=2000
damping=20


#%%samplecodestart%%

import exudyn as exu
from exudyn.utilities import *
import exudyn.graphics as graphics 

import numpy as np

SC = exu.SystemContainer()
mbs = SC.AddSystem()

oGround = mbs.CreateGround()

oMassPoint = mbs.CreateMassPoint(referencePosition=[ length, 0, 0],
                                 initialVelocity=[0,vy,0],
                                 physicsMass=mass,
                                 gravity=[0,0,-gravity])

if stiffness == -1:
    mbs.CreateDistanceConstraint(bodyNumbers=[oGround,oMassPoint])
else:
    mbs.CreateSpringDamper(bodyNumbers=[oGround,oMassPoint],
                           stiffness=stiffness,
                           damping=damping)
    
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
SC.visualizationSettings.nodes.defaultSize=0.05
SC.visualizationSettings.nodes.tiling = 32

exu.StartRenderer()
mbs.WaitForUserToContinue()

#start solver:
mbs.SolveDynamic(simulationSettings)

SC.WaitForRenderEngineStopFlag()
exu.StopRenderer()

#%%samplecodestop%%
mbs.PlotSensor(sPos,components=[2])
mbs.SolutionViewer()


