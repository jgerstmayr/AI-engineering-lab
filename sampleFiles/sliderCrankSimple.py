# -*- coding: utf-8 -*- 
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# This is an EXUDYN example
#
# Details:  Create a reference solution for LLM-code evaluation
#
# Model:    double pendulum
#
# Author:   Johannes Gerstmayr
# Date:     2025-03-11
#
# Copyright:This file is part of Exudyn. Exudyn is free software. You can redistribute it and/or modify it under the terms of the Exudyn license. See 'LICENSE.txt' for more details.
#
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

# "description": "Simple slider-crank mechanism modelled with two mass points that are connected with"
# " distance constraints. The crank is modelled with a point mass m1 = {massCrank} kg, located at "
# "radius r = {radius} m (initially located at x=0, y=r) and constrained to ground with a distance r; "
# "the slider is a point mass m2 = {massSlider} kg, initially located at xSlider = {xSlider} m and "
# "ySlider = 0. The connecting rod is only represented as distance constraint between crank mass and "
# "slider mass. Add a spherical joint between mass 1 and ground and only constrain the z-axis motion and a "
# "second spherical joint to constrain the y- and z-axes motion of mass 2. "
# "A force fx = {forceSlider} acts on the slider in positive x-direction. "
# "The system is initially at rest, and no gravity is applied.",

#%%parametersstart%%
#parameters which can be varied
massCrank=0.5
massSlider=2
radius=0.5
xSlider=2
forceSlider=10

#%%samplecodestart%%

import exudyn as exu
from exudyn.utilities import *
import exudyn.graphics as graphics 

import numpy as np

SC = exu.SystemContainer()
mbs = SC.AddSystem()

oGround = mbs.CreateGround()

oMassCrank = mbs.CreateMassPoint(referencePosition=[0,radius,0],
                        physicsMass=massCrank)

mbs.CreateDistanceConstraint(bodyNumbers=[oGround,oMassCrank])
oMassSlider = mbs.CreateMassPoint(referencePosition=[xSlider,0,0],
                        physicsMass=massSlider)

mbs.CreateDistanceConstraint(bodyNumbers=[oMassCrank,oMassSlider])

mbs.CreateForce(bodyNumber=oMassSlider, loadVector=[forceSlider,0,0])

mbs.CreateSphericalJoint(bodyNumbers=[oGround, oMassSlider], 
                         position=[xSlider,0,0],
                         constrainedAxes=[0,1,1], jointRadius=0.02)

mbs.CreateSphericalJoint(bodyNumbers=[oGround, oMassCrank], 
                         position=[0,radius,0],
                         constrainedAxes=[0,0,1],show=False)

#add sensors:
sPos = mbs.AddSensor(SensorBody(bodyNumber=oMassSlider, storeInternal=True,
                                outputVariableType=exu.OutputVariableType.Position))

#%%
mbs.Assemble()

tEnd = 1
stepSize = 0.001

simulationSettings = exu.SimulationSettings()
simulationSettings.solutionSettings.solutionWritePeriod = 5e-2
simulationSettings.solutionSettings.sensorsWritePeriod = 1e-2
simulationSettings.timeIntegration.numberOfSteps = int(tEnd/stepSize) #must be integer
simulationSettings.timeIntegration.endTime = tEnd

SC.visualizationSettings.nodes.drawNodesAsPoint=False
SC.visualizationSettings.nodes.defaultSize=0.05
SC.visualizationSettings.nodes.tiling = 32

exu.StartRenderer()
mbs.WaitForUserToContinue()

#start solver:
mbs.SolveDynamic(simulationSettings)

SC.WaitForRenderEngineStopFlag()
exu.StopRenderer()

#%%samplecodestop%%
mbs.SolutionViewer()
mbs.PlotSensor(sPos)


