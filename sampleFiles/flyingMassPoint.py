# -*- coding: utf-8 -*- 
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# This is an EXUDYN example
#
# Details:  Create a reference solution for LLM-code evaluation
#
# Model:    Flying mass
#
# Author:   Johannes Gerstmayr
# Date:     2025-03-11
#
# Copyright:This file is part of Exudyn. Exudyn is free software. You can redistribute it and/or modify it under the terms of the Exudyn license. See 'LICENSE.txt' for more details.
#
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

# "Projectile motion of a point mass with the following properties: mass m = {mass} kg, gravity g = {gravity} m/s^2, initial velocity in x/y/z-direction: "
# "vx = {vx} m/s, vy = {vy} m/s, vz = 0 m/s. The initial position is given as x=0 and y=0. Gravity acts along the negative y-axis, and there is no other external propulsion or resistance. "
# "The motion shall be evaluated for 1 s. Contact with ground is not modelled, so the projectile can go below y=0.",
       

#%%parametersstart%%
#parameters which can be varied
mass=10
gravity=9.81
vx=5
vy=1

#%%samplecodestart%%

import exudyn as exu
from exudyn.utilities import *
import exudyn.graphics as graphics 

import numpy as np

SC = exu.SystemContainer()
mbs = SC.AddSystem()

oGround = mbs.CreateGround(graphicsDataList=[graphics.CheckerBoard(point=[0,0,-0.1],size=5)])

oMass = mbs.CreateMassPoint(referencePosition = [0,0,0],
                            initialVelocity= [vx,vy,0],
                            physicsMass = mass,
                            gravity = [0,-gravity,0])

#add sensors:
sPos = mbs.AddSensor(SensorBody(bodyNumber=oMass, storeInternal=True,
                                outputVariableType=exu.OutputVariableType.Position))

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
SC.visualizationSettings.nodes.defaultSize=0.1

exu.StartRenderer()
mbs.WaitForUserToContinue()

#start solver:
mbs.SolveDynamic(simulationSettings)

SC.WaitForRenderEngineStopFlag()
exu.StopRenderer()

#%%samplecodestop%%
mbs.PlotSensor(sPos,components=[0,1])
mbs.SolutionViewer()

