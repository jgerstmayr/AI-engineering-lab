# -*- coding: utf-8 -*-
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# This is part of the AI engineering lab project
#
# Filename: agentDriver.py
#
# Details:  Runs agent.py methods from command line; use python agentDriver.py -h to see help;
#           besides running agent for LLM models, it also can merge results and exports latex tables
#
# Authors:  Johannes Gerstmayr
# Date:     2025-04-05
# Notes:    Ensure that the appropriate model files are available locally or through the Hugging Face model hub.
#
# License:  BSD-3 license
#
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

#%%++++++++++++++++++++++++++++++++++++++++++++
from agent import *

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
parser.add_argument("-c", "--numberOfConjecturesPerModel", type=int, default=10, help="Number of conjectures per model")
parser.add_argument("-r", "--randomizations", type=int, default=1, help="Number of randomizations / space variations")
parser.add_argument("-d", "--difficulty", type=int, default=25, help="Max difficulty level")
parser.add_argument("-wc", "--evaluateWrongConjectures",  action='store_true', help="use wrong models in conjectures")
parser.add_argument("-simOnly", "--useSimEvaluationOnly",  action='store_true', help="use simulation evaluation instead of conjectures")
parser.add_argument("-mult", "--useMultScore",  action='store_true', help="use multiplicative scores instead of summed scores")
parser.add_argument("-twoFails", "--useTwoFailsScore",  action='store_true', help="use score based on two fails per model")
parser.add_argument("-m", "--merge", type=str, default="", help="folder name to merge all results.json")
parser.add_argument("-l", "--writeLatexResults", action='store_true', help="write latex overview table")


parser.add_argument("-sMC", "--skipModelConjLoop",  action='store_true', help="skip generating model descriptions and conjectures")
parser.add_argument("-sGE", "--skipGenExudynLoop",  action='store_true', help="skip generating Exudyn models")
parser.add_argument("-sEC", "--skipConjecturesLoop",  action='store_true', help="skip evaluating conjectures")

# Parse arguments
args = parser.parse_args()

# Assigning values
llmShortName = args.llmName
numberOfConjecturesPerModel = args.numberOfConjecturesPerModel
numberOfRandomizations = args.randomizations
maxDifficultyLevel = args.difficulty
evaluateWrongConjectures = args.evaluateWrongConjectures
useSimEvaluationOnly = args.useSimEvaluationOnly
useMultScore = args.useMultScore
useTwoFailsScore = args.useTwoFailsScore
writeLatexResults = args.writeLatexResults
mergeDir = args.merge
doMerge = mergeDir != ''

skipModelConjLoop = args.skipModelConjLoop
skipGenExudynLoop = args.skipGenExudynLoop
skipConjecturesLoop = args.skipConjecturesLoop


#%%++++++++++++++++++++++++++++++++++++++++++++++++++++
#call from console with python testModelCreationJoh.py -m logsTM
if doMerge:
    from agent import MergeConjecturesResults
    MergeConjecturesResults(dirTestModels=mergeDir, 
                          resultsFileName="agentResults.csv",
                          useMultScore=useMultScore,
                          useTwoFailsScore=useTwoFailsScore,
                          writeLatexResults=writeLatexResults,
                          )
    sys.exit()
    
#%%+++++++++++++++++++++++++++++++++++++++++



from agent import *
from utilities import WriteDictToJSON, ReadJSONToDict


#%%+++++++++++++++++++++++++++++++++++++++++

llmModelName = ''
modelVRAM = 0
for key, value in llmModelsDict.items():
    if llmShortName == value['shortName']:
        llmModelName = key
        modelVRAM = value['VRAM']

if llmModelName == '':
    print('agent: NO VALID LLM MODEL SHORT NAME FOUND!\ncall with -h to get all available names')
    sys.exit()



