# -*- coding: utf-8 -*-
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# This is part of the AI engineering lab project
#
# Filename: testModelCreation.py
#
# Details:  Main code and class for simulation model creation and testing;
#           In RunMBSmodelTests, Exudyn elements are extracted, example code is generated and LLM is asked to create code; 
#           Further, code is tested on executabilty and correctness (using ground-truth sample codes);
#           use MergeTestModelResults to merge results
#
# Authors:  Johannes Gerstmayr, Tobias Möltner
# Date:     2024-09-18
# Notes:    Ensure that the appropriate model files are available locally or through the Hugging Face model hub.
#
# License:  BSD-3 license
#
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

import sys
import traceback
import time
import os
import numpy as np
import datetime
import exudyn as exu

from mbsModelLoader import ModelLoader

from agent import LabAgent
from utilities import ReadFile, WriteFile, WriteDictToJSON, GetScalarClassObjectsDict,\
        String2PythonComment, JoinPath, DeleteFileIfExisting, EnsureEmptyDir, \
        EvaluateNumerical, AddSpacesToCamelCase, NumToCSV, DynamicRound, OverallResults2LaTexTable,\
        MergeData, LogOverallCounter2File, CalcEvalMetricsCorrelationMatrix


from myLLM import MyLLM, llmModelsDict, GetLLMmodelNameFormShortName
from logger import Logger #, STYLE

from templatesAndLists import EvaluationType
import templatesAndLists as tmplts

#!!!!!!!!!!! needed to execute code:
from motionAnalysis import CheckLinearTrajectory, CheckPlanarTrajectory, CheckSphericalMotion, CheckCircularMotion 
from motionAnalysis import CheckMotionSpace, CheckVelocitySpace, CheckAccelerationSpace, CheckParabolicMotion
#!!!!!!!!!!!

#%%++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

#a fictive model which replaces LLM output for tests (runWithoutLLM=True):
minimalMBSmodel="""
import exudyn as exu
SC = exu.SystemContainer()
mbs = SC.AddSystem()
oMass = mbs.CreateMassPoint(referencePosition = [0,0,0],physicsMass = 10,gravity = [0,0,-10])
mbs.Assemble()
mbs.SolveDynamic()
"""

#%%++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++        

#%% 

