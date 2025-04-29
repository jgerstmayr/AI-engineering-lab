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

# "description": "A rotor is modelled with a rigid body mounted on ground with Cartesian spring-dampers. "
# "The rotor is modelled as cylinder with mass m = {mass} kg, disc radius r = {radius} m, and length = {length}. "
# "The axis of the rotor is initially oriented along the x-axis and the reference point of the rotor lies at [{length}/2,0,0] (which is also the COM). "
# "The rotor is connected to ground with Cartesian spring-dampers at global positions [0,0,0] and [{length}/2,0,0], "
# "the positions being identical with the local positions of the spring-dampers on the rotor. "
# "The Cartesian spring-dampers have stiffness values [{kx},{ky},{ky}] N/m and damping values [{dx},{dy},{dy}] Ns/m. "
# "The initial angular velocity of the rotor is [{angularVelocity},0,0]. "
# "Gravity g = {gravity} m/s^2 acts in negative {gAxis}-direction, and no further forces or damping are applied.",

#default values if inactive
angularVelocity = 0
comY = 0

#%%parametersstart%%
#parameters which can be varied

mass = 2
radius = 0.1
length = 0.5
kx = 1500
ky = 4000
dx = 5
dy = 10
# angularVelocity = 500
comY = 0.002
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

volume = pi * radius**2 * length
inertiaCylinder = InertiaCylinder(density=mass/volume, length=length, outerRadius=radius, axis=0)
inertiaCylinder = inertiaCylinder.Translated([0,comY,0])

# Creates a free rigid body with defined inertia and applies an initial rotation and velocity.
oBody = mbs.CreateRigidBody(inertia = inertiaCylinder,
                            referencePosition = [0,0,0], #reference position, not COM
                            initialAngularVelocity=[angularVelocity,0,0],
                            gravity = -gravity*dirG,
                            graphicsDataList=[graphics.Cylinder(pAxis=[-length/2,0,0],
                                                                vAxis=[length,0,0],
                                                                radius=radius,
                                                                color=graphics.color.dodgerblue),
                                              graphics.Basis(length=radius*1.5)])

mbs.CreateCartesianSpringDamper(bodyNumbers=[oGround, oBody],
                                localPosition0=[-length/2,0,0],
                                localPosition1=[-length/2,0,0],
                                stiffness=[kx,ky,ky],
                                damping=[dx,dy,dy],
                                )
mbs.CreateCartesianSpringDamper(bodyNumbers=[oGround, oBody],
                                localPosition0=[ length/2,0,0],
                                localPosition1=[ length/2,0,0],
                                stiffness=[kx,ky,ky],
                                damping=[dx,dy,dy],
                                )

torque = 1
if comY != 0: #in this case, we simulate runup
    mbs.CreateTorque(bodyNumber=oBody, loadVector=[torque,0,0])

#add sensors:
sPos = mbs.AddSensor(SensorBody(bodyNumber=oBody, storeInternal=True,
                                outputVariableType=exu.OutputVariableType.Position))
sAngVel = mbs.AddSensor(SensorBody(bodyNumber=oBody, storeInternal=True,
                                outputVariableType=exu.OutputVariableType.AngularVelocity))

#%%
mbs.Assemble()

tEnd = 2
stepSize = 0.0002 #for large rotation speeds

simulationSettings = exu.SimulationSettings()
simulationSettings.solutionSettings.solutionWritePeriod = 2e-1
simulationSettings.solutionSettings.sensorsWritePeriod = 5e-3
simulationSettings.timeIntegration.numberOfSteps = int(tEnd/stepSize) #must be integer
simulationSettings.timeIntegration.endTime = tEnd
# simulationSettings.timeIntegration.verboseMode = 1

SC.visualizationSettings.nodes.drawNodesAsPoint=False
SC.visualizationSettings.nodes.defaultSize=1
SC.visualizationSettings.openGL.lineWidth = 3
SC.visualizationSettings.general.drawCoordinateSystem = False
SC.visualizationSettings.general.drawWorldBasis = True

#start solver:
mbs.SolveDynamic(simulationSettings)

#%%samplecodestop%%
mbs.PlotSensor(sPos,components=[1 if gAxis =='y' else 2], closeAll=True)
mbs.PlotSensor(sAngVel,components=[0],)

mbs.SolutionViewer()

