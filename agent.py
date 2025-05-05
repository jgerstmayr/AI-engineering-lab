# -*- coding: utf-8 -*-
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# This is part of the AI engineering lab project
#
# Filename: agent.py
#
# Details:  This is the main file (main class) for self-validation and export of results (MergeConjecturesResults); to run, use agentDriver.py with args from command line;
#           Main functions:
#           - GenerateModelsAndConjecturesLoop: create models and conjectures (with separate LLM)
#           - GenerateExudynModelsAndEval: create Exudyn models, execute and write evaluation results
#           - EvaluateAllConjectures: evaluate simulation results OR conjectures
#
# Authors:  Johannes Gerstmayr, Tobias Möltner
# Date:     2024-09-18 (last update 2025-04-29)
# Notes:    Ensure that the appropriate model files are available locally or through the Hugging Face model hub.
#
# License:  BSD-3 license
#
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


# from misc import GetLongestWords

from myLLM import MyLLM, llmModelsDict, GetLLMmodelNameFormShortName
from logger import Logger, STYLE

from readExudynHelper import ParseExudynHelper, GetRequiredTags, CreateSampleCode,\
    listSystemTags, listSimulationTags

from mbsModelLoader import ModelLoader 

from templatesAndLists import EvaluationType
import templatesAndLists as tmplts

from utilities import WriteDictToJSON, ReadJSONToDict, ExtractElementsInResponse, CheckLLMoutput,\
            PreProcessLLMcode, JoinPath, DeleteFileIfExisting, EnsureEmptyDir, SaveClassObjectConfig, \
            ExtractListFromStringAndTest, ExtractXMLtaggedString, ConvertResultsToPlainText,\
            ConvertSensors2Text, ExecuteCode, DynamicRound, \
            ReadFile, WriteFile, String2PythonComment, EvaluateNumerical,\
            AddSpacesToCamelCase, NumToCSV, RemoveTrailingDigits, GetScalarClassObjectsDict,\
            LogOverallCounter2File
            

#!!!!!!!!!!! needed to execute code:
from motionAnalysis import CheckLinearTrajectory, CheckPlanarTrajectory, CheckSphericalMotion, CheckCircularMotion 
from motionAnalysis import CheckMotionSpace, CheckVelocitySpace, CheckAccelerationSpace, CheckParabolicMotion
from utilities import GetSensorData
#!!!!!!!!!!!

import traceback
import time
import datetime
import copy
import os
import sys
import multiprocessing
#++++++++++++++++++++++++
import exudyn as exu

#++++++++++++++++++++++++
#ensure that these libs are available in global scope for exec() user functions ...
import numpy as np
import math
#++++++++++++++++++++++++

import numpy.random as random
random.seed(42)
import ast

