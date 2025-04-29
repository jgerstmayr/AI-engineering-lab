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

# "description": "A slider-crank mechanism is given with a crank rotating about the z-axis. "
# "The crank is modelled as rigid body with cylinder shape (axis=z) with mass m = {mass} kg, radius r = {radius} m, and width = {width} m, "
# "and it is initially located at [0,0,-{width}]. "
# "The brick-shaped conrod and piston have identical parameters: density = {density} kg/m^3, "
# "and xyz-dimensions lx={lx} m, wy={wy} m, hz={hz} m, initially not rotated (straight configuration of slider-crank). "
# "The conrod's center is located initially at [r+0.5*lx,0,0] and the piston is initially located at [r+1.5*lx,0,0]. "
# "A torque [0,0,T] shall act on the crank, employing a user-function with T={torque} Nm until 1 s and 0 thereafter. "
# "The revolute joint between ground and crank is located at [0,0,0] (global coordinates), "
# "the revolute joint between crank and conrod is located at [r,0,0] (global coordinates), "
# "and the revolute joint between conrod and piston is located at [r+lx,0,0] (global coordinates). "
# "The prismatic joint (axis=x) between ground and piston is located at [r+1.5*lx,0,0] (global coordinates). "
# "No gravity acts on the system. Simulate the system for 2 s.",

#%%parametersstart%%
#parameters which can be varied

mass = 2
radius = 0.25
width = 0.1

density=7850
lx = 0.4
wy = 0.05
hz = 0.05

torque=2

#%%samplecodestart%%

import exudyn as exu
from exudyn.utilities import *
import exudyn.graphics as graphics 

import numpy as np

SC = exu.SystemContainer()
mbs = SC.AddSystem()

oGround = mbs.CreateGround(graphicsDataList=[graphics.CheckerBoard(point=[0,0,-0.25],size=4)])

volume = pi * radius**2 * width
inertiaCylinder = InertiaCylinder(density=mass/volume, length=width, outerRadius=radius, axis=2)

# Creates a free rigid body with defined inertia and applies an initial rotation and velocity.
oCrank = mbs.CreateRigidBody(inertia = inertiaCylinder,
                            referencePosition = [0,0,-width], #reference position, not COM
                            graphicsDataList=[graphics.Cylinder(pAxis=[0,0,-width/2],
                                                                vAxis=[0,0,width],
                                                                radius=radius,
                                                                color=graphics.color.dodgerblue,nTiles=64),
                                              graphics.Basis(length=radius*1.5)])

inertiaCube = InertiaCuboid(density=density, sideLengths=[lx,wy,hz])

oBody1 = mbs.CreateRigidBody(inertia = inertiaCube,
                            referencePosition = [radius+0.5*lx,0,0], #reference position, not COM
                            graphicsDataList=[graphics.Brick(size=[0.95*lx,wy,hz],color=graphics.color.blue,addEdges=True)])

oBody2 = mbs.CreateRigidBody(inertia = inertiaCube,
                            referencePosition = [radius+1.5*lx,0,0], #reference position, not COM
                            graphicsDataList=[graphics.Brick(size=[0.95*lx,wy,hz],color=graphics.color.orange,addEdges=True)])

mbs.CreateRevoluteJoint(bodyNumbers=[oGround, oCrank],
                        position=[0,0,-1*width], #-width; global position of joint
                        axis=[0,0,1], #rotation along global z-axis
                        axisRadius = 0.7*wy, axisLength=1.25*width,
                        )
mbs.CreateRevoluteJoint(bodyNumbers=[oCrank,oBody1],
                        position=[radius,0,0], #global position of joint
                        axis=[0,0,1], #rotation along global z-axis
                        axisRadius = 0.7*wy, axisLength=1.5*hz,
                        )
mbs.CreateRevoluteJoint(bodyNumbers=[oBody1,oBody2],
                        position=[radius+lx,0,0], #global position of joint
                        axis=[0,0,1], #rotation along global z-axis
                        axisRadius = 0.7*wy, axisLength=1.25*hz,
                        )

mbs.CreatePrismaticJoint(bodyNumbers=[oGround,oBody2],
                        position=[radius+1.5*lx,0,0], #global position of joint
                        axis=[1,0,0], #rotation along global z-axis
                        axisRadius = 0.02, axisLength=0.4
                        )


def UFtorque(mbs, t, loadVector):
    fact = 1 if t <= 1 else 0
    return fact*np.array(loadVector)

mbs.CreateTorque(bodyNumber=oCrank, loadVector=[0,0,torque], loadVectorUserFunction=UFtorque)


#add sensors:
sPos = mbs.AddSensor(SensorBody(bodyNumber=oBody2, storeInternal=True,
                                outputVariableType=exu.OutputVariableType.Position))
sAngVel = mbs.AddSensor(SensorBody(bodyNumber=oCrank, storeInternal=True,
                                outputVariableType=exu.OutputVariableType.AngularVelocity))

#%%
mbs.Assemble()

tEnd = 2
stepSize = 0.001

simulationSettings = exu.SimulationSettings()
simulationSettings.solutionSettings.solutionWritePeriod = 1e-1
simulationSettings.solutionSettings.sensorsWritePeriod = 5e-3
simulationSettings.timeIntegration.numberOfSteps = int(tEnd/stepSize) #must be integer
simulationSettings.timeIntegration.endTime = tEnd
# simulationSettings.timeIntegration.verboseMode = 1

simulationSettings.linearSolverSettings.ignoreSingularJacobian = True
simulationSettings.linearSolverType = exu.LinearSolverType.EigenDense

SC.visualizationSettings.nodes.drawNodesAsPoint=False
SC.visualizationSettings.nodes.defaultSize=1
SC.visualizationSettings.openGL.lineWidth = 3
SC.visualizationSettings.openGL.shadow = 0.25

exu.StartRenderer()
mbs.WaitForUserToContinue()

#start solver:
mbs.SolveDynamic(simulationSettings)

SC.WaitForRenderEngineStopFlag()
exu.StopRenderer()

#%%samplecodestop%%
mbs.PlotSensor(sPos,components=[0], closeAll=True)
mbs.PlotSensor(sAngVel,components=[2])
mbs.SolutionViewer()

