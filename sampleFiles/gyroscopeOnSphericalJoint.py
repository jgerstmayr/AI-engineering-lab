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

# "description": "A gyro is modelled with a rigid body and a spherical joint. The gyro is modelled as 
# cylindrical disc with mass m = {mass} kg, disc radius r = {radius} m, and disc width w = {width}. The 
# axis of the disc is initially oriented along positive x-axis and the disc is positioned at [{offsetX},0,0] 
# (which is also the COM). The local position [-{offsetX},0,0] of the disc is connected with a spherical joint 
# to ground at [0,0,0]. The initial angular velocity of the disc is [{angularVelocity},0,0]. Gravity 
# g = {gravity} m/s^2 acts in negative {gAxis}-direction, and no further forces or daming are applied.


#%%parametersstart%%
#parameters which can be varied

mass = 20
radius = 0.2
width = 0.025
offsetX = 0.25
angularVelocity = 200
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

oGround = mbs.CreateGround()

volume = pi * radius**2 * width
inertiaCylinder = InertiaCylinder(density=mass/volume, length=width, outerRadius=radius, axis=0)

# Creates a free rigid body with defined inertia and applies an initial rotation and velocity.
oBody = mbs.CreateRigidBody(inertia = inertiaCylinder,
                            referencePosition = [offsetX,0,0], #reference position, not COM
                            initialAngularVelocity=[angularVelocity,0,0],
                            gravity = -gravity*dirG,
                            graphicsDataList=[graphics.Cylinder(pAxis=[-width/2,0,0],
                                                                vAxis=[width,0,0],
                                                                radius=radius,
                                                                color=graphics.color.green),
                                              graphics.Cylinder(pAxis=[-offsetX,0,0],
                                                                vAxis=[offsetX,0,0],
                                                                radius=radius*0.1,
                                                                color=graphics.color.grey),
                                              graphics.Basis(length=radius*1.5)])

mbs.CreateSphericalJoint(bodyNumbers=[oGround, oBody],
                         position=[0,0,0])

#add sensors:
sPos = mbs.AddSensor(SensorBody(bodyNumber=oBody, storeInternal=True,
                                outputVariableType=exu.OutputVariableType.Position))

#%%
mbs.Assemble()

tEnd = 10
stepSize = 0.0005 #for large rotation speeds

simulationSettings = exu.SimulationSettings()
simulationSettings.solutionSettings.solutionWritePeriod = 5e-1
simulationSettings.solutionSettings.sensorsWritePeriod = 1e-2
simulationSettings.timeIntegration.numberOfSteps = int(tEnd/stepSize) #must be integer
simulationSettings.timeIntegration.endTime = tEnd

SC.visualizationSettings.nodes.drawNodesAsPoint=False
SC.visualizationSettings.nodes.defaultSize=1
SC.visualizationSettings.openGL.lineWidth = 3
SC.visualizationSettings.general.drawCoordinateSystem = False
SC.visualizationSettings.general.drawWorldBasis = True

#start solver:
mbs.SolveDynamic(simulationSettings)

#%%samplecodestop%%
mbs.PlotSensor(sPos,components=[1 if gAxis =='y' else 2], closeAll=True)
mbs.SolutionViewer()