#class to represent agent
#initialize agent with verbose and debug flags to activate console output
#logDir is used to set subdirectory for logging output
class LabAgent:
    def __init__(self, llmModel, logger, mbsModelLoader, agentOutputDataDir='agentOutputData/', 
                 maxDifficultyLevel=10000):
        """
        Initialize the agent
        """
        self.llmModel = llmModel
        self.logger = logger
        self.mbsModelLoader = mbsModelLoader
        
        self.llmGenerateDefaultArgs = {}
        # exclude user input in llm-output and cleanup. show number of generated tokens and tokens per second
        self.llmGenerateDefaultArgs['returnFullText'] = False
        self.llmGenerateDefaultArgs['cleanUpTokenizationSpaces'] = True
        self.llmGenerateDefaultArgs['showTiming'] = False
        self.llmGenerateDefaultArgs['showTokensPerSecond'] = False
        self.llmGenerateDefaultArgs['doSample'] = False
        self.llmGenerateDefaultArgs['numBeams'] = 1

        #+++++++++++++++++++++++++++++++++++++++++++++++++++++++
        
        self.logger.LogDebug('Initialize Agent ...')
        import platform
        import sys
        pythonVersion = str(sys.version_info.major)+'.'+str(sys.version_info.minor)+'.'+str(sys.version_info.micro)
        
        self.logger.LogText('architecture        = '+platform.architecture()[0], separator=True, timestamp=False)
        self.logger.LogText('processor           = '+platform.processor(), timestamp=False)
        self.logger.LogText('platform            = '+sys.platform, timestamp=False)
        self.logger.LogText('Python version      = '+pythonVersion, timestamp=False)
        self.logger.LogText('NumPy version       = '+np.__version__, timestamp=False)

        #+++++++++++++++++++++++++++++++++++++++++++++++++++++++

        #model test+conjectures:
        self.maxTokensChooseItems = 512 
        self.maxTokensGenerateModel = 1024*3 #1024*4 causes lot of swapping
        #conjectures:
        self.maxTokensGenerateEvalMethods = 1024 #original: 1024*2
        self.maxTokensGenerateConjecture = 768 #original: 1024*2
        self.maxTokensEvaluateConjecture = 2048 #base: 1024; 1024*2 causes a lot of causes lot of swapping
        #+++++++++++++++++++++++++++++++++++++++++++++++++++++++

      
        self.nDigitsEvaluate = 4 #number of effective digits
        self.nResampleSize = 10+1 #number of rows in sensor data that are used
        self.diffSolutionTolerance = 1e-5 #for small numerical deviations due to object order!
        self.numberOfModelVariations = 1
        self.useAlternativeModel = False #set True to compute statistics with wrong/alternative models

        #+++++++++++++++++++++++++++++++++++++++++++++++++++++++
        self.useExudynTimeout = False
        # self.randomizeModelParameters = False
        
        # machine output files (JSON)
        if len(agentOutputDataDir) > 0 and agentOutputDataDir[-1] != '/':
            agentOutputDataDir += '/'
            
        #+++++++++++++++++++++++++++++++++++++++++++++++++++++++
        self.agentOutputDataDir = agentOutputDataDir
        #DELETE:
        # self.conjectureLoopDataJSONfile = self.agentOutputDataDir+"conjectureLoopData.JSON" # data of one MBS model and one conjecture (incl. information about agent tasks (e.g. in-/output prompts)
        # self.modelLoopDataJSONfile = self.agentOutputDataDir+"modelLoopData.JSON" # data of one MBS model and multiple conjectures (incl. information about agent tasks (e.g. in-/output prompts)
        # self.overallLoopDataJSONfile = self.agentOutputDataDir+"overallLoopData.JSON" # data of multiple MBS models and multiple conjectures (incl. information about agent tasks (e.g. in-/output prompts)
        # self.conjectureLoopStatisticsJSONfile = self.agentOutputDataDir+"conjectureLoopStatistics.JSON" # statistics of one model and multiple conjectures 
        # self.mbsModelLoopStatisticsJSONfile = self.agentOutputDataDir+"mbsModelLoopStatistics.JSON" # statistics of multiple MBS models and statistics on single MBS model level
        # self.overallLoopStatisticsJSONfile = self.agentOutputDataDir+"overallLoopStatistics.JSON" # statistics of multiple LLMs and the statisctics on multi multi MBS model level  
        
        # get exudyn helper file (alternativ to syntax string)
        self.maxDifficultyLevel = maxDifficultyLevel
        self.filePathExudynHelper = "helperFiles/exudynHelper.py"
        self.filePathEvalHelper = "helperFiles/evalHelper.py"
        self.parsedDictExudyn = ParseExudynHelper(self.filePathExudynHelper, maxDifficultyLevel, 
                                                  excludeTags=['simulationPure','visualization']) # the difficulty level of the mbs model applies to the used exudyn elements in the same manner 
        self.parsedDictEval = ParseExudynHelper(self.filePathEvalHelper, maxDifficultyLevel, 
                                                excludeTags=['visualization'])
        self.parsedDictExudynEval = ParseExudynHelper(self.filePathEvalHelper, maxDifficultyLevel, 
                                                      excludeTags=['visualization'],
                                                      parsedDictInit = self.parsedDictExudyn)
        
        self.listSystemTags = listSystemTags
        
        #some global counters:
        self.totalNumberOfCodesGenerated = 0
    
    def LogLLMresponse(self, task, prompt, response, keyValues={}):
        task = str(task)
        prompt = str(prompt)
        response = str(response)
        
        self.logger.LogText('LLM task: '+task, style=STYLE.bold, timestamp=True, separator=True)
        
        self.logger.LogText('LLM input prompt:', style=STYLE.bold, timestamp=False, separator=True)
        self.logger.LogText(prompt, style=STYLE.python, timestamp=False)
        self.logger.LogText('LLM response:', style=STYLE.bold, timestamp=False, separator=True)
        self.logger.LogText(response, style=STYLE.python, timestamp=False)

        loggingDict = {
            "duration": round(self.llmModel.durationLocal, 2),
            "tokens generated": self.llmModel.numberOfTokensLocal,
            "tokens per second": self.llmModel.tokensPerSecondLocal,
        }
        loggingDict.update(keyValues)

        #DELETE:        
        # self.currentConjectureDict[task] = {}
        # self.currentConjectureDict[task].update(copy.copy(loggingDict) )
        # self.currentConjectureDict[task]['LLM prompt'] = prompt
        # self.currentConjectureDict[task]['LLM response'] = response
        
        self.logger.LogDict(loggingDict, header='summary of '+task+':', inline=True, timestamp=False)

    #print out information and time to go independently of task
    def PrintTimeToGoString(self, taskStr, tStart, rr, mDict):
        
        timeToGo = ''
        tElapsed = time.time() - tStart
        nTotalCnt = mDict['nTotalCnt']
        totalTasks  = rr['numberOfModelCreationTasks']
        mbsModelCnt = mDict['mbsModelCnt']
        numberOfMBSmodelsLoaded = rr['numberOfMBSmodelsLoaded']
        numberOfRandomizations = rr['numberOfRandomizations']
        randomID = mDict['randomIDstr']
        randomizeParameters = (rr['numberOfRandomizations']>0)
        
        if tElapsed > 10 and nTotalCnt > 0:
            ttg = tElapsed/nTotalCnt * (totalTasks - nTotalCnt)
            if ttg < 3600: 
                timeToGo = '; time to go='+str(round(ttg,2))+'s'
            else: 
                timeToGo = '; time to go='+str(round(ttg/3600,2))+'hours'
        
        print('=======================================')
        self.logger.LogText(taskStr+
                       f' model ID{mbsModelCnt} / {numberOfMBSmodelsLoaded}'
                       +(f' (random ID{randomID} / {numberOfRandomizations})')*randomizeParameters
                       +timeToGo,
                       separator=True, printToConsole=True, quickinfo=True)

    #%%++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

    #create Exudyn model from description and return created text (only for testing!)
    def CreateExudynItemsAndModel(self, mbsModelDescription, maxTokensChooseItems, maxTokensGenerateModel):
        # Choose tags needed for Exudyn model out of a list of tags and corresponding code
        exuTagsString = self.ChooseItemsForModel(mbsModelDescription, max_tokens=maxTokensChooseItems)
        exuTags = ExtractElementsInResponse(exuTagsString, self.parsedDictExudynEval) 
        
        self.logger.LogDebug('extracted tags='+str(exuTags))
        
        # Generate Exudyn model
        #original:
        exuModel = self.GenerateExudynModel(exuTags, mbsModelDescription, max_tokens=maxTokensGenerateModel)
    
        if exuModel is not None:
            exudynCodeClean = PreProcessLLMcode(self.logger, exuModel, False, False) 
        else: exudynCodeClean = ''
        
        return exudynCodeClean
    

    
    def ChooseEvalItemsForModel(self, mbsModelDescription, evaluationDescription, max_tokens=None, includeEvalItems=False):
        
        exudynItems = self.parsedDictExudynEval if includeEvalItems else self.parsedDictExudyn
        
        # get all items and corresponding descriptions (#INFO) for general exudyn model
        itemsModel = []
        for key, value in exudynItems.items():
            if key not in self.listSystemTags or includeEvalItems:
                itemsModel.append(f"{key}: {value['INFO']}")
                
        promptTemplate = tmplts.chooseEvalItemsForModel[0]
        prompt = promptTemplate.format(
            modelDescription = mbsModelDescription,
            evaluationDescription = evaluationDescription, 
            exudynItems = "\n".join(itemsModel)
        )
        
        #systemPrompt = "You are an AI-assistant that lists items that represent the models mechanical behavior and the required output generation best. You strictly follow the format item1, item2, ... without additional text or information added."
        systemPrompt = None 
        response = self.llmModel.Generate(prompt=prompt, 
                                          systemPrompt=systemPrompt, 
                                          max_tokens=max_tokens, 
                                          **self.llmGenerateDefaultArgs)
          
        response = CheckLLMoutput(self.logger, response, checkUndesiredKeywords=True, 
                                 checkHarmfulCommands=True)
        
        self.LogLLMresponse("choose Exudyn eval elements", prompt, response, keyValues={"maxTokens": max_tokens})
                    
        return response
    
    
    #create Exudyn model from description and return created text (only for testing!)
    def CreateExudynWithEvalItemsAndModel(self, mbsModelDescription, evaluationDescription, 
                                          evalMethodDict, maxTokensChooseItems, maxTokensGenerateModel):
        # Choose tags needed for Exudyn model out of a list of tags and corresponding code
        exuTagsString = self.ChooseEvalItemsForModel(mbsModelDescription, 
                                                evaluationDescription=evaluationDescription,
                                                max_tokens=maxTokensChooseItems, includeEvalItems=True)
        
        exuTags = ExtractElementsInResponse(exuTagsString, self.parsedDictExudynEval)
        originalTags=str(exuTags)
    
        # exuTags += listSystemTags + listSimulationTags
        for tag in listSystemTags:
            if tag not in exuTags:
                exuTags.append(tag)
        for tag in listSimulationTags:
            if tag not in exuTags:
                exuTags.append(tag)
        
        evalType = evalMethodDict['type']
        isAnalysis = EvaluationType.IsAnalysisType(evalType)
        if isAnalysis:
            if 'dynamic solver' in exuTags: exuTags.remove('dynamic solver')
            if 'static solver' in exuTags: exuTags.remove('static solver')
        
        self.logger.LogDebug('Extracted tags: '+originalTags+'\nUsed tags:'+str(exuTags))
        
        # Generate Exudyn model
        exuModel = self.GenerateExudynModelWithEvalDesc(exuTags=exuTags, 
                                       mbsModelDescription=mbsModelDescription, 
                                       evaluationDescription=evaluationDescription,
                                       promptTemplate=tmplts.generateExudynWithEvalModel[0],
                                       max_tokens=maxTokensGenerateModel)
    
        if exuModel is not None:
            exudynCodeClean = PreProcessLLMcode(self.logger, exuModel, False, False) # preProcess code before storing (put in comment, if real LLM response should be used)
        else: exudynCodeClean = ''
        
        return exudynCodeClean
    
    # Executes provided code in a separate process to prevent infinite loops.
    # replaceCoordinatesSolutionFile: provide string to replace the output filename
    def ExecuteCodeAndGetLocalVariables(self, code, codeType, showTiming=False, timeout=60,
                                        replaceCoordinatesSolutionFile = None,
                                        logCodeAndOutput = True):
        #++++++++++++++++++
        exudynLogOutput = ''
        exudynLogFileName = JoinPath(self.logger.logDir,'exudynTemp.log')
        with open(exudynLogFileName, 'w', encoding='utf-8') as file:
            file.write("")  # Overwrite with an empty file
        
        code = PreProcessLLMcode(self.logger, code, 
                                 replaceCoordinatesSolutionFile=replaceCoordinatesSolutionFile) 
        
        if logCodeAndOutput:
            self.logger.LogText("Execution code type: " + str(codeType) + '\n'+
                                "Exudyn code:\n" +
                                code, style=STYLE.python)
    
        executable = False
        errorMessage = ''
        
        if self.useExudynTimeout:
    
            #run code with timeout
            manager = multiprocessing.Manager()
            returnDict = manager.dict() #Note this is a DictProxy, not a dict!
            process = multiprocessing.Process(target=ExecuteCode, args=(code, globals(), returnDict))
    
            ts = time.time()
            process.start()
            process.join(timeout)
    
            if process.is_alive():
                #timeout, kill process
                try:
                    process.terminate()
                    process.join()
                except KeyboardInterrupt:
                    print("Keyboard interrupt requested...exiting")
                    raise
                except:
                    self.logger.LogError("Execution timeout, failed to kill process.")
                returnDict = {}
                errorMessage = 'Execution killed due to timeout '+str(timeout)+' seconds'
            else:
                returnDict = dict(returnDict)
                if 'error' in returnDict:
                    errorMessage = str(returnDict['error'])
                else:
                    executable = True
    
                    
            ts = time.time() - ts
            #++++++++++++++++++
        else:
            localEnv = {}
            
            ts = time.time()
    
            try:
                exec(code, globals(), localEnv)
                executable = True
            except Exception as e:
                errorMessage = traceback.format_exc()
                errorMessage = f"{str(e)}\n{errorMessage}"
                
            ts = time.time() - ts
            
            returnDict = localEnv
    
        try:
            with open(exudynLogFileName, 'r') as file:
                exudynLogOutput = file.read()
    
            if logCodeAndOutput: #and exudynLogOutput!='':
                self.logger.LogText('Exudyn code log:\n'+exudynLogOutput, style=STYLE.python)
        except KeyboardInterrupt:
            print("Keyboard interrupt requested...exiting")
            raise
        except:
            pass #no reporting
            
        if showTiming and logCodeAndOutput:
            self.logger.LogText("Exudyn code execution time: "+str( round(ts, 2)))
        
        #DELETE:        
        # self.currentConjectureDict[codeType] = {}
        # self.currentConjectureDict[codeType]['code'] = code
        # self.currentConjectureDict[codeType]['exudyn log'] = exudynLogOutput
        # self.currentConjectureDict[codeType]['errorMessage'] = errorMessage
        # self.currentConjectureDict[codeType]['code is executable'] = str(executable)
        # self.currentConjectureDict[codeType]['execution time'] = round(ts,3)
        
        if not executable:
            self.logger.LogError('Execute code error message: '+errorMessage)
            if not logCodeAndOutput:
                self.logger.LogText("Execution code type: " + str(codeType) + '\n'+
                                    "Exudyn code (not executable):\n" +
                                    code, style=STYLE.python)
    
        return executable, returnDict

            
    #evaluate either sample code or Exudyn code; mode is used to printout infos
    def EvaluateMBScode(self, code, currentMBSmodelName, solutionFileName, mode='', isAnalysis=False):
        logger = self.logger
        logCodeAndOutput = False if 'sample' in mode.lower() else True
    
        DeleteFileIfExisting(logger.logDir, solutionFileName)
        [executable, localVariables] = self.ExecuteCodeAndGetLocalVariables(code, 
                                                        mode+", general exudyn model",
                                                        replaceCoordinatesSolutionFile=solutionFileName,
                                                        logCodeAndOutput=logCodeAndOutput )
        if logCodeAndOutput or not executable:
            logger.LogText(mode+f' code is executable for {currentMBSmodelName}: {str(executable)}')
    
        solvedDynamicSuccesful = None
        solvedStaticSuccesful = None
        solvedGeneral = None #eigenvalues, DOF, etc.
        output = None
        try:
            mbsSysDict = localVariables['mbs'].sys
            if not isAnalysis:
                if 'dynamicSolver' in mbsSysDict:
                    solvedDynamicSuccesful = mbsSysDict["dynamicSolver"].output.finishedSuccessfully
                elif 'staticSolver' in mbsSysDict:
                    solvedStaticSuccesful = mbsSysDict.sys["staticSolver"].output.finishedSuccessfully
                else:
                    logger.LogError(f'Evaluate executables, {mode} code: mbs.sys does not contain dynamicSolver/staticSolver (probably did not solve)')
            else:
                solvedGeneral = False
    
                if 'output' in localVariables:
                    output = localVariables['output']
                    if type(output)==list or type(output)==dict: #we cannot evaluate more for now!
                        solvedGeneral = True
                        logger.LogDebug(f'Received output, {mode} code:\noutput="{output}"')
                    else:
                        solvedGeneral = False
                else:
                    logger.LogError(f'Evaluate executables, {mode} code: local variables do not contain "output"')
        except KeyboardInterrupt:
            print("Keyboard interrupt requested...exiting")
            raise
        except:
            logger.LogError(f'Evaluate executables, {mode} code: dynamicSolver/staticSolver/output: failed to retrieve solution information (probably no mbs has been created!)')
    
        #print('static/dynamic:',solvedStaticSuccesful,solvedDynamicSuccesful)
        solverSuccess = solvedDynamicSuccesful == True or solvedStaticSuccesful == True or solvedGeneral == True
        if not solverSuccess:
            if solvedDynamicSuccesful == False:
                logger.LogError(f'Evaluate executables, {mode} code: dynamicSolver not successful!')
            elif solvedStaticSuccesful == False:
                logger.LogError(f'Evaluate executables, {mode} code: staticSolver not successful!')
            elif solvedGeneral == False:
                logger.LogError(f'Evaluate executables, {mode} code: evaluation method not successful! output:"{output}"')
    
            #DELETE:
            # if trial == 0 and not isAnalysis:
            #     #do second try:
            #     logger.LogDebug('NOTE: code is not executable, therefore adding mbs.Assemble() for a second try')
            #     code = code.replace('\nmbs.SolveDynamic(','\nmbs.Assemble()\nmbs.SolveDynamic(')
            #     code = code.replace('\nmbs.SolveStatic(','\nmbs.Assemble()\nmbs.SolveStatic(')
    
        
        return [executable, localVariables, solverSuccess]
    
    
    #%%++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    
    # Generates a number of methods for evaluation for a corresponding MBS model.
    def GenerateEvaluationMethodsList(self, mbsModelDescription, nEvalMethods, max_tokens=None):
        
        listOfEvaluationMethods = ''
        for key, value in tmplts.dictOfEvaluationMethods.items():
            listOfEvaluationMethods += ' - '+key + '\n'
        
        promptTemplate = tmplts.generateEvalMethodsListTemplate[0]
        prompt = promptTemplate.format(
            modelDescription = mbsModelDescription,
            possibleOutputVariables = listOfEvaluationMethods,
            nEvalMethods = nEvalMethods,
        )
    
        systemPrompt = None # for guiding the LLM in creating a response (future)
        response = self.llmModel.Generate(prompt=prompt, systemPrompt=systemPrompt, 
                                           max_tokens=max_tokens, 
                                           **self.llmGenerateDefaultArgs)
        #print('evaluation methods:',response)
    
        response = CheckLLMoutput(self.logger, response)
                    
        self.LogLLMresponse("generate evaluation methods list", prompt, response, keyValues={"maxTokens": max_tokens})
                
        #%% extract list and check for errors
        [evalList, errMsg] = ExtractListFromStringAndTest(response)
        
        evalListOk = True
        if evalList is None:
            evalListOk = False
            self.logger.LogError('GenerateEvaluationMethodsList: no valid list returned: '+ errMsg)
        elif errMsg != '':
            self.logger.LogWarning('GenerateEvaluationMethodsList: list is not fully correct: '+ errMsg)
            
        if evalListOk:
            for evalMethod in evalList:
                if evalMethod not in tmplts.dictOfEvaluationMethods:
                    self.logger.LogError('GenerateEvaluationMethodsList: invalid item in evalList: '+ evalMethod)
                    evalListOk = False
    
        if not evalListOk: 
            evalList = None #we signal that it won't work
        
        #TODO: consider a second iteration (with modified template?) to see, if correct list returns
        self.logger.LogDebug('generate evaluation methods list: final list: '+str(evalList))
        
        return evalList
    
    # Generates a number of conjectures for a corresponding MBS model.
    def GenerateConjecture(self, mbsModelDescription, evaluationMethod, max_tokens=None):
        
        evalDict = tmplts.dictOfEvaluationMethods[evaluationMethod]
        evalType = evalDict['type']
        evalDescription = evalDict['description']
        evalTypeAddInfo = tmplts.evaluationTypeDependentStringsDict[evalType]
        if evalTypeAddInfo != '':
            evalTypeAddInfo = evalTypeAddInfo+"\nPut sensor-related information in plain text between tags: <sensor> ... </sensor>."
        
        evalString = 'Use the evaluation method "'+evaluationMethod+'", which states: '+evalDescription
        
        promptTemplate = tmplts.generateConjectureFromEvaluationMethod[0]
        prompt = promptTemplate.format(
            modelDescription = mbsModelDescription,
            evaluationMethodDescription = evalString,
            evaluationTypeDependentString = evalTypeAddInfo
        )
    
        systemPrompt = None # for guiding the LLM in creating a response (future)
        response = self.llmModel.Generate(prompt=prompt, systemPrompt=systemPrompt, 
                                           max_tokens=max_tokens, 
                                           **self.llmGenerateDefaultArgs)
        
        response = CheckLLMoutput(self.logger, response)   
                    
        self.LogLLMresponse("generate conjecture", prompt, response, keyValues={"maxTokens": max_tokens})
        
        requiredSensors = EvaluationType.RequiredSensors(evalType)
        
        errorMsg = ''
        xmlString = ExtractXMLtaggedString(response,'conjecture')
        if xmlString['text'] == None:
            self.logger.LogError('GenerateConjecture ExtractXMLtaggedString: '+xmlString['message'])
            errorMsg = xmlString['message']
        elif xmlString['text'] == '':
            self.logger.LogDebug('Warning: GenerateConjecture ExtractXMLtaggedString: '+xmlString['message'])
        conjecture = xmlString['text']
        
        if requiredSensors != 0:
            xmlString = ExtractXMLtaggedString(response,'sensor')
            if xmlString['text'] == None:
                self.logger.LogError('GenerateConjecture ExtractXMLtaggedString (sensor): '+xmlString['message'])
                errorMsg = 'extract sensor text:'+xmlString['message']
            elif xmlString['text'] == '':
                self.logger.LogDebug('Warning: GenerateConjecture ExtractXMLtaggedString (sensor): '+xmlString['message'])
            sensorText = xmlString['text']
        else:
            sensorText = None
        
        return [conjecture, sensorText, errorMsg]
        
    
    
    #%%++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    #return score (<0 indicates error) and simulation results as readable string
    def SimulationResultsToText(self, evalMethodDict, localVariablesEvalLLM):
        evalType = evalMethodDict['type']
        evalFunction = evalMethodDict['evaluationFunction']
        response=''
    
        #write function to convert case-dependent output to text
        if (evalType == EvaluationType.SystemAnalysis
            or evalType == EvaluationType.SensorBasedFunction
            or evalType == EvaluationType.SensorsBasedFunction
            ):
            if 'output' in localVariablesEvalLLM:
                output  = localVariablesEvalLLM['output']
                resultsDict = ConvertResultsToPlainText(output, functionName=evalFunction, nDigits=self.nDigitsEvaluate)
                simulationResults = resultsDict['text']
                if resultsDict['error']:
                    self.logger.LogError('Postprocessing simulation1: error in ConvertResultsToPlainText; error=\n'+
                                    resultsDict['text']+', output=\n'+str(output))
                    return [-7, response]
                if resultsDict['warning'] != '':
                    self.logger.LogWarning('Postprocessing simulation (function/analysis): warning='+str(resultsDict['warning']))
            else:
                self.logger.LogError('Postprocessing simulation (function/analysis): no variable "output" found in locals() of exudyn model, which is required for the chosen evaluation method!!!\n')
                return [-6, response]
        elif EvaluationType.IsPureSensorType(evalType): # then print sensor information!
            #in this case, we only convert all sensor results into text:
            nExpectedSensors = EvaluationType.RequiredSensors(evalType)
            
            try:
                resultsDict = ConvertSensors2Text(localVariablesEvalLLM, 
                                                  nResampleSize=self.nResampleSize,
                                                  nDigits=self.nDigitsEvaluate, 
                                                  nExpectedSensors=nExpectedSensors)
            except KeyboardInterrupt:
                print("Keyboard interrupt requested...exiting")
                raise
            except:
                exceptionText = traceback.format_exc()
                self.logger.LogError(f'ConvertSensors2Text failed: {exceptionText}')
                return [-5, response]
                
            simulationResults = resultsDict['text']
            if resultsDict['error']:
                self.logger.LogError('Postprocessing simulation (sensor): error in ConvertSensors2Text; error='+resultsDict['text'])
                return [-5, response]
            if resultsDict['warning'] != '':
                self.logger.LogWarning('Postprocessing simulation (sensor): warning='+str(resultsDict['warning']))
        
        else:
            self.logger.LogError('Postprocessing simulation: invalid evalType -> requires implementation\n')
            return [-4, response]
        
        simulationResults = 'The numerical results of the simulation model are:\n'+simulationResults+'\n'
        
        self.logger.LogText('Simulation results for evaluation are:\n'+simulationResults,separator=True)

        return [0, simulationResults] #0 indicates that no error occured



    #take simulation results from local variables, model and conjecture 
    #return [scoreValue, evaluationLLMresponse] where score is in range 0..100
    def EvaluateConjecture(self, mbsModelDescription, evalMethodDict, conjecture, simulationResults, 
                           evaluateWrongConjectures, max_tokens, useSimEvaluationOnly=False,
                           sensorText=''):
        
        response = ''
        if sensorText is None:
            sensorTextClean = ''
        else:
            sensorTextClean = 'Information about used sensors: '+sensorText.strip()+'\n'
    
        #+++++++++++++++++++++++++++++++ 
        if useSimEvaluationOnly:
            promptTemplate = tmplts.evaluateSimResults[0]
            prompt = promptTemplate.format(
                modelDescription = mbsModelDescription,
                evaluationMethod = evalMethodDict['method_'],
                evaluationDescription = evalMethodDict['description'],
                simulationResults = simulationResults,
                sensorText = sensorTextClean,
            )
        else:
            promptTemplate = tmplts.evaluateConjecture[0]
            prompt = promptTemplate.format(
                modelDescription = mbsModelDescription,
                conjecture = conjecture,
                simulationResults = simulationResults,
                sensorText = sensorTextClean,
            )
    
        systemPrompt = None # for guiding the LLM in creating a response (future)
        
        response = self.llmModel.Generate(prompt=prompt, systemPrompt=systemPrompt, 
                                           max_tokens=max_tokens, 
                                           **self.llmGenerateDefaultArgs)
        
        response = CheckLLMoutput(self.logger, response)   
                    
        self.LogLLMresponse("evaluate " + "wrong model "*evaluateWrongConjectures 
                            + "conjecture"*(1-useSimEvaluationOnly)
                            + "simulation results"*useSimEvaluationOnly, 
                            prompt, response, keyValues={"maxTokens": max_tokens})
        self.logger.LogDebug('evaluation method was: "'+evalMethodDict['method_']+'"')
        
        xmlString = ExtractXMLtaggedString(response,'score')
    
        if xmlString['text'] == None or xmlString['text'] == '':
           self.logger.LogError('EvaluateConjecture: score is invalid: '+xmlString['message'])
           scoreValue = -3 #invalid
        else:
            score = xmlString['text']
            scoreValue = -2 #conversion error
    
            try:
                scoreValue = float(score) #not always an integer
            except KeyboardInterrupt:
                print("Keyboard interrupt requested...exiting")
                raise
            except:
                self.logger.LogError('EvaluateConjecture: score cannot be converted to float: ',score)
            if scoreValue < 0 or scoreValue > 100:
                self.logger.LogError('EvaluateConjecture: score is out of range: ',scoreValue)
                scoreValue = -1 #range error
            else:
                scoreValue = scoreValue/100
        
        return [scoreValue, response, prompt]
    
        
        
        #create final evaluation query text for model, exudyn model, proposed conjecture and model outputs
        #ask to put True / False into <result> </result> if initial conjecture is substantiated by numerical results
        #possibly also use rating <rating> </rating> in range of 0..100
        
    
    #%%++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

    # Chooses Exudyn elements of a list of available Exudyn elements that are necessary for building the simulation model (code) for a corresponding MBS model. 
    def ChooseItemsForModel(self, mbsModelDescription, max_tokens=None):
        
        exudynItems = self.parsedDictExudyn #OLD without EVAL
        
        # get all items and corresponding descriptions (#INFO) for general exudyn model
        itemsModel = []
        for key, value in exudynItems.items():
            if key not in self.listSystemTags:
                itemsModel.append(f"{key}: {value['INFO']}")
                
        promptTemplate = tmplts.chooseItemsForModel[0] 
        prompt = promptTemplate.format(
            modelDescription = mbsModelDescription,
            exudynItems = "\n".join(itemsModel)
        )
        
        # systemPrompt = "You are an AI-assistant that lists items that represent the models mechanical behavior best. You strictly follow the format item1, item2, ... without additional text or information added."
        systemPrompt = None
        response = self.llmModel.Generate(prompt=prompt, systemPrompt=systemPrompt, 
                                          max_tokens=max_tokens, 
                                          **self.llmGenerateDefaultArgs)
          
        response = CheckLLMoutput(self.logger, response, checkUndesiredKeywords=True, 
                                 checkHarmfulCommands=True)
        
        self.LogLLMresponse("choose Exudyn elements", prompt, response, keyValues={"maxTokens": max_tokens})
                    
        return response
    
    
    # Generates an Exudyn model with preselected Exudyn tags for a corresponding MBS model
    def GenerateExudynModel(self, exuTags, mbsModelDescription, max_tokens=None):
    
        for tag in exuTags:  # Look for additionally required tags due to dependencies
            requiredTags = GetRequiredTags(self.parsedDictExudyn, tag)
            if requiredTags is not None:
                newTags = [tag for tag in requiredTags if tag not in exuTags]
                exuTags.extend(newTags)
        
        promptTemplate = tmplts.generateExudynModel[0]
        tagSyntax = CreateSampleCode(self.parsedDictExudyn, exuTags)
        generalStructure = CreateSampleCode(self.parsedDictExudyn, self.listSystemTags)
        generalStructure = generalStructure.replace('# add Exudyn items here',tagSyntax)
        prompt = promptTemplate.format(
            generalStructure = generalStructure,
            modelDescription = mbsModelDescription
        )
        
        systemPrompt = None
        response = self.llmModel.Generate(prompt=prompt, systemPrompt=systemPrompt, max_tokens=max_tokens, **self.llmGenerateDefaultArgs)
        response = CheckLLMoutput(self.logger, response, checkUndesiredKeywords=True, 
                                 checkHarmfulCommands=True)  
        
        self.LogLLMresponse("generate general Exudyn code", prompt, response, keyValues={"maxTokens": max_tokens})
        
        #clean up code, as it will be used in the eval prompt:
        response = PreProcessLLMcode(self.logger, response, addTimeout = False, addFileWrite = False)
        if True:
            self.logger.LogDebug('cleaned-up code of model:\n'+response) #check if cleanup worked
        self.totalNumberOfCodesGenerated += 1
        
        return response
    
    # Generates an Exudyn model with preselected Exudyn elements for a corresponding MBS model
    # also include task for evaluation (sensor / analysis method)
    def GenerateExudynModelWithEvalDesc(self, exuTags, mbsModelDescription, evaluationDescription, promptTemplate, max_tokens=None):
        
        for tag in exuTags:  # Look for additionally required tags due to dependencies
            requiredTags = GetRequiredTags(self.parsedDictExudynEval, tag) 
            if requiredTags is not None:
                newTags = [tag for tag in requiredTags if tag not in exuTags]
                exuTags.extend(newTags)
    
            
        generalStructure = CreateSampleCode(self.parsedDictExudynEval, exuTags)
        generalStructure = generalStructure.replace('# add Exudyn items here\n','') #DELETE as soon as template has been adjusted
    
        prompt = promptTemplate.format(
            generalStructure=generalStructure,
            modelDescription=mbsModelDescription,
            evaluationDescription=evaluationDescription,
        )
        
        systemPrompt = None
        response = self.llmModel.Generate(prompt=prompt, systemPrompt=systemPrompt, max_tokens=max_tokens, **self.llmGenerateDefaultArgs)
        response = CheckLLMoutput(self.logger, response, checkUndesiredKeywords=True, 
                                 checkHarmfulCommands=True)  
        
        self.LogLLMresponse("generate general Exudyn code", prompt, response, keyValues={"maxTokens": max_tokens})
        
        #clean up code, as it will be used in the eval prompt:
        response = PreProcessLLMcode(self.logger, response, addTimeout = False, addFileWrite = False)
        if True:
            self.logger.LogDebug('cleaned-up code of model:\n'+response) #check if cleanup worked
        self.totalNumberOfCodesGenerated += 1

        return response
    

    #%%++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    
    #read sample file, use sample dict to replace parameters from chosenParameters
    #chosenParameters={'mass':10,'stiffness':5000}
    def GetSampleFileDict(self, filePath, fileName, sampleDict, chosenParametersDict=None):
        #sample files:
        parametersStart = '#%%parametersstart%%'
        sampleCodeStart = '#%%samplecodestart%%'
        sampleCodeStop = '#%%samplecodestop%%'
        sampleCodeAssemble = 'mbs.Assemble()'

        try:
            code = ReadFile(filePath, fileName)
        except KeyboardInterrupt:
            print("Keyboard interrupt requested...exiting")
            raise
        except:
            raise ValueError(f'GetSampleFileDict with path {filePath}, file {fileName} failed')
            
        if sampleCodeStart not in code:
            raise ValueError('GetSampleFileDict: '+sampleCodeStart+' tag not found')
    
        preCode = ''
        mainCode = code
        if parametersStart in code:
            preCode = code.split(parametersStart)[0]
            mainCode = code.split(parametersStart)[1]
    
        #process code:
        for text in ['exu.StartRenderer()',
                     'mbs.WaitForUserToContinue()',
                     'SC.WaitForRenderEngineStopFlag()',
                     'exu.StopRenderer()',]:
            mainCode = mainCode.replace(text, 'pass') #replace with pass, e.g. if code appears in if-clause
    
        for _ in range(4):
            mainCode = mainCode.replace('\npass\n','\n')
    
        modelCode = mainCode.split(sampleCodeStart)[1].split(sampleCodeAssemble)[0]
        solverCode = sampleCodeAssemble + mainCode.split(sampleCodeAssemble)[1].split(sampleCodeStop)[0] 
        paramsCode = mainCode.split(sampleCodeStart)[0]
    
    
        params = sampleDict['parameters']
        #check if parameters are included
        for key, value in params.items():
            if not key.startswith('_') and key not in paramsCode:
                raise ValueError('GetSampleFileDict: parameter"'+key+'" missing in sample file "'
                                 +fileName+'"')
    
        paramsText = ''
        if chosenParametersDict != None: #if parameters are available, use them
            for key, value in chosenParametersDict.items():
                valueStr = str(value)
                if isinstance(value,str): 
                    valueStr = '"' + valueStr + '"'
                paramsText += key + ' = ' + valueStr  + '\n'
        else:
            for key, value in sampleDict.items():
                valueStr = str(value['default'])
                if isinstance(value['default'],str):
                    valueStr = '"' + valueStr + '"'
                paramsText += key + ' = ' + valueStr + '\n'
        paramsText += '\n'
        
        executableCodeShort = paramsText + modelCode + solverCode
        executableCode = preCode + executableCodeShort
                
        return {'modelCode':modelCode,
                'solverCode':solverCode,
                'executableCode':executableCode,
                'paramsCode':paramsCode,
                'executableCodeShort':executableCodeShort,
                'fileContent':code,
                }
        

    #%%++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

    #build basic model description dictionary
    #if differentFromTheseParameters is not None, then parameters shall be different from these parameters
    def GetMBSmodelDescriptionDict(self, currentMBSmodelName, randomIDstr, numberOfRandomizations,
                                   differentFromTheseParameters=None):
    
        if numberOfRandomizations == 0:
            raise ValueError('GetMBSmodelDescriptionDict: differentFromTheseParameters must be None if numberOfRandomizations == 0')
        currentMBSmodelNameID = currentMBSmodelName + randomIDstr            
    
        mDict = {} #dict for a single model
        mDict['mbsModelNameID'] = currentMBSmodelNameID
        mDict['mbsModelName'] = currentMBSmodelName
        mDict['randomIDstr'] = randomIDstr
        mDict['modelParameters'] = {}
            
        [mDict['modelDescription'], mDict['modelData'],
         mDict['modelParameters']] = self.mbsModelLoader.GetModelDescriptionAndDict(currentMBSmodelName, 
                                                                               randomizeParameters=(numberOfRandomizations>0),
                                                                               differentFromTheseParameters=differentFromTheseParameters,
                                                                               logger=self.logger)

        return mDict

    #return string which contains additional information for Exudyn model creation 
    #  related to evaluation method (sensors, eigenvalue methods, ...)
    def GetEvaluationMethodDescription(self, evaluationMethod, sensorText):
        evalMethodDict = tmplts.dictOfEvaluationMethods[evaluationMethod] #was already checked that all items in evalList are VALID!
        evalType = evalMethodDict['type']
        requiredSensors = EvaluationType.RequiredSensors(evalType)
        
        evaluationDescription = 'Use the evaluation method "'+evaluationMethod+'", which states: '+evalMethodDict['description']+'\n'
        #extend standard Exudyn model creation prompt
        if requiredSensors!=0:
            evaluationDescription += 'A sensor shall be added and stored as sensorNumber - it will be evaluated by the user later on. Set the flag "storeInternal=True", and use the following information:\n'+sensorText.strip()

        #specific code-generation-specific information
        if evalMethodDict['evaluationCodeHints'] != '':
            evaluationDescription += '\n\n'+evalMethodDict['evaluationCodeHints']
        return evaluationDescription

    #%%++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        

    #loop over all models with model variations
    #perform conjectures evaluation for each parameterized model
    def GenerateModelsAndConjecturesLoop(self, numberOfConjecturesPerModel, numberOfRandomizations=1, 
                                         generateWrongConjectures=False):
        logger = self.logger
        mbsModelLoader = self.mbsModelLoader
        logDir = logger.logDir
        
        solutionDir = JoinPath(logDir, 'solution')
        os.makedirs(solutionDir, exist_ok=True)
    
        #additional directory for model comparison
        os.makedirs(logDir, exist_ok=True)
        mbsModelsLLMdir = JoinPath(logDir, 'mbsModelsLLM')
        mbsEvalModelsLLMdir = JoinPath(logDir, 'mbsEvalModelsLLM')
        os.makedirs(mbsModelsLLMdir, exist_ok=True)
        os.makedirs(mbsEvalModelsLLMdir, exist_ok=True)

        EnsureEmptyDir(solutionDir) # creates empty Dir or deletes content if existend
        EnsureEmptyDir(mbsModelsLLMdir) # creates empty Dir or deletes content if existend
        EnsureEmptyDir(mbsEvalModelsLLMdir) # creates empty Dir or deletes content if existend

        logger.LogText('Run ModelsAndConjecturesLoop: using LLM model: '+self.llmModel.modelName, 
                       printToConsole=True, separator=True, quickinfo=True)
        logger.LogText('Using mbs models: '+ str(mbsModelLoader.ListOfModels()), 
                       printToConsole=True, separator=True, quickinfo=True)
    


        #++++++++++++++++++++++
        #variables
        rr = {} #this is the overall dictionary for a llmModel, initialized here
        rr['numberOfConjecturesPerModel'] = numberOfConjecturesPerModel

        rr['numberOfRandomizations'] = numberOfRandomizations
        rr['generateWrongConjectures'] = generateWrongConjectures

        mbsModelNamesLoaded = mbsModelLoader.ListOfModels()
        rr['mbsModelNamesLoaded'] = mbsModelNamesLoaded

        numberOfMBSmodelsLoaded = mbsModelLoader.NumberOfModels()
        rr['numberOfMBSmodelsLoaded'] = numberOfMBSmodelsLoaded

        numberOfModelCreationTasks = numberOfMBSmodelsLoaded*max(1,numberOfRandomizations) #including randomizations
        rr['numberOfModelCreationTasks'] = numberOfModelCreationTasks

        #rr['exudynVersion'] = exu.GetVersionString()
        rr['maxDifficultyLevel'] = self.mbsModelLoader.maxDifficultyLevel

        #even though that the evaluation LLM could differ, we use these solution dirs:
        rr['mbsModelsLLMdir'] = mbsModelsLLMdir
        rr['mbsEvalModelsLLMdir'] = mbsEvalModelsLLMdir
        rr['solutionDir'] = solutionDir

        rr['allMbsModelsDict'] = {} #here, all created models are stored
        rr['genMC'] = {} #data related to model creation
        rr['genMC']['executionDateStr'] = datetime.date.today().strftime("%Y-%m-%d")
        rr['genMC']['executionTimeStr'] = datetime.datetime.now().strftime("%H:%M:%S")
        rr['genMC']['llmModelName'] = self.llmModel.modelName #this is the base LLM, used for gen; also used for naming of dirs!

        rr['genMC']['numberOfConjectureCreationTasks'] = numberOfModelCreationTasks * numberOfConjecturesPerModel
        rr['genMC']['totalAvailableConjectures'] = 0

        nTotalCnt = -1
        tStart = time.time()

        for mbsModelCnt, currentMBSmodelName in enumerate(mbsModelNamesLoaded):

            for randomID in range(max(1,numberOfRandomizations) ):

                nTotalCnt+=1
                
                randomIDstr = ''
                
                if numberOfRandomizations > 0:
                    randomIDstr = str(randomID)

                mDict = self.GetMBSmodelDescriptionDict(currentMBSmodelName, randomIDstr, numberOfRandomizations)
                mDict['mbsModelCnt'] = mbsModelCnt
                mDict['nTotalCnt'] = nTotalCnt

                #get parameterized model description and Evaluation method
                try:
                    self.PrintTimeToGoString('GenerateModelsAndConjecturesLoop', tStart, rr, mDict)
                
                    if generateWrongConjectures:
                        logger.LogDebug('\n+++++++++++++++++++++++++++++++++++++++++++\nCREATE WRONG MODEL and CONJECTURE'+
                                        '\n+++++++++++++++++++++++++++++++++++++++++++\n')
                        mDictWrong = self.GetMBSmodelDescriptionDict(currentMBSmodelName, randomIDstr, numberOfRandomizations,
                                                                     differentFromTheseParameters=mDict['modelParameters'])
                        logger.LogDebug('\n+++++++++++++++++++++++++++++++++++++++++++\nOriginal mbs model description:\n'+mDict['modelDescription']+
                                        '\n+++++++++\nWrong mbs model description:\n'+mDictWrong['modelDescription']+
                                        '\n+++++++++++++++++++++++++++++++++++++++++++' )

                        mDict['modelDescription_wrong'] = mDictWrong['modelDescription']
                
                    mDict['conjectures'] = []
                    #++++++++++++++++++++++++++++++++++++++
                    #choose evaluation method
                    evalList = self.GenerateEvaluationMethodsList(
                                                             mbsModelDescription=mDict['modelDescription'],
                                                             nEvalMethods=numberOfConjecturesPerModel,
                                                             max_tokens=self.maxTokensGenerateEvalMethods)
                    conjecture=None
                    sensorText=None
                    requiredSensors = None
                    if evalList is not None and type(evalList) == list:
                        listOfEvaluationMethods = list(tmplts.dictOfEvaluationMethods)
                        evalListLower = [x.lower() for x in listOfEvaluationMethods]
                        if len(evalList) != numberOfConjecturesPerModel:
                            logger.LogError(f'GenerateEvaluationMethodsList: requested {numberOfConjecturesPerModel} eval methods, but received {len(evalList)}!')
                            if len(evalList) > numberOfConjecturesPerModel:
                                evalList = evalList[:numberOfConjecturesPerModel]
                            
                        cID = 0
                        for evaluationMethod in evalList:
                            
                            ###propose conjecture for model, based on evaluation method
                            if evaluationMethod.lower() not in evalListLower:
                                logger.LogError('found invalid evaluation method:'+evaluationMethod)
                            else:
                                evaluationMethod = listOfEvaluationMethods[evalListLower.index(evaluationMethod.lower())]
                                evalMethodDict = tmplts.dictOfEvaluationMethods[evaluationMethod] #was already checked that all items in evalList are VALID!

                                evalType = evalMethodDict['type']
                                requiredSensors = EvaluationType.RequiredSensors(evalType)
        
                                [conjecture, sensorText, errorMsg] = self.GenerateConjecture( 
                                                                               mbsModelDescription=mDict['modelDescription'], 
                                                                               evaluationMethod = evaluationMethod,
                                                                               max_tokens=self.maxTokensGenerateConjecture)

                                conjectureDict = {}
                                conjectureDict['currentMBSmodelNameID'] = mDict['mbsModelNameID'] 
                                conjectureDict['cID'] = cID
                                cID+=1
                                conjectureDict['evaluationMethod'] = evaluationMethod
                                conjectureDict['requiredSensors'] = requiredSensors
                                conjectureDict['conjecture'] = conjecture
                                conjectureDict['sensorText'] = sensorText
                                conjectureDict['genConjectureError'] = errorMsg

                                if generateWrongConjectures:
                                    [conjecture_wrong, sensorText_wrong, errorMsg_wrong] = self.GenerateConjecture( 
                                                                                   mbsModelDescription=mDict['modelDescription_wrong'], 
                                                                                   evaluationMethod = evaluationMethod,
                                                                                   max_tokens=self.maxTokensGenerateConjecture)
                                    conjectureDict['conjecture_wrong'] = conjecture_wrong
                                
                                if conjecture is not None and (sensorText is not None or (requiredSensors==0) ):
                                    if not generateWrongConjectures or conjecture_wrong is not None: #we require both conjectures to be valid!
                                        mDict['conjectures'].append(conjectureDict)
                                        rr['genMC']['totalAvailableConjectures'] += 1

                    #add mDict at the end: only added, if all tasks successful!
                    rr['allMbsModelsDict'][mDict['mbsModelNameID']] = mDict #this is the basic models collection, used for all subsequent steps

                
                except KeyboardInterrupt:
                    print("Keyboard interrupt requested...exiting")
                    raise
                except:
                    exceptionText = traceback.format_exc()
                    logger.LogError('Generate conjecture failed: "'+mDict['mbsModelNameID']
                                    +f'", ID {mbsModelCnt}/{numberOfMBSmodelsLoaded}'
                                    +f', RID{randomIDstr}'*bool(randomIDstr)
                                    +f': {exceptionText}')

                #counters updated in every task
                rr['genMC']['numberOfRemovedTokensGlobal'] = self.llmModel.numberOfRemovedTokensGlobal
                rr['genMC']['numberOfTokensGlobal'] = self.llmModel.numberOfTokensGlobal
                
                rr['genMC']['runTime'] = time.time() - tStart #update in every iteration

        rr['genMC']['llmConfig'] = GetScalarClassObjectsDict(self.llmModel)
        rr['genMC']['agentConfig'] = GetScalarClassObjectsDict(self)

        rr['genMC']['loggerErrors'] = logger.errorCount
        rr['genMC']['loggerWarnings'] = logger.warningCount
        logger.PrintAndLogCounters()

        logger.PrintScalarQuantities(title='Summary of GenerateModelsAndConjecturesLoop',dataDict=rr['genMC'], separator=True)

        return rr



    #%%++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    #loop over all models with model variations
    #generate Exudyn model, evaluate Exudyn model and store simulation results
    def GenerateExudynModelsAndEval(self, rr):
        logger = self.logger
        logDir = logger.logDir
        logger.ResetCounters()

        # mbsModelLoader = rr['mbsModelLoader']
        mbsModelsLLMdir = rr['mbsModelsLLMdir']
        mbsEvalModelsLLMdir = rr['mbsEvalModelsLLMdir']
        solutionDir = rr['solutionDir']

        EnsureEmptyDir(solutionDir) # creates empty Dir or deletes content if existend
        EnsureEmptyDir(mbsModelsLLMdir) # creates empty Dir or deletes content if existend
        EnsureEmptyDir(mbsEvalModelsLLMdir) # creates empty Dir or deletes content if existend
        
        DeleteFileIfExisting(logDir, "coordinatesSolution.txt") #this is unused, but could show up in case something goes wrong
        logger.LogText('Using Exudyn version: '+exu.GetVersionString(), 
                       printToConsole=True, separator=True, quickinfo=True)

        # totalNumberOfConjectures = len(list(rr['allMbsModelsDict']))
        numberOfMBSmodelsLoaded = rr['numberOfMBSmodelsLoaded']

        logger.LogText('Generate Exudyn models and evaluate: nModels='
                       + str(len(list(rr['allMbsModelsDict'])))
                       + ', nConjPerModel=' + str(rr['numberOfConjecturesPerModel'])
                       + ', LLM model='+self.llmModel.modelName, 
                       printToConsole=True, separator=True, quickinfo=True)

        genExu = {}
        rr['genExu'] = genExu

        #counters to be updated!
        genExu['nTotalExecutable'] = 0
        genExu['nTotalExecutableEval'] = 0
        genExu['nTotalExecutableSamples'] = 0
        genExu['nTotalCorrect'] = 0
        genExu['nTotalAvailableConjectures'] = 0
        genExu['nTotalAvailableEvalModels'] = 0 #theoretically given, but some models provide shorter eval list
        genExu['nCompletedSamples'] = 0
        genExu['diffSolutionTolerance'] = self.diffSolutionTolerance
        genExu['llmModelName'] = self.llmModel.modelName #this is the base LLM, used for gen; also used for naming of dirs!
        genExu['executionDateStr'] = datetime.date.today().strftime("%Y-%m-%d")
        genExu['executionTimeStr'] = datetime.datetime.now().strftime("%H:%M:%S")

        genExu['exudynVersion'] = exu.GetVersionString()

        genExu['numberOfRemovedTokensGlobal'] = -self.llmModel.numberOfRemovedTokensGlobal
        genExu['numberOfTokensGlobal'] = -self.llmModel.numberOfTokensGlobal

        genExu['resultsDicts'] = {} #here, geDicts are stored
        
        tStart = time.time()

        for key, mDict in rr['allMbsModelsDict'].items(): #these are models+random variations

            mbsModelCnt = mDict['mbsModelCnt']
            currentMBSmodelName = mDict['mbsModelName']
            randomIDstr = mDict['randomIDstr']
            currentMBSmodelNameID = key
            
            self.PrintTimeToGoString('GenerateExudynModelsAndEval', tStart, rr, mDict)

            geDict = {} #generated exudyn model and simulation results
            genExu['resultsDicts'][currentMBSmodelNameID] = geDict #results per model
            geDict['resultsPerConj'] = [] #result per conjecture (for now, only the numerical results, not the conjecture!)
            geDict['nExecutablePerModel'] = 0
            geDict['nCorrectPerModel'] = 0
            geDict['nExecutableEvalPerModel'] = 0
            geDict['nAvailableConjectures'] = 0
            geDict['nAvailableEvalModels'] = 0

            for cID, conjectureDict in enumerate(mDict['conjectures']):
                print(' * --------------------------------- * ')
                self.logger.LogText(f'Generate Exudyn model for conjecture {cID} / {len(mDict["conjectures"])}',
                                    separator=True, printToConsole=True, quickinfo=True)
                currentMBSmodelNameIDcID = currentMBSmodelNameID+'c'+str(cID)
            
                crDict = {} #results for conjecture
                geDict['resultsPerConj'].append(crDict)
                crDict['scoreValue'] = -100 #should be always available
                crDict['currentMBSmodelNameIDcID'] = currentMBSmodelNameIDcID
                crDict['currentMBSmodelNameID'] = currentMBSmodelNameID
                crDict['cID'] = cID
                genExu['nTotalAvailableEvalModels'] += 1 #for every model and all conjecture, there could be one executable model
                geDict['nAvailableEvalModels'] += 1
                #get parameterized model description and Evaluation method
                try:
                    
                    solutionNameLLM = JoinPath(solutionDir,currentMBSmodelName + 'LLM.txt') #do not store all solutions...
                    #solutionNameLLM = JoinPath(solutionDir,currentMBSmodelNameIDcID + 'LLM.txt')
                    solutionNameSample = JoinPath(solutionDir,currentMBSmodelName + 'Sample.txt') #will change over time


                    evaluationMethod = conjectureDict['evaluationMethod']
                    sensorText = conjectureDict['sensorText']
                    evaluationDescription = self.GetEvaluationMethodDescription(evaluationMethod, sensorText)
                    
                    evalMethodDict = tmplts.dictOfEvaluationMethods[evaluationMethod]
                    mbsModelDescription = mDict['modelDescription']
                    #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
                    #create Exudyn model
                    exudynCode = self.CreateExudynWithEvalItemsAndModel(
                                                                   mbsModelDescription=mbsModelDescription,
                                                                   evaluationDescription=evaluationDescription,
                                                                   evalMethodDict=evalMethodDict, 
                                                                   maxTokensChooseItems=self.maxTokensChooseItems, 
                                                                   maxTokensGenerateModel=self.maxTokensGenerateModel)
                    
                    crDict['exudynCode'] = exudynCode
                    #++++++++++++++++++++++++++++++++++++
                    #%% verify main part of model (check correctness)
                    modelData = mDict['modelData']
                    chosenParameters = mDict['modelParameters']
                    
                    sampleFileDict = self.GetSampleFileDict(filePath="sampleFiles", 
                                                            fileName=modelData["sampleFileName"], 
                                                            sampleDict=modelData, 
                                                            chosenParametersDict=chosenParameters) 
                    solverCode = sampleFileDict["solverCode"]
        
                    sampleCode = sampleFileDict['executableCode']
    
                    exudynCodeClean = exudynCode.split('\nmbs.Assemble()')[0] + '\n' 
                    exudynCodeClean += solverCode
                    
                    mbsModelDescriptionPython = '# ** given model description: **\n'
                    mbsModelDescriptionPython += String2PythonComment(mbsModelDescription)
                    
                    WriteFile(currentMBSmodelNameID+'.py', 
                              mbsModelDescriptionPython+exudynCodeClean, #add description to simplify manual error checking
                              path=mbsModelsLLMdir, flush=True)
                    WriteFile(currentMBSmodelNameIDcID+'.py', 
                              mbsModelDescriptionPython+exudynCode, #add description to simplify manual error checking
                              path=mbsEvalModelsLLMdir, flush=True)
    
                    executableLLM = -1
                    executableEvalLLM = -1
                    differenceLLM = -1

                    #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
                    #Evaluate code if possible
                    if 'mbs.Assemble()' not in exudynCode:
                        logger.LogError('Check Exudyn code: no mbs.Assemble() found in code!')
                        logger.LogText(f'LLM generated eval code is executable for {currentMBSmodelNameIDcID}: False') #for consistency!
                    else:
            
                        
                        [executableSample, localVariablesSample, solverSuccessSample] = self.EvaluateMBScode(
                                                                                        sampleCode, 
                                                                                        currentMBSmodelNameIDcID,
                                                                                        solutionFileName=solutionNameSample, 
                                                                                        mode='Sample file based')
                        [executableLLM, localVariablesLLM, solverSuccessLLM] = self.EvaluateMBScode(
                                                                               exudynCodeClean,
                                                                               currentMBSmodelNameIDcID,
                                                                               solutionFileName=solutionNameLLM, 
                                                                               mode='LLM generated')
                        genExu['nCompletedSamples'] += 1
                      
                        #here, local variables do not need to be stored!
                        crDict['executableSample'] = executableSample  
                        crDict['solverSuccessSample'] = solverSuccessSample  
                        crDict['executableLLM'] = executableLLM  
                        crDict['solverSuccessLLM'] = solverSuccessLLM  
                        crDict['scoreValue'] = -100
                        geDict['nExecutablePerModel'] += executableLLM

                        genExu['nTotalExecutable'] += executableLLM
                        genExu['nTotalExecutableSamples'] += solverSuccessSample

                        crDict['modelIsCorrect'] = False
                        # check if simulation worked - not necessary if the two following succeds
                        if (executableSample and executableLLM and solverSuccessSample and solverSuccessLLM):
                            # simulation worked, compare with reference coordinatesSolution.txt
            
                            differenceLLM = EvaluateNumerical(fileNameReference=solutionNameSample,
                                                    fileNameEvaluate=solutionNameLLM,
                                                    logger=logger)
                            crDict['differenceLLM'] = differenceLLM 
                            if differenceLLM >= 0 and differenceLLM < self.diffSolutionTolerance:
                                geDict['nCorrectPerModel'] += 1
                                crDict['modelIsCorrect'] = True

                        genExu['nTotalCorrect'] += crDict['modelIsCorrect']

                        #++++++++++++++++++++++++++++++++++++++++++++++
                        #%% now evaluate full model with evaluation
                        #run full code
                        
                        [executableEvalLLM, localVariablesEvalLLM, solverSuccessEvalLLM] = self.EvaluateMBScode(
                                                                               exudynCode, 
                                                                               currentMBSmodelNameIDcID,
                                                                               solutionFileName=solutionNameLLM, 
                                                                               mode='LLM generated eval',
                                                                               isAnalysis = EvaluationType.IsAnalysisType(evalMethodDict['type']),
                                                                               )

                        crDict['executableEvalLLM'] = executableEvalLLM
                        crDict['solverSuccessEvalLLM'] = solverSuccessEvalLLM  
                        geDict['nExecutableEvalPerModel'] += executableEvalLLM
                        genExu['nTotalExecutableEval'] += executableEvalLLM

                        if executableEvalLLM and solverSuccessEvalLLM:
                            [scoreValue, simulationResults] = self.SimulationResultsToText(evalMethodDict, localVariablesEvalLLM)
                            
                            crDict['scoreValue'] = scoreValue #temporary; only negative number means failure
                            crDict['simulationResults'] = simulationResults
                            
                            geDict['nAvailableConjectures'] += (scoreValue>=0)
                            genExu['nTotalAvailableConjectures'] += (scoreValue>=0)

                    currentScore = genExu['nTotalCorrect']/max(1,genExu['nTotalAvailableEvalModels'])
                    self.logger.LogText(f'  ==> exec={executableLLM}, execEval={executableEvalLLM}, diff={DynamicRound(differenceLLM,6)}, currentScore={currentScore}',
                                        separator=True, printToConsole=True, quickinfo=True)

                    #++++++++++++++++++++++++++++++++++++++
    
                except KeyboardInterrupt:
                    print("Keyboard interrupt requested...exiting")
                    raise
                except:
                    exceptionText = traceback.format_exc()
                    logger.LogError('Generate Exudyn model/eval failed: "'+mDict['mbsModelNameID']
                                    +f'", ID {mbsModelCnt}/{numberOfMBSmodelsLoaded}'
                                    +f', RID{randomIDstr}'*bool(randomIDstr)
                                    +f': {exceptionText}')
            #++++++++++++++++++++++++++++++
            #do evaluation per model
            nDivModel = max(1, geDict['nAvailableEvalModels'])
            geDict['scoreCorrect'] = geDict['nCorrectPerModel'] / nDivModel
            geDict['scoreExecutable'] = geDict['nExecutablePerModel'] / nDivModel
            geDict['scoreExecutableEval'] = geDict['nExecutableEvalPerModel'] / nDivModel

        #++++++++++++++++++++++++++++++
        #do evaluation for all models
        nDiv = max(1,genExu['nTotalAvailableEvalModels'])
        genExu['totalScoreExecutable'] = genExu['nTotalExecutable'] / nDiv
        genExu['totalScoreExecutableEval'] = genExu['nTotalExecutableEval'] / nDiv
        genExu['totalScoreCorrect'] = genExu['nTotalCorrect'] / nDiv


        genExu['numberOfRemovedTokensGlobal'] += self.llmModel.numberOfRemovedTokensGlobal
        genExu['numberOfTokensGlobal'] += self.llmModel.numberOfTokensGlobal
        
        genExu['runTime'] = time.time() - tStart #update in every iteration
        genExu['llmConfig'] = GetScalarClassObjectsDict(self.llmModel)
        genExu['agentConfig'] = GetScalarClassObjectsDict(self)

        genExu['loggerErrors'] = logger.errorCount
        genExu['loggerWarnings'] = logger.warningCount
        logger.PrintAndLogCounters()

        if genExu['nTotalExecutableSamples'] != genExu['nCompletedSamples']:
            logger.LogError(f"Some Samples (reference files) were not executable: nCompletedSamples={genExu['nCompletedSamples']} while nTotalExecutableSamples={genExu['nTotalExecutableSamples']}")

        logger.PrintScalarQuantities(title='Summary of GenerateExudynModelsAndEval',dataDict=genExu, separator=True)

        return rr



    #%%++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

    #loop over all models with model variations
    #perform conjectures evaluation for each parameterized model
    def EvaluateAllConjectures(self, rr, evaluateWrongConjectures=False, useSimEvaluationOnly=False):
        logger = self.logger
        logDir = logger.logDir
        logger.ResetCounters()
        strUseWrongModels=' (using wrong models)'*evaluateWrongConjectures

        # mbsModelLoader = rr['mbsModelLoader']
        # mbsModelsLLMdir = rr['mbsModelsLLMdir']
        # mbsEvalModelsLLMdir = rr['mbsEvalModelsLLMdir']
        # solutionDir = rr['solutionDir']
        
        # DeleteFileIfExisting(logDir, "coordinatesSolution.txt") #this is unused, but could show up in case something goes wrong
        # logger.LogText('Using Exudyn version: '+exu.GetVersionString(), 
        #                printToConsole=True, separator=True, quickinfo=True)

        # totalNumberOfConjectures = len(list(rr['allMbsModelsDict']))
        numberOfMBSmodelsLoaded = rr['numberOfMBSmodelsLoaded']

        if evaluateWrongConjectures and not rr['generateWrongConjectures']:
            raise ValueError('EvaluateAllConjectures: evaluateWrongConjectures only possible if generateWrongConjectures in model dicts')
        
        logger.LogText('Evaluate conjectures'+strUseWrongModels
                       +': nModels='+ str(len(list(rr['allMbsModelsDict'])))
                       + ', nConjPerModel=' + str(rr['numberOfConjecturesPerModel'])
                       + ', LLM model='+self.llmModel.modelName, 
                       printToConsole=True, separator=True, quickinfo=True)

        
        evalConj = {}
        rr['evalConj'+'_WM'*evaluateWrongConjectures] = evalConj
        rr['executionDateStr'] = datetime.date.today().strftime("%Y-%m-%d") #this is the time of final conjecture ...
        rr['executionTimeStr'] = datetime.datetime.now().strftime("%H:%M:%S")


        evalConj['useSimEvaluationOnly'] = useSimEvaluationOnly
        #counters to be updated!

        evalConj['sumScoreTotalConjectures'] = 0
        evalConj['nTotalConjectures'] = 0

        evalConj['sumScoreTotalConjectureCorrectModels'] = 0   #sum of score for correct models
        evalConj['sumScoreTotalConjectureWrongModels'] = 0     #sum of score for wrong models
        evalConj['nTotalConjectureCorrectModels'] = 0       #number of conjectures with correct models
        evalConj['nTotalConjectureWrongModels'] = 0         #number of conjectures with wrong models

        evalConj['sumMultScoreTotalConjectureCorrectModels'] = 0   #sum of score for correct models
        evalConj['sumMultScoreTotalConjectureWrongModels'] = 0     #sum of score for wrong models
        evalConj['nTotalMultConjectureCorrectModels'] = 0   #counter for mult scores
        evalConj['nTotalMultConjectureWrongModels'] = 0     #counter for mult scores


        #init counters, if we do not start with zero
        evalConj['numberOfRemovedTokensGlobal'] = -self.llmModel.numberOfRemovedTokensGlobal
        evalConj['numberOfTokensGlobal'] = -self.llmModel.numberOfTokensGlobal
        evalConj['llmModelName'] = self.llmModel.modelName #this is the base LLM, used for gen; also used for naming of dirs!
        
        evalConj['allModelsResultsDicts'] = {} #here, geDicts are stored
        
        
        tStart = time.time()

        for key, mDict in rr['allMbsModelsDict'].items():

            self.PrintTimeToGoString('EvaluateAllConjectures '+key+':', tStart, rr, mDict)
            logger.LogText('\n',quickinfo=True, timestamp=False)
            
            mbsModelCnt = mDict['mbsModelCnt']
            # currentMBSmodelName = mDict['mbsModelName']
            randomIDstr = mDict['randomIDstr']
            currentMBSmodelNameID = key
            mbsModelDescription = mDict['modelDescription'] if not evaluateWrongConjectures else mDict['modelDescription_wrong']
            

            geDict = rr['genExu']['resultsDicts'][currentMBSmodelNameID] #this contains data of previous step
            
            modelECdict = {} #generated exudyn model and simulation results
            modelECdict.update(geDict) #update with general information from geDict ?
            del modelECdict['resultsPerConj'] #we do not copy this value
            
            evalConj['allModelsResultsDicts'][currentMBSmodelNameID] = modelECdict #evaluated conjectures
            
            modelECdict['nAvailableConjectures'] = 0
            modelECdict['nConjecturesCorrectModels'] = 0
            modelECdict['nConjecturesWrongModels'] = 0
            modelECdict['sumScoreConjectureCorrectModels'] = 0
            modelECdict['multScoreConjectureCorrectModels'] = 1
            modelECdict['sumScoreConjectureWrongModels'] = 0
            modelECdict['multScoreConjectureWrongModels'] = 1

            modelECdict['conjecturesEvaluated'] = [] #this list containes results per conjecture

            for cID, conjectureDict in enumerate(mDict['conjectures']):

                #get get evaluation results and conjecture to evaluate conjecture
                try:
                    logger.LogText('Evaluate conjecture '+str(cID)+' of model '+currentMBSmodelNameID,
                            #printToConsole=True, quickinfo=True #done later with results
                            )
                    
                    ecDict = {} #results for conjecture
                    modelECdict['conjecturesEvaluated'].append(ecDict)
                    crDict = geDict['resultsPerConj'][cID] #from model evaluation
                    ecDict.update(crDict)
                    #del exudynCode from ecDict!
    
                    if crDict['scoreValue'] >= 0:
                        evaluationMethod = conjectureDict['evaluationMethod']
                        evalMethodDict = tmplts.dictOfEvaluationMethods[evaluationMethod]

                        conjecture = conjectureDict['conjecture'] if not evaluateWrongConjectures else conjectureDict['conjecture_wrong']
                        sensorText = conjectureDict['sensorText']
                        simulationResults = crDict['simulationResults']
                        
                        [scoreValue, conjLLMresponse, conjPrompt] = self.EvaluateConjecture(
                                                                      mbsModelDescription, 
                                                                      evalMethodDict, 
                                                                      conjecture, 
                                                                      simulationResults,
                                                                      evaluateWrongConjectures,
                                                                      self.maxTokensEvaluateConjecture,
                                                                      useSimEvaluationOnly,
                                                                      sensorText,
                                                                      )
                        ecDict['scoreValue'] = scoreValue
                        posScoreValue = scoreValue if scoreValue >= 0 else 0 #we only must sum the positive values
                        
                        ecDict['conjecture'] = conjecture
                        #ecDict['simulationResults'] = simulationResults #included in crDict
                        ecDict['conjPrompt'] = conjPrompt #do we need that?
                        ecDict['conjLLMresponse'] = conjLLMresponse

                        evalConj['sumScoreTotalConjectures'] += posScoreValue
                        evalConj['nTotalConjectures'] += 1

                        logger.LogText(f" - Evaluation for {crDict['currentMBSmodelNameIDcID']}"+strUseWrongModels+":"
                                        +f" method={evaluationMethod},"
                                        +f" modelIsCorrect={crDict['modelIsCorrect']},"
                                        +f" scoreValue={scoreValue}\n", 
                                        printToConsole=True, quickinfo=True)
                        
                        if crDict['modelIsCorrect']:
                            modelECdict['sumScoreConjectureCorrectModels'] += posScoreValue
                            evalConj['sumScoreTotalConjectureCorrectModels'] += posScoreValue
                            modelECdict['nConjecturesCorrectModels'] += 1
                            evalConj['nTotalConjectureCorrectModels'] += 1     
                            if scoreValue >= 0:
                                modelECdict['multScoreConjectureCorrectModels'] *= posScoreValue

                        else:
                            modelECdict['sumScoreConjectureWrongModels'] += posScoreValue
                            evalConj['sumScoreTotalConjectureWrongModels'] += posScoreValue
                            modelECdict['nConjecturesWrongModels'] += 1
                            evalConj['nTotalConjectureWrongModels'] += 1
                            if scoreValue >= 0:
                                modelECdict['multScoreConjectureWrongModels'] *= posScoreValue
                            
                            

                    #++++++++++++++++++++++++++++++++++++++
    
                except KeyboardInterrupt:
                    print("Keyboard interrupt requested...exiting")
                    raise
                except:
                    exceptionText = traceback.format_exc()
                    logger.LogError('\nEvaluate Conjecture failed: "'+mDict['mbsModelNameID']
                                    +f'", ID {mbsModelCnt}/{numberOfMBSmodelsLoaded}'
                                    +f', RID{randomIDstr}'*bool(randomIDstr)
                                    +f': {exceptionText}')

            #finalize score for single model (how good did the prediction work?)
            modelECdict['scoreConjectureCorrectModels'] = modelECdict['sumScoreConjectureCorrectModels']/max(1,modelECdict['nConjecturesCorrectModels'])
            modelECdict['scoreConjectureWrongModels'] = modelECdict['sumScoreConjectureWrongModels']/max(1,modelECdict['nConjecturesWrongModels'])


            if modelECdict['nConjecturesCorrectModels'] > 0:
                modelECdict['multScoreConjectureCorrectModels'] = modelECdict['multScoreConjectureCorrectModels']**(1/modelECdict['nConjecturesCorrectModels'])
                evalConj['sumMultScoreTotalConjectureCorrectModels'] += modelECdict['multScoreConjectureCorrectModels']
                evalConj['nTotalMultConjectureCorrectModels'] += 1
            else:
                modelECdict['multScoreConjectureCorrectModels'] = -1

            if modelECdict['nConjecturesWrongModels'] > 0:
                modelECdict['multScoreConjectureWrongModels'] = modelECdict['multScoreConjectureWrongModels']**(1/modelECdict['nConjecturesWrongModels'])
                evalConj['sumMultScoreTotalConjectureWrongModels'] += modelECdict['multScoreConjectureWrongModels']
                evalConj['nTotalMultConjectureWrongModels'] += 1
            else:
                modelECdict['multScoreConjectureWrongModels'] = -1

            logger.LogText(f"\nEvaluation summary for {currentMBSmodelNameID}"+strUseWrongModels+":\n"
                            +f"  scoreConjectureCorrectModels={round(modelECdict['scoreConjectureCorrectModels'],5)}," 
                            +f"  scoreConjectureWrongModels={round(modelECdict['scoreConjectureWrongModels'],5)}\n"
                            +f"  multScoreConjectureCorrectModels={round(modelECdict['multScoreConjectureCorrectModels'],5)}," 
                            +f"  multScoreConjectureWrongModels={round(modelECdict['multScoreConjectureWrongModels'],5)}\n",
                            printToConsole=True, quickinfo=True,
                            )


        #finalize scores for all models:
        evalConj['totalScoreConjectureCorrectModels']= evalConj['sumScoreTotalConjectureCorrectModels']/max(1,evalConj['nTotalConjectureCorrectModels'])
        evalConj['totalScoreConjectureWrongModels']= evalConj['sumScoreTotalConjectureWrongModels']/max(1,evalConj['nTotalConjectureWrongModels'])

        evalConj['totalMultScoreConjectureCorrectModels']= evalConj['sumMultScoreTotalConjectureCorrectModels']/max(1,evalConj['nTotalMultConjectureCorrectModels'])
        evalConj['totalMultScoreConjectureWrongModels']= evalConj['sumMultScoreTotalConjectureWrongModels']/max(1,evalConj['nTotalMultConjectureWrongModels'])


        #statistics
        evalConj['numberOfRemovedTokensGlobal'] += self.llmModel.numberOfRemovedTokensGlobal
        evalConj['numberOfTokensGlobal'] += self.llmModel.numberOfTokensGlobal
        
        evalConj['runTime'] = time.time() - tStart #update in every iteration

        evalConj['loggerErrors'] = logger.errorCount
        evalConj['loggerWarnings'] = logger.warningCount

        evalConj['llmConfig'] = GetScalarClassObjectsDict(self.llmModel)
        evalConj['agentConfig'] = GetScalarClassObjectsDict(self)

        logger.PrintAndLogCounters()

        logger.PrintScalarQuantities(title='Summary of EvaluateAllConjectures'+strUseWrongModels,
                                     dataDict=evalConj, separator=True)

        #do not collect all data (total counters, etc.)
        try:
            listRetrievers = ['numberOfTokensGlobal','numberOfRemovedTokensGlobal','runTime',
                              'loggerErrors','loggerWarnings']
            for item in listRetrievers:
                rr[item] = 0

            listDicts = ['genMC', 'genExu', 'evalConj', 'evalConj_WM']
            for dStr in listDicts:
                if dStr in rr:
                    d = rr[dStr]
                    for item in listRetrievers:
                        if item in d:
                            rr[item] += d[item]

        except:
            exceptionText = traceback.format_exc()
            logger.LogError(f'Something went wrong when merging all counters and timers: {exceptionText}')

        return rr


