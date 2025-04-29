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

# "description": "Two free flying rigid elements, each modeled as a rigid body with brick-shape "
# "(density = {density} kg/m^3, lx={lx} m, wy={wy} m, hz={hz} m). Rigid body 1 is placed at [lx/2,0,0] "
# "and rigid body 2 at [3*lx/2,0,0]. A Cartesian spring-damper is attached between rigid body 1 "
# "at [lx/2,0,0] (local position) and at rigid body 2 at [-lx/2,0,0] (also local position). "
# "Body1 has initial velocity [0,{vy},0] and body2 has initial velocity [0,-{vy},0] and gravity is zero.",

#%%parametersstart%%
#parameters which can be varied

density=2000
lx = 1
wy = 0.2
hz = 0.1
vy = 4
k = 20000
d = 100

#%%samplecodestart%%

import exudyn as exu
from exudyn.utilities import *
import exudyn.graphics as graphics 

import numpy as np

SC = exu.SystemContainer()
mbs = SC.AddSystem()

oGround = mbs.CreateGround(graphicsDataList=[graphics.CheckerBoard(point=[0,0,-0.25],size=5)])

inertiaCube = InertiaCuboid(density=density, sideLengths=[lx,wy,hz])

# Creates a free rigid body with defined inertia and applies an initial rotation and velocity.
oBody1 = mbs.CreateRigidBody(inertia = inertiaCube,
                             referencePosition = [lx/2,0,0], #reference position, not COM
                             initialVelocity = [0,vy,0],
                             graphicsDataList=[graphics.Brick(size=[lx,wy,hz],color=graphics.color.blue,addEdges=True)])

oBody2 = mbs.CreateRigidBody(inertia = inertiaCube,
                             referencePosition = [3*lx/2,0,0], #reference position, not COM
                             initialVelocity = [0,-vy,0],
                             graphicsDataList=[graphics.Brick(size=[lx,wy,hz],color=graphics.color.green,addEdges=True)])

mbs.CreateCartesianSpringDamper( bodyNumbers=[oBody1, oBody2],
                        localPosition0=[lx/2,0,0],
                        localPosition1=[-lx/2,0,0],
                        stiffness = [k]*3,
                        damping = [d]*3,
                        )

#add sensors:
sPos = mbs.AddSensor(SensorBody(bodyNumber=oBody2, storeInternal=True,
                                outputVariableType=exu.OutputVariableType.Position))

#%%
mbs.Assemble()

tEnd = 2
stepSize = 0.001

simulationSettings = exu.SimulationSettings()
simulationSettings.solutionSettings.solutionWritePeriod = 1e-1
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

