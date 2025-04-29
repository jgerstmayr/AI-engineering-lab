# -*- coding: utf-8 -*- 
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# This is an EXUDYN example
#
# Details:  Create a reference solution for LLM-code evaluation
#
# Model:    n-pendulum, representing a chain of mass points and distance constraints under gravity
#
# Author:   Johannes Gerstmayr
# Date:     2025-03-11
#
# Copyright:This file is part of Exudyn. Exudyn is free software. You can redistribute it and/or modify it under the terms of the Exudyn license. See 'LICENSE.txt' for more details.
#
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

# "description": "Straight elastic chain modelled with {nMasses} mass points connected with spring-dampers 
# with the following properties: masses m = {mass} kg, lengths of each chain element L = {length} m, 
# stiffness k = {stiffness} and damping d = {damping} of chain elements, and gravity g = {gravity} m/s^2 
# which acts in negative y-direction. The pendulum starts from horizontal configuration, where all masses 
# are aligned with the x-axis. The top-left and top-right spring-dampers are attached to ground accordingly, 
# where the left ground position shall be at x=0 and y=0.",

#%%parametersstart%%
#parameters which can be varied
nMasses=20
mass=5
length=4
gravity=9.81
stiffness=2000
damping=100

#%%samplecodestart%%

import exudyn as exu
from exudyn.utilities import *
import exudyn.graphics as graphics 

import numpy as np

SC = exu.SystemContainer()
mbs = SC.AddSystem()

oGround = mbs.CreateGround()

firstBody = None
lastBody = None
midBody = None
for i in range(nMasses):
    oMass = mbs.CreateMassPoint(referencePosition=[length*i,0,0],
                                physicsMass=mass,
                                gravity=[0,-gravity,0])
    if int(nMasses/2) == i:
        midBody = oMass
    if i == 0:
        firstBody = oMass
    else:
        mbs.CreateSpringDamper(bodyNumbers=[lastBody,oMass],
                               stiffness=stiffness,
                               damping=damping)
    lastBody = oMass

#last body
oGround2 = mbs.CreateGround(referencePosition=[length*(nMasses-1),0,0])

mbs.CreateSphericalJoint(bodyNumbers=[firstBody,oGround],
                         position=[0,0,0])
mbs.CreateSphericalJoint(bodyNumbers=[lastBody,oGround2],
                         position=[length*(nMasses-1),0,0])

#add sensors:
sPos = mbs.AddSensor(SensorBody(bodyNumber=midBody, storeInternal=True,
                                outputVariableType=exu.OutputVariableType.Position))

#%%
mbs.Assemble()

tEnd = 2
stepSize = 0.005

simulationSettings = exu.SimulationSettings()
simulationSettings.solutionSettings.solutionWritePeriod = 0.5
simulationSettings.solutionSettings.sensorsWritePeriod = 1e-2
simulationSettings.timeIntegration.numberOfSteps = int(tEnd/stepSize) #must be integer
simulationSettings.timeIntegration.endTime = tEnd

SC.visualizationSettings.nodes.drawNodesAsPoint=False
SC.visualizationSettings.nodes.defaultSize=0.5
SC.visualizationSettings.nodes.tiling = 16
SC.visualizationSettings.connectors.defaultSize = 0.05 #spring

exu.StartRenderer()
mbs.WaitForUserToContinue()

#start solver:
mbs.SolveDynamic(simulationSettings)

SC.WaitForRenderEngineStopFlag()
exu.StopRenderer()

#%%samplecodestop%%
mbs.PlotSensor(sPos, components=[1])
mbs.SolutionViewer()


