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

# "description": "Double pendulum consisting of two mass points which are connected with a spring-damper 
# with the following properties: mass m1 = {mass1} kg, mass m2 = {mass2} kg, length of the strings 
# L1 = {length1} m, L2 = {length2} m, and gravity g = {gravity} m/s^2 which acts in negative y-direction. 
# The first arm of the pendulum points in {arm1direction}-direction and the second arm in 
# {arm2direction}-direction (relative to mass1)."

#%%parametersstart%%
#parameters which can be varied
mass1=1
mass2=0.5
length1=0.5
length2=0.3
stiffness1=1000
stiffness2=500
gravity=9.81
arm1direction='positive x'
arm2direction='positive y'

#%%samplecodestart%%

import exudyn as exu
from exudyn.utilities import *
import exudyn.graphics as graphics 

import numpy as np

vecDict = {'positive x':[1,0,0],
           'positive y':[0,1,0],
           'negative x':[-1,0,0],
           'negative y':[0,-1,0],
           }

vec1 = length1*np.array(vecDict[arm1direction])
vec2 = length2*np.array(vecDict[arm2direction])

SC = exu.SystemContainer()
mbs = SC.AddSystem()

oGround = mbs.CreateGround()

oMassPoint1 = mbs.CreateMassPoint(referencePosition=vec1,
                        physicsMass=mass1,
                        gravity=[0,-gravity,0])

mbs.CreateSpringDamper(bodyNumbers=[oGround,oMassPoint1],stiffness=stiffness1)
oMassPoint2 = mbs.CreateMassPoint(referencePosition=vec1+vec2,
                        physicsMass=mass2,
                        gravity=[0,-gravity,0])

mbs.CreateSpringDamper(bodyNumbers=[oMassPoint1,oMassPoint2],stiffness=stiffness2)

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
SC.visualizationSettings.nodes.defaultSize=0.1
SC.visualizationSettings.nodes.tiling = 32
SC.visualizationSettings.connectors.defaultSize = 0.05 #spring

exu.StartRenderer()
mbs.WaitForUserToContinue()

#start solver:
mbs.SolveDynamic(simulationSettings)

SC.WaitForRenderEngineStopFlag()
exu.StopRenderer()

#%%samplecodestop%%
mbs.SolutionViewer()
mbs.PlotSensor(sPos)


