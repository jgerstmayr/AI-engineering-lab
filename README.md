# AI Engineering Lab Project

![License: BSD-3-Clause](https://img.shields.io/badge/License-BSD%203--Clause-blue.svg)

**Authors**: Johannes Gerstmayr, Tobias Möltner, Peter Manzl, Michael Pieber

This repository contains the main code for the AI Engineering Lab project, see the preprint:

Tobias Möltner, Peter Manzl, Michael Pieber, and Johannes Gerstmayr. Creation, Evaluation and Self-Validation of Simulation Models with Large Language Models, 01 May 2025, PREPRINT (Version 1) available at Research Square
<https://doi.org/10.21203/rs.3.rs-6566994/v1>

This GitHub project includes tools for AI agents, LLM model evaluations, test model creation, multibody system processing, and result analysis.

The project introduces a benchmark framework for evaluating LLMs on mechanical engineering problems, specifically multibody dynamics. It supports automated generation of simulation models in Python, using parametrized setups with ground truth solutions to test model executability and correctness. LLM agents generate models and perform self-validation using predefined checks to identify errors in parametrization. Results are evaluated using F-score metrics, showing that while most models capture general trends, only the best-performing LLM accurately detects invalid simulations.

---

## Notes for running LLM agents

In order to run the code, you need to install at least:

`pip install exudyn==1.9.83 gpt4all[cuda]`

or if run via HuggingFace's transformers:

`pip install exudyn==1.9.83 transformers==4.51.3` 

For agents to run, you **first need to extract samples** in folder `sampleFiles` (see readme there)!

In the root folder, you can run the following scrips:

```
python testModelCreationDriver.py -n Llama3.1-8B-Q4
python agentDriver.py -n QwenCoder-32B-Q4 -c 8 -r 2 -wc -simOnly
python agentDriver.py -n Phi4-Q4 -c 8 -r 2 -wc -simOnly -sMC -sGE
```
Before running the agent for Phi-Q4, you need to copy `results_MC.json` and `results_GE.json` from the folder `log_QwenCoder-32B-Q4` to the folder `log_Phi4-Q4`.

For merging the results of several agent runs, either run:

`python ./testModelCreationDriver.py -m 'logsTM'`

or:

`python ./agentDriver.py -m 'logsAgent'`

For further options, run the files with the -h option to see help.

---

## Description of Python scripts

Below is the description of the Python scripts contained in this project:

### `agent.py`

- **Details**: This is the main file (main class) for self-validation and export of results (MergeConjecturesResults); to run, use agentDriver.py with args from command line; Main functions: - GenerateModelsAndConjecturesLoop: create models and conjectures (with separate LLM) - GenerateExudynModelsAndEval: create Exudyn models, execute and write evaluation results - EvaluateAllConjectures: evaluate simulation results OR conjectures
- **Notes**: Ensure that the appropriate model files are available locally or through the Hugging Face model hub.

### `agentDriver.py`

- **Details**: Runs agent.py methods from command line; use python agentDriver.py -h to see help; besides running agent for LLM models, it also can merge results and exports latex tables
- **Notes**: Ensure that the appropriate model files are available locally or through the Hugging Face model hub.

### `conjexplorerVisualizer.py`

- **Details**: Visualizes and compares model evaluation scores across conjectures using interactive heatmaps and stacked bar plots.
- **Notes**: Ensure that the appropriate model files are available locally or through the Hugging Face model hub.
- **Requirements**:  pip install dash; pip install plotly; pip install openpyxl

### `logger.py`

- **Details**: This script defines a class for logging different information of agent-functionalities. It logs the information both in human- and machinereadable format depending on the information provided.

### `mbsModelLoader.py`

- **Details**: Read textual Exudyn model descriptions, define standard (convenient) random numbers and add randomized parametrization for models

### `misc.py`

- **Details**: Special functions like string operations, etc. used for AI agents
- **Notes**: Ensure that the appropriate model files are available locally or through the Hugging Face model hub.

### `motionAnalysis.py`

- **Details**: main functionality to process sensor output and perform special multibody analysis; postprocessing of data, error and warning handling and conversion in AI-text-readable format

### `myLLM.py`

- **Details**: The MyLLM class is intended for interacting with large language models (LLMs) of different kinds with one interface. It includes functionalities for loading LLMs, to generate text, and to log at different levels; Currently, it supports HF Transformers and GPT4All; It also includes procedures to extract special tokens (thinking, etc.); and logs token counts and performance The model and tokenizer are loaded from the Hugging Face `transformers` library. The script supports both CPU and GPU-based inference, depending on the availability of CUDA and user preference. The llmModelsDict includes a list of models and some metrics to automatically process several models
- **Notes**: Ensure that the appropriate model files are available locally or through the Hugging Face model hub.

### `postProcessing.py`

- **Details**: Post-processing functionalities for agent-results, using Levensthein and other metrics.
- **Notes**: Place the "results.json" on the same level as this script for analysis.

### `processResultsWithOpenAI_GPT4o.py`

- **Details**: This file uses the API from OpenAI to run judge on LLM conjectures with ChatGPT
- **Notes**: Ensure that the appropriate model files are available locally or through the Hugging Face model hub.

### `readExudynHelper.py`

- **Details**: Read and parse exudynHelper.py and evalHelper and provide information as dictionary with tags

### `templatesAndLists.py`

- **Details**: main prompt templates (template to create the prompt for LLMs, using their prompt templates ...), further lists, and dictionaries used by agent; dictOfEvaluationMethods: defines the evaluation methods with hints, needed codes and descriptions
- **Notes**: Ensure that the appropriate model files are available locally or through the Hugging Face model hub.

### `testModelCreation.py`

- **Details**: Main code and class for simulation model creation and testing; In RunMBSmodelTests, Exudyn elements are extracted, example code is generated and LLM is asked to create code; Further, code is tested on executabilty and correctness (using ground-truth sample codes); use MergeTestModelResults to merge results
- **Notes**: Ensure that the appropriate model files are available locally or through the Hugging Face model hub.

### `testModelCreationDriver.py`

- **Details**: Driver file for testModelCreation, to be used from command line; type python testModelCreationDriver.py -h to see help Run tests for single LLM, or merge results and export to latex
- **Notes**: Ensure that the appropriate model files are available locally or through the Hugging Face model hub.

### `utilities.py`

- **Details**: Basic support functions for LLM-agents, and further functionalities of the LLM Lab. Mainly processing text, numbers, extraction of xml-tags, logging helpers, file/json read/write, camelCase processing, latex export, ...

### `writeREADME.py`

- **Details**: This script just writes the headers of the .py files in this folder to a .txt file

### `agentInputData/modelDescriptions.py`

- **Details**: Lists, dictionaries and lists used by agend
- **Notes**: Collection of modeldescriptions and according possible parametrizations.

### `helperFiles/evalHelper.py`

- **Details**: this file serves as a documented example that shall be used by LLMs to update information on their internal knowledge of Exudyn; this file specifically addresses evaluation; the text is split by #%% comments, including tags for respective functionality

### `helperFiles/exudynHelper.py`

- **Details**: this file serves as a documented example that shall be used by LLMs to update information on their internal knowledge of Exudyn; the text is split by #%% comments, including tags for respective functionality

---

## License

BSD-3-Clause license
