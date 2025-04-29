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

# "description": "A system consisting of a brick-shaped rigid body with mass m = {mass} kg freely moving
#  along a prismatic joint in {axis}-direction. The COM of the rigid body is placed at [0,0,0]. The side 
#  lengths of the rigid body are all equal with s = {s} m. A force f = {force} N acts on the rigid 
#  body's COM in {axis}-direction. Gravity is neglected.",

#%%parametersstart%%
#parameters which can be varied
mass=10
s = 0.5
axis = "x"
force = 20

#%%samplecodestart%%

import exudyn as exu
from exudyn.utilities import *
import exudyn.graphics as graphics 

import numpy as np

axisDict = {'x':0,'y':1,'z':2}
axisVec = np.array([0,0,0])
axisVec[axisDict[axis]] = 1

SC = exu.SystemContainer()
mbs = SC.AddSystem()

groundNormal = np.array([0,0,1]) #for visualization
if axis == 'z':
    groundNormal = np.array([1,0,0]) 
    
oGround = mbs.CreateGround(graphicsDataList=[graphics.CheckerBoard(point=-0.5*s*groundNormal,size=2,
                                                                   normal=groundNormal)])

inertiaCube = InertiaCuboid(density=mass/(s*s*s), sideLengths=[s,s,s])

# Creates a free rigid body with defined inertia and applies an initial rotation and velocity.
oBody = mbs.CreateRigidBody(inertia = inertiaCube,
                            referencePosition = [0,0,0], #reference position, not COM
                            graphicsDataList=[graphics.Brick(size=[s,s,s],color=graphics.color.blue)])

mbs.CreatePrismaticJoint(bodyNumbers=[oGround, oBody],
                        position=[0,0,0], #global position of joint
                        axis=axisVec,
                        axisLength = 1,
                        axisRadius=0.05,
                        )

mbs.CreateForce(bodyNumber=oBody, loadVector=force*axisVec)

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

