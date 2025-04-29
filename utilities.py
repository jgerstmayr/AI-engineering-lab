# -*- coding: utf-8 -*-
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# This is part of the AI engineering lab project
#
# Filename: utilities.py
#
# Details:  Basic support functions for LLM-agents, and further functionalities of the LLM Lab.
#           Mainly processing text, numbers, extraction of xml-tags, logging helpers, file/json read/write, camelCase processing, latex export, ...
#
# Author:   Tobias Möltner and Johannes Gerstmayr
# Date:     2025-03-11
#
# License:  BSD-3 license
#
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

import os
import time
import shutil
import json
import re
import ast
import textwrap
import traceback
import numpy as np

#check if is scalar
def IsScalar(x):
    if isinstance(x, (np.floating, float)) or isinstance(x, (np.integer, int)): 
        return True
    else:
        return False

#check if is scalar
def IsScalarOrComplex(x):
    if (isinstance(x, (np.floating, float)) 
        or isinstance(x, (np.integer, int))
        or isinstance(x, (np.complex128, complex))
        ): 
        return True
    else:
        return False

#check if is scalar
def IsIntType(x):
    if isinstance(x, (np.integer, int)): 
        return True
    else:
        return False

#check if is scalar
def IsBool(x):
    if isinstance(x, (bool, np.bool_)):
        return True
    else:
        return False

#check if x is any list or array (any dimension)
def IsListOrArray(x):
    if type(x) != list and type(x) != np.ndarray:
        return False
    return True

# Dynamically round a number based on its magnitude.
# NOTE: this does not work with larger numbers!
def DynamicRound(x, nDigits=1):

    if x == 0:
        return 0
    
    magnitude = np.abs(x)
    decimal_places = int(np.floor(np.log10(magnitude))) + 1 - nDigits
    
    if decimal_places < 0:
        return np.round(x*(10**(-decimal_places)), 0) / (10**(-decimal_places))
    else:
        return (10**decimal_places)*np.round(x/(10**decimal_places), 0)
    
# Apply dynamic round to all types: text, bool, scalar, list, n-dim numpy arrays
# convert all numpy arrays to list of lists
def DynamicRoundAll(x, nDigits=1):
    if (type(x) == list or
        (type(x) == np.ndarray) ):
        rv = []
        for item in x:
            rv.append(DynamicRoundAll(item, nDigits))
        return rv
    elif IsBool(x) or type(x) == str:
        return x
    elif IsScalarOrComplex(x):
        return DynamicRound(x, nDigits)
    
    raise ValueError('DynamicRoundArray: illegal value:"'+str(x)+'"')
    return None

#remove trailing digits in string (convert model with numbers to model names)
def RemoveTrailingDigits(s):
    while s and s[-1].isdigit():
        s = s[:-1]
    return s

#convert number to string for better readability in Excel; round to nDigits
def NumToCSV(value, nDigits=None):
    if round is None:
        return str(value).replace('.',',')
    else:
        return str(round(value,nDigits)).replace('.',',')
    return 
    
#convert any int, float, list of float, etc. to readable text
#use dynamic rounding
def ConvertValueArray2Text(x, nDigits):
    return str(DynamicRoundAll(x, nDigits))

