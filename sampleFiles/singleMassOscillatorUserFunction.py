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

# "description": "Mass-spring-damper with the following properties: mass m = {mass} kg, stiffness 
# k = {stiffness} N/m, and damping d = {damping} Ns/m. The force applied to the mass in x-direction 
# is given by the time-dependent function f(t) = {forceFunction}. The spring-damper is aligned with 
# the x-axis and the spring has a length of {length} m and is relaxed in the initial position. 
# Gravity is neglected.",

#import math  #?ADD this for safety because of the user functions?

#%%parametersstart%%
#parameters which can be varied
mass=1
stiffness=2000
damping=20
length=0.2
forceFunction = "10.*math.sin(2*math.pi*t)"

#%%samplecodestart%%

import exudyn as exu
from exudyn.utilities import *
import exudyn.graphics as graphics 

import numpy as np
import math  


SC = exu.SystemContainer()
mbs = SC.AddSystem()

oGround = mbs.CreateGround()

oMass = mbs.CreateMassPoint(referencePosition = [length,0,0], #convert cm to m
                            physicsMass = mass)

#create spring damper with reference length computed from reference positions (=L)
oSD = mbs.CreateSpringDamper(bodyOrNodeList = [oMass, oGround], 
                             stiffness = stiffness, 
                             damping = damping) 

f = lambda t: eval(forceFunction)

def UFforce(mbs,t,loadVector):
    global f, forceFunction, math #this local scope does not see anything during exec !
    return [f(t),0,0]

#add load on body:
mbs.CreateForce(bodyNumber = oMass, 
                loadVectorUserFunction=UFforce,
                )

#add sensors:
sDisp = mbs.AddSensor(SensorBody(bodyNumber=oMass, storeInternal=True,
                                  outputVariableType=exu.OutputVariableType.Displacement))

#%%
mbs.Assemble()

tEnd = 1.2
stepSize = 0.002

simulationSettings = exu.SimulationSettings()
simulationSettings.solutionSettings.solutionWritePeriod = 1e-2
simulationSettings.solutionSettings.sensorsWritePeriod = 5e-3
simulationSettings.timeIntegration.numberOfSteps = int(tEnd/stepSize) #must be integer
simulationSettings.timeIntegration.endTime = tEnd

SC.visualizationSettings.nodes.drawNodesAsPoint=False
SC.visualizationSettings.openGL.lineWidth = 3
SC.visualizationSettings.nodes.defaultSize=0.05
SC.visualizationSettings.nodes.tiling = 16
SC.visualizationSettings.connectors.defaultSize = 0.005 #spring

exu.StartRenderer()
mbs.WaitForUserToContinue()

#start solver:
mbs.SolveDynamic(simulationSettings)

SC.WaitForRenderEngineStopFlag()
exu.StopRenderer()

#%%samplecodestop%%
mbs.PlotSensor(sDisp)


