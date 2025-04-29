# -*- coding: utf-8 -*-
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# This is part of the AI engineering lab project
#
# Filename: testModelCreationDriver.py
#
# Details:  This file uses the API from OpenAI to run judge on LLM conjectures with ChatGPT
#
# Authors:  Peter Manzl
# Date:     2025-03-15
# Notes:    Ensure that the appropriate model files are available locally or through the Hugging Face model hub.
#
# License:  BSD-3 license
#
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

import os
import sys
import time
import json
import copy
import datetime



# libraries for API calls
import openai
from openai import OpenAI
import backoff # to avoid rate limits of openAI api calls
from dotenv import load_dotenv
from utilities import ExtractXMLtaggedString

if __name__ == '__main__': 
    flagSaveAPICall = True # if False, API calls are not saved in between and only result is saved at the end. 
    logsDir = 'logsAgent/logsFinal_r2_c8'
    str_delimiter = '\n\n###############################\n'
    
    modelsResultDir = os.listdir(logsDir)
    iCalls = 0 
    iCallsModel = 0
    iCallsMax = 1000 # 960 calls expected
    modelAPI_name = 'gpt-4o' # 'gpt-4.1-nano-2025-04-14' could also be used for faster experiments
    # at time of experiments, snapshot "gpt-4o-2024-08-06" was used
    
    
    now = datetime.datetime.now()
    date_time_str = now.strftime("%y%m%d_%H_%M_%S")
    
    
    # load OpenAI API key from environment 
    # this API key is generated at https://platform.openai.com/api-keys  and saved in the .env file
    flag_env = load_dotenv("openai_api_key.env")
    if not(flag_env): 
        print('Warning: api key could not be loaded.')
        
    client = OpenAI(
        api_key= os.environ.get("OPENAI_API_KEY", None),
    )
    
    
    def addToLogFile(filename, APIResponse, dictResults): 
        try: 
            with open(filename, "a") as api_file:
                api_file.write(str_delimiter)
                api_file.write(str(dictResults['currentMBSmodelNameIDcID']) + '\n')
                api_file.write('API response: \n')
                api_file.write(str(APIResponse) + '\n'*2)
                api_file.write(str(dictResults))
                # could be read (if neccessary) using e.g. ast.literal_eval in case something goes wrong
        except: 
            print('file could not be written!')
        return
    
    
    def writeResultsGPT(resultsFileWrite, resultsRunGPT): 
        with open(resultsFileWrite, 'w') as file: 
            json.dump(resultsRunGPT, file, indent=2, sort_keys=True)
            
    def callGPTAPI(dictConjecture, gptModel = None): 
        # 
        dictConjectureNew = copy.deepcopy(dictConjecture)
        if gptModel is None:  # for Testing
            dictConjectureNew['conjLLMresponse'] = 'None'
            dictConjectureNew['scoreValue'] = str(-100)
            # add to logfile
            return dictConjectureNew , {'usage': {'prompt_tokens': 0}}
        
        # this is only to avoid doing inference with other models which might be expensive
        # otherwise the api client will anyway return an error. 
        if gptModel not in ['gpt-4.1-nano-2025-04-14', 'gpt-4.1-nano', 'gpt-4o', 
                            'gpt-4o-2024-11-20', 'gpt-4o-2024-05-13', 'gpt-4o-2024-08-06']: 
            raise ValueError("model " + str(gptModel) + 'not in list of models. ')
        strSystemContent = ''# could give a system prompt  
        response = client.chat.completions.create(
          model=gptModel,
          messages=[
            {"role": "system", "content": strSystemContent},
            {"role": "user", "content": dictConjecture['conjPrompt']}
          ], 
          store=False, 
        )  
        
        # print(response.choices[0].message.content) # uncomment to show response
        responseDict = response.to_dict(mode='json')
    
        # get response from API; might not be in coices[0] according to documentation, but always was in the experiments
        dictConjectureNew['conjLLMresponse'] = response.choices[0].message.content 
        try: 
            # extract score from tag XML tag <score>
            score = float(ExtractXMLtaggedString(dictConjectureNew['conjLLMresponse'], 'score')['text']) / 100 
        except: 
            # warning if no score is extracted
            score = -1
            print('WARNING: XML string could not be exctracted, model might not given correct values.')
            
        dictConjectureNew['scoreValue'] = score 
        return dictConjectureNew, responseDict
    
    
    
    
    
    
    apiResponseList = []
    iModel = 0 # could loop over multiple model outputs
    LLMmodel = 'log_Phi4-Q4'
    # repeat evaluation which was previously done with Phi4-Q4 --> quantizisesd to 4 bit
    dt_total, nTokensTotal = 0, 0
    # apiResponseDict = {}
    if modelAPI_name == None or 'GPT-4o'.lower() in modelAPI_name.lower() : 
        LLMmodelPath = 'log_GPT-4o'
    elif 'gpt-4.1-nano'.lower() in modelAPI_name.lower(): 
        LLMmodelPath='log_gpt-4-1-nano'
    else: 
        # if using a different model create according alias for directory
        raise ValueError()
    
    # read from path */log_Phi-4-Q4, write to *GPT-4o 
    resultsFileRead = '{}/{}/results.json'.format(logsDir, LLMmodel) 
    resultsFileWrite = '{}/{}/results.json'.format(logsDir, LLMmodelPath)
    dirWrite = resultsFileWrite.split('results')[0]
    
    # save API calls in seperate file with curent timestamp
    gptResultsFile = dirWrite + "{}_GPT_APICalls".format(date_time_str) 
    if modelAPI_name is None: 
        gptResultsFile += '_Test'
    gptResultsFile += '.txt'
    
    apiResponseList += [[]] 
    
    with open(resultsFileRead, 'r') as file:
        results_run = json.load(file)
        resultsRunGPT = copy.deepcopy(results_run)
    os.makedirs(dirWrite, exist_ok = True)
    
    
    resultsRunGPT['openai_API'] = {'backend': 'openai', 
                                   'model': str(modelAPI_name), 
                                   'dt_total': 0,
                                    'nTokensTotal': 0,}
    
    inp_data = input('Running {} on results from {}. Resume (y/n): '.format(modelAPI_name, resultsFileRead))
    if not(inp_data.lower() == 'y'):
        print('canceled')
        sys.exit()
        
        
    for runType in ['evalConj', 'evalConj_WM']: 
        resultsRunGPT[runType]['numberOfTokensGlobal'] = 0
        resultsRunGPT[runType]['runTime'] = 0
        resultsRunGPT[runType]['tokens_per_second'] = 0
        for mbdModel in results_run[runType]['allModelsResultsDicts'].keys(): 
            # if not(mbdModel in ['rigidRotorUnbalanced0', 'sliderCrankRigidBodies1', 'elasticChain1']):
                # can be uncommented to only run specific models. 
                # continue 
            
            print('i=', iCalls, runType, '- model: ', mbdModel, ': {} Tokens / {}s / {}Tps'.format(
                resultsRunGPT[runType]['numberOfTokensGlobal'], resultsRunGPT[runType]['runTime'],resultsRunGPT[runType]['tokens_per_second'] ) )
            nConjectures = len(results_run[runType]['allModelsResultsDicts'][mbdModel]['conjecturesEvaluated'])
            iConj = []
            for i in range(nConjectures): 
                t1 = time.time() # get time for measuring tokens per second
                results_run[runType]['allModelsResultsDicts'][mbdModel]['conjecturesEvaluated'][i]
                dictConjecture = results_run[runType]['allModelsResultsDicts'][mbdModel]['conjecturesEvaluated'][i]
                
                # for some models the key conjPrompt might not exist
                if not('conjPrompt' in dictConjecture):
                    print('skip: no conjecture prompt available for ', mbdModel, ' conjecture ', dictConjecture['cID'])
                    continue
                
                
                # call API
                dictResults, APIResponseDict = callGPTAPI(dictConjecture, gptModel=modelAPI_name)
                apiResponseList[iModel] += [APIResponseDict] # append response to list for saving/debugging
    
                nTokens = APIResponseDict['usage']['prompt_tokens']
                dt = time.time() - t1
                
                resultsRunGPT['openai_API']['tokens_per_second'] = resultsRunGPT['openai_API']['nTokensTotal'] / (resultsRunGPT['openai_API']['dt_total']+1e-16)
                TPS_current = nTokens / (dt + 1e-16) # 1e-16: eps to avoid div0
    
                # write intermediate results to textfile
                if flagSaveAPICall: 
                    addToLogFile(gptResultsFile, APIResponseDict, dictResults)
                        
                # write data to dict for saving
                resultsRunGPT[runType]['allModelsResultsDicts'][mbdModel]['conjecturesEvaluated'][i] = dictResults
                resultsRunGPT[runType]['allModelsResultsDicts'][mbdModel]['conjecturesEvaluated'][i]['generatedTokens'] = nTokens
                resultsRunGPT[runType]['allModelsResultsDicts'][mbdModel]['conjecturesEvaluated'][i]['runTime'] = dt
                resultsRunGPT[runType]['allModelsResultsDicts'][mbdModel]['conjecturesEvaluated'][i]['tokens_per_second'] = TPS_current
                
                
                # write global statistics
                resultsRunGPT['openai_API']['dt_total'] += dt
                resultsRunGPT['openai_API']['nTokensTotal'] += nTokens
                resultsRunGPT[runType]['numberOfTokensGlobal'] += nTokens
                resultsRunGPT[runType]['runTime'] += dt
                resultsRunGPT[runType]['tokens_per_second'] = resultsRunGPT[runType]['numberOfTokensGlobal'] / ( resultsRunGPT[runType]['runTime'] + 1e-16)
                
                iConj += [ dictConjecture['cID']]
                iCalls += 1
                iCallsModel += 1 # only needed if running on several models
    
                if iCalls >= iCallsMax: 
                    writeResultsGPT(resultsFileWrite, resultsRunGPT)
                    print('stop after {} API calls'.format(iCallsMax))
                    sys.exit()
            print('conjectures: ', iConj)
    writeResultsGPT(resultsFileWrite, resultsRunGPT)
    
    print('finished with a total of {} API calls.'.format(iCalls))
                    