# Resamples the input and output arrays to a reduced size while preserving trends.    
def ResampleInOutData(ins, outs, targetSize = 10):

    originalSize = len(ins)

    # Ensure target_size does not exceed the original size
    targetSize = min(targetSize, originalSize)
    
    # Determine the step size for resampling
    step = max(originalSize // targetSize, 1)
    
    # Downsample inputs and outputs using the determined step
    resampledInputs = ins[::step][:targetSize]
    resampledOutputs = outs[::step][:targetSize]

    return resampledInputs, resampledOutputs

# Resamples the data
def ResampleData(data, nResampleSize):

    originalSize = len(data)

    # Ensure target_size does not exceed the original size
    nResampleSize = max(min(nResampleSize-1, originalSize),1)
    
    # Determine the step size for resampling
    step = max(originalSize // nResampleSize, 1)
    
    # Downsample inputs and outputs using the determined step
    resampledData = data[::step][:nResampleSize]
    resampledData = np.vstack((resampledData,data[-1]))
    #print('resampledData.shape:', resampledData.shape, ', data.shape:', data.shape)

    return resampledData


#%%+++++++++++++++++++++++++++++++++++++++++++++++++++
#take output for a specific method and convert it to plain text
#return dict with information and text
#used for system analysis or sensor-based-functions
def ConvertResultsToPlainText(output, functionName, nDigits=3):
    result = {'text':'', 'error':True, 'warning':''}
    notes = ''
    notesBodies = 'System message: Note that a point mass always has 3 DOF and a rigid body has 6 DOF, as point masses and rigid bodies are always modelled in 3D.'
    notesBodiesEP = ' Rigid bodies are modelled with Euler-Parameters, thus having 7 coordinates and 1 additional constraint.'
    notesConstraints = 'System message: Note that spring-dampers impose no constraints, as they are elastic.'
    notesEigenvalues = ' (equivalent to the number of eigenvalues).'    
    
    if 'ComputeODE2Eigenvalues' in functionName:
        if type(output) != list or len(output) != 2:
            result['text'] = 'ConvertResultsToPlainText: output for "'+functionName+'" is no valid list!'
            return result
        else:
            if 'computeComplexEigenvalues=True' not in functionName:
                if len(output[0]) <= 12:
                    output = {'eigenFrequenciesInHz':np.sqrt(output[0])/(2*np.pi),
                              'numberOfEigenvalues':len(output[0])}
                else:
                    output = {'first12EigenfrequenciesInHz':np.sqrt(output[0][:12])/(2*np.pi),
                              'totalNumberOfEigenvalues':len(output[0])}
            else:
                if len(output[0]) <= 12:
                    output = {'complexEigenvalues':output[0],
                              'numberOfEigenvalues':len(output[0])}
                else:
                    output = {'first12ComplexEigenvalues':output[0][:12],
                              'totalNumberOfEigenvalues':len(output[0])}
                
            notes = notesBodies[:-1]+notesEigenvalues+'\n'+notesConstraints
    
    if type(output) != dict:
        result['text'] = 'ConvertResultsToPlainText: output for "'+functionName+'" is no valid dictionary'
        return result

    result['error'] = False
    if 'success' in output and not output['success']:
        # result['error'] = not output['success']
        result['warning'] = 'ConvertResultsToPlainText: method "'+functionName+'" returned success=False'
        result['text'] = result['warning']
        result['text'] += '; this indicates that sensor results are singular or not appropriate for this method.'
        return result
    
    if functionName == 'mbs.ComputeSystemDegreeOfFreedom(verbose=False)': #constraints
        output = {'numberOfConstraints':output['nAE'],
                  'numberOfRedundantConstraints':output['redundantConstraints'],
                  'degreeOfFreedom':output['degreeOfFreedom'],
                  'numberOfSystemCoordinates':output['nODE2'],
                  }
        notes = notesBodies+notesBodiesEP+'\n'+notesConstraints
    if functionName == 'mbs.ComputeSystemDegreeOfFreedom()': #DOF
        output = {'degreeOfFreedom':output['degreeOfFreedom']}
        notes = notesBodies+'\n'+notesConstraints

    for key, value in output.items():
        if key != 'success': #success not forwarded to LLM
            result['text'] += AddSpacesToCamelCase(key) + ' = '+ConvertValueArray2Text(value, nDigits)+'\n'
    result['text'] = result['text'].replace(' hz',' Hz')
    result['text'] += notes

    return result

#read Exudyn sensor data independently how it has been stored (internally or in files)
def GetSensorData(mbs, sensorNumber):
    #print('sensorNumber=',sensorNumber)
    if type(sensorNumber) == str:
        try:
            sensorNumber = mbs.GetSensorNumber(sensorNumber)
        except KeyboardInterrupt:
            print("Keyboard interrupt requested...exiting")
            raise
        except:
            raise ValueError('GetSensorData: received illegal sensor name:'+str(sensorNumber))

    if sensorNumber == -1:#invalid index
        raise ValueError('GetSensorData: received illegal sensor name:'+str(sensorNumber))

    if int(sensorNumber) >= mbs.systemData.NumberOfSensors():
        raise ValueError('GetSensorData: received illegal sensor number:'+
                         str(sensorNumber)+'; system has only '+
                         str(mbs.systemData.NumberOfSensors())+ ' sensors')
    #print('sensorNumber2=',sensorNumber)
    sensor = mbs.GetSensor(sensorNumber)
    if sensor['storeInternal']:
        return mbs.GetSensorStoredData(sensorNumber)
    elif sensor['writeToFile'] and sensor['fileName'] != '':
        #read data
        fileName=sensor['fileName']
        try:
            data = np.loadtxt(fileName, comments='#', delimiter=',')
        except KeyboardInterrupt:
            print("Keyboard interrupt requested...exiting")
            raise
        except:
            raise ValueError('GetSensorData: sensor number='+str(sensorNumber)+
                             ', name="'+sensor['name']+'": unable to load data!')
        return data

    raise ValueError('GetSensorData: sensor number='+str(sensorNumber)+
                     ', name="'+sensor['name']+'", has no available data to read!')
    return None
                     


#evaluate Exudyn sensors given in mbs, contained in localVariables
#resample sensor data and convert sensor results to text 
def ConvertSensors2Text(localVariablesEvalLLM, nResampleSize, nDigits, nExpectedSensors):
    result = {'text':'', 'error':False, 'warning':''}
    
    if 'mbs' in localVariablesEvalLLM:
        text = 'After simulation, the following sensor results have been obtained. '
        text += 'For every sensor data is given per time instant containing [time,x,y,z], where the meaning of x,y,z depends on the sensor type:\n'
        mbs = localVariablesEvalLLM['mbs']
        nSensors = mbs.systemData.NumberOfSensors()
        listOfSensors = np.arange(0,nSensors).tolist()
        if nSensors > 2:
            listOfSensors = [1,2,nSensors-1]
            
        if nSensors > nExpectedSensors:
            result['warning'] = 'ConvertSensors2Text: mbs has '+str(nSensors)+' sensors, but expected was '+str(nExpectedSensors)
        for i in listOfSensors:
            sensor = mbs.GetSensor(i)
            sensorName = sensor['name']
            sensorOutputType = str(sensor['outputVariableType']).replace('OutputVariableType.','') #gives Position, Velocity, ...
            
            text += 'Sensor '+sensorName+' of type "'+sensorOutputType+'" has the following values:\n'
            fullData = GetSensorData(mbs, sensorNumber=i)
            
            if len(fullData) != 0:
                data = ResampleData(fullData, nResampleSize)
            else: 
                data = fullData
            text += ConvertValueArray2Text(data,nDigits).replace('], [','],\n [') #each row has line break
            if i < nSensors-1:
                text += '\n'
        result['text'] = text
        if nSensors < nExpectedSensors:
            result['text'] = 'Not enough sensors available in multibody system; expected='+str(nExpectedSensors)+', available='+str(nSensors)
            result['error'] = True
    else:
        result['text'] = 'ConvertSensors2Text: no mbs found in localVariablesEvalLLM'
        result['error'] = True

    return result



#%%+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
#%%+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

#join paths or path and file name
#prefer over path.join as it allows more consistent handling
def JoinPath(path, subpath, subpath2=None):
    path = path.replace('\\','/')
    subpath = subpath.replace('\\','/')
    
    if path != '' and subpath != '' and path[-1] != '/':
        path += '/'
    if subpath != '' and subpath[0] == '/':
        subpath = subpath[1:]
    path = path+subpath
    
    #further subpath
    if subpath2 is not None:
        path = JoinPath(path, subpath2)
    
    return path

# ensures that directory is empty, if not all files are deleted within
def EnsureEmptyDir(dirPath):
    if not os.path.exists(dirPath):
        os.makedirs(dirPath)
    else:
        for filename in os.listdir(dirPath):
            filePath = JoinPath(dirPath, filename)
            if os.path.isfile(filePath) or os.path.islink(filePath):
                os.remove(filePath)
            elif os.path.isdir(filePath):
                for root, dirs, files in os.walk(filePath, topdown=False):
                    for f in files:
                        os.remove(JoinPath(root, f))
                    for d in dirs:
                        os.rmdir(JoinPath(root, d))
                os.rmdir(filePath)

#get scalar quantities + addOns, put into dict and return
def GetScalarClassObjectsDict(obj, addOns=[]):
    scalarConfig = {}
    for attrName in dir(obj):
        if attrName.startswith('__'):
            continue
        try:
            attrValue = getattr(obj, attrName)
            if IsScalar(attrValue) or isinstance(attrValue,str) or attrValue in addOns:
                scalarConfig[attrName] = attrValue
            # add other attribute types that should be saved to config (e.g. string) here 
        except Exception:
            continue
    return scalarConfig

def SaveClassObjectConfig(obj, logger, filePath = None):        
    className = obj.__class__.__name__
    if filePath is None:
        filePath = JoinPath(logger.logDir, f'configFiles/{className}_config.json')

    DeleteFileIfExisting(filePath, '')
    
    scalarConfig = GetScalarClassObjectsDict(obj)

    WriteDictToJSON(scalarConfig, filePath)

#helper function to load utf-8 files with error handling
def ReadFile(filePath, fileName):
    text = None
    fullPath = JoinPath(filePath, fileName)  # Construct the full file path
    
    if not os.path.exists(fullPath):
        raise FileNotFoundError(f"Error: File '{fullPath}' not found!")

    try:
        with open(fullPath, 'r', encoding='utf-8') as file:
            text = file.read()
    except Exception as e:
        raise ValueError(f"LoadFile failed for file: '{fullPath}'. Error: {e}")
        
    return text

#helper function to write data (string or anything that can be converted to string) into utf-8 files;
# create required directories, with error handling
def WriteFile(fileName, data, path='', append=False, flush=False):
    if path != '':
        fileName = JoinPath(path, fileName)
    try:
        os.makedirs(os.path.dirname(fileName), exist_ok=True)
    except KeyboardInterrupt:
        print("Keyboard interrupt requested...exiting")
        raise
    except:
        pass #makedirs may fail on some systems, but we keep going

    try:
        mode = 'w' if append==False else 'a'
        with open(fileName, mode=mode, encoding='utf-8') as file:
            file.write(str(data))  # Append mode     
            if flush: 
                file.flush()
    except KeyboardInterrupt:
        print("Keyboard interrupt requested...exiting")
        raise
    except:
        raise ValueError('WriteFile: fileName:"'+fileName+'" failed')

#convert variation ID to IDs of combinatorial sub-IDs
#var is in range [0,nTotalVariations-1], otherwise it repeats
#singleVariations contains the total number of variations, e.g. [2,5,4] => 2 x 5 x 4 = 40 nTotalVariations
#returns list of sub-IDs
#if var == None, then it returns the number of total variations
def VariationID2listIDs(var, singleVariations=[]):
    n = len(singleVariations) #number of sub-IDs
    subIDs = [None] * n
    
    #cnt total variations:
    nTotalVariations = 1
    for i in range(n):
        nTotalVariations *= singleVariations[i]
        
    if var is None:
        return nTotalVariations
    
    var = var % nTotalVariations #limit var; we could add warning
    
    x = var
    for i in range(n):
        subIDs[i] = x % singleVariations[i]
        x = int(x / singleVariations[i])

    return subIDs
    
# make systematic text variations; variationID=0,1,...
#if variationID == None, then it returns the number of total variations
def MakeTextVariation(text, variationID=None):

    m = len(text.split(' '))-1
    n = len(text.split('. '))-1
    
    nTotalVariations = (m + 1) * (n + 1) # possible variations

    if variationID is None:
        return nTotalVariations

    if variationID >= nTotalVariations:
        raise ValueError(f"variationID={variationID} exceeds maximum allowed={nTotalVariations - 1}")
    
    [variationIDm, variationIDn] = VariationID2listIDs(variationID, singleVariations=[m+1,n+1])

    #variate spaces:
    textlist=text.split(' ')
    m = len(textlist)-1
    newText = textlist[0]
    for i, item in enumerate(textlist[1:]):
        sep = '  ' if i == variationIDm-1 else ' '
        newText += sep+item
    text = newText

    #variate '. '
    textlist=text.split('. ')
    n = len(textlist)-1
    newText = textlist[0]
    for i, item in enumerate(textlist[1:]):
        sep = '.\n' if i == variationIDn-1 else '. '
        newText += sep+item
    text = newText

    return text

#special encoder to avoid problems with numpy types:
class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (np.integer,)):
            return int(obj)
        elif isinstance(obj, (np.floating,)):
            return float(obj)
        elif isinstance(obj, (np.ndarray,)):
            return obj.tolist()
        return super().default(obj)

    
def WriteDictToJSON(dictToWrite, jsonOutputFile):
        try:
            os.makedirs(os.path.dirname(jsonOutputFile), exist_ok=True)
        except KeyboardInterrupt:
            print("Keyboard interrupt requested...exiting")
            raise
        except:
            pass #makedirs may fail on some systems, but we keep going

        with open(jsonOutputFile, "w", encoding="utf-8") as json_file:
            json.dump(dictToWrite, json_file, indent=4, ensure_ascii=False, cls=NumpyEncoder)


def ReadJSONToDict(jsonInputFile):
    """
    Reads a JSON file and returns its contents as a dictionary.
    
    :param jsonInputFile: Path to the JSON file to read.
    :return: Dictionary with JSON contents or an empty dictionary if an error occurs.
    """
    if not os.path.exists(jsonInputFile):  # Check if file exists
        print(f"Error: File '{jsonInputFile}' not found.")
        return {}

    try:
        with open(jsonInputFile, "r", encoding="utf-8") as json_file:
            return json.load(json_file)  # Load JSON into a dictionary
    except json.JSONDecodeError:
        print(f"Error: File '{jsonInputFile}' is not a valid JSON file.")
        return {}
    except Exception as e:
        print(f"Error reading '{jsonInputFile}': {e}")
        return {}   
     
# Extract elements from a LLM response based on the keys of the parsed dictionary (exudyn-/eval-elements) (Case-insensitive!)
def ExtractElementsInResponse(llmResponse, parsedDict):
    # Build a case-insensitive pattern
    pattern = r'\b(' + '|'.join(map(re.escape, parsedDict.keys())) + r')\b'
    matches = re.findall(pattern, llmResponse, flags=re.IGNORECASE)

    # Normalize matches back to dictionary key casing (all letters written "small")
    lowerKeyMap = {key.lower(): key for key in parsedDict.keys()} #map of lower() keys to correct keys
    normalizedMatches = [lowerKeyMap[m.lower()] for m in matches if m.lower() in lowerKeyMap]

    finalList = []
    for item in normalizedMatches:
        if item not in finalList:
            finalList.append(item)

    return finalList

#check: replace substrings contained in undesiredKeywords from text
#       if text contains harmfulCommands, returns None (indicates that check failed)
#       success: return revised text; failure: returns None
def CheckLLMoutput(logger, text, checkUndesiredKeywords=False, checkHarmfulCommands=False): # inner function checking the quality of the LLM-output
    
    undesiredKeywords = [
        'The final answer is:', 'The answer is:', 'Answer:',
        '# noqa: E501', 
        '$\\boxed{0', #this is the only difference: not used in GenerateModelInputsFromConjecture
        '$\\boxed{', '}$',
        '"""', '```'
        # 'python', #this is dangerous, as the word python may be used as variable, etc.!
        # '"""', '```' 
        #==> python should be removed only if it before """ and this could be a separate function to 
        #    extract python code
    ]

    harmfulCommands = [
        "import os", "import subprocess", "import sys",
        "eval(", "open(", "subprocess.", "os.system"
    ]

    if not checkUndesiredKeywords: 
        undesiredKeywords = []
    
    if not checkHarmfulCommands: 
        harmfulCommands = []

    # Replace undesired phrases with an empty string
    for keyword in undesiredKeywords:
        if keyword in text: #not needed => just replace
            logger.LogText(f"Warning: Removing undesired keyword: '{keyword}'")
            text = text.replace(keyword, '')

    # detect harmful commands, which shall not be executed (remove all ...)
    for keyword in harmfulCommands:
        if keyword in text:
            logger.LogText(f"ERROR: Generated code contains potentially harmful command: '{keyword}'; aborting")
            return None  
    
    if "The prompt size exceeds the context window size and cannot be processed." in text:
        logger.LogText(f"ERROR: LLM produced no response, because context window size exceeded:\n{text}\n")
        return None  
    
    text = text.removeprefix("\n") # delete leading linebreak
    text = textwrap.dedent(text) # correct indentation

    return text

#extract code from LLM output; 
#modify code to improve safety, adjust Exudyn settings, avoid infinite waiting, etc.
def PreProcessLLMcode(logger, code, 
                      addTimeout = True, 
                      addFileWrite = True, 
                      replaceCoordinatesSolutionFile = None,
                      ):
                      #useTryExcept = False):
    #Exudyn/Python only accepts /
    if replaceCoordinatesSolutionFile is not None:
        replaceCoordinatesSolutionFile = replaceCoordinatesSolutionFile.replace('\\','/')

    textBeforeCode = code.split('import exudyn')[0]
    isReasoningModel = False
    if 'wait, ' in textBeforeCode.lower(): isReasoningModel = True
    if 'putting all together'.lower() in textBeforeCode.lower(): isReasoningModel = True
    if 'putting it all together'.lower() in textBeforeCode.lower(): isReasoningModel = True

    codeLines = code.strip().split('\n')
    
    debug = False
    newCode = ''
    foundPython = False
    foundSimulationSettings = False
    filledCoordinatesSolution = False
    importExudynFound = False
    importFound = False
    
    for line in codeLines:
        line0 = line.strip().lower() #python usually written Python
        if (#line0.startswith('Here is the Exudyn'.lower())
            #or line0.startswith('Here is the modified code'.lower())
            #or line0.startswith('Here is the updated code'.lower())
            #or line0.startswith('Here is the adapted code'.lower())
            line0.startswith('Here is the '.lower())
           ): #any version of this shall be erased
            if debug: print('** remove1:'+line0)
            continue
        if line0.startswith('import '): importFound = True
        if line0.startswith('import exudyn as '): importExudynFound = True

        if line0.startswith('<|im_start|>'): #this is typical for reasoning models
            continue
        if 'SolutionViewer()' in line0 and not line0[0].strip().startswith('#'): #avoid during execution
            #line0 = '*** '+line0 #this causes an exception and SolutionViewer is not executed, however this could be marked as error
            line0 = '#manually removed by PreProcessLLMcode:'+line0 
            logger.LogWarning('PreProcessLLMcode: SolutionViewer() found and removed')
            
        
        if line0 == 'python':
            if debug: print('** remove2')
            if not importExudynFound: #Qwen2.5 adds python also at the end!
                newCode = ''
            continue
        if line0 == '```python':
            if debug: print('** remove3')
            foundPython = True
            newCode = ''
            continue
        if (line0 == '```'):
            if not foundPython:
                if debug: print('** remove3')
                newCode = ''
                foundPython = True
                continue
            else:
                break #no more text read (would fail for several parts!)
        if line0.startswith('#end-of-code'):
            break
        if replaceCoordinatesSolutionFile is not None and filledCoordinatesSolution:
            if 'simulationSettings.solutionSettings.coordinatesSolutionFileName' in line:
                continue #do not add setting, otherwise it will overwrite the desired filename
        
        newCode += line+'\n'

        if isReasoningModel and line0.startswith('import exudyn as'): #this is the last way to erase all earlier text 
            newCode = line+'\n'
            continue

        if 'import exudyn as exu' in line:
            if addTimeout:
                newCode += 'exu.special.solver.timeout = 120\n' #2 minutes simulation timeout
            if addFileWrite:
                newCode += 'exu.SetWriteToConsole(False) #no output to console\n'
                newCode += 'exu.SetWriteToFile(filename="'+logger.logDir+'exudynTemp.log", flagFlushAlways=True)\n'

        if replaceCoordinatesSolutionFile is not None:
            if not foundSimulationSettings and 'exu.SimulationSettings()' in line:
                foundSimulationSettings = True
            if foundSimulationSettings and not filledCoordinatesSolution:
                newCode += 'simulationSettings.solutionSettings.coordinatesSolutionFileName = "'+replaceCoordinatesSolutionFile+'"\n'
                newCode += 'simulationSettings.timeIntegration.verboseMode = 1\n' #to see output in log
                filledCoordinatesSolution = True
                
    stopWrinting = 'exu.SetWriteToFile("",False)\n' #this only works, if no exception was raise
    if addFileWrite: #this is for the case that no exception is raised!
        newCode += stopWrinting

    if len(newCode)>=1 and newCode[-1] == '\n':
        newCode = newCode[:-1]
    
    #add try except to safely close file in case of exceptions (when we also like to know the issues ...!)
    # if useTryExcept:
    #     newCode = textwrap.indent(newCode, ' '*4)
    #     newCode = 'try:\n' + newCode + '\n'
    #     newCode += 'except:\n'
    #     newCode += ' '*4 + 'import exudyn as exu\n'
    #     newCode += ' '*4 + stopWrinting #this is always done!
    #     newCode += ' '*4 + 'raise\n'
    
    return newCode


# function extracts [ ... ] from a text which possibly has text before and after list
# return None, if no list has been found
def ExtractListFromString(s):
    match = re.search(r'\[.*?\]', s, re.DOTALL)
    return match.group(0) if match else None

# function extracts [ ... ] from a text which possibly has text before and after list
# test also if list can be converted to Python
# test if all items are valid lists
# return [list, ""] if list is valid;
# return [None, errorString] if no valid list has been found
def ExtractListFromStringAndTest(s):
    warn = ''
    if s.strip()[0] != '[' or s.strip()[-1] != ']':
        warn = 'ExtractListFromStringAndTest: list has additional text outside list []'
    sList = ExtractListFromString(s)

    if '"' not in s and "'" not in s:
        return [None, "ExtractListFromStringAndTest: list has no quotation marks!"]

    if sList is None:
        return [None, "ExtractListFromString: no valid list found:\n"+s]

    localEnv = {}
    try:
        extractedList = eval(sList)
    except Exception as e:
        msg = f"{str(e)}\n{traceback.format_exc()}"
        return [None, "ExtractListFromString:\n"+msg]

    return [extractedList, warn]

# function extracts information from text inside a html-tagged information and returns the information; 
# if tag is not found, return None
def ExtractXMLtaggedString(text, tag):
    response = {'text':None,'message':''} #message contains errors, etc.
    startTag = '<'+tag+'>'
    endTag = '</'+tag+'>'
    nStartTag = text.count(startTag)
    nEndTag = text.count(endTag)
    if nStartTag == 0 or nEndTag == 0:
        response['message'] = f'ERROR in ExtractXMLtaggedString: received {nStartTag} start tags and {nEndTag} end tags!'
        #response['message'] += text + '\n\n' #not needed; we anyway see the LLM output
        return response
    elif text.find(startTag) > text.find(endTag):
        response['message'] = f'ERROR in ExtractXMLtaggedString: {startTag} placed after {endTag}!'
        #response['message'] += text + '\n\n' #not needed; we anyway see the LLM output
        return response
    elif nStartTag != 1 or nEndTag != 1:
        response['message'] = f'Warning in ExtractXMLtaggedString: received {nStartTag} start tags and {nEndTag} end tags!'
        
    response['text'] = text.split(startTag)[1].split(endTag)[0]
    
    return response




# checks if a file exists in a directory (filepath)
def FileExists(filePath, fileName):
    fullPath = JoinPath(filePath, fileName)  # Construct full file path
    return os.path.exists(fullPath)  # Return True if the file exists, False otherwise

# delete a file if it exists in a specific path
def DeleteFileIfExisting(filePath, fileName):
    fullPath = JoinPath(filePath, fileName)  # Construct full file path
    if os.path.exists(fullPath):  # Check if the file exists
        try:
            os.remove(fullPath)   # Delete the file
        except Exception as e:
            print(f"Error deleting file '{fileName}': {e}")

# convert a string into a nice multi-line Python comment, using a limited number of characters per line
def String2PythonComment(text):
    words = text.split(' ')
    cols = 0
    newText = '#'
    for word in words:
        if cols > 70:
            newText += '\n# '+word
            cols=0
        else:
            newText += ' '+word
            cols += len(word)+1
    newText+='\n'
    return newText
            
# needs to be at module level to make it pickable for multiprocessing
def ExecuteCode(code, globalsDict, returnDict):
    """
    Executes the provided code and stores local variables in return_dict.

    Args:
        code (str): code to be executed
        globalsDict (dict): global variables of the code 
        returnDict (dict): localVariable dict which will be updated 
    Returns:
        tuple (bool, dict): true if code is executable and local variables in dict format
    """
    localEnv = {}
    try:
        exec(code, globalsDict, localEnv)
        # Filter out non-picklable objects (e.g., modules, functions, classes)
        safeEnv = {
            k: v for k, v in localEnv.items() 
            if isinstance(v, (int, float, str, list, dict, tuple, bool, set))  # Only allow basic types
        }
        returnDict.update(safeEnv)
    except Exception as e:
        returnDict['error'] = f"{str(e)}\n{traceback.format_exc()}"
        
        
#%%++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++        


#convert 'this is it' into thisIsIt
def SpacedText2CamelCase(s):
    parts = re.split(r'[\s_\-]+', s.strip())
    return parts[0].lower() + ''.join(p.capitalize() for p in parts[1:])

#replace camel case strings to strings with spaces
def AddSpacesToCamelCase(text):
    return re.sub(r'(?<=[a-z])([A-Z])', r' \1',text).lower()

#read out Exudyn solution file header and store in dict
def ParseExudynSolutionFileHeaderToDict(file_path, maxLinesHeader = 10):
    header_dict = {}

    with open(file_path, 'r') as f:
        for i, line in enumerate(f):
            if not line.startswith('#'):
                continue
            if i >= maxLinesHeader:
                break

            line = line[1:].strip()  # Remove '#' and whitespace
            if '=' in line:
                key, value = line.split('=', 1)
            elif ':' in line:
                key, value = line.split(':', 1)
            else:
                continue  # skip if not key-value style

            key = key.split('[')[0].split('(')[0]
            key = SpacedText2CamelCase(key.strip())
            value = value.strip()
            if '[' in value:
                #x = value.strip('[]').split(',')
                try:
                    value = ast.literal_eval(value) #convert into list
                except KeyboardInterrupt:
                    print("Keyboard interrupt requested...exiting")
                    raise
                except:
                    pass
            
            header_dict[key] = value

    return header_dict


# Generate LaTeX table for given list of rows, where the first element is used for the header row
def PerturbationCorrectness2LaTexTable(tableRows, latexFilePath):
    headerRow = tableRows[0]
    dataRows = tableRows[1:]

    numColumns = len(headerRow) - 1  # Exclude first column (Variation ID)
    columnWidth = "0.275cm" 
    groupSize = 5
    numGroups = (numColumns + groupSize - 1) // groupSize

    group = "".join([f"p{{{columnWidth}}}" for _ in range(groupSize)])  # no separator inside
    columnDef = "p{0.275cm}|" + "|".join([group for _ in range(numGroups)]) +"|" # | only between groups

    # Use tabular* with extracolsep
    latexCode = [r"\setlength{\tabcolsep}{1pt}" + r"\begin{tabular*}{\textwidth}{@{\extracolsep{\fill}}" + columnDef + "}"]

    # print("NumColumns: ", numColumns)
    # print("GroupSize: ", groupSize)
    # print("numGroup: ", numGroups)
    # print("LatexCode: ", latexCode)
    latexCode.append(r"\toprule")

    # 2. First header row: single merged "k"
    latexCode.append(r"\multirow{3}{*}{\rotatebox{90}{" + str(headerRow[0]) + r"}}" + r" & \multicolumn{" + str(numColumns) + r"}{c}{k} \\")
    # \multirow{3}{*}{\rotatebox{90}{var. ID}} & \multicolumn{35}{c}{k}

    # 3. Second header row: numeric labels (5, 10, 15, ...)
    numericHeaders = [""]
    for i in range(0, numColumns, groupSize):
        span = min(groupSize, numColumns - i)
        groupLabel = headerRow[i + 1 + span - 1]  # get last model ID in the group
        numericHeaders.append(r"\multicolumn{" + str(span) + r"}{r|}{" + str(groupLabel) + r"}")
    latexCode.append(" & ".join(numericHeaders) + r" \\")

    # 4. Third header row: actual rotated model IDs
    rotatedIDs = [""] * (numColumns + 1)
    latexCode.append(" & ".join(rotatedIDs) + r" \\")
    latexCode.append(r"\hline")

    # 5. Data rows
    for row in dataRows:
        rowEntries = []
        for idx, cell in enumerate(row):
            if idx == 0:
                rowEntries.append(str(cell))
            else:
                if cell == "red":
                    rowEntries.append(r"\cellcolor{red} ")
                elif cell == "green":
                    rowEntries.append(r"\cellcolor{green!30} ")
                else:
                    rowEntries.append("")
        latexCode.append(" & ".join(rowEntries) + r" \\")

    latexCode.append(r"\hline")
    latexCode.append(r"\end{tabular*}")

    with open(latexFilePath, "w") as f:
        f.write("\n".join(latexCode))

    print(f"LaTeX table written to: {latexFilePath}")

    
# merge Data for list of tables into one table listing merged results 
# keyColumn defines which column should be deduplicated - meaning that all other columns will be merged for each keyColumn entry
# if columns have identical headers, only first occurance will be kept
def MergeData(tables, keyColumn="model name", debug = False):
    
    seen = set()
    mergedHeader = []
    columnMaps = []
    keyIndexByTable = []

    # Step 1: Build merged header and track column mappings
    for tableIndex, table in enumerate(tables):
        header = table[0]
        columnMap = []
        for col in header:
            if col not in seen:
                seen.add(col)
                mergedHeader.append(col)
            columnMap.append(mergedHeader.index(col))
        columnMaps.append(columnMap)
        keyIndexByTable.append(header.index(keyColumn))

    # Step 2: Merge rows by key (e.g., model name)
    mergedData = {}

    for tableIndex, table in enumerate(tables):
        dataRows = table[1:]
        colMap = columnMaps[tableIndex]
        keyIdx = keyIndexByTable[tableIndex]

        for rowIndex, row in enumerate(dataRows):
            if keyIdx >= len(row):
                if debug:
                    print(f"[WARN] No key in row {rowIndex}: {row}")
                continue

            key = row[keyIdx]

            if key not in mergedData:
                mergedData[key] = [""] * len(mergedHeader)

            # Insert values into the right places
            for i, colIndex in enumerate(colMap):
                if i < len(row):
                    mergedData[key][colIndex] = row[i]

    # Final step: return rows in order of appearance
    mergedRows = [mergedHeader] + list(mergedData.values())

    if debug:
        print("Merged Header:", mergedHeader)
        print("Merged Rows:", mergedRows)

    return mergedRows

# Generate LaTeX table for given list of rows, where the first element is used for the header row
def OverallResults2LaTexTable(tableRows, desiredColumns, latexFilePath):
    headerRow = tableRows[0]
    dataRows = tableRows[1:]
    
   
    # print("headerRow: ", headerRow)
    # print("dataRows: ", dataRows)
    
    # Find indices of desired columns
    selectedIndices = [headerRow.index(col) for col in desiredColumns if col in headerRow]
    selectedHeader = [headerRow[i] for i in selectedIndices]
    
    # Rename for presentation
    for i in range(len(selectedHeader)):
        if selectedHeader[i] == 'correct all models':
            selectedHeader[i] = r'correctness (\%)'
        elif selectedHeader[i] == 'executable all models':
            selectedHeader[i] = r'executability (\%)'
        elif selectedHeader[i] == 'Quant.':
            selectedHeader[i] = 'quantization'
        elif selectedHeader[i] == 'pipeline':
            selectedHeader[i] = 'backend'
        elif selectedHeader[i] == '#Params (B)':
            selectedHeader[i] = r'\#parameters (B)'

    latexCode = []
    broadColumns = 3

    numColumns = len(selectedHeader)
    columnDef = r"p{3.2cm}" + r"|p{0.3cm}"*(numColumns-(broadColumns+1)) + r"|p{0.6cm}"*(broadColumns)
    latexCode.append(r"\begin{tabular}{" + columnDef + "}")
    latexCode.append(r"\toprule")
    latexCode.append(selectedHeader[0] + " & " + " & ".join([r"\rotatebox{90}{" + col + "}" for col in selectedHeader[1:]]) + r" \\")
    # latexCode.append(" & ".join(selectedHeader) + r" \\")
    latexCode.append(r"\hline")

    #++++++++++++++++++++++++
    #colored cells
    bestCellColor = r"\cellcolor{green!20}" #

    highlightColumns={
        3:-1,#small is good
        5:1, #large is good
        7:1, #large is good
        8:1, #large is good
        }
    bestIndicesValues = ['0']*len(selectedIndices)
    bestIndicesValues[3] = 1e10

    for row in dataRows:
        for k, i in enumerate(selectedIndices):
            if k in highlightColumns:
                cell = str(row[i]).replace(",", ".")
                #print('cell=',cell, ', best=',bestIndicesValues[k])
                if highlightColumns[k] < 0 and float(cell) < float(bestIndicesValues[k]):
                    bestIndicesValues[k] = cell
                elif highlightColumns[k] > 0 and float(cell) > float(bestIndicesValues[k]):
                    bestIndicesValues[k] = cell
    #++++++++++++++++++++++++
                    

    for row in dataRows:
        selectedRow = []
        for k, i in enumerate(selectedIndices):
            cell = str(row[i]).replace(",", ".")
            isBest = (bestIndicesValues[k] == cell and k in highlightColumns)
                
            try:
                s = bestCellColor*isBest
                val = float(cell)
                if '%' in selectedHeader[k]:
                    s += str(round(val * 100, 2))
                else:
                    s += str(int(val))
                selectedRow.append(s)
            except ValueError:
                if cell == 'huggingface':
                    selectedRow.append('HF')
                # add other formatting for cells here
                else:
                    selectedRow.append(cell)  # if it can't be parsed, just keep it as a string
        latexCode.append(" & ".join(selectedRow) + r" \\")

    latexCode.append(r"\hline")
    latexCode.append(r"\end{tabular}")

    with open(latexFilePath, "w") as f:
        f.write("\n".join(latexCode))

    print(f"LaTeX table written to: {latexFilePath}")
 
 
# reads a value from file and adds deltaCounter
def LogOverallCounter2File(filePath, deltaCounter):
    retry_count = 100
    wait_time = 0.1  # 100ms

    # Create file if it doesn't exist
    if not os.path.exists(filePath):
        with open(filePath, 'w') as f:
            f.write(f"{deltaCounter}\n")
        return deltaCounter
    else:
        with open(filePath, "r+") as f:

            # Read current counter
            content = f.read().strip()
            current_value = int(content) if content else 0

            # Create backup
            shutil.copy(filePath, filePath + ".bck")

            # Update the counter
            new_value = current_value + deltaCounter

            # Write new value
            f.seek(0)
            f.write(str(new_value))
            f.truncate()

    
# calculates the correlation between eval metrics which are the columns (desired) in a table (2D-array) and illustrates it as in a png file.
def CalcEvalMetricsCorrelationMatrix(tableRows, desiredColumns, filePath):
    import matplotlib.pyplot as plt
    from scipy.stats import spearmanr
    
    if not tableRows:
        print("No data provided.")
        return

    headerRow = tableRows[0]
    dataRows = tableRows[1:]

    # Find indices of desired columns
    selectedIndices = [headerRow.index(col) for col in desiredColumns if col in headerRow]

    selectedHeader = [headerRow[i] for i in selectedIndices]

    # Rename column headers for illustration
    for i in range(len(selectedHeader)):
        if selectedHeader[i] == 'correct all models':
            selectedHeader[i] = 'Correctness'
        elif selectedHeader[i] == 'executable all models':
            selectedHeader[i] = 'Executability'

    # Extract numeric data
    numericData = []
    for row in dataRows:
        try:
            numericRow = [float(row[i].replace(',', '.')) for i in selectedIndices]
            if any(value < 0 for value in numericRow):
                continue  # skip rows with any negative value (benchmark evaluation metric unknown)
            numericData.append(numericRow)
        except ValueError:
            continue  # skip non-numeric rows

    if not numericData:
        print("No numeric data found.")
        return

    matrix = np.array(numericData)

    # Compute Spearman correlation matrix
    correlationMatrix, _ = spearmanr(matrix)

    # If only 2 columns, spearmanr returns a single value; wrap it into a 2x2 matrix
    if matrix.shape[1] == 2:
        correlationMatrix = np.array([[1.0, correlationMatrix], [correlationMatrix, 1.0]])

    # Plotting
    fig, ax = plt.subplots(figsize=(10, 8))
    cax = ax.matshow(correlationMatrix, cmap='plasma', vmin=-1, vmax=1)

    for (i, j), val in np.ndenumerate(correlationMatrix):
        ax.text(j, i, f"{val:.2f}", ha='center', va='center', fontsize=15, color='black')

    ax.set_xticks(range(len(selectedHeader)))
    ax.set_yticks(range(len(selectedHeader)))
    ax.set_xticklabels(selectedHeader, rotation=45, ha='left', fontsize=15)
    ax.set_yticklabels(selectedHeader, fontsize=15)

    cb = fig.colorbar(cax)
    cb.ax.tick_params(labelsize=15)

    plt.tight_layout()
    plt.savefig(filePath, bbox_inches='tight', format='pdf')
    plt.close()
    print(f"Spearman correlation matrix saved to: {filePath}")

# takes a reference-solution file and calculates the numerical difference between values to a second solution file
# returns difference, or -2 if file was not found or -1 if shape of data was different
def EvaluateNumerical(fileNameReference, fileNameEvaluate,  localVariablesReference=None,
                      localVariablesEvaluate=None, logger=None):
    #TODO: we should also compare the reference values:
    #      mbs.systemData.GetODE2Coordinates(exu.ConfigurationType.Reference)
    import exudyn as exu
    if not FileExists(filePath='', fileName=fileNameReference):
        logger.LogError('EvaluateNumerical: reference file '+fileNameReference+' not found')
        return -2 #cannot be evaluated
    if not FileExists(filePath='', fileName=fileNameEvaluate):
        logger.LogError('EvaluateNumerical: eval file '+fileNameEvaluate+' not found')
        return -2 #cannot be evaluated

    refConfig0 = None
    refConfig1 = None
    if localVariablesReference is not None and localVariablesEvaluate is not None:
        if 'mbs' in localVariablesReference:
            mbsRef = localVariablesReference['mbs']
            if 'mbs' in localVariablesEvaluate:
                mbsEval = localVariablesEvaluate['mbs']
                refConfig0 = mbsRef.systemData.GetODE2Coordinates(configuration=exu.ConfigurationType.Reference)
                refConfig1 = mbsEval.systemData.GetODE2Coordinates(configuration=exu.ConfigurationType.Reference)
            else:
                logger.LogDebug('EvaluateNumerical: mbs not found in LLM solution')
        else:
            logger.LogDebug('EvaluateNumerical: mbs not found in sample solution')
            
    solution0 = np.loadtxt(fileNameReference, comments='#', delimiter=',')
    solution1 = np.loadtxt(fileNameEvaluate, comments='#', delimiter=',')

    diff = 0
    successODE2 = False
    #only compare ODE2 coordinates; constraints could be interchanged, still correct!
    try:    
        header0 = ParseExudynSolutionFileHeaderToDict(fileNameReference)
        header1 = ParseExudynSolutionFileHeaderToDict(fileNameEvaluate)
        
        # if 'numberOfSystemCoordinates' not in header0 or 'numberOfSystemCoordinates' not in header1:
        #     logger.LogDebug('compare ODE2 values, numberOfSystemCoordinates not found!')
    
        nODE2_0 = header0['numberOfSystemCoordinates'][0]
        nODE2_1 = header1['numberOfSystemCoordinates'][0]
        nCompare0 = 0
        nCompare1 = 0
        for i in range(3):
            nCompare0 += header0['numberOfWrittenCoordinates'][i]
            nCompare1 += header1['numberOfWrittenCoordinates'][i]

        # logger.LogDebug(f'EvaluateNumerical: nODE2_0={nODE2_0} and nODE2_1={nODE2_1}')
        
        #only compare ODE2 coordinates!
        if nCompare0 == nCompare1 and nODE2_0 == nODE2_1:
            
            diff = np.linalg.norm(solution0[:,:nCompare0] - solution1[:,:nCompare1])
            
            #try to add reference config
            if refConfig0 is not None and refConfig1 is not None and diff > 1e-10:
                solution0[:,:nODE2_0] += refConfig0
                solution1[:,:nODE2_1] += refConfig1
                diff1 = np.linalg.norm(solution0[:,:nCompare0] - solution1[:,:nCompare1])
                diff = min(diff, diff1)
                if diff <= 1e-10:
                    logger.LogWarning('EvaluateNumerical: solutions general difference > 0 but with reference values difference is ok')
            
            successODE2 = True
        else:
            logger.LogError('EvaluateNumerical: Solutions have different shape; nODE2 values = ('+
                            str(nODE2_0)+','+str(nODE2_0)+')' )
            
    except KeyboardInterrupt:
        print("Keyboard interrupt requested...exiting")
        raise
    except:
        exceptionText = traceback.format_exc()
        logger.LogError(f'EvaluateNumerical failed: {exceptionText}')

    
    if successODE2:
        logger.LogText(f'EvaluateNumerical: Solutions difference = {diff} [ODE2-based]')
        if solution0.shape != solution1.shape:
            logger.LogWarning('EvaluateNumerical: solutions have different shape; shapes = ('+
                            str(solution0.shape)+','+str(solution1.shape)+') - but we only compare ODE2 values!' )

        return diff

    if solution0.shape != solution1.shape:
        logger.LogError('EvaluateNumerical: Solutions have different shape; shapes = ('+
                        str(solution0.shape)+','+str(solution1.shape)+')' )
    else:
        diff = np.linalg.norm(solution0 - solution1)
        logger.LogText(f'EvaluateNumerical: Solutions difference = {diff}')

        return diff

    return -1


#%%++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++        



if __name__ == '__main__':
    from readExudynHelper import ParseExudynHelper
    filePathExudynHelper = "helperFiles/exudynHelper.py"
    parsedDict = ParseExudynHelper(filePathExudynHelper, maxDifficultyLevel=25, 
                                   excludeTags=['simulationPure','visualization'])
    llmResponse = 'Assemble, rigid body sphere, Assemble, Assemble, ground, point Mass'
    tags = ExtractElementsInResponse(llmResponse, parsedDict)
    print('extracted tags=',tags)
    