#%%+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
#helper function to write latex table of final results
def WriteAgentResults2LatexTable(filePath, finalResultsAllModels):
    nDigits = 2
    #keys=columns selected; value=column heading
    names2text = {
        'runTimeAll':r'eval.\ run time (min)', #for correct and wrong models
        'numberOfTokensGlobal':r'k-tokens generated',# ($\times$1000)
        'tokensPerSecond':'tokens per second',
        #'correctScore':'correct score%', #same for all models!
        #'executableScore':'executable score%',
        'totalScoreConjectureCorrectModels':'correct cases score',
        'nFailsThreshold':'fails threshold',
        'F1correctModels':r'{\bf F1-score}',
        'FPR':r'{\bf FPR}',
        'TPR':r'{\bf TPR}',
        'scoreCorrect':'TP',
        'scoreWrong':'FN',
        'scoreCorrect_WM':'FP',
        'scoreWrong_WM':r'TN',
        'scoreInvalidAll':'non-decidable',
        }

    
    headerList = []
    #create header list
    for key, latexName in names2text.items():
        headerList.append(r'\rotatebox{90}{'+latexName.replace('%','')+'}')

    latexCode = []

    numColumns = len(names2text)
    columnDef = r"p{2.63cm}" + r"|p{0.55cm}|p{0.36cm}|p{0.42cm}||p{0.42cm}|p{0.16cm}|p{0.42cm}|p{0.42cm}|p{0.42cm}" + r"|p{0.2cm}"*(numColumns-8)
    latexCode.append(r"\begin{tabular}{" + columnDef + "}")
    latexCode.append(r"\toprule")
    latexCode.append("LLM name & " + " & ".join(headerList) + r" \\")
    latexCode.append(r"\hline")

    #++++++++++++++++++++++++
    #colored cells
    bestCellColor = r"\cellcolor{green!20}" #

    highlightColumns={
        'runTimeAll':-1,#small is good
        'F1correctModels':1, #large is good
        'tokensPerSecond':1,
        'totalScoreConjectureCorrectModels':1,
        'FNR':-1,
        'FPR':-1,
        'TPR':1,
        # 'scoreCorrect':1,
        # 'scoreWrong':-1,
        # 'scoreCorrect_WM':-1,
        }

    bestIndicesValues = {}
    for key, latexName in names2text.items(): 
        bestIndicesValues[key]=0 if (key in highlightColumns and highlightColumns[key]>0) else 1e10


    for llmName, finalResults in finalResultsAllModels.items():
        if 'qwq' in llmName.lower(): continue

        for key, latexName in names2text.items():
            value = finalResults[key]
            if key in highlightColumns:
                value = finalResults[key]

                if highlightColumns[key] < 0 and value < bestIndicesValues[key]:
                    bestIndicesValues[key] = value
                elif highlightColumns[key] > 0 and value > bestIndicesValues[key]:
                    bestIndicesValues[key] = value
    #++++++++++++++++++++++++



    for llmName, finalResults in finalResultsAllModels.items():
        if 'qwq' in llmName.lower(): continue

        row = llmName
        for key, latexName in names2text.items():
            value = finalResults[key]
            isBest = (bestIndicesValues[key] == value and key in highlightColumns)
            if 'run time' in latexName:
                valueStr = str(int(round(value/60,0))) if value/60 < 1000 else str(int(value/60))
            elif 'tokens generated' in latexName:
                valueStr = str(int(round(value/1024)))
            elif 'tokens per second' in latexName:
                valueStr = str(int(round(value,0)))
            elif '%' in latexName:
                valueStr = str(round(value*100,1))+r'\%'
            else:
                valueStr = str(round(value,nDigits))
            row += " & " + bestCellColor*isBest + valueStr
        latexCode.append(row + r" \\")

    latexCode.append(r"\hline")
    latexCode.append(r"\end{tabular}")

    with open(filePath, "w") as f:
        f.write("\n".join(latexCode))

    print(f"Agent results written to LaTeX table: {filePath}")