# Tests Exudyn simulation code generation for multiple models, writes files into directories
# runWithoutLLM: if True, no results are produced, but just some default model is used
# useWrongModelsInConjectures: uses wrong models for given conjectures
# doSpaceVariation: if non-zero, it variates spaces, using increasing ID for variation; 
def RunMBSmodelTests(agent, numberOfRandomizations=0, includeConjectures=False,
                     runWithoutLLM=False, useWrongModelsInConjectures=False, 
                     numberOfConjecturesPerModel=3,
                     doSpaceVariation=0, storeGeneratedTextsAndResults=False):
    logger = agent.logger
    mbsModelLoader = agent.mbsModelLoader
    logDir = logger.logDir
    solutionDir = JoinPath(logDir, 'solution')
    os.makedirs(solutionDir, exist_ok=True)

    #additional directory for model comparison
    os.makedirs(logDir, exist_ok=True)
    mbsModelsLLMdir = JoinPath(logDir, 'mbsModelsLLM')
    mbsEvalModelsLLMdir = JoinPath(logDir, 'mbsEvalModelsLLM')

    EnsureEmptyDir(mbsModelsLLMdir) # creates empty Dir or deletes content if existend
    EnsureEmptyDir(mbsEvalModelsLLMdir) # creates empty Dir or deletes content if existend
    EnsureEmptyDir(solutionDir) # creates empty Dir or deletes content if existend

    randomizeParameters = (numberOfRandomizations>0) and not doSpaceVariation
    if includeConjectures and doSpaceVariation:
        raise ValueError('Space variation not possible together with conjectures!')

    mbsModelNamesLoaded = mbsModelLoader.ListOfModels()
    numberOfMBSmodelsLoaded = mbsModelLoader.NumberOfModels()
    numberOfModelCreationTasks = numberOfMBSmodelsLoaded*max(1,numberOfRandomizations) #including randomizations
    logger.LogText('RunMBSmodelTests: using LLM model: '+agent.llmModel.modelName, 
                   printToConsole=True, separator=True, quickinfo=True)
    logger.LogText('Creating simulation code for mbs models: '+ str(mbsModelNamesLoaded), 
                   printToConsole=True, separator=True, quickinfo=True)
    logger.LogText('RunMBSmodelTests: using Exudyn version: '+exu.GetVersionString(), 
                   printToConsole=True, separator=True, quickinfo=True)
    if doSpaceVariation:
        logger.LogText('Do space variation with factor: '+str(doSpaceVariation),
                       printToConsole=True, separator=True, quickinfo=True)
    if includeConjectures:
        logger.LogText('Including conjectures, nConj='+numberOfConjecturesPerModel+', wrong conjectures='+str(useWrongModelsInConjectures),
                       printToConsole=True, separator=True, quickinfo=True)


    DeleteFileIfExisting(logDir, "coordinatesSolution.txt") #this is unused, but could show up in case something goes wrong

    tStart = time.time()
    nExecutable = 0
    nExecutableEval = 0
    nExecutableSamples = 0 #just for debugging, if implemented models are not running
    nCompletedSamples = 0    #to see what is max nExecutableSamples
    differenceLLMlist = []
    executableLLMlist = []
    executableEvalLLMlist = []
    scoreConjLLMlist = []
    modelsWithIDlist = []
    resultsDict = {}
    
    storedDataPerModel = {}

    nTotalCnt = -1
    for mbsModelCnt, currentMBSmodelName in enumerate(mbsModelNamesLoaded):
        for randomID in range(max(1,numberOfRandomizations) ):

            nTotalCnt+=1
            randomIDstr = ''
            
            if numberOfRandomizations > 0:
                randomIDstr = str(randomID)

            currentMBSmodelNameID = currentMBSmodelName + randomIDstr            
            
            solutionNameLLM = JoinPath(solutionDir,currentMBSmodelNameID + 'LLM.txt')
            solutionNameSample = JoinPath(solutionDir,currentMBSmodelName + 'Sample.txt') #will change over time
            
            timeToGo = ''
            tElapsed = time.time() - tStart

            if tElapsed > 10 and nTotalCnt > 0:
                ttg = tElapsed/nTotalCnt * (numberOfModelCreationTasks - nTotalCnt)
                if ttg < 3600: timeToGo = '; time to go='+str(round(ttg,2))+'s'
                else: timeToGo = '; time to go='+str(round(ttg/3600,2))+'hours'

            
            print('=======================')
            logger.LogText(f'Creating simulation code for {currentMBSmodelName};'+
                           (f' random ID{randomID} / {numberOfRandomizations};')*randomizeParameters+
                           (f' spaceVar ID{randomID} / {numberOfRandomizations};')*(doSpaceVariation>0)+
                           f' model ID{mbsModelCnt} / {numberOfMBSmodelsLoaded}'+timeToGo,
                           separator=True, printToConsole=True, quickinfo=True)
            
            spaceVariationID=randomID*doSpaceVariation

            storedModelData = {}
            storedModelData['currentMBSmodelName'] = currentMBSmodelName
            storedModelData['currentMBSmodelNameID'] = currentMBSmodelNameID
            storedModelData['randomID'] = randomID
            storedModelData['spaceVariationID'] = spaceVariationID
            storedModelData['solutionNameLLM'] = solutionNameLLM
            
            #get parameterized model description
            [mbsModelDescription, modelData, 
             chosenParameters] = mbsModelLoader.GetModelDescriptionAndDict(currentMBSmodelName, 
                                                                           randomizeParameters=randomizeParameters,
                                                                           spaceVariationID=spaceVariationID)
            
            exudynCodeClean = ''
            logger = agent.logger
            executableLLM = False
            executableEvalLLM = False
            executableSample = False
            differenceLLM = -3 #-3==exception, -2==solution file invalid; -1==invalid format; >= 0: difference
            sampleFileDict = {}
            solverCode = None
            scoreValueConj = -10    # -7..errorConvertResults, -6..no output, -5..errorConvertSensors, -4..implementation missing,
                                    # -3..invalid score, -2..score conversion error, -1..score range error
            evaluationTextEval = ''
            
            if not includeConjectures:
                #%%
                try:
                    if not runWithoutLLM:
                        exudynCode = agent.CreateExudynItemsAndModel(mbsModelDescription, agent.maxTokensChooseItems, agent.maxTokensGenerateModel)
                    else:
                        exudynCode = minimalMBSmodel
                    
                    logger.LogDebug("\n===========================\nLLM-created Exudyn code:\n" + exudynCodeClean, printToConsole=False)
                    
                    sampleFileDict = agent.GetSampleFileDict(filePath="sampleFiles", 
                                                       fileName=modelData["sampleFileName"], 
                                                       sampleDict=modelData, 
                                                       chosenParametersDict=chosenParameters) 
                    solverCode = sampleFileDict["solverCode"]
        
                    sampleCode = sampleFileDict['executableCode']
                    storedModelData['sampleCode'] = sampleFileDict['executableCodeShort']
                    
                    #replace solver part in LLM-generated model:
                    exudynCodeClean = exudynCode.split('\nmbs.Assemble()')[0]+'\n'
                    exudynCodeClean += solverCode
                    
                    mbsModelDescriptionPython = '# ** given model description: **\n'
                    mbsModelDescriptionPython += String2PythonComment(mbsModelDescription)
                    
                    WriteFile(currentMBSmodelName+randomIDstr+'.py', 
                              mbsModelDescriptionPython+exudynCodeClean, #add description to simplify manual error checking
                              path=mbsModelsLLMdir, flush=True)
        
                    storedModelData['exudynCodeClean'] = exudynCodeClean
                    
                    [executableSample, localVariablesSample, solverSuccessSample] = agent.EvaluateMBScode(
                                                                                    sampleCode, 
                                                                                    currentMBSmodelNameID,
                                                                                    solutionFileName=solutionNameSample, 
                                                                                    mode='Sample file based')
                    [executableLLM, localVariablesLLM, solverSuccessLLM] = agent.EvaluateMBScode(
                                                                           exudynCodeClean,
                                                                           currentMBSmodelNameID,
                                                                           solutionFileName=solutionNameLLM, 
                                                                           mode='LLM generated')
                    nCompletedSamples += 1
                    
                    
                    # check if simulation worked - not necessary if the two following succeds
                    if (executableSample and executableLLM and solverSuccessSample and solverSuccessLLM):
                        # simulation worked, compare with reference coordinatesSolution.txt
        
                        differenceLLM = EvaluateNumerical(fileNameReference=solutionNameSample,
                                                fileNameEvaluate=solutionNameLLM,
                                                localVariablesReference=localVariablesSample,
                                                localVariablesEvaluate=localVariablesLLM,
                                                logger=logger)

                    storedModelData['executableLLM'] = executableLLM
                    storedModelData['differenceLLM'] = differenceLLM

                except KeyboardInterrupt:
                    print("Keyboard interrupt requested...exiting")
                    raise
                except:
                    exceptionText = traceback.format_exc()
                    logger.LogError(f'Exudyn model "{currentMBSmodelNameID}", model {mbsModelCnt}/{numberOfMBSmodelsLoaded} failed: {exceptionText}')
                        
            else:
                #%% test evaluation pipeline
                try:
                    conjectureMbsModelDescription = mbsModelDescription
                    #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
                    #use wrong models to check reliability
                    if useWrongModelsInConjectures:
                        foundOtherModel = False
                        otherModelCnt = 0 #default, not used!
                        otherMBSmodelName = mbsModelNamesLoaded[otherModelCnt] #default, not used!

                        for i in range(100): #this should be more than enough trials
                            otherModelCnt = np.random.randint(len(mbsModelNamesLoaded))
                            otherMBSmodelName = mbsModelNamesLoaded[otherModelCnt]
                            [conjectureMbsModelDescription, otherModelData, 
                                                     otherChosenParameters] = mbsModelLoader.GetModelDescriptionAndDict(otherMBSmodelName, 
                                                                                                                   randomizeParameters=randomizeParameters)

                            #a simpler approach, as other models would ususally behave more different
                            if otherModelCnt != mbsModelCnt:
                                foundOtherModel = True
                                break
                            #minimum requirement: this could be just 1 parameter changed!!! But this would be the more sophisticated approach
                            # if conjectureMbsModelDescription != mbsModelDescription:
                            #     foundOtherModel = True
                            #     break

                        if not foundOtherModel:
                            logger.LogError('\n************************\nDid not find wrong model for conjecture!\n************************\n')

                    
                    #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
                    #prompt model and choose evaluation from evaluation list
                    evalList = agent.GenerateEvaluationMethodsList(
                                                             mbsModelDescription=mbsModelDescription, 
                                                             nEvalMethods=numberOfConjecturesPerModel,
                                                             max_tokens=agent.maxTokensGenerateEvalMethods)
                    conjecture=None
                    sensorText=None
                    requiredSensors = None
                    if evalList is not None and type(evalList) == list:
                        ###propose conjecture for model, based on evaluation method
                        chosenEvalIndex = np.random.randint(min(numberOfConjecturesPerModel,len(evalList)))
                        evaluationMethod = evalList[chosenEvalIndex]
                        if evaluationMethod not in tmplts.dictOfEvaluationMethods:
                            logger.LogError('found invalid evaluation method:'+evaluationMethod)
                        else:
                            evalMethodDict = tmplts.dictOfEvaluationMethods[evaluationMethod] #was already checked that all items in evalList are VALID!
                            evalType = evalMethodDict['type']
                            requiredSensors = EvaluationType.RequiredSensors(evalType)
                            # evalFunction = evalMethodDict['evaluationFunction']
    
                            if useWrongModelsInConjectures:
                                logger.LogDebug('Create wrong conjecture with wrong sensor text')

                            [conjecture, sensorText, errorMsg] = agent.GenerateConjecture( 
                                                                           mbsModelDescription=conjectureMbsModelDescription, 
                                                                           evaluationMethod = evaluationMethod,
                                                                           max_tokens=agent.maxTokensGenerateConjecture)
                            if useWrongModelsInConjectures:
                                #originalConjecture unused, but sensorText must fit mbsModelDescription
                                logger.LogDebug('Create original conjecture with appropriate sensor text')
                                [originalConjecture, sensorText, errorMsg] = agent.GenerateConjecture(
                                                                               mbsModelDescription=mbsModelDescription, 
                                                                               evaluationMethod = evaluationMethod,
                                                                               max_tokens=agent.maxTokensGenerateConjecture)

                    #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
                    #if conjecture exists, continue
                    if conjecture is not None and (sensorText is not None or (requiredSensors==0) ):
                        if False: #this is anyway logged in GenerateConjecture
                            logger.LogText('evaluationMethod: '+str(evaluationMethod)+
                                           '\nconjecture: '+str(conjecture)+
                                           '\nsensorText: '+str(sensorText),printToConsole=True)
    
                        evaluationDescription = agent.GetEvaluationMethodDescription(evaluationMethod, sensorText)

                        evaluationDescription = 'Use the evaluation method "'+evaluationMethod+'", which states: '+evalMethodDict['description']+'\n'
                        #extend standard Exudyn model creation prompt
                        if requiredSensors!=0:
                            evaluationDescription += 'A sensor shall be added and stored as sensorNumber - it will be evaluated by the user later on. Set the flag "storeInternal=True", and use the following information:\n'+sensorText.strip()
                        # else:
                        #     evaluationDescription += '\n'+sensorText.strip()

                        #specific code-generation-specific information
                        if evalMethodDict['evaluationCodeHints'] != '':
                            evaluationDescription += '\n\n'+evalMethodDict['evaluationCodeHints']
                        
                        #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
                        #create Exudyn model
                        exudynCode = agent.CreateExudynWithEvalItemsAndModel(
                                                                       mbsModelDescription=mbsModelDescription,
                                                                       evaluationDescription=evaluationDescription,
                                                                       evalMethodDict=evalMethodDict, 
                                                                       maxTokensChooseItems=agent.maxTokensChooseItems, 
                                                                       maxTokensGenerateModel=agent.maxTokensGenerateModel)
                       
                        #++++++++++++++++++++++++++++++++++++
                        #%% verify main part of model (check correctness)
                        
                        sampleFileDict = agent.GetSampleFileDict(filePath="sampleFiles", 
                                                           fileName=modelData["sampleFileName"], 
                                                           sampleDict=modelData, 
                                                           chosenParametersDict=chosenParameters) 
                        solverCode = sampleFileDict["solverCode"]
            
                        sampleCode = sampleFileDict['executableCode']

                        exudynCodeClean = exudynCode.split('\nmbs.Assemble()')[0] + '\n' 
                        exudynCodeClean += solverCode
                        
                        mbsModelDescriptionPython = '# ** given model description: **\n'
                        mbsModelDescriptionPython += String2PythonComment(mbsModelDescription)
                        
                        WriteFile(currentMBSmodelName+randomIDstr+'.py', 
                                  mbsModelDescriptionPython+exudynCodeClean, #add description to simplify manual error checking
                                  path=mbsModelsLLMdir, flush=True)
                        WriteFile(currentMBSmodelName+randomIDstr+'.py', 
                                  mbsModelDescriptionPython+exudynCode, #add description to simplify manual error checking
                                  path=mbsEvalModelsLLMdir, flush=True)

                        #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
                        #Evaluate code if possible
                        if 'mbs.Assemble()' not in exudynCode:
                            logger.LogError('Check Exudyn code: no mbs.Assemble() found in code!')
                        else:
                
                            
                            [executableSample, localVariablesSample, solverSuccessSample] = agent.EvaluateMBScode(
                                                                                            sampleCode, 
                                                                                            currentMBSmodelNameID,
                                                                                            solutionFileName=solutionNameSample, 
                                                                                            mode='Sample file based')
                            [executableLLM, localVariablesLLM, solverSuccessLLM] = agent.EvaluateMBScode(
                                                                                   exudynCodeClean,
                                                                                   currentMBSmodelNameID,
                                                                                   solutionFileName=solutionNameLLM, 
                                                                                   mode='LLM generated')
                            nCompletedSamples += 1
                          
                            # check if simulation worked - not necessary if the two following succeds
                            if (executableSample and executableLLM and solverSuccessSample and solverSuccessLLM):
                                # simulation worked, compare with reference coordinatesSolution.txt
                
                                differenceLLM = EvaluateNumerical(fileNameReference=solutionNameSample,
                                                        fileNameEvaluate=solutionNameLLM,
                                                        logger=logger)
                            
                            #++++++++++++++++++++++++++++++++++++++++++++++
                            #%% now evaluate full model with evaluation
                            #run full code
                            
                            [executableEvalLLM, localVariablesEvalLLM, solverSuccessEvalLLM] = agent.EvaluateMBScode(
                                                                                   exudynCode, 
                                                                                   currentMBSmodelNameID,
                                                                                   solutionFileName=solutionNameLLM, 
                                                                                   mode='LLM generated',
                                                                                   isAnalysis = EvaluationType.IsAnalysisType(evalType),
                                                                                   )
                            if executableEvalLLM and solverSuccessEvalLLM:
                                [scoreValue, simulationResults] = agent.SimulationResultsToText(evalMethodDict, localVariablesEvalLLM)
                                if scoreValue == 0: 
                                    [scoreValueConj, evaluationTextEval, conjPrompt] = agent.EvaluateConjecture(
                                                                                  mbsModelDescription, 
                                                                                  evalMethodDict, 
                                                                                  conjecture, 
                                                                                  simulationResults,
                                                                                  False,
                                                                                  agent.maxTokensEvaluateConjecture)
                                else:
                                    scoreValueConj = scoreValue
                                    evaluationTextEval = ''
                                    
                            else:
                                logger.LogDebug('Skipping EvaluateConjecture because there was no successful simulation!')
                    
                except KeyboardInterrupt:
                    print("Keyboard interrupt requested...exiting")
                    raise
                except:
                    exceptionText = traceback.format_exc()
                    logger.LogError(f'Exudyn model "{currentMBSmodelNameID}", model {mbsModelCnt}/{numberOfMBSmodelsLoaded} failed: {exceptionText}')

            #%%
            storedDataPerModel[currentMBSmodelNameID] = storedModelData
                            
            nExecutableSamples  += int(executableSample)
            nExecutable += int(executableLLM)
            nExecutableEval += int(executableEvalLLM)
            differenceLLMlist.append(differenceLLM)
            executableLLMlist.append(executableLLM)
            executableEvalLLMlist.append(executableEvalLLM)
            scoreConjLLMlist.append(scoreValueConj)
            modelsWithIDlist.append([currentMBSmodelName,randomID])
                
            resultsDict[currentMBSmodelNameID] =  {
                'executable':executableLLM,
                'diff':differenceLLM,
                }
            if includeConjectures:
                resultsDict[currentMBSmodelNameID]['executableEval'] = executableEvalLLM
                resultsDict[currentMBSmodelNameID]['scoreValueConj'] = scoreValueConj
            
            #print('  ==> diff=',differenceLLM)
            logger.LogText(' - executable='+ str(executableLLM)+
                           ', diff='+ str(DynamicRound(differenceLLM,6))+ 
                           (', execEval='+ str(executableEvalLLM)+
                            ', scoreConj='+ str(scoreValueConj))*includeConjectures, 
                           printToConsole=True, separator=True, quickinfo=True)
        
    totalRunTime = time.time()-tStart
    print('\n==========================')
    logger.LogText('nExecutable = '+str(nExecutable) + ' of ' + str(numberOfModelCreationTasks) + '\n'
                   #+ 'difference = '+str(list(np.round(differenceLLMlist,3)) )
                   , printToConsole=True, separator=True)
    
    if nExecutableSamples != nCompletedSamples:
        logger.LogError('Only '+str(nExecutableSamples)+' samples out of '
                        +str(nCompletedSamples)+' evaluated samples worked! CHECK implementation!')
    
    print('\n==========================')
    logger.LogDict(resultsDict, header='FINAL TEST RESULTS', quickinfo=True)
    
    llmModelName = agent.llmModel.modelName
    #llmShortName = llmModelsDict[llmModelName]['shortName']
    #create dict to return (and store as json file)
    rr = {
         #general info:
         'llmModelName':llmModelName,  #full name
         'exudynVersion':exu.GetVersionString(),
         'mbsModelNamesLoaded':mbsModelNamesLoaded, 
         'runTime':totalRunTime, 
         'useWrongModelsInConjectures':useWrongModelsInConjectures,
         'doSpaceVariation':doSpaceVariation,
         'numberOfConjecturesPerModel':numberOfConjecturesPerModel,
         # 'solutionNameLLMbase':solutionNameLLMbase, #unused DELETE
         # 'solutionNameSamplebase':solutionNameSamplebase, #DELETE
         'numberOfRandomizations':numberOfRandomizations,
         'diffSolutionTolerance':agent.diffSolutionTolerance,
         'maxDifficultyLevel': agent.mbsModelLoader.maxDifficultyLevel,
         #specific results:
         'executableLLMlist':executableLLMlist, 
         'differenceLLMlist':differenceLLMlist,
         'executableEvalLLMlist':executableEvalLLMlist, 
         'scoreConjLLMlist':scoreConjLLMlist, 
         'modelsWithIDlist':modelsWithIDlist,
         'numberOfMBSmodelsLoaded':numberOfMBSmodelsLoaded,
         'numberOfModelCreationTasks':numberOfModelCreationTasks,#all model creation tasks
         'nExecutableLLMs':nExecutable,
         'nExecutableEvalLLMs':nExecutable,
         'nExecutableSamples':nExecutableSamples,
         'numberOfRemovedTokensGlobal':agent.llmModel.numberOfRemovedTokensGlobal,
         'numberOfTokensGlobal':agent.llmModel.numberOfTokensGlobal,
         'mbsModelsLLMdir':mbsModelsLLMdir,
         'logDir':logDir,
         'solutionDir':solutionDir,
         }

    rr['llmConfig'] = GetScalarClassObjectsDict(agent.llmModel)
    rr['agentConfig'] = GetScalarClassObjectsDict(agent)

    if storeGeneratedTextsAndResults:
        rr['storedDataPerModel'] = storedDataPerModel
    
    #%%+++++++++++++++++++++++++++++++++++++
    #now print and log final results
    nCorrect = 0
    nConjectureCorrect = 0
    nConjectureWrong = 0
    nExecutable = 0
    nExecutableEval = 0
    nScoreConjecture = 0
    sumScoreConjecture = 0
    sumScoreConjectureCorrect = 0
    sumScoreConjectureWrong = 0
    numberOfRandomizations = rr['numberOfRandomizations']
    modelsSuccess = {} #summary per model
    modelsEval = {}

    for i, name in enumerate(mbsModelNamesLoaded):
        modelsSuccess[name] = {'exec':0,'correct':0,'execEval':0,'scoreConj':0,'successConj':0,
                               'scoreConjCorrect':0, #score conjecture if model=correct
                               'scoreConjWrong':0,   #score conjecture if model=wrong
                               }
        modelsEval[name] = {}
    
    for i, [name, ID] in enumerate(rr['modelsWithIDlist']):
        # if name not in modelsSuccess:
        #     modelsSuccess[name] = [0,0] #nExecutable, nCorrect
        if ID == 0:
            nModelCorrect = 0
            nModelWrong = 0

        isCorrect = False
        if rr['differenceLLMlist'][i] >= 0 and rr['differenceLLMlist'][i] < agent.diffSolutionTolerance:
            nCorrect += 1
            modelsSuccess[name]['correct'] += 1
            isCorrect = True
        if rr['executableLLMlist'][i]:
            nExecutable += 1
            modelsSuccess[name]['exec'] += 1
        if rr['executableEvalLLMlist'][i]:
            nExecutableEval += 1
            modelsSuccess[name]['execEval'] += 1
        if rr['scoreConjLLMlist'][i] >= 0: #so, it did not fail
            nScoreConjecture += 1
            scoreConj = rr['scoreConjLLMlist'][i]
            sumScoreConjecture += scoreConj
            modelsSuccess[name]['scoreConj'] += scoreConj
            modelsSuccess[name]['successConj'] += 1
            
            modelsSuccess[name]['scoreConjCorrect'] += isCorrect * scoreConj
            modelsSuccess[name]['scoreConjWrong'] += (1-isCorrect) * scoreConj

            nModelCorrect += isCorrect
            nModelWrong += (1-isCorrect)

            sumScoreConjectureCorrect += isCorrect * scoreConj
            sumScoreConjectureWrong += (1-isCorrect) * scoreConj
            nConjectureCorrect += isCorrect
            nConjectureWrong += (1-isCorrect)
            
        s = (' - model '+name+str(ID)+':'
             ' exec='+str(int(rr['executableLLMlist'][i]))+
             ',diff='+str(DynamicRound(rr['differenceLLMlist'][i],6))+
             (',execEval='+str(round(rr['executableEvalLLMlist'][i],3))+
              ',scoreConj='+str(rr['scoreConjLLMlist'][i])
              )*includeConjectures
             )
        print(s)
        logger.LogText(s+'\n', quickinfo=True, timestamp=False)

        if numberOfRandomizations >= 1 and ID==numberOfRandomizations-1:
            scoreExecutable = round(modelsSuccess[name]['exec']/numberOfRandomizations,4)
            scoreCorrect = round(modelsSuccess[name]['correct']/numberOfRandomizations,4)
            scoreExecutableEval = round(modelsSuccess[name]['execEval']/numberOfRandomizations,4)
            nConj = max(1,modelsSuccess[name]['successConj']) #in case of 0, score is anyway zero
            scoreConjecture = round(modelsSuccess[name]['scoreConj']/nConj,4)
            
            scoreConjCorrect = round(modelsSuccess[name]['scoreConjCorrect']/(max(1,nModelCorrect)),4)
            scoreConjWrong = round(modelsSuccess[name]['scoreConjWrong']/(max(1,nModelWrong)),4)
            
            modelsEval[name]['scoreExecutable'] = scoreExecutable
            modelsEval[name]['scoreCorrect'] = scoreCorrect
            modelsEval[name]['scoreExecutableEval'] = scoreExecutableEval
            modelsEval[name]['scoreConjecture'] = scoreConjecture

            modelsEval[name]['scoreConjCorrect'] = scoreConjCorrect
            modelsEval[name]['scoreConjWrong'] = scoreConjWrong
            
            s = ('\nSUMMARY model '+name+
                  ': exec='+str(scoreExecutable*100)+'%'+
                  ', correct='+str(scoreCorrect*100)+'%' ) 
            if includeConjectures:
                s+=', execEval='+str(scoreExecutableEval*100)+'%'
                s+=', scoreConj='+str(scoreConjecture*100)+'%'
                s+=', scoreConjCorrect='+str(scoreConjCorrect*100)+'%'
                s+=', scoreConjWrong='+str(scoreConjWrong*100)+'%'
            print(s)
            logger.LogText(s+'\n', quickinfo=True)

    rr['modelsEval'] = modelsEval
    rr['nExecutable'] = nExecutable
    rr['nCorrect'] = nCorrect
    rr['nScoreConjecture'] = nScoreConjecture
    rr['nConjectureCorrect'] = nConjectureCorrect
    rr['nConjectureWrong'] = nConjectureWrong

    rr['totalScoreExecutable'] = round(nExecutable/rr['numberOfModelCreationTasks'],4)
    rr['totalScoreCorrect'] = round(nCorrect/rr['numberOfModelCreationTasks'],4)
    rr['totalScoreExecutableEval'] = round(nExecutableEval/rr['numberOfModelCreationTasks'],4)
    rr['totalScoreConjecture'] = round(sumScoreConjecture/rr['numberOfModelCreationTasks'],4)
    
    rr['totalScoreConjectureCorrect'] = round(sumScoreConjectureCorrect/max(1,nConjectureCorrect),4)
    rr['totalScoreConjectureWrong'] = round(sumScoreConjectureWrong/max(1,nConjectureWrong),4)


    rr['executionDateStr'] = datetime.date.today().strftime("%Y-%m-%d")
    rr['executionTimeStr'] = datetime.datetime.now().strftime("%H:%M:%S")

    print('\n==========================')
    logger.LogText("Overall evaluation duration: " + str(round(totalRunTime, 3)), 
                   printToConsole=True, separator=True)

    logger.LogText('numberOfTokensGlobal:'+str(agent.llmModel.numberOfTokensGlobal) +', '+
                   'numberOfRemovedTokensGlobal:'+str(agent.llmModel.numberOfRemovedTokensGlobal) + ', ' +
                   'tokensPerSecondGlobal:'+str(agent.llmModel.tokensPerSecondGlobal)+'\n',
                    printToConsole=True,separator=True,quickinfo=True)


    s = ('\nexecutable      = '+str(rr['totalScoreExecutable']*100)+'%' + 
         '\ncorrect         = '+str(rr['totalScoreCorrect']*100)+'%' +
         ('\nnexecutableEval = '+str(rr['totalScoreExecutableEval']*100)+'%'
          + '\ntotalScoreConj = '+str(rr['totalScoreConjecture']*100)+'%'
          + '\ntotalScoreConjectureCorrect = '+str(rr['totalScoreConjectureCorrect']*100)+'%'
          + '\ntotalScoreConjectureWrong = '+str(rr['totalScoreConjectureWrong']*100)+'%'
          )*includeConjectures
         )

    logger.LogText(s, quickinfo=True, separator=True, printToConsole=True)

    return rr

