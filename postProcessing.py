# -*- coding: utf-8 -*-
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# This is part of the AI engineering lab project
#
# Filename: postProcessing.py
#
# Details:  Post-processing functionalities for agent-results, using Levensthein and other metrics. 
#
# Author:   Tobias Möltner
# Date:     2025-04-08
# Notes:    Place the "results.json" on the same level as this script for analysis.
#
# License:  BSD-3 license
# 
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

from utilities import JoinPath, WriteDictToJSON, ReadJSONToDict, PerturbationCorrectness2LaTexTable
from logger import Logger
import os
import numpy as np
import matplotlib.pyplot as plt
import argparse

# Create the argument parser
description = "Performin post-processing on result-files (results.json) in specific logDirectory \n"

parser = argparse.ArgumentParser(description=description)

# Define arguments
parser.add_argument("-lv", "--levensthein",  action='store_true', help="evaluate/visualize Levensthein distances")
parser.add_argument("-nm", "--numerical",  action='store_true', help="evaluate/visualize numerical")
parser.add_argument("-d", "--directory", type=str, default="logsTMS/log_Llama3.1-8B-Q4", help="Log-directory of results.json")

# Parse arguments
args = parser.parse_args()

# Assigning values
evaluateLevenshtein = args.levensthein
evaluateNumerical = args.numerical
resultsDir = args.directory

################################################################################################################################################


# visualize correctnes comparisson (diff) between mbs models variations and their reference solutions
# rows = MBS model names; columns = variation IDs; cells = 'green' if difference == 0.0, 'red' otherwise
def VisualizeNumerical(storedDataPerModel, filePath, logger=None):
    from agentInputData.modelDescriptions import modelName2mbsID
    import csv
    
    argSpaceVariations = 7
    correctnessTable = {}
    allVariationIDs = set()

    for key, mbsModelData in storedDataPerModel.items():
        modelName = mbsModelData.get('currentMBSmodelName')
        variationID = mbsModelData.get('spaceVariationID')
        diff = mbsModelData.get('differenceLLM', None)

        if modelName not in correctnessTable:
            correctnessTable[modelName] = {}

        if diff is not None:
            correctnessTable[modelName][variationID] = "green" if diff == 0.0 else "red"
        else:
            correctnessTable[modelName][variationID] = "N/A"

        allVariationIDs.add(variationID)

    sortedVariationIDs = sorted(allVariationIDs)
    sortedModelNames = sorted(correctnessTable.keys(), key=lambda name: int(modelName2mbsID[name]))

    # Create header row: Variation ID label + model IDs
    headerRow = [r"var. ID"] + [str(modelName2mbsID[name]) for name in sortedModelNames] 

    # Now flip the structure: build one row per Variation ID
    tableRows = []
    for variationID in sortedVariationIDs:
        row = [int(variationID/argSpaceVariations)+1] # / argSpaceVariations(7) to let variation ID start from 1
        for modelName in sortedModelNames:
            value = correctnessTable.get(modelName, {}).get(variationID, "N/A")
            row.append(value)
        tableRows.append(row)

    # CSV export
    csvFilePath = filePath + 'CorrectnessVariationMap.csv'
    with open(csvFilePath, mode="w", newline="") as f:
        writer = csv.writer(f, delimiter=';')
        writer.writerow(headerRow)
        writer.writerows(tableRows)

    if logger:
        logger.LogText(f"Correctness variation map written to: {csvFilePath}", printToConsole=True)

    # LaTeX export
    latexFilePath = csvFilePath.replace('.csv', '.tex')
    PerturbationCorrectness2LaTexTable(tableRows=[headerRow] + tableRows, latexFilePath=latexFilePath)

# visualizes Levensthein distance matrix (symmetrical) in the form of a lower triangle matrix and the numerical difference (correctnes) 
# between llm-generated solution files and reference solution files in the diagonal
def VisualizeLevensthein(distanceMatrix, modelNames, filePath):
    import seaborn as sns  # pip install seaborn
    # from agentInputData.modelDescriptions import modelName2mbsID (might be necessary to ensure that ID matches name)

    def JoinPath(*args):
        return os.path.join(*args)

    numberOfModels = len(modelNames)
    variationIDs = [f"var. ID {i+1}" for i in range(numberOfModels)]
    fig, ax = plt.subplots(figsize=(10, 8))
    fullMatrix = np.full((numberOfModels, numberOfModels), np.nan)
    annotations = [["" for _ in range(numberOfModels)] for _ in range(numberOfModels)]

    # Fill lower triangle with Levenshtein distances
    for i in range(numberOfModels):
        for j in range(i):
            fullMatrix[i, j] = distanceMatrix[i][j]
            annotations[i][j] = f"{distanceMatrix[i][j]:.0f}"

    # Create heatmap with annotations
    ax = sns.heatmap(fullMatrix, 
                annot=annotations,
                fmt="",  # since we provide full formatted strings
                mask=np.isnan(fullMatrix), 
                xticklabels=variationIDs, 
                yticklabels=variationIDs, 
                cmap="plasma", 
                linewidths=.5, 
                square=True, 
                annot_kws={"size": 15},
    )
    
    # ax.set_title("Levenshtein Distances of Simulation Codes", fontsize=20, pad=20)
    colorbar = ax.collections[0].colorbar
    colorbar.ax.tick_params(labelsize=15)
    ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha='right', fontsize=15)
    ax.set_yticklabels(ax.get_yticklabels(), fontsize=15)
    ax.figure.axes[-1].yaxis.label.set_size(14)  # Colorbar label font size
    
    plt.tight_layout()
    plt.savefig(filePath + "levenstheinDistance.pdf", format='pdf')
    plt.show()
    
    logger.LogText(f"Visualization of Levenshtein Distances Matrix saved to: {filePath + 'levenstheinDistance.pdf'}", printToConsole=True)

