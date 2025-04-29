# -*- coding: utf-8 -*-
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# This is part of the AI engineering lab project
#
# Filename: mbsModelLoader.py
#
# Details:  Read textual Exudyn model descriptions, define standard (convenient) random numbers and add randomized parametrization for models
#
# Author:   Tobias Möltner, Johannes Gerstmayr
# Date:     2025-02-10
#
# License:  BSD-3 license
#
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

import numpy as np
from agentInputData.modelDescriptions import modelDescriptions
from utilities import MakeTextVariation, VariationID2listIDs, IsScalar, IsIntType

class ModelLoader:
    def __init__(self):
        self.modelDescriptions = {}

    #load models from modelDescriptions.py, only models <= difficultyLevel, 
    #specificModels can be a list of model names that are used
    def LoadStandardModelDescriptions(self, maxDifficultyLevel = 10000, 
                                      specificModels = None,
                                      onlyWithSampleFiles = False,
                                      onlyParameterizedModels = False):
        mbsModels = modelDescriptions
        self.modelDescriptions = {}
        self.maxDifficultyLevel = maxDifficultyLevel

        if specificModels is None:
            specificModels = []

        for key, value in mbsModels.items():
            if ( ('difficulty' not in value or value['difficulty'] <= maxDifficultyLevel)
                and (specificModels == [] or key in specificModels)
                and (not onlyParameterizedModels or 'parameters' in value) 
                and (not onlyWithSampleFiles or 'sampleFileName' in value) 
                ):
                self.modelDescriptions[key] = value
        
    
    def LoadWikipediaModelDescriptions(self, maxNumber = 100): #TODO
        raise ValueError('not implemented')

    def NumberOfModels(self):
        return len(self.modelDescriptions)
    
    def ListOfModels(self):
        listModels = []
        for key, value in self.modelDescriptions.items():
            listModels.append(key)
        return listModels
        
    def GetStandardNumbersList(self, minVal, maxVal):
        """
        Generates list of values from a predefined set pattern within a given range.

        :param minVal: The minimum value of the range.
        :param maxVal: The maximum value of the range.
        :return: A numpy array of randomly selected values.
        """
        # Base pattern to be repeated across powers of 10
        base_pattern = np.array([1, 1.2, 1.25, 1.5, 2, 2.5, 3, 4, 5, 6, 7.5, 8])

        smallestValue = 0.01 #in case of zero
        if abs(minVal) < smallestValue and minVal != 0:
            smallestValue = abs(minVal)
        if abs(maxVal) < smallestValue and maxVal != 0:
            smallestValue = abs(maxVal)

        if minVal > maxVal:
            raise ValueError('GetStandardRandomNumber: invalid interval: minVal must be <= maxVal')
        if minVal == maxVal:
            return float(minVal)
        #++++++++++++++++++++
        def GetPosStandardNumbers(minVal, maxVal):
            # Determine the logarithmic range
        
            log_min = np.log10(minVal)
            log_max = np.log10(maxVal)
            
            # Generate scaled patterns using powers of 10
            values = []
            
            for exponent in range(int(np.floor(log_min)), int(np.ceil(log_max)) + 1):
                scaledValues = base_pattern * (10 ** exponent)
                values.extend(scaledValues[(scaledValues >= minVal) & (scaledValues <= maxVal)])
            
            values = np.array(values)
            return values
        #++++++++++++++++++++
        
        if minVal < 0 and maxVal <= 0:
            if maxVal == 0:
                maxVal = -smallestValue
            values = -GetPosStandardNumbers(-maxVal, -minVal)[::-1] #reversed
        elif minVal < 0 and maxVal >= 0:
            values = list(-GetPosStandardNumbers(smallestValue,-minVal))[::-1] #reversed
            values += list(GetPosStandardNumbers(smallestValue,maxVal))
            values = np.array(values)
        else: #all positive
            if minVal == 0:
                minVal = smallestValue
            values = GetPosStandardNumbers(minVal, maxVal)
        
        # print(values)
        return values
        
    def GetStandardRandomNumber(self, minVal, maxVal):
        """
        Generates random values from a predefined set pattern within a given range.

        :param minVal: The minimum value of the range.
        :param maxVal: The maximum value of the range.
        :return: A numpy array of randomly selected values.
        """

        values = self.GetStandardNumbersList(minVal, maxVal)
        
        # Select random values
        randVal = np.random.choice(values, size=None, replace=True)
        randVal = round(randVal,10) #we need to round as the exp function leads to small round off errors!

        if type(randVal) == str: #Joh: can this happen?
            pass
        elif randVal == int(randVal):
            randVal = int(randVal) #we avoid '.0' in string representation
        else:
            randVal = float(randVal)  #avoid numpy float (problems in json files)!
        
        return randVal  
        
    
    #Generates a model description with parameters (random if desired) within defined ranges.
    #spaceVariationID: do text variation by changing spaces and line breaks
    #differentFromTheseParameters: will try to always find parameters that are all different from given ones
    def GetModelDescriptionAndDict(self, modelKey, randomizeParameters = False,
                                   spaceVariationID=None, wordingVariationID=None,
                                   differentFromTheseParameters=None, logger=None):
        
        if modelKey not in self.modelDescriptions:
            raise ValueError(f"Model '{modelKey}' not found.")

        modelData = self.modelDescriptions[modelKey]
        chosenParameters = {}
        
        for param, values in modelData["parameters"].items():
            newParam = None
            itMax = 30
            it = 0
            foundParam = False
            while it < itMax and not foundParam:
                it += 1
                if randomizeParameters:
                    if ("range" in values):
                        newParam = self.GetStandardRandomNumber(values["range"][0], values["range"][1])
                    elif("list" in values):
                        newParam = np.random.choice(values["list"], size=None, replace=True) # get random element of list
                        if IsIntType(newParam):
                            newParam = int(newParam)
                        elif IsScalar(newParam):
                            newParam = float(newParam)
                    else:
                        newParam = values["default"] 
                        raise ValueError("GetModelDescriptionAndDict") # information about what failed 

                    if differentFromTheseParameters is not None:
                        if str(differentFromTheseParameters[param]) != str(newParam):
                            foundParam = True
                    else:
                        foundParam = True
                else:
                    newParam = values["default"]
                    foundParam = True

            if it >= itMax:
                warningText = 'Warning: GetModelDescriptionAndDict: alternative parameters failed for '+modelKey+', param='+param+'!'
                if logger is not None:
                    logger.LogWarning(warningText, printToConsole=True)
                else:
                    print(warningText)

            chosenParameters[param] = newParam
            
        # Format description with randomized values
        modelDescription = modelData["description"].format(**chosenParameters)
        for param in chosenParameters:
            if '{'+param+'}' not in modelData["description"]:
                raise ValueError('GetModelDescriptionAndDict: parameter "'+param+'" not in model description!')
        
        if wordingVariationID is not None:
            if "alternativeDescription" not in modelData:
                raise ValueError("GetModelDescriptionAndDict: no alternativeDescription available")
                
            alternativeParameters = modelData["alternativeDescriptionParameters"]
            altLists = []
            for key, value in alternativeParameters.items():
                altLists.append(len(value))
            #totalVariations = VariationID2listIDs(None, altLists)
            paramIDs = VariationID2listIDs(wordingVariationID, altLists)
            
            chosenAlternativeParameters = {}
            cnt = 0
            for key, value in alternativeParameters.items():
                chosenAlternativeParameters[key] = value[paramIDs[cnt]]
                cnt += 1
            
            modelDescription = modelData["alternativeDescription"].format(**chosenParameters,**chosenAlternativeParameters)
            
        if spaceVariationID is not None:
            modelDescription = MakeTextVariation(modelDescription, spaceVariationID)
        
        return [modelDescription, modelData, chosenParameters] # [string, dict, dict]


