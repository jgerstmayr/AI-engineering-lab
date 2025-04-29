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

# "description": "A rigid body is suspended by 4 Cartesian spring-dampers. The rigid body has a 
# brick-shape with density = {density} kg/m^3, and xyz-dimensions lx={lx}m, ly={ly}m, lz={lz}m. 
# The COM of the body is located at [0,{ly}/2,0]. The Cartesian spring-dampers are located at the 
# x/z positions of the vertices of the body. The y-position at the body is -{ly}/2 and on ground y=0. 
# All spring-dampers have equal parameters: stiffness = [{kx},{ky},{kz}] N/m and 
# damping = [{dx},{dy},{dz}] Ns/m. Gravity g = {gravity} m/s^2 acts in negative y-direction, and 
# no further forces or daming are applied and contact with ground is ignored.",


#%%parametersstart%%
#parameters which can be varied

density = 400
lx = 4
ly = 0.75
lz = 1.5
kx = 10000
ky = 100000
kz = 10000
dx = 200
dy = 2000
dz = 200
gravity = 9.81

#%%samplecodestart%%

import exudyn as exu
from exudyn.utilities import *
import exudyn.graphics as graphics 

import numpy as np

SC = exu.SystemContainer()
mbs = SC.AddSystem()

oGround = mbs.CreateGround()

inertiaCube = InertiaCuboid(density=density, sideLengths=[lx,ly,lz])

# Creates a free rigid body with defined inertia and applies an initial rotation and velocity.
oBody = mbs.CreateRigidBody(inertia = inertiaCube,
                            referencePosition = [0,ly/2,0], #reference position, not COM
                            gravity = [0,-gravity,0],
                            graphicsDataList=[graphics.Brick(size=[lx,ly*0.8,lz],color=graphics.color.blue)])

mbs.CreateCartesianSpringDamper(bodyNumbers=[oGround, oBody],
                       localPosition0=[-lx/2,0,    -lz/2],
                       localPosition1=[-lx/2,-ly/2,-lz/2],
                       stiffness=[kx,ky,kz], 
                       damping=[dx,dy,dz])

mbs.CreateCartesianSpringDamper(bodyNumbers=[oGround, oBody],
                       localPosition0=[-lx/2,0,     lz/2],
                       localPosition1=[-lx/2,-ly/2, lz/2],
                       stiffness=[kx,ky,kz], 
                       damping=[dx,dy,dz])

mbs.CreateCartesianSpringDamper(bodyNumbers=[oGround, oBody],
                       localPosition0=[ lx/2,0,    -lz/2],
                       localPosition1=[ lx/2,-ly/2,-lz/2],
                       stiffness=[kx,ky,kz], 
                       damping=[dx,dy,dz])

mbs.CreateCartesianSpringDamper(bodyNumbers=[oGround, oBody],
                       localPosition0=[ lx/2,0,     lz/2],
                       localPosition1=[ lx/2,-ly/2, lz/2],
                       stiffness=[kx,ky,kz], 
                       damping=[dx,dy,dz])

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
mbs.PlotSensor(sPos,components=[1], closeAll=True)
mbs.SolutionViewer()