#%%+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
#merge tests from directory; use all subdirs starting with "log_"
#in each subdir, "results.json" is evaluated
#write output to resultsFileName
def MergeTestModelResults(dirTestModels, resultsFileName="overallResults.csv", 
                          includeConjectures=False, writeLatexResults=False):
    #%%++++++++++++++++++++++++++++
    from utilities import ReadJSONToDict
    import os
    
    doEval = includeConjectures

    print('Merge results.json from directory "'+dirTestModels+'"'+'; using evaluation tests'*doEval)
    log_dirs = [d for d in os.listdir(dirTestModels) if d.startswith("log_") and os.path.isdir(JoinPath(dirTestModels, d))]
    
    # Read 'results.json' from each valid subdirectory
    resultsData = {}
    
    for log_dir in log_dirs:
        shortName = log_dir[4:]
        json_path = JoinPath(dirTestModels, log_dir, "results.json")
        
        if os.path.exists(json_path):  # Check if 'results.json' exists
            resultsData[shortName] = ReadJSONToDict(json_path)  # Read JSON data into dict
        else:
            print(f"Warning: 'results.json' not found in {log_dir}")
            
    
    if resultsData == {}:
        print("No valid data found -> check directory / results.json must be available in log_* dirs")
        sys.exit()
    else:
        #%%++++++++++++++++++++++++++++
        #now export into an Excel file:
        import csv
        
        firstData = list(resultsData.keys())[0]
        mbsModelsList = resultsData[firstData]['mbsModelNamesLoaded']
        maxDifficultyLevel = resultsData[firstData]['maxDifficultyLevel']
        useWrongModelsInConjectures = False
        if 'useWrongModelsInConjectures' in resultsData[firstData]:
            useWrongModelsInConjectures = resultsData[firstData]['useWrongModelsInConjectures']
        
        for i in range(len(mbsModelsList)):
            mbsModelsList[i] = AddSpacesToCamelCase(mbsModelsList[i])
            
        nMBSmodels = len(mbsModelsList)
            
        from time import gmtime, strftime
        strftime("%Y-%m-%d", gmtime())
        
        dateStr = datetime.date.today().strftime("%Y-%m-%d")
        timeStr = datetime.datetime.now().strftime("%H:%M:%S")
        header = ['EVALUATION report', dateStr, timeStr]
        columnNamesC = ['model name', 'date', 'time', 
                        'pipeline', # gpt4all or huggingface
                        '#Params (B)', 'VRAM (GB)', 'Quant.', 'runtime (min)', 
                        'maxCtx (k)', #max context size of model
                        'nTokGen (k)', 'tokens per second', 'nTokRem (k)', #number of total generated tokens, number of removed tokens
                        'MATH', 'IFEval', 'MMLU-Pro','GPQA'] 

        #E..Executable, C..Correct, EE..Executable Eval
        columnNamesE = list(columnNamesC)
        columnNamesEE = list(columnNamesC)
        columnNamesCJ = list(columnNamesC)
        columnNamesCJ_C = list(columnNamesC)
        columnNamesCJ_W = list(columnNamesC)
        columnNamesC += ['correct all models']+ mbsModelsList
        columnNamesE += ['executable all models']+ mbsModelsList
        columnNamesEE += ['exec eval all models']+ mbsModelsList
        columnNamesCJ += ['conjecture all models']+ mbsModelsList
        columnNamesCJ_C += ['conjecture correct model']+ mbsModelsList
        columnNamesCJ_W += ['conjecture wrong model']+ mbsModelsList

        nRound = 3

        headerC = [header, 
                 ['Number of models:',nMBSmodels],
                 ['Max difficulty level:',maxDifficultyLevel],
                 ['Correct score:']]
        dataC = [columnNamesC]
        headerE = [[''],['Executable score:']]
        dataE = [columnNamesE]
        dataEE = [[''],['Exec eval score:'], columnNamesEE]
        dataCJ = [[''],['Conjecture score:'], columnNamesCJ]
        dataCJ_C = [[''],['Conjecture correct models score:'], columnNamesCJ_C]
        dataCJ_W = [[''],['Conjecture wrong models score:'], columnNamesCJ_W]
        
        addConjectures_CW = False

        for key, value in resultsData.items():
            try:
                llmFullName = GetLLMmodelNameFormShortName(key)
                llmData = llmModelsDict[llmFullName]
                #not available in old files:
                numberOfTokensGlobal = 0 if 'numberOfTokensGlobal' not in value else value['numberOfTokensGlobal']
                numberOfRemovedTokensGlobal = 0 if 'numberOfRemovedTokensGlobal' not in value else value['numberOfRemovedTokensGlobal']
                llmDataDate = '' if 'executionDateStr' not in value else value['executionDateStr']
                llmDataTime = '' if 'executionTimeStr' not in value else value['executionTimeStr']
                keyValues = [key, 
                        llmDataDate,llmDataTime,
                        llmData['type'], # pipeline (gpt4all, HF)
                        NumToCSV(llmData['nParam']),NumToCSV(llmData['VRAM'],1), NumToCSV(llmData['Q']),
                        NumToCSV(value['runTime']/60,2),
                        NumToCSV(llmData['ctxSize']),
                        int(numberOfTokensGlobal/1024),
                        NumToCSV(numberOfTokensGlobal/max(0.01,value['runTime']),2),
                        int(numberOfRemovedTokensGlobal/1024),
                        NumToCSV(llmData['MATH']/100.,2), 
                        NumToCSV(llmData['IFEval']/100.,2), 
                        NumToCSV(llmData['MMLU-Pro']/100.,2),
                        NumToCSV(llmData['GPQA']/100.,2),
                        ]
                rowC = keyValues + [NumToCSV(value['totalScoreCorrect'],nRound)]
                rowE = keyValues + [NumToCSV(value['totalScoreExecutable'],nRound)]
                if doEval:
                    rowEE = keyValues + [NumToCSV(value['totalScoreExecutableEval'],nRound)]
                    rowCJ = keyValues + [NumToCSV(value['totalScoreConjecture'],nRound)]
                    totalScoreConjectureCorrect = 0
                    totalScoreConjectureWrong = 0
                    if 'totalScoreConjectureCorrect' in value:
                        totalScoreConjectureCorrect = value['totalScoreConjectureCorrect']
                        totalScoreConjectureWrong = value['totalScoreConjectureWrong']
                        
                    rowCJ_C = keyValues + [NumToCSV(totalScoreConjectureCorrect,nRound)]
                    rowCJ_W = keyValues + [NumToCSV(totalScoreConjectureWrong,nRound)]
                for key1, value1 in value['modelsEval'].items():
                    rowC.append(NumToCSV(value1['scoreCorrect'],nRound))
                    rowE.append(NumToCSV(value1['scoreExecutable'],nRound))
                    if doEval:
                        rowEE.append(NumToCSV(value1['scoreExecutableEval'],nRound))
                        rowCJ.append(NumToCSV(value1['scoreConjecture'],nRound))
                        if 'scoreConjCorrect' in value1:
                            addConjectures_CW = True
                            rowCJ_C.append(NumToCSV(value1['scoreConjCorrect'],nRound))
                            rowCJ_W.append(NumToCSV(value1['scoreConjWrong'],nRound))
    
                dataC.append(rowC)
                dataE.append(rowE)
                if doEval:
                    dataEE.append(rowEE)
                    dataCJ.append(rowCJ)
                    if addConjectures_CW:
                        dataCJ_C.append(rowCJ_C)
                        dataCJ_W.append(rowCJ_W)
                        
                    
            except KeyboardInterrupt:
                raise
            except:
                exceptionText = traceback.format_exc()
                print('ERROR in Merge: could not process data from llm '+key+'\ntraceback=',exceptionText)
        
        # Define the CSV file name
        csv_filename = JoinPath(dirTestModels, resultsFileName)
        if useWrongModelsInConjectures:
            csv_filename = csv_filename.replace('.csv','_WC.csv')

        # print('addConjectures_CW:',addConjectures_CW)
        # Write data to CSV file
        with open(csv_filename, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file,delimiter=";")
            writer.writerows(headerC+dataC+
                             headerE+dataE
                             +(dataEE+dataCJ)*doEval
                             +(dataCJ_C+dataCJ_W)*addConjectures_CW
                             )  # Writes all rows from the list
        
        #process latex output
        if writeLatexResults:
            # overall-results (paper-visualization) of overallResults
            mergedData = MergeData(tables=[dataC]+[dataE], keyColumn='model name') # unique merge of table columns per LLM model name
            
            # define what colums to include in LaTeX-table via header strings (e.g. correct all models, executable all models)
            desiredColumnsResults = ['model name', 
                              '#Params (B)', 
                              'Quant.', 
                              'runtime (min)',
                              'tokens per second',
                              'VRAM (GB)',
                              'pipeline',
                              'correct all models',
                              'executable all models',
                              ]
        
            latexFilePath = '../../01_paper/overallResults.tex'
            OverallResults2LaTexTable(tableRows=mergedData, desiredColumns=desiredColumnsResults, 
                                      latexFilePath=latexFilePath)
            
            # compute correlation matrix for eval metrics
            figFilePath = '../../01_paper/figures/MetricsCorrelation.pdf'
            desiredColumnsCorrelation = ['MATH',
                                         'IFEval',
                                         'MMLU-Pro',
                                         'GPQA',
                                         'correct all models',
                                         'executable all models',
                                         ]
            
            CalcEvalMetricsCorrelationMatrix(tableRows=mergedData, desiredColumns=desiredColumnsCorrelation, filePath=figFilePath)
        

