# -*- coding: utf-8 -*-
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# This is part of the AI engineering lab project
#
# Filename: testModelCreationDriver.py
#
# Details:  Driver file for testModelCreation, to be used from command line; type python testModelCreationDriver.py -h to see help
#           Run tests for single LLM, or merge results and export to latex
#
# Authors:  Johannes Gerstmayr
# Date:     2025-03-15
# Notes:    Ensure that the appropriate model files are available locally or through the Hugging Face model hub.
#
# License:  BSD-3 license
#
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

#%%++++++++++++++++++++++++++++++++++++++++++++++++++++
import argparse
import sys
from myLLM import llmModelsDict, GetLLMmodelNameFormShortName
from utilities import JoinPath, LogOverallCounter2File

# Create the argument parser
description = "Call test models with LLM model name and other parameters. Available LLM models are:\n"
sep=''
for key, value in llmModelsDict.items():
    description += sep+value['shortName']+'\n'
    sep = ', '

parser = argparse.ArgumentParser(description=description)

# Define arguments
parser.add_argument("-n", "--llmName", type=str, default="Llama3.1-8B-Q4", help="LLM Model Name")
parser.add_argument("-r", "--randomizations", type=int, default=10, help="Number of randomizations / space variations")
parser.add_argument("-d", "--difficulty", type=int, default=25, help="Max difficulty level")
parser.add_argument("-c", "--includeConjectures",  action='store_true', help="include conjectures")
parser.add_argument("-s", "--doSpaceVariation",  action='store_true', help="perform space variations instead of randomizations")
parser.add_argument("-wc", "--useWrongModelsInConjectures",  action='store_true', help="use wrong models in conjectures")
parser.add_argument("-m", "--merge", type=str, default="", help="folder name to merge all results.json")
parser.add_argument("-l", "--writeLatexResults", action='store_true', help="write latex overview table")
# Parse arguments
args = parser.parse_args()

# Assigning values
llmShortName = args.llmName
numberOfRandomizations = args.randomizations
maxDifficultyLevel = args.difficulty
includeConjectures = args.includeConjectures
doSpaceVariation = args.doSpaceVariation * 7 #7 used to also include some endline variations ...
useWrongModelsInConjectures = args.useWrongModelsInConjectures
writeLatexResults = args.writeLatexResults
mergeDir = args.merge
# mergeDir = 'logsTM'
doMerge = mergeDir != ''

#%%+++++++++++++++++++++++++++++
#choose manually:
# llmShortName = 'Llama3.1-8B-HF'
# llmShortName = 'Llama3-8B-Q8'
# llmShortName = 'Llama3-8B-Q4'
# llmShortName = 'Llama3.1-8B-Q8'
# llmShortName = 'Llama3.1-8B-Q4'
# llmShortName = 'Phi4-Q4'
# maxDifficultyLevel = 5 # 9=13 models;7=5 models; 25=20 models
# numberOfRandomizations = 1
# includeConjectures = True
#+++++++++++++++++++++++++++++


# Print values to verify
if not doMerge: 
    print(f"LLM Model Name: {llmShortName}")
    print(f"Number of Randomizations: {numberOfRandomizations}")
    print(f"Max Difficulty Level: {maxDifficultyLevel}")
    print(f"Include Conjectures: {includeConjectures}")
    print(f"Do space variations: {doSpaceVariation}")
    print(f"Use wrong conjecture models: {useWrongModelsInConjectures}")

#%%++++++++++++++++++++++++++++++++++++++++++++++++++++
#call from console with python testModelCreationJoh.py -m logsTM
if doMerge:
    from testModelCreation import MergeTestModelResults
    MergeTestModelResults(dirTestModels=mergeDir, 
                          resultsFileName="overallResults.csv",
                          includeConjectures=includeConjectures,
                          writeLatexResults=writeLatexResults,
                          )
    sys.exit()
    
#%%+++++++++++++++++++++++++++++++++++++++++

from agent import *
from testModelCreation import *
from utilities import WriteDictToJSON


#%%+++++++++++++++++++++++++++++++++++++++++