#testing
if __name__ == '__main__':
    
    # mbsModelNames = ['singleMassOscillatorF', 'singleMassOscillatorFG']
    
    logDir='logsAgent/'+'log_'+llmShortName
    # skipModelConjLoop = False
    # skipGenExudynLoop = False
    # skipConjecturesLoop = False

    device=None #'cpu'
    modelQuantization=None
    
    suffix = '_MC'          #generate models and conjectures
    if skipModelConjLoop:
        suffix = '_GE'      #generate Exudyn
        if skipGenExudynLoop:
            suffix = '_EC'  #evaluate conjectures
    else:
        if skipGenExudynLoop and not skipConjecturesLoop:
            raise ValueError('impossible to skip Exudyn generation only')
    
    logger = Logger(logDir=logDir, suffix=suffix)
    logger.limitConsoleText = 500

    #%%+++++++++++++++++++++++++++++++++++++++++
    # Print values to verify
    if True: 
        logger.LogText(f"LLM model name: {llmShortName}", printToConsole=True)
        logger.LogText(f"Number of randomizations: {numberOfRandomizations}", printToConsole=True, timestamp=False)
        logger.LogText(f"Number of conjectures per model: {numberOfConjecturesPerModel}", printToConsole=True, timestamp=False)
        logger.LogText(f"Max difficulty level: {maxDifficultyLevel}", printToConsole=True, timestamp=False)
        logger.LogText(f"Use wrong conjecture models: {evaluateWrongConjectures}", printToConsole=True, timestamp=False)
        logger.LogText(f"Use simulation evaluation only: {useSimEvaluationOnly}", printToConsole=True, timestamp=False)
        logger.LogText(f"Skip skipModelConjLoop: {skipModelConjLoop}", printToConsole=True, timestamp=False)
        logger.LogText(f"Skip skipGenExudynLoop: {skipGenExudynLoop}", printToConsole=True, timestamp=False)
        logger.LogText(f"Skip skipConjecturesLoop: {skipConjecturesLoop}", printToConsole=True, timestamp=False)
    
    #%%+++++++++++++++++++++++++++++++++++++++++


    contextWindowMaxSize = 1024*3 #2048 is exceeded in some Exudyn generation tasks
    if 'qwq-32b' in llmModelName:
        contextWindowMaxSize = 1024*7

    llmModel = MyLLM(modelName=llmModelName, 
                     logger=logger, 
                     device=device, 
                     contextWindowMaxSize=contextWindowMaxSize, 
                     modelQuantization=modelQuantization)


    mbsModelLoader = ModelLoader()
    # only loading models with sample files (needed for comparison) and parameters - ATM
    mbsModelLoader.LoadStandardModelDescriptions(maxDifficultyLevel=maxDifficultyLevel, 
                                                 #specificModels=mbsModelNames, 
                                                 onlyWithSampleFiles=True, 
                                                 onlyParameterizedModels=True)

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


    if 'qwq-32b' in llmModelName:
        print('increasing maxTokens for Conjecture Evaluation for qwq-32b')
        agent.maxTokensEvaluateConjecture = 1024*6

    if not skipModelConjLoop: #False: read data
        # Tests Exudyn simulation code generation for multiple models, writes files into directories
        rr = agent.GenerateModelsAndConjecturesLoop(
                                          numberOfConjecturesPerModel=numberOfConjecturesPerModel,
                                          numberOfRandomizations=numberOfRandomizations,
                                          generateWrongConjectures=evaluateWrongConjectures,
                                          )
    
        WriteDictToJSON(rr, JoinPath(logDir,'results_MC.json') )

    if not skipGenExudynLoop:
        rr = ReadJSONToDict(JoinPath(logDir,'results_MC.json') )
    
        rr = agent.GenerateExudynModelsAndEval(rr)

        WriteDictToJSON(rr, JoinPath(logDir,'results_GE.json') )
    
    if not skipConjecturesLoop:
        rr = ReadJSONToDict(JoinPath(logDir,'results_GE.json') )

        rr = agent.EvaluateAllConjectures(rr, evaluateWrongConjectures=False,
                                          useSimEvaluationOnly=useSimEvaluationOnly)

        if evaluateWrongConjectures:
            logger.LogText('\n'*5+'************************\nNOW SWITCHING TO WRONG MODEL CONJECTURES\n************************'+'\n'*5,
                           separator=True, printToConsole=True)
            rr = agent.EvaluateAllConjectures(rr, evaluateWrongConjectures=True, 
                                              useSimEvaluationOnly=useSimEvaluationOnly)

        WriteDictToJSON(rr, JoinPath(logDir,'results.json') )
        
        
    LogOverallCounter2File(filePath='_globalTokenCount.txt', deltaCounter=llmModel.numberOfTokensGlobal)
    
    llmModel.FreeMemory()
    