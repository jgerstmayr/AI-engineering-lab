# -*- coding: utf-8 -*- 
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# This is an EXUDYN example
#
# Details:  Create a reference solution for LLM-code evaluation
#
# Model:    Pendulum modeled with a brick-shape rigid body
#
# Author:   Johannes Gerstmayr
# Date:     2025-03-12
#
# Copyright:This file is part of Exudyn. Exudyn is free software. You can redistribute it and/or modify it under the terms of the Exudyn license. See 'LICENSE.txt' for more details.
#
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

# "description": "Pendulum modeled with a brick-shape rigid body and a revolute joint. The body has 
# density = {density} kg/m^3, and xyz-dimensions lx={lx}m, wy={wy}m, hz={hz}m. The center of mass is 
# equal to the reference point and initially located at [lx/2,0,0], while the revolute joint (rotation 
# around z-axis) is located at [0,0,0] (global coordinates). Gravity g = {gravity} m/s^2 acts in negative
#  y-direction, and no further force acts."

#%%parametersstart%%
#parameters which can be varied
density=1000
lx = 1.2
wy = 0.4
hz = 0.2
gravity=9.81

#%%samplecodestart%%

import exudyn as exu
from exudyn.utilities import *
import exudyn.graphics as graphics 

import numpy as np

SC = exu.SystemContainer()
mbs = SC.AddSystem()

oGround = mbs.CreateGround(graphicsDataList=[graphics.CheckerBoard(point=[0,0,-0.5],size=2)])

inertiaCube = InertiaCuboid(density=density, sideLengths=[lx,wy,hz])

# Creates a free rigid body with defined inertia and applies an initial rotation and velocity.
oBody = mbs.CreateRigidBody(inertia = inertiaCube,
                            referencePosition = [lx/2,0,0], #reference position, not COM
                            gravity = [0,-gravity,0],
                            graphicsDataList=[graphics.Brick(size=[lx,wy,hz],color=graphics.color.blue)])

mbs.CreateRevoluteJoint(bodyNumbers=[oGround, oBody],
                        position=[0,0,0], #global position of joint
                        axis=[0,0,1], #rotation along global z-axis
                        )

#add sensors:
sPos = mbs.AddSensor(SensorBody(bodyNumber=oBody, storeInternal=True,
                                outputVariableType=exu.OutputVariableType.Position))

#%%
mbs.Assemble()

tEnd = 1
stepSize = 0.001

simulationSettings = exu.SimulationSettings()
simulationSettings.solutionSettings.solutionWritePeriod = 5e-2
simulationSettings.solutionSettings.sensorsWritePeriod = 5e-3
simulationSettings.timeIntegration.numberOfSteps = int(tEnd/stepSize) #must be integer
simulationSettings.timeIntegration.endTime = tEnd

SC.visualizationSettings.nodes.drawNodesAsPoint=False
SC.visualizationSettings.nodes.defaultSize=1
SC.visualizationSettings.openGL.lineWidth = 3

exu.StartRenderer()
mbs.WaitForUserToContinue()

#start solver:
mbs.SolveDynamic(simulationSettings)

SC.WaitForRenderEngineStopFlag()
exu.StopRenderer()

#%%samplecodestop%%
mbs.PlotSensor(sPos,components=[1])
mbs.SolutionViewer()

