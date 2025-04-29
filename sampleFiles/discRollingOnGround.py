# -*- coding: utf-8 -*- 
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# This is an EXUDYN example
#
# Details:  Create a reference solution for LLM-code evaluation
#
# Model:    Rotational motion of a spinning disk (around z-axis)
#
# Author:   Johannes Gerstmayr
# Date:     2025-03-12
#
# Copyright:This file is part of Exudyn. Exudyn is free software. You can redistribute it and/or modify it under the terms of the Exudyn license. See 'LICENSE.txt' for more details.
#
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

# "description": "Rolling motion of a solid disc with the following properties: mass m = {mass} kg, 
# radius r = {radius} m, width w = {width} m, and gravity g = {gravity} m/s^2 (in negative z-direction). 
# The disc's axis is initially aligned with the x-axis and it moves on the x-y plane. 
# The COM of the disc has an initial position of p0 = [{px},{py},{radius}], translational 
# velocity of vy = {initialVelocity} m/s and an according angular velocity. 
# Rolling shall be modelled ideal and without slipping.",

#%%parametersstart%%
#parameters which can be varied
mass = 4
radius = 0.3
width = 0.05
px = 1
py = 1
initialVelocity = 1
gravity = 9.81

#%%samplecodestart%%

import exudyn as exu
from exudyn.utilities import *
import exudyn.graphics as graphics 

import numpy as np

SC = exu.SystemContainer()
mbs = SC.AddSystem()

oGround = mbs.CreateGround(graphicsDataList=[graphics.CheckerBoard(size=6)])

volume = pi * radius**2 * width
inertiaCylinder = InertiaCylinder(density=mass/volume, length=width, outerRadius=radius, axis=0)

angularVelocity = initialVelocity/radius

# Creates a free rigid body with defined inertia and applies an initial rotation and velocity.
oDisc = mbs.CreateRigidBody(inertia = inertiaCylinder,
                            referencePosition = [0,0,radius], #reference position, not COM
                            initialAngularVelocity=[-angularVelocity,0,0],
                            initialVelocity=[0,initialVelocity,0],
                            graphicsDataList=[graphics.Cylinder(pAxis=[-width/2,0,0],
                                                                vAxis=[width,0,0],
                                                                radius=radius,
                                                                color=graphics.color.orange),
                                              graphics.Basis(length=radius*1.5)])

mbs.CreateRollingDisc(bodyNumbers=[oGround, oDisc], discRadius = radius, 
                      axisPosition=[0,0,0], axisVector=[1,0,0], #relative to disc
                      planePosition = [0,0,0], planeNormal = [0,0,1], #defines plane
                      constrainedAxes=[1,1,1] #constrain lateral motion, forward motion and normal contact
                      )

#add sensors:
sVel = mbs.AddSensor(SensorBody(bodyNumber=oDisc, storeInternal=True,
                                outputVariableType=exu.OutputVariableType.Velocity))

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
SC.visualizationSettings.openGL.lineWidth = 2

exu.StartRenderer()
mbs.WaitForUserToContinue()

#start solver:
mbs.SolveDynamic(simulationSettings)

SC.WaitForRenderEngineStopFlag()
exu.StopRenderer()

#%%samplecodestop%%
mbs.PlotSensor(sVel,components=[0,1])
mbs.SolutionViewer()