if __name__ == "__main__":
    modelLoader = ModelLoader()

    if False:
        # only loading models with sample files (needed for comparison) and parameters - ATM
        modelLoader.LoadStandardModelDescriptions(maxDifficultyLevel=15, specificModels=None, onlyWithSampleFiles=True, onlyParameterizedModels=True)
        
        [modelDescription, modelData, chosenParameters] = modelLoader.GetModelDescriptionAndDict(modelKey='singleMassOscillatorFG', randomizeParameters=False)
        print("Default model description:")
        print(modelDescription)
        print("\Default Parameters:", modelData['parameters'])
        
        [modelDescription, modelData, chosenParameters] = modelLoader.GetModelDescriptionAndDict(modelKey='singleMassOscillatorFG', randomizeParameters=True)
        print("\nRandomized model description:")
        print(modelDescription)
        print("\nRandomized Parameters:", modelData['parameters'])
    
    if True:
        #count number of possible models due to parameter variations
        modelLoader.LoadStandardModelDescriptions(maxDifficultyLevel=99, 
                                                  onlyWithSampleFiles=True,
                                                  onlyParameterizedModels=True)
        totalPossibleModels = 0     
        for modelName, modelData in modelDescriptions.items():
            modelPossibilities = 1
            for param, values in modelData["parameters"].items():
                paramCnt = 1
                if ("range" in values):
                    paramCnt = len(modelLoader.GetStandardNumbersList(values["range"][0], values["range"][1]))
                elif("list" in values):
                    paramCnt = len(values["list"])
                else:
                    print(f'model {modelName} parameter {param} is neither list nor range')
                modelPossibilities *= paramCnt 
            print(f'model {modelName} has {modelPossibilities} possibilities')
            totalPossibleModels += modelPossibilities
        print(f'totalPossibleModels={totalPossibleModels}')
    