llmModelName = ''
modelVRAM = 0
for key, value in llmModelsDict.items():
    if llmShortName == value['shortName']:
        llmModelName = key
        modelVRAM = value['VRAM']

if llmModelName == '':
    print('testModelCreation: NO VALID LLM MODEL SHORT NAME FOUND!\ncall with -h to get all available names')
    sys.exit()


logDir='logsTM'+'E'*includeConjectures+'S'*(doSpaceVariation>0)+'_WC'*useWrongModelsInConjectures+'/log_'+llmShortName
# logDir='logsTest'

#for RTX 4090 with 24GB VRAM:
#device=None if modelVRAM < 23 else 'cpu' #i9:None, cpu:'cpu'
device=None

modelQuantization=None

logger = Logger(logDir=logDir)
logger.LogDebug('logDir='+logDir,printToConsole=True)

logger.limitConsoleText = 200 #5000
llmModel = MyLLM(modelName=llmModelName, 
                 logger=logger, 
                 device=device, 
                 modelQuantization=modelQuantization,
                 contextWindowMaxSize=4096, #4096 no problem for llama8B, Phi4, QwenCoder?, FluentlyLM?
                 #nThreads=1,
                 )

specificModels = ['doubleMassOscillatorFG','massPointOnStringRigid','massPointOnStringElastic','xyLinkage','flyingRigidBody',
     'suspendedRigidBody','gyroscopeOnSphericalJoint','prismaticJointSystem','twoMassPointsWithSprings','twoMassPointsWithDistances']
specificModels = ['elasticChain','doublePendulumElasticSpring',
                  'discRollingOnGround','invertedSinglePendulum',
                  'elasticChain',
                  'doublePendulumElasticSpring',
                  #'nPendulum',
                  'nMassOscillatorFG',
                  #done:
                  # 'singlePendulum',
                  # 'discRollingOnGround',
                  # 'xyLinkage',
                  # 'nPendulumElasticSpring', 1 fail
                  # 'singlePendulumRigidBody', #had gravity fixed as 9.81
                  #'singlePendulumElasticSpring',#1 fail
                  #'suspendedRigidBody',
                  #'invertedSinglePendulum',
                  ]
                  

mbsModelLoader = ModelLoader()
# only loading models with sample files (needed for comparison) and parameters - ATM
mbsModelLoader.LoadStandardModelDescriptions(maxDifficultyLevel=maxDifficultyLevel, 
                                             # specificModels=['nMassOscillatorFG'],
                                             #specificModels=specificModels,
                                             onlyWithSampleFiles=True, 
                                             onlyParameterizedModels=True
                                             )

agent = LabAgent(llmModel=llmModel, 
                 logger=logger, 
                 mbsModelLoader=mbsModelLoader,
                 agentOutputDataDir=logDir, 
                 maxDifficultyLevel=maxDifficultyLevel)

#consider:
agent.useExudynTimeout = False #in case that infinite loops are added or very small time steps

if ( (llmModelsDict[llmModelName]['VRAM'] < 20)
      and 'gguf' in llmModelName.lower()):
    n_batch = 64 #default is 8
    if llmModelsDict[llmModelName]['VRAM'] < 15:
        n_batch *= 2

    print(f'increasing batch size to {n_batch} for smaller llmModel!')
    agent.llmGenerateDefaultArgs['n_batch'] = n_batch


# Tests Exudyn simulation code generation for multiple models, writes files into directories
r = RunMBSmodelTests(agent, 
                     # runWithoutLLM=True,
                     includeConjectures=includeConjectures,
                     numberOfRandomizations=numberOfRandomizations,
                     useWrongModelsInConjectures=useWrongModelsInConjectures,
                     numberOfConjecturesPerModel=8, #default: 8
                     doSpaceVariation=doSpaceVariation,
                     storeGeneratedTextsAndResults=(doSpaceVariation!=0),
                     )

WriteDictToJSON(r, JoinPath(logDir,'results.json') )
    
LogOverallCounter2File(filePath='_globalTokenCount.txt', deltaCounter=llmModel.numberOfTokensGlobal)
       
llmModel.FreeMemory()
