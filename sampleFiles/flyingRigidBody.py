# -*- coding: utf-8 -*- 
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# This is an EXUDYN example
#
# Details:  Create a reference solution for LLM-code evaluation
#
# Model:    Free flying brick-shape rigid body with initial velocities
#
# Author:   Johannes Gerstmayr
# Date:     2025-04-07
#
# Copyright:This file is part of Exudyn. Exudyn is free software. You can redistribute it and/or modify it under the terms of the Exudyn license. See 'LICENSE.txt' for more details.
#
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

# "description": "A free flying rigid body with brick-shape, density = {density} kg/m^3, and 
# xyz-dimensions of the cuboid lx={lx}m, wy={wy}m, hz={hz}m is investigated. The COM of the body 
# is initially located at [0,0,0]. The initial velocity shall be [{vx},{vy},{vz}] and the initial
# angular velocity is [{avx},{avy},{avz}]. Gravity g = {gravity} m/s^2 acts in negative {gAxis}-direction. 
# Contact with ground is not considered.",

#%%parametersstart%%
#parameters which can be varied

density = 200
lx = 4
wy = 0.8
hz = 1.5
vx = 5
vy = 5
vz = 5
avx = 0.5
avy = 2
avz = 0.5
gravity = 9.81
gAxis = "y"

#%%samplecodestart%%

import exudyn as exu
from exudyn.utilities import *
import exudyn.graphics as graphics 

import numpy as np

axisDict = {'x':0,'y':1,'z':2}
dirG = np.array([0,0,0])
dirG[axisDict[gAxis]] = 1

SC = exu.SystemContainer()
mbs = SC.AddSystem()

inertiaCube = InertiaCuboid(density=density, sideLengths=[lx,wy,hz])

# Creates a free rigid body with defined inertia and applies an initial rotation and velocity.
oBody = mbs.CreateRigidBody(inertia = inertiaCube,
                            referencePosition = [0,0,0], #reference position, not COM
                            initialVelocity=[vx,vy,vz],
                            initialAngularVelocity=[avx,avy,avz],
                            gravity = -gravity * dirG,
                            graphicsDataList=[graphics.Brick(size=[lx,wy,hz],color=graphics.color.blue)])


#add sensors:
sPos = mbs.AddSensor(SensorBody(bodyNumber=oBody, storeInternal=True,
                                outputVariableType=exu.OutputVariableType.Position))

#%%
mbs.Assemble()

tEnd = 2
stepSize = 0.001

simulationSettings = exu.SimulationSettings()
simulationSettings.solutionSettings.solutionWritePeriod = 5e-2
simulationSettings.solutionSettings.sensorsWritePeriod = 5e-3
simulationSettings.timeIntegration.numberOfSteps = int(tEnd/stepSize) #must be integer
simulationSettings.timeIntegration.endTime = tEnd

SC.visualizationSettings.nodes.drawNodesAsPoint=False
SC.visualizationSettings.nodes.defaultSize=1
SC.visualizationSettings.openGL.lineWidth = 3

#start solver:
mbs.SolveDynamic(simulationSettings)

#%%samplecodestop%%
mbs.PlotSensor(sPos,components=[1])
mbs.SolutionViewer()

