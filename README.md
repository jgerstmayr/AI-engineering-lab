# AI Engineering Lab Project

![License: BSD-3-Clause](https://img.shields.io/badge/License-BSD%203--Clause-blue.svg)

**Authors**: Tobias Möltner, Peter Manzl, Michael Pieber, Johannes Gerstmayr

**Date**: 2025-04-29

This repository contains the main code for the AI Engineering Lab project.  
It includes tools for AI agents, LLM model evaluations, test model creation, multibody system processing, and result analysis.

---

## Table of Contents

- [Description of Python scripts](#description-of-python-scripts)
  - [`agent.py`](#agentpy)
  - [`agentDriver.py`](#agentdriverpy)
  - [`conjexplorerVisualizer.py`](#conjexplorervisualizerpy)
  - [`logger.py`](#loggerpy)
  - [`mbsModelLoader.py`](#mbsmodelloaderpy)
  - [`misc.py`](#miscpy)
  - [`motionAnalysis.py`](#motionanalysispy)
  - [`myLLM.py`](#myllmpy)
  - [`postProcessing.py`](#postprocessingpy)
  - [`processResultsWithOpenAI_GPT4o.py`](#processresultswithopenaigpt4opy)
  - [`readExudynHelper.py`](#readexudynhelperpy)
  - [`templatesAndLists.py`](#templatesandlistspy)
  - [`testModelCreation.py`](#testmodelcreationpy)
  - [`testModelCreationDriver.py`](#testmodelcreationdriverpy)
  - [`utilities.py`](#utilitiespy)
  - [`writeREADME.py`](#writereadmepy)
  - [`agentInputData/modelDescriptions.py`](#agentinputdatamodeldescriptionspy)
  - [`helperFiles/evalHelper.py`](#helperfilesevalhelperpy)
  - [`helperFiles/exudynHelper.py`](#helperfilesexudynhelperpy)
- [License](#license)

---

## Description of Python scripts

Below is the description of the Python scripts contained in this project:

### `agent.py`

- **Details**: This is the main file (main class) for self-validation and export of results (MergeConjecturesResults); to run, use agentDriver.py with args from command line;
- **Authors**: Johannes Gerstmayr, Tobias Möltner
- **Date**: 2024-09-18 (last update 2025-04-29)
- **Notes**: Ensure that the appropriate model files are available locally or through the Hugging Face model hub.

### `agentDriver.py`

- **Details**: Runs agent.py methods from command line; use python agentDriver.py -h to see help;
- **Authors**: Johannes Gerstmayr
- **Date**: 2025-04-05
- **Notes**: Ensure that the appropriate model files are available locally or through the Hugging Face model hub.

### `conjexplorerVisualizer.py`

- **Details**: Visualizes and compares model evaluation scores across conjectures using interactive heatmaps and stacked bar plots.
- **Authors**: Michael Pieber
- **Date**: 2025-04-15
- **Notes**: Ensure that the appropriate model files are available locally or through the Hugging Face model hub.

### `logger.py`

- **Details**: This script defines a class for logging different information of agent-functionalities.
- **Authors**: Tobias Möltner, Johannes Gerstmayr
- **Date**: 2024-12-20

### `mbsModelLoader.py`

- **Details**: Read textual Exudyn model descriptions, define standard (convenient) random numbers and add randomized parametrization for models
- **Authors**: Tobias Möltner, Johannes Gerstmayr
- **Date**: 2025-02-10

### `misc.py`

- **Details**: Special functions like string operations, etc. used for AI agents
- **Authors**: Johannes Gerstmayr, Tobias Möltner
- **Date**: 2024-09-18
- **Notes**: Ensure that the appropriate model files are available locally or through the Hugging Face model hub.

### `motionAnalysis.py`

- **Details**: main functionality to process sensor output and perform special multibody analysis;
- **Authors**: Johannes Gerstmayr
- **Date**: 2025-03-23

### `myLLM.py`

- **Details**: The MyLLM class is intended for interacting with large language models (LLMs) of different kinds with one interface.
- **Authors**: Tobias Möltner, Johannes Gerstmayr
- **Date**: 2024-09-18
- **Notes**: Ensure that the appropriate model files are available locally or through the Hugging Face model hub.

### `postProcessing.py`

- **Details**: Post-processing functionalities for agent-results, using Levensthein and other metrics.
- **Authors**: Tobias Möltner
- **Date**: 2025-04-08
- **Notes**: Place the "results.json" on the same level as this script for analysis.

### `processResultsWithOpenAI_GPT4o.py`

- **Details**: This file uses the API from OpenAI to run judge on LLM conjectures with ChatGPT
- **Authors**: Peter Manzl
- **Date**: 2025-03-15
- **Notes**: Ensure that the appropriate model files are available locally or through the Hugging Face model hub.

### `readExudynHelper.py`

- **Details**: Read and parse exudynHelper.py and evalHelper and provide information as dictionary with tags
- **Authors**: Johannes Gerstmayr
- **Date**: 2025-01-05

### `templatesAndLists.py`

- **Details**: main prompt templates (template to create the prompt for LLMs, using their prompt templates ...),
- **Authors**: Johannes Gerstmayr, Tobias Möltner
- **Date**: 2025-02-10
- **Notes**: Ensure that the appropriate model files are available locally or through the Hugging Face model hub.

### `testModelCreation.py`

- **Details**: Main code and class for simulation model creation and testing;
- **Authors**: Johannes Gerstmayr, Tobias Möltner
- **Date**: 2024-09-18
- **Notes**: Ensure that the appropriate model files are available locally or through the Hugging Face model hub.

### `testModelCreationDriver.py`

- **Details**: Driver file for testModelCreation, to be used from command line; type python testModelCreationDriver.py -h to see help
- **Authors**: Johannes Gerstmayr
- **Date**: 2025-03-15
- **Notes**: Ensure that the appropriate model files are available locally or through the Hugging Face model hub.

### `utilities.py`

- **Details**: Basic support functions for LLM-agents, and further functionalities of the LLM Lab.
- **Authors**: Tobias Möltner and Johannes Gerstmayr
- **Date**: 2025-03-11

### `writeREADME.py`

- **Details**: This script just writes the headers of the .py files in this folder to a .txt file
- **Authors**: Michael Pieber
- **Date**: 2025-04-29

### `agentInputData/modelDescriptions.py`

- **Details**: Lists, dictionaries and lists used by agend
- **Authors**: Tobias Möltner
- **Date**: 2025-02-25
- **Notes**: Collection of modeldescriptions and according possible parametrizations.

### `helperFiles/evalHelper.py`

- **Details**: this file serves as a documented example that shall be used by
- **Authors**: Johannes Gerstmayr, Tobias Möltner
- **Date**: 2025-01-13

### `helperFiles/exudynHelper.py`

- **Details**: this file serves as a documented example that shall be used by
- **Authors**: Johannes Gerstmayr
- **Date**: 2024-12-30

---

## License

BSD-3 license