#testing
if __name__ == '__main__':
    
    # simple model generation test

    # llmModelName ='Meta-Llama-3-8B-Instruct.Q4_0.gguf'     #param model: result=12/20
    # llmModelName ='qwen2.5-coder-32b-instruct-q5_0.gguf'
    llmModelName ='phi-4-Q4_0.gguf'
    # llmModelName ='DeepSeek-Coder-V2-Lite-Instruct-Q6_K.gguf'


    if True:
        #%%+++++++++++++++++++++++++++++++++++++++++
        # logDir='johLogTestModels/Llama8B'
        # logDir='johLogTestModels/Qwen'
        # logDir='johLogTestModels/Phi4'
        logDir='logsTM/Test'

        # mbsModelNames = ['freeFallMassPoint', 'flyingMassPoint']
        # mbsModelNames = ['freeFallMassPoint']
        mbsModelNames = [
                         # 'freeFallMassPoint', 'flyingMassPoint',
                         # 'rigidRotorSimplySupported',
                         # 'rigidRotorUnbalanced',
                         'sliderCrankSimple',
                         # 'springCoupledFlyingRigidBodies', 
                         # 'sliderCrankRigidBodies'
                         ]
        maxDifficultyLevel=25
        device=None #'cpu'
        modelQuantization=None
    
        
        logger = Logger(logDir=logDir)
        logger.limitConsoleText = 5000
        llmModel = MyLLM(modelName=llmModelName, 
                         logger=logger, 
                         device=device, 
                         modelQuantization=modelQuantization)

        mbsModelLoader = ModelLoader()
        # only loading models with sample files (needed for comparison) and parameters - ATM
        mbsModelLoader.LoadStandardModelDescriptions(maxDifficultyLevel=maxDifficultyLevel, 
                                                     specificModels=mbsModelNames, 
                                                     onlyWithSampleFiles=True, 
                                                     onlyParameterizedModels=True)

        agent = LabAgent(llmModel=llmModel, 
                         logger=logger,
                         mbsModelLoader=mbsModelLoader,
                         agentOutputDataDir=logDir, 
                         maxDifficultyLevel=maxDifficultyLevel)
        #consider:
        agent.useExudynTimeout = False #in case that infinite loops are added or very small time steps
        agent.nResampleSize = 11
        agent.nDigitsEvaluate = 3 #convert all results to 3 digits (still using exp notation)
        doSpaceVariation = 0
        # Tests Exudyn simulation code generation for multiple models, writes files into directories
        rr = RunMBSmodelTests(agent, 
                             numberOfRandomizations=5,
                             doSpaceVariation=doSpaceVariation, #instead of model randomizations
                             includeConjectures=False,
                             storeGeneratedTextsAndResults=(doSpaceVariation!=0),
                             )

        LogOverallCounter2File(filePath='_globalTokenCount.txt', deltaCounter=llmModel.numberOfTokensGlobal)


        llmModel.FreeMemory()


