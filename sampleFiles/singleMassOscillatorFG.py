# -*- coding: utf-8 -*- 
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# This is an EXUDYN example
#
# Details:  Create a reference solution for LLM-code evaluation
#
# Model:    single mass-spring-damper element
#
# Author:   Johannes Gerstmayr, Tobias Möltner
# Date:     2025-03-11
#
# Copyright:This file is part of Exudyn. Exudyn is free software. You can redistribute it and/or modify it under the terms of the Exudyn license. See 'LICENSE.txt' for more details.
#
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

# "Mass-spring-damper with the following properties: The mass point with mass m = {mass} kg lies at [{length} cm,0,0], stiffness k = {stiffness} N/m, and damping d = {damping} Ns/m. "
# "The force applied to the mass in x-direction is f = {force} N. The spring-damper between mass point and ground at [0,0,0] is aligned with the x-axis, "
# "the spring has a length of {length} cm and is initially relaxed. Gravity is neglected."

gravity=0 #default if it does not exist

#%%parametersstart%%
#parameters which can be varied
mass=1
stiffness=2000
damping=20
length=5        #cm
force=10
gravity=9.81

#static solution: u=0.009905

#%%samplecodestart%%

import exudyn as exu
from exudyn.utilities import *
import exudyn.graphics as graphics 

import numpy as np

SC = exu.SystemContainer()
mbs = SC.AddSystem()

oGround = mbs.CreateGround()

oMass = mbs.CreateMassPoint(referencePosition = [length*0.01,0,0], #convert cm to m
                            physicsMass = mass,
                            gravity = [gravity,0,0])

#create spring damper with reference length computed from reference positions (=L)
oSD = mbs.CreateSpringDamper(bodyOrNodeList = [oMass, oGround], 
                             stiffness = stiffness, 
                             damping = damping) 

#add load on body:
mbs.CreateForce(bodyNumber = oMass, loadVector = [force,0,0])

#add sensors:
sDisp = mbs.AddSensor(SensorBody(bodyNumber=oMass, storeInternal=True,
                                  outputVariableType=exu.OutputVariableType.Displacement))

#%%
mbs.Assemble()

tEnd = 1
stepSize = 0.001

simulationSettings = exu.SimulationSettings()
simulationSettings.solutionSettings.solutionWritePeriod = 1e-2
simulationSettings.solutionSettings.sensorsWritePeriod = 5e-3
simulationSettings.timeIntegration.numberOfSteps = int(tEnd/stepSize) #must be integer
simulationSettings.timeIntegration.endTime = tEnd

SC.visualizationSettings.nodes.drawNodesAsPoint=False
SC.visualizationSettings.nodes.defaultSize=0.01
SC.visualizationSettings.openGL.lineWidth = 3

exu.StartRenderer()
mbs.WaitForUserToContinue()

#start solver:
mbs.SolveDynamic(simulationSettings)

SC.WaitForRenderEngineStopFlag()
exu.StopRenderer()

#%%samplecodestop%%
mbs.PlotSensor(sDisp)


