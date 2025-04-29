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

# "description": "Multibody n-pendulum system consisting of {nMasses} point masses connected with spring-dampers
 # with the following properties: masses m = {mass} kg, lengths of single elastic strings L = {length} m, 
 # stiffness k = {stiffness} and damping d = {damping} of strings, and gravity g = {gravity} m/s^2 which acts 
 # in negative y-direction. The pendulum starts from horizontal configuration, where all masses are aligned
 # with the x-axis.",


#%%parametersstart%%
#parameters which can be varied
nMasses=8
mass=0.5
length=0.25
gravity=9.81
stiffness=1000
damping=50

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
                                physicsMass=mass,
                                gravity=[0,-gravity,0])
    
    mbs.CreateSpringDamper(bodyNumbers=[lastBody,oMass],
                           stiffness=stiffness,
                           damping=damping)
    lastBody = oMass

#add sensors:
sPos = mbs.AddSensor(SensorBody(bodyNumber=lastBody, storeInternal=True,
                                outputVariableType=exu.OutputVariableType.Position))

#%%
mbs.Assemble()

tEnd = 0.5
stepSize = 0.001

simulationSettings = exu.SimulationSettings()
simulationSettings.solutionSettings.solutionWritePeriod = 5e-2
simulationSettings.solutionSettings.sensorsWritePeriod = 1e-2
simulationSettings.timeIntegration.numberOfSteps = int(tEnd/stepSize) #must be integer
simulationSettings.timeIntegration.endTime = tEnd

SC.visualizationSettings.nodes.drawNodesAsPoint=False
SC.visualizationSettings.nodes.defaultSize=0.06
SC.visualizationSettings.nodes.tiling = 16
SC.visualizationSettings.connectors.defaultSize = 0.02 #spring

exu.StartRenderer()
mbs.WaitForUserToContinue()

#start solver:
mbs.SolveDynamic(simulationSettings)

SC.WaitForRenderEngineStopFlag()
exu.StopRenderer()

#%%samplecodestop%%
mbs.SolutionViewer()
# mbs.PlotSensor(sPos)