#merge tests from directory; use all subdirs starting with "log_"
#in each subdir, "results.json" is evaluated
#write output to resultsFileName
def MergeConjecturesResults(dirTestModels, resultsFileName="agentResults.csv", 
                            useMultScore=False, useTwoFailsScore=False, writeLatexResults=False):
    #%%++++++++++++++++++++++++++++
    from utilities import ReadJSONToDict
    import os
    
    print('Merge results.json from directory "'+dirTestModels+'"')
    log_dirs = [d for d in os.listdir(dirTestModels) if d.startswith("log_") and os.path.isdir(JoinPath(dirTestModels, d))]
    print(f'useMultScore={useMultScore}')
    print(f'useTwoFailsScore={useTwoFailsScore}')
    # Read 'results.json' from each valid subdirectory
    resultsData = {}
    
    for log_dir in log_dirs:
        shortName = log_dir[4:]
        json_path = JoinPath(dirTestModels, log_dir, "results.json") #this is the final file and it must exist!
        
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
        
        #unique function for binary score computation
        def Score2Binary(scoreValue):
            return 1 if scoreValue > 0.5 else 0
            
        minConjectures = 5  #final:5 minimum number of conjectures required
        

        excludedEvalMethods = [] 



        firstData = list(resultsData.keys())[0]

        maxDifficultyLevel = resultsData[firstData]['maxDifficultyLevel']
        numberOfConjecturesPerModel = resultsData[firstData]['numberOfConjecturesPerModel']
        numberOfRandomizations = resultsData[firstData]['numberOfRandomizations']

        finalResultsAllModels = {} #results then used for latex tables

        mbsModelsList = []
        for key, value in resultsData.items():
            if maxDifficultyLevel != resultsData[firstData]['maxDifficultyLevel']:
                print('WARNING: '+key+' has different maxDifficultyLevel: '+str(maxDifficultyLevel))
            if numberOfRandomizations != resultsData[firstData]['numberOfRandomizations']:
                print('WARNING: '+key+' has different numberOfRandomizations: '+str(numberOfRandomizations))
            if numberOfConjecturesPerModel != resultsData[firstData]['numberOfConjecturesPerModel']:
                print('WARNING: '+key+' has different numberOfConjecturesPerModel: '+str(numberOfConjecturesPerModel))
            for item in resultsData[key]['mbsModelNamesLoaded']:
                if item not in mbsModelsList:
                    mbsModelsList.append(item)
                    
        #print('mbsModelsList:',mbsModelsList)

        mbsModelsListPrint = []
        key2ind = {}
        for i in range(len(mbsModelsList)):
            key2ind[mbsModelsList[i]] = i
            mbsModelsListPrint.append(AddSpacesToCamelCase(mbsModelsList[i]) )
            
        nMBSmodels = len(mbsModelsList)
            
        from time import gmtime, strftime
        strftime("%Y-%m-%d", gmtime())
        
        dateStr = datetime.date.today().strftime("%Y-%m-%d")
        timeStr = datetime.datetime.now().strftime("%H:%M:%S")
        header = ['AGENT EVALUATION report', dateStr, timeStr]
        columnNamesC = ['model name', 'date', 'time', 
                        '#Params (B)', 'VRAM (GB)', 'Quant.', 'maxCtx (k)', #max context size of model
                        'runtime (min)', 'tokens per second', 'nTokGen (k)', 'nTokRem (k)', 'nErrors',  #from rr
                        'MATH', 'IFEval', 'MMLU-Pro','GPQA']

        #E..Executable, C..Correct, EE..Executable Eval
        columnNamesEE = list(columnNamesC)      #executable during evaluation
        columnNamesCJ_C = list(columnNamesC)    #conjecture with correct models
        columnNamesCJ_W = list(columnNamesC)    #conjecture rate with wrong models (that should be correct)
        columnNamesCJ_WM = list(columnNamesC)    #conjecture rate with conjectures made with wrong models 

        columnNamesC += ['correct']+ ['']+ mbsModelsListPrint
        columnNamesEE += ['executable eval']+ ['']+ mbsModelsListPrint
        columnNamesCJ_C += ['conjectures score']+ ['erronously wrong']+ mbsModelsListPrint
        columnNamesCJ_W += ['conjectures score']+ ['']+ mbsModelsListPrint
        columnNamesCJ_WM += ['conjectures score']+ ['erronously correct']+ mbsModelsListPrint

        #multStr = 'mult'*useMultScore
        multScoreStr = 'multScore' if useMultScore else 'score'
        multStrUC = 'Mult'*useMultScore
        multStr2 = ' (mult)'*useMultScore
        
        multScoreStr = 'twoFailsScore' if useTwoFailsScore else 'score'
        multStrUC = 'TwoFails'*useTwoFailsScore
        multStr2 = ' (two fails score)'*useTwoFailsScore

        
        nRound = 3
        dataC = [header, 
                 ['Number of models:',nMBSmodels],
                 ['Max difficulty level:',maxDifficultyLevel],
                 ['Number of conjectures per model:',numberOfConjecturesPerModel],
                 ['Number of randomizations:',numberOfRandomizations],
                 ['Correct score:'], columnNamesC]
        dataEE = [[''],['Exec eval score:'], columnNamesEE]
        dataCJ_C = [[''],['Conjectures correct models score'+multStr2+':'], columnNamesCJ_C]
        dataCJ_W = [[''],['Conjectures incorrect models score'+multStr2+':'], columnNamesCJ_W]
        dataCJ_WM= [[''],['Conjectures from wrong models score'+multStr2+':'], columnNamesCJ_WM]
        
        addConjectures_CW = False

        totalErronouslyWrongCount = {}
        totalErronouslyCorrectCount = {}

        totalCorrectCount = {}
        totalWrongCount = {}

        for key, value in resultsData.items():
            nFailsThreshold = 1 #
            if ('GPT-4o' in key 
                or 'Llama3.1-70B-HF' in key 
                or 'QwenCoder' in key 
                or 'QwenQwQ' in key): 
                nFailsThreshold = 2

            
            totalErronouslyWrongCount[key] = 0
            totalErronouslyCorrectCount[key] = 0
            totalCorrectCount[key] = 0
            totalWrongCount[key] = 0

            try:
                print('\n*************\nLLM MODEL='+key)
                llmFullName = GetLLMmodelNameFormShortName(key)
                llmData = llmModelsDict[llmFullName]
                genExu = value['genExu']
                evalConj = value['evalConj']
                hasWC = False
                evalConjList = [evalConj]
                if 'evalConj_WM' in value:
                    evalConj_WM = value['evalConj_WM']
                    evalConjList.append(evalConj_WM)
                    hasWC = True
                else: evalConj_WM = evalConj

                #+++++++++++++++++++++++++++++++++++++++++++++++++++
                #for Latex:
                finalResults = {}
                finalResultsAllModels[key] = finalResults
                
                #--- these times and counters are only for Evaluate Conjectures (EC) part:
                finalResults['runTime'] = evalConj['runTime']
                if hasWC:
                    finalResults['runTimeAll'] = evalConj['runTime'] + evalConj_WM['runTime']

                finalResults['numberOfTokensGlobal'] = evalConj['numberOfTokensGlobal']
                #finalResults['tokens removed'] = evalConj['numberOfRemovedTokensGlobal']
                finalResults['tokensPerSecond'] = evalConj['numberOfTokensGlobal'] / max(0.1,finalResults['runTime'])
                #---
                totalModels = value['numberOfModelCreationTasks']
                nTotalAvailableEvalModels = genExu['nTotalAvailableEvalModels']     #==available conjectures after MC
                nTotalAvailableConjectures = genExu['nTotalAvailableConjectures']   #available conjectures after GE
                nTotalExecutable = genExu['nTotalExecutable']
                nTotalExecutableEval = genExu['nTotalExecutableEval']
                nTotalCorrect = genExu['nTotalCorrect']
                correctness = nTotalCorrect/max(1,nTotalAvailableEvalModels)

                finalResults['correctScore'] = correctness
                finalResults['executableScore'] = nTotalExecutable/max(1,nTotalAvailableEvalModels)
                finalResults['nFailsThreshold'] = nFailsThreshold

                #finalResults['xx'] = evalConj['xx']
                
                #+++++++++++++++++++++++++++++++++++++++++++++++++++



                #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
                #use dict d to count methods "method". if method does not exist, add it to dict d
                def IncDict(d, method):
                    if method not in d:
                        d[method] = 1
                    else:
                        d[method] += 1
                        
                methodsCorrectCount = [{}, {}]
                methodsWrongCount = [{}, {}]
                #compute values
                #loop over all models:
                for storeCnt, evalConjStore in enumerate(evalConjList):
                    valTotalCorrect = 0
                    valTotalWrong = 0 
                    nTotalCorrect = 0
                    nTotalWrong = 0 
                    nTotalInvalid = 0 

                    for keyModel, valueModel in evalConjStore['allModelsResultsDicts'].items():
                        # print('model=',keyModel)
                        valCorrect = 0
                        valWrong = 0 
                        nCorrectCount = 0
                        nWrongCount = 0
                        
                        conjecturesInfo = value['allMbsModelsDict'][keyModel]['conjectures']
                        for conjecture in valueModel["conjecturesEvaluated"]:
                            currentMBSmodelNameIDcID = conjecture['currentMBSmodelNameIDcID']
                            cID = int(currentMBSmodelNameIDcID.split('c')[-1])
                            method = conjecturesInfo[cID]['evaluationMethod']
                            if conjecture["modelIsCorrect"]:
                                if conjecture["scoreValue"] >= 0:
                                    if method not in excludedEvalMethods:
                                        valCorrect += Score2Binary(conjecture["scoreValue"])
                                        nCorrectCount += 1
                                    
                                    if not Score2Binary(conjecture["scoreValue"])-storeCnt: 
                                        IncDict(methodsCorrectCount[storeCnt], method)
                                        
                            else:
                                if conjecture["scoreValue"] >= 0:
                                    if method not in excludedEvalMethods:
                                        valWrong += Score2Binary(conjecture["scoreValue"])
                                        nWrongCount += 1
                                    if Score2Binary(conjecture["scoreValue"])-storeCnt: IncDict(methodsWrongCount[storeCnt], method)

                        #require 3 correct results; 1 evaluation may have failed
                        if nCorrectCount < minConjectures: 
                            valCorrect = -1
                        else: 
                            valCorrect = valCorrect/nCorrectCount if nCorrectCount-valCorrect < nFailsThreshold else 0
                        if nWrongCount < minConjectures: 
                            valWrong = -1
                        else: 
                            valWrong = valWrong/nWrongCount if nWrongCount-valWrong < nFailsThreshold else 0

                        if valCorrect > 0:
                            nTotalCorrect += 1
                            totalErronouslyCorrectCount[key] += storeCnt #only for wrong models
                        if valCorrect == 0:
                            nTotalWrong += 1
                            totalErronouslyWrongCount[key] += 1-storeCnt #only for correct models
                        if valCorrect < 0:
                            nTotalInvalid += 1

                        # print('  valCorrect=',valCorrect)
                        if useTwoFailsScore:
                            valueModel[multScoreStr+'ConjectureCorrectModels'] = valCorrect
                            valueModel[multScoreStr+'ConjectureWrongModels'] = valWrong

                        valTotalCorrect += max(0,valCorrect)
                        valTotalWrong += max(0,valWrong)

                    if useTwoFailsScore:
                        evalConjStore['total'+multStrUC+'ScoreConjectureCorrectModels'] = valTotalCorrect/nMBSmodels
                        evalConjStore['total'+multStrUC+'ScoreConjectureWrongModels'] = valTotalWrong/nMBSmodels


                    #print number how often methods leading to low score in correct models / high score in wrong models
                    if True:
                        print('============================')
                        print('  using '+'CORRECT'*(1-storeCnt)+'WRONG'*storeCnt+' models')
                        print('============================')
                        if storeCnt == 0:
                            print('totalErronouslyWrongCount=',totalErronouslyWrongCount[key])
                        else:
                            print('totalErronouslyCorrectCount=',totalErronouslyCorrectCount[key])

                        print(' - totalCorrectCount=',nTotalCorrect)
                        print(' - totalWrongCount=',nTotalWrong)
                        print(' - totalInvalidCount=',nTotalInvalid)

                    addStr = '_WM'*storeCnt
                    finalResults['totalCorrectCount'+addStr] = nTotalCorrect
                    finalResults['totalWrongCount'+addStr] = nTotalWrong
                    finalResults['totalInvalidCount'+addStr] = nTotalInvalid
                    finalResults['totalCount'+addStr] = nTotalCorrect+nTotalWrong+nTotalInvalid

                nModels2 = max(1,finalResults['totalCount'] + finalResults['totalCount_WM'])
                finalResults['scoreCorrect'] =  finalResults['totalCorrectCount'] #/ nModels2        #TP
                finalResults['scoreWrong'] =  finalResults['totalWrongCount'] #/ nModels2            #FN
                finalResults['scoreInvalid'] =  finalResults['totalInvalidCount'] #/ nModels2        #
                finalResults['scoreCorrect_WM'] =  finalResults['totalCorrectCount_WM'] #/ nModels2  #FP
                finalResults['scoreWrong_WM'] =  finalResults['totalWrongCount_WM'] #/ nModels2      #TN
                finalResults['scoreInvalid_WM'] =  finalResults['totalInvalidCount_WM'] #/ nModels2
                finalResults['scoreInvalidAll'] =  (finalResults['totalInvalidCount'] + finalResults['totalInvalidCount_WM']) #/ nModels2

                #additive score:
                finalResults['totalScoreConjectureCorrectModels'] = evalConj['totalScoreConjectureCorrectModels']

                TP = finalResults['scoreCorrect'] 
                FN = finalResults['scoreWrong']
                FP = finalResults['scoreCorrect_WM']
                TN = finalResults['scoreWrong_WM']
                Psum = TP+FN #all positives
                Nsum = FP+TN #all negatives
                #F1: 
                precision = TP / (TP + FP) 
                recall = TP / (TP + FN)
                finalResults['F1precision'] = precision
                finalResults['F1recall'] =  recall
                finalResults['F1correctModels'] =  2*TP / (2*TP + FP + FN) #=2*precision*recall / (precision + recall)
                finalResults['FNR'] =  FN / Psum 
                finalResults['FPR'] =  FP / Nsum 
                finalResults['TPR'] =  TP / Psum 
                print('precision=',precision)
                print('recall=',recall)
                print('F1correctModels=',finalResults['F1correctModels'])
                print('F1correctModels=',2*precision*recall / (precision + recall))
                            
                #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++



                numberOfTokensGlobal = 0 if 'numberOfTokensGlobal' not in value else value['numberOfTokensGlobal']
                numberOfRemovedTokensGlobal = 0 if 'numberOfRemovedTokensGlobal' not in value else value['numberOfRemovedTokensGlobal']
                llmDataDate = value['executionDateStr']
                llmDataTime = value['executionTimeStr']
                keyValues = [key, 
                        llmDataDate,llmDataTime,
                        NumToCSV(llmData['nParam']),NumToCSV(llmData['VRAM']), NumToCSV(llmData['Q']),NumToCSV(llmData['ctxSize']),
                        NumToCSV(value['runTime']/60,4), # for all 3 steps (MC, GE, EC)
                        NumToCSV(value['numberOfTokensGlobal'] / max(0.1,value['runTime']),3), # for all 3 steps (MC, GE, EC)
                        int(value['numberOfTokensGlobal']/1024), # for all 3 steps (MC, GE, EC)
                        int(value['numberOfRemovedTokensGlobal']/1024), # for all 3 steps (MC, GE, EC)
                        NumToCSV(value['loggerErrors'],2),
                        NumToCSV(llmData['MATH']/100.,2), NumToCSV(llmData['IFEval']/100.,2), 
                        NumToCSV(llmData['MMLU-Pro']/100.,2),NumToCSV(llmData['GPQA']/100.,2),
                        ]

                if 'totalScoreCorrect' not in genExu:
                    genExu['totalScoreCorrect'] = 0
                    genExu['totalScoreExecutableEval'] = 0

                resultRows = [{'baseData':genExu, 'total':'totalScoreCorrect', 'value':'scoreCorrect', 'valueStore':genExu['resultsDicts']},
                              {'baseData':genExu, 'total':'totalScoreExecutableEval', 'value':'scoreExecutableEval', 'valueStore':genExu['resultsDicts']},
                              {'baseData':evalConj, 'total':'total'+multStrUC+'ScoreConjectureCorrectModels', 'value':multScoreStr+'ConjectureCorrectModels', 'valueStore':evalConj['allModelsResultsDicts']},
                              {'baseData':evalConj, 'total':'total'+multStrUC+'ScoreConjectureWrongModels', 'value':multScoreStr+'ConjectureWrongModels', 'valueStore':evalConj['allModelsResultsDicts']},
                              ]
                if hasWC:
                    resultRows += [{'baseData':evalConj_WM, 'total':'total'+multStrUC+'ScoreConjectureCorrectModels', 'value':multScoreStr+'ConjectureCorrectModels', 'valueStore':evalConj_WM['allModelsResultsDicts'],'WM':True}]
    
                for item in resultRows:
                    item['row'] = keyValues + [NumToCSV(item['baseData'][item['total']],nRound)]
                    if 'ScoreConjectureCorrectModels' in item['total']:
                        if 'WM' not in item:
                            item['row'] += [totalErronouslyWrongCount[key]]
                        else:
                            item['row'] += [totalErronouslyCorrectCount[key]]
                    else:
                        item['row'] += ['']
                    item['results'] = np.zeros(nMBSmodels).tolist()
                    item['resultsCnt'] = np.zeros(nMBSmodels).tolist()

                    for key1, value1 in item['valueStore'].items(): #run over all evaluated models with IDs
                        mbsName = RemoveTrailingDigits(key1)
                        if mbsName in key2ind:
                            ind = key2ind[mbsName]
                            item['resultsCnt'][ind] += 1
                            item['results'][ind] += value1[item['value']]
                        else:
                            print('WARNING: key '+mbsName+' not in mbsModelsList')
                    for i, cnt in enumerate(item['resultsCnt']):
                        item['results'][i] = NumToCSV(item['results'][i]/max(1,cnt),nRound)
                    item['row'] += item['results']
                    
                    #=> now item['row'] can be exported to Excel

    
                dataC.append(resultRows[0]['row'])
                # dataE.append(rowE)
                dataEE.append(resultRows[1]['row'])
                dataCJ_C.append(resultRows[2]['row'])
                dataCJ_W.append(resultRows[3]['row'])
                if hasWC: 
                    dataCJ_WM.append(resultRows[4]['row'])
                    
            except:
                exceptionText = traceback.format_exc()
                print('ERROR in Merge: could not process data from llm '+key+'\ntraceback=',exceptionText)


        # Define the CSV file name
        csv_filename = JoinPath(dirTestModels, resultsFileName)
        
        print(finalResultsAllModels)
        if writeLatexResults:
            WriteAgentResults2LatexTable('../../01_paper/agentResults.tex', finalResultsAllModels)
        
        # print('addConjectures_CW:',addConjectures_CW)
        # Write data to CSV file
        with open(csv_filename, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file,delimiter=";")
            writer.writerows(dataC+dataEE
                             +dataCJ_C+dataCJ_W+dataCJ_WM
                             )  # Writes all rows from the list

