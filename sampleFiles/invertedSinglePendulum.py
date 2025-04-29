# -*- coding: utf-8 -*- 
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# This is an EXUDYN example
#
# Details:  Create a reference solution for LLM-code evaluation
#
# Model:    An inverted pendulum on a cart modelled with two mass points
#
# Author:   Johannes Gerstmayr
# Date:     2025-03-12
#
# Copyright:This file is part of Exudyn. Exudyn is free software. You can redistribute it and/or modify it under the terms of the Exudyn license. See 'LICENSE.txt' for more details.
#
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

# "description": "An inverted pendulum on a cart modelled with two mass points, where the cart is attached
# to ground with a spherical joint where the x-coordinate is not constrained, such that it can move along 
# the x-direction. The pendulum is modelled with a distance constraint between cart and pendulum mass: 
# cart mass m1 = {mass1} kg, pendulum mass m2 = {mass2} kg, pendulum length L = {length} m, and 
# gravity g = {gravity} m/s^2 which acts in negative y-direction. A disturbance force f = {force} N 
# acts in x-direction at the pendulum and no control is applied on the cart.",

#%%parametersstart%%
#parameters which can be varied
mass1=4
mass2=0.5
length=0.8
force=0.1
stiffness=1e5
gravity=9.81

#%%samplecodestart%%

import exudyn as exu
from exudyn.utilities import *
import exudyn.graphics as graphics 

import numpy as np

SC = exu.SystemContainer()
mbs = SC.AddSystem()

oGround = mbs.CreateGround()

oCart = mbs.CreateMassPoint(referencePosition=[0,0,0],
                            physicsMass=mass1,
                            gravity=[0,-gravity,0],
                            graphicsDataList=[graphics.Brick(size=[0.2,0.05,0.05],color=graphics.color.red)])

# only works for exudyn >= 1.9.69
mbs.CreateSphericalJoint(bodyNumbers=[oGround, oCart],
                          constrainedAxes=[0,1,1],
                          position=[0,0,0],
                          jointRadius=0.01)


oPendulum = mbs.CreateMassPoint(referencePosition=[0,length,0],
                            physicsMass=mass2,
                            gravity=[0,-gravity,0])

mbs.CreateDistanceConstraint(bodyNumbers=[oCart,oPendulum])

mbs.CreateForce(bodyNumber=oPendulum, loadVector=[force,0,0])

#add sensors:
sPos = mbs.AddSensor(SensorBody(bodyNumber=oPendulum, storeInternal=True,
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
SC.visualizationSettings.openGL.lineWidth = 3

exu.StartRenderer()
mbs.WaitForUserToContinue()

#start solver:
mbs.SolveDynamic(simulationSettings)

SC.WaitForRenderEngineStopFlag()
exu.StopRenderer()

#%%samplecodestop%%
mbs.PlotSensor(sPos)
mbs.SolutionViewer()


