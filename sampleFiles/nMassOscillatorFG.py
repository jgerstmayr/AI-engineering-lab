# -*- coding: utf-8 -*- 
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# This is an EXUDYN example
#
# Details:  Create a reference solution for LLM-code evaluation
#
# Model:    N-link chain of mass-spring-damper elements
#
# Author:   Johannes Gerstmayr, Tobias Möltner
# Date:     2025-03-11
#
# Copyright:This file is part of Exudyn. Exudyn is free software. You can redistribute it and/or modify it under the terms of the Exudyn license. See 'LICENSE.txt' for more details.
#
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

# "description": "A serial chain of {nMasses} masses connected with springs-dampers. 
# Each mass has m = {mass} kg, the stiffnesses are k = {stiffness} N/m, and the damping 
# coefficients are d = {damping} Ns/m. The force applied to the mass with highest index 
# f = {force} N and the first mass is connected to ground via the first spring-damper. 
# The relaxed length of each spring is {distance} m. The system is subject to gravity 
# g = {gravity} m/s^2, and the serial chain is oriented along the global {axis}-axis.

gravity=0 #default if it does not exist
force=0
axis='x'

#%%parametersstart%%
#parameters which can be varied
nMasses=5
mass=10
stiffness=5000
damping=50
force=100
gravity=9.81
distance=0.5
axis='x'

#%%samplecodestart%%

import exudyn as exu
from exudyn.utilities import *
import exudyn.graphics as graphics 

import numpy as np

SC = exu.SystemContainer()
mbs = SC.AddSystem()

oGround = mbs.CreateGround()

axisDict = {'x':0,'y':1,'z':2}

dirVec = np.array([0,0,0])
dirVec[axisDict[axis]] = 1

lastBody = oGround
for i in range(nMasses):
    oMass = mbs.CreateMassPoint(referencePosition = (i+1)*distance*dirVec, #convert cm to m
                                physicsMass = mass,
                                gravity = gravity*dirVec)
    
    #create spring damper with reference length computed from reference positions (=L)
    oSD = mbs.CreateSpringDamper(bodyOrNodeList = [lastBody, oMass], 
                                 stiffness = stiffness, 
                                 damping = damping) 
    lastBody = oMass
    
#add load on body:
mbs.CreateForce(bodyNumber = oMass, loadVector = force*dirVec)

#add sensors:
sDisp = mbs.AddSensor(SensorBody(bodyNumber=lastBody, storeInternal=True,
                                 outputVariableType=exu.OutputVariableType.Displacement))

mbs.Assemble()

tEnd = 2
stepSize = 0.001

simulationSettings = exu.SimulationSettings()
simulationSettings.solutionSettings.solutionWritePeriod = 1e-1
simulationSettings.solutionSettings.sensorsWritePeriod = 5e-3
simulationSettings.timeIntegration.numberOfSteps = int(tEnd/stepSize) #must be integer
simulationSettings.timeIntegration.endTime = tEnd

SC.visualizationSettings.nodes.drawNodesAsPoint=False
SC.visualizationSettings.nodes.defaultSize=0.1

exu.StartRenderer()
mbs.WaitForUserToContinue()

#start solver:
mbs.SolveDynamic(simulationSettings)

SC.WaitForRenderEngineStopFlag()
exu.StopRenderer()

#%%samplecodestop%%
mbs.PlotSensor(sDisp)