#testing
if __name__ == '__main__':
    
    # llmModelName = 'Meta-Llama-3-8B-Instruct.Q4_0.gguf'
    llmModelName ='phi-4-Q4_0.gguf'
    
    logDir='logsAgent/test'
    skipModelConjLoop = True
    skipGenExudynLoop = True
    skipConjecturesLoop = False

    # mbsModelNames = ['nMassOscillatorFG']
    mbsModelNames = ['singleMassOscillatorF'] #, 'singleMassOscillatorFG']
    maxDifficultyLevel=5
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
    llmModel = MyLLM(modelName=llmModelName, 
                     logger=logger, 
                     device=device, 
                     contextWindowMaxSize = 1024*3, #2048 is exceeded in some Exudyn generation tasks
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

    if not skipModelConjLoop: #False: read data
        # Tests Exudyn simulation code generation for multiple models, writes files into directories
        rr = agent.GenerateModelsAndConjecturesLoop(
                                          numberOfConjecturesPerModel=1,
                                          numberOfRandomizations=1,
                                          generateWrongConjectures=False,
                                          )
    
        WriteDictToJSON(rr, JoinPath(logDir,'results_MC.json') )

    if not skipGenExudynLoop:
        rr = ReadJSONToDict(JoinPath(logDir,'results_MC.json') )
    
        rr = agent.GenerateExudynModelsAndEval(rr)

        WriteDictToJSON(rr, JoinPath(logDir,'results_GE.json') )
    
    if not skipConjecturesLoop:
        rr = ReadJSONToDict(JoinPath(logDir,'results_GE.json') )
    
        rr = agent.EvaluateAllConjectures(rr, evaluateWrongConjectures=False,
                                          useSimEvaluationOnly=True)

        WriteDictToJSON(rr, JoinPath(logDir,'results.json') )
    
    LogOverallCounter2File(filePath='_globalTokenCount.txt', deltaCounter=llmModel.numberOfTokensGlobal)

    llmModel.FreeMemory()