# calculates and normalizes the Levensthein difference for MBD models (.py-files) in "mbsModelsLLMdir" - (syntax-level: string) comparison
def EvaluateLevenshtein(mbsModelsDir, logger, visualizeSolution=False):
    from Levenshtein import distance as LevenshteinDistance  # pip install python-Levenshtein
    
    modelContents = {}
    numberOfFiles = 0

    pyFilesFound = False  # <-- NEW

    # Read all .py files in the directory
    for filename in os.listdir(mbsModelsDir):
        if filename.endswith('.py'):
            pyFilesFound = True
            numberOfFiles += 1
            filePath = JoinPath(mbsModelsDir, filename)
            with open(filePath, 'r', encoding='utf-8') as file:
                modelContents[filename] = file.read()

    if not pyFilesFound:  # <-- Moved outside the loop
        logger.LogError(f'EvaluateLevenshtein: No .py files found in directory: {mbsModelsDir}')
        return None
        
    logger.LogText(f'EvaluateLevenshtein: Found {numberOfFiles} .py files for comparison.')

    modelNames = list(modelContents.keys())
    distanceMatrix = np.zeros((len(modelNames), len(modelNames)))

    logger.LogText('Evaluating normalized Levenshtein distances between model files...')
    for i in range(len(modelNames)):
        for j in range(i + 1, len(modelNames)):
            dist = LevenshteinDistance(modelContents[modelNames[i]], modelContents[modelNames[j]])
            
            distanceMatrix[i, j] = dist
            distanceMatrix[j, i] = dist
            
    if visualizeSolution:
        logger.LogText('Visualizing Levenshtein distance matrix...')
        VisualizeLevensthein(distanceMatrix, modelNames, filePath=JoinPath('../../01_paper/figures/', backend))

    return distanceMatrix

def AnalyzeLevenstheinDistanceThresholds(distanceMatrix, logger):
    numModels = distanceMatrix.shape[0]
   
    totalComparisons = (numModels * (numModels - 1)) // 2  # Only unique pairs (i < j)
    
    dists = distanceMatrix[np.triu_indices(numModels, k=1)] # distance matrix is symmetrical, only use upper triangle row and columns and skip diagonal (comparissons with itself)

    # threshold for code difference
    threshold = 0.0
    
    aboveThreshold = np.sum(dists > threshold)
    belowThreshold = totalComparisons - aboveThreshold

    logger.LogText(f'Total comparisons: {totalComparisons}')
    logger.LogText(f'Threshold = {threshold:.2f}')
    logger.LogText(f'Pairs with distance < lower: {threshold} ({100 * belowThreshold / totalComparisons:.2f}%)')
    logger.LogText(f'Pairs with distance > upper: {threshold} ({100 * aboveThreshold / totalComparisons:.2f}%)')

    return {
        'total': totalComparisons,
        'below': belowThreshold,
        'above': aboveThreshold,
        'threshold': round(threshold, 2),
    }

### Copy detector not used in current evaluation!
def VisualizeCopyDetector(detector, logDir):
    import networkx as nx
    graph = nx.Graph()
    
    results = detector.get_copied_code_list()  # Get detected similarities

    for result in results:
        file1, file2, similarity = result[2], result[3], result[0]  # Extract files and similarity
        graph.add_edge(file1, file2, weight=similarity)

    plt.figure(figsize=(10, 8))
    pos = nx.spring_layout(graph)
    edges = graph.edges(data=True)
    weights = [d['weight'] for (_, _, d) in edges]
    
    nx.draw(graph, pos, with_labels=True, node_color='lightblue', edge_color=weights, edge_cmap=plt.cm.Blues, width=2)
    plt.title("Code Similarity Graph")
    plt.savefig(JoinPath(logDir, "copydetector_graph.pdf"), format='pdf')
    plt.show()

# provided a directory with python files the copy detector identifies similarities between code-pairs on syntax-level
def EvaluateCopyDetector(mbsModelsLLMdir, logDir):
    from copydetect import CopyDetector  # pip install copydetect
    detector = CopyDetector(test_dirs=[mbsModelsLLMdir], out_file=JoinPath(logDir, "copydetector_report.html"))  # Set output file path
    detector.run()  
    detector.generate_html_report(output_mode="save")  # Save the HTML report
    
    VisualizeCopyDetector(detector, logDir)  # Pass detector object



#%%++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++    

resultsDict = ReadJSONToDict(JoinPath(resultsDir, 'results.json'))

try:
    logDir = resultsDict['logDir']
    backend = resultsDict['llmConfig']['backend']
    mbsModelsLLMdir = resultsDict['mbsModelsLLMdir']
    storedDataPerModel = resultsDict['storedDataPerModel']
except KeyError as e: # fields might not exist in results.json
    raise KeyError(f"Missing required key in resultsDict: {e}")

logger = Logger(logDir + 'logsPost')


#### Levensthein-distance between simulation codes ####
if evaluateLevenshtein:
    normDistanceMatrixLLM = EvaluateLevenshtein(mbsModelsDir=mbsModelsLLMdir,
                                                logger=logger,
                                                visualizeSolution=True)
    levenstheinResults = AnalyzeLevenstheinDistanceThresholds(distanceMatrix=normDistanceMatrixLLM,
                                                                logger=logger)

    WriteDictToJSON(dictToWrite=levenstheinResults, jsonOutputFile=JoinPath('../../01_paper/figures/', backend + 'levensthein_results.json'))

#### Numerical-difference between mbs models and their reference solution ####
if evaluateNumerical:
    VisualizeNumerical(storedDataPerModel=storedDataPerModel, filePath=JoinPath('../../01_paper/figures/', backend), logger=logger)


# %%
