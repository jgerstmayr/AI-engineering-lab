# -*- coding: utf-8 -*- 
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# This is an EXUDYN example
#
# Details:  Create a reference solution for LLM-code evaluation
#
# Model:    double mass-spring-damper oscillator
#
# Author:   Johannes Gerstmayr
# Date:     2025-04-07
#
# Copyright:This file is part of Exudyn. Exudyn is free software. You can redistribute it and/or modify it under the terms of the Exudyn license. See 'LICENSE.txt' for more details.
#
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

#"description": "Two-mass-spring-damper system consisting of two masses with the following properties: 
# mass m1 = m2 = {mass} kg, stiffness k1 = k2 = {stiffness} N/m, and damping d1 = d2 = {damping} Ns/m. 
# Each spring has a length of {length} cm and is relaxed in the initial configuration. The first mass is 
# placed at [{length},0,0] and the second mass at [2*{length},0,0]. The first spring is connected to 
# ground at [0,0,0]. A force {force} is applied in x-direction to mass 2. No gravity is applied to the system.

#%%parametersstart%%
#parameters which can be varied
mass=1
stiffness=2000
damping=20
force=10
length=5

#%%samplecodestart%%

import exudyn as exu
from exudyn.utilities import *
import exudyn.graphics as graphics 

import numpy as np

SC = exu.SystemContainer()
mbs = SC.AddSystem()

oGround = mbs.CreateGround()

oMass1 = mbs.CreateMassPoint(referencePosition = [length*0.01,0,0], #convert cm to m
                            physicsMass = mass)
oMass2 = mbs.CreateMassPoint(referencePosition = [2*length*0.01,0,0], #convert cm to m
                            physicsMass = mass)

#create spring damper with reference length computed from reference positions (=L)
oSD1 = mbs.CreateSpringDamper(bodyOrNodeList = [oGround, oMass1], 
                             stiffness = stiffness, 
                             damping = damping) 

oSD2 = mbs.CreateSpringDamper(bodyOrNodeList = [oMass1, oMass2], 
                             stiffness = stiffness, 
                             damping = damping) 
    
#add load on body:
mbs.CreateForce(bodyNumber = oMass2, loadVector = [force,0,0])

#add sensors:
sDisp = mbs.AddSensor(SensorBody(bodyNumber=oMass2, storeInternal=True,
                                 outputVariableType=exu.OutputVariableType.Displacement))

mbs.Assemble()

tEnd = 1
stepSize = 0.001

simulationSettings = exu.SimulationSettings()
simulationSettings.solutionSettings.solutionWritePeriod = 1e-1
simulationSettings.solutionSettings.sensorsWritePeriod = 1e-2
simulationSettings.timeIntegration.numberOfSteps = int(tEnd/stepSize) #must be integer
simulationSettings.timeIntegration.endTime = tEnd

SC.visualizationSettings.nodes.drawNodesAsPoint=False
SC.visualizationSettings.nodes.defaultSize=0.015
SC.visualizationSettings.connectors.defaultSize=0.01

# exu.StartRenderer()
# mbs.WaitForUserToContinue()

#start solver:
mbs.SolveDynamic(simulationSettings)

# SC.WaitForRenderEngineStopFlag()
# exu.StopRenderer()

#%%samplecodestop%%
mbs.PlotSensor(sDisp, closeAll=True)
mbs.SolutionViewer()


