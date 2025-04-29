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

# "description": "Torsional oscillator consisting of a cylindrical disc with rotational motion around 
# z-axis and a torsional spring-damper with the following properties: mass m = {mass} kg, disc radius 
# r = {radius} m, disc width w = {width}, torsional stiffness k = {stiffness} Nm/rad, torsional damping 
# coefficient d = {damping} Nms/rad and initial angular velocity omega_z = {angular_velocity} rad/s. 
# The disk is mounted on a frictionless revolute joint and experiences a constant torque T_z = {torque}.

#%%parametersstart%%
#parameters which can be varied
mass = 20
radius = 0.2
width = 0.025
angular_velocity = 50
torque = 2
stiffness = 2000
damping = 5

#%%samplecodestart%%

import exudyn as exu
from exudyn.utilities import *
import exudyn.graphics as graphics 

import numpy as np

SC = exu.SystemContainer()
mbs = SC.AddSystem()

oGround = mbs.CreateGround()

volume = pi * radius**2 * width
inertiaCylinder = InertiaCylinder(density=mass/volume, length=width, outerRadius=radius, axis=2)

# Creates a free rigid body with defined inertia and applies an initial rotation and velocity.
oBody = mbs.CreateRigidBody(inertia = inertiaCylinder,
                            referencePosition = [0,0,0], #reference position, not COM
                            initialAngularVelocity=[0,0,angular_velocity],
                            graphicsDataList=[graphics.Cylinder(pAxis=[0,0,-width/2],
                                                                vAxis=[0,0,width],
                                                                radius=radius,
                                                                color=graphics.color.green),
                                              graphics.Basis(length=radius*1.5)])

mbs.CreateRevoluteJoint(bodyNumbers=[oGround, oBody],
                        position=[0,0,0], #global position of joint
                        axis=[0,0,1], #rotation along global z-axis
                        axisRadius=0.01, axisLength=0.02,
                        )

mbs.CreateTorque(bodyNumber=oBody, loadVector=[0,0,torque])

mbs.CreateTorsionalSpringDamper(bodyNumbers=[oGround, oBody],
                                position=[0,0,0],
                                axis=[0,0,1],
                                stiffness=stiffness,
                                damping=damping,
                                )

#add sensors:
sRot = mbs.AddSensor(SensorBody(bodyNumber=oBody, storeInternal=True,
                                outputVariableType=exu.OutputVariableType.AngularVelocity))

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
mbs.PlotSensor(sRot,components=[2])
mbs.SolutionViewer()

