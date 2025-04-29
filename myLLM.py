# -*- coding: utf-8 -*-
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# This is part of the AI engineering lab project
#
# Filename: myLLM.py
#
# Details:  The MyLLM class is intended for interacting with large language models (LLMs) of different kinds with one interface.
#           It includes functionalities for loading LLMs, to generate text, and to log at different levels;
#           Currently, it supports HF Transformers and GPT4All;
#           It also includes procedures to extract special tokens (thinking, etc.); and logs token counts and performance
#           The model and tokenizer are loaded from the Hugging Face `transformers` library.
#           The script supports both CPU and GPU-based inference, depending on the availability of CUDA and
#           user preference.
#           The llmModelsDict includes a list of models and some metrics to automatically process several models
#
# Authors:  Tobias Möltner, Johannes Gerstmayr 
# Date:     2024-09-18
# Notes:    Ensure that the appropriate model files are available locally or through the Hugging Face model hub.
#
# License:  BSD-3 license
#
# Installation:
#           For GPT4All, use: pip install gpt4all[cuda]
# 
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

import sys
import os
import time
import numpy as np
from difflib import get_close_matches
import ast
import traceback

# try:
#     from exuai.misc import GetLongestWords, IsNumberOrSpecialCharacter, ReplaceDuplicates
#     from exuai.logger import Logger, STYLE
# except: #running locally
from misc import GetLongestWords, IsNumberOrSpecialCharacter, ReplaceDuplicates
from logger import Logger, STYLE
from utilities import SaveClassObjectConfig

isLinux = 'linux' in sys.platform #win32 is windows, darwin is MacOS!
if isLinux:
    print('running MyLLM on linux')

# if imported here, it always takes some time to load
# try:
#     from transformers import  AutoConfig, pipeline, BitsAndBytesConfig
# except:
#     pass

# try:
#     from gpt4all import GPT4All
# except:
#     pass


#a list of models (currently only gguf), including some info, short names and number of parameters (in billion)
#quality includes the current score of correct models (0-100) in %
#NOTE: short names should include only characters that are valid file names
#Q = quantization

#Meta-Llama-3.1-8B-Instruct-128k-Q4_0: from gpt4all app internal
#Meta-Llama-3-8B-Instruct.Q4_0.gguf: from gpt4all app internal
#phi-4-Q4_0.gguf: from gpt4all app internal

# Meta-Llama-3-8B-Instruct-Q8_0.gguf: https://huggingface.co/QuantFactory/Meta-Llama-3-8B-Instruct-GGUF/tree/main
# Meta-Llama-3.1-8B-Instruct-Q8_0.gguf: https://huggingface.co/bartowski/Meta-Llama-3.1-8B-Instruct-GGUF/tree/main

# Tested alternatives (overall results V5)
# UNUSED: Meta-Llama-3-8B-Instruct_QF.Q8_0.gguf: https://huggingface.co/QuantFactory/Meta-Llama-3-8B-Instruct-GGUF/tree/main
# UNUSED: Meta-Llama-3-8B-Instruct_LMS-Q8_0.gguf: https://huggingface.co/lmstudio-community/Meta-Llama-3-8B-Instruct-GGUF/tree/main
# UNUSED: Meta-Llama-3.1-8B-Instruct_MP.Q8_0.gguf: https://huggingface.co/MaziyarPanahi/Meta-Llama-3.1-8B-Instruct-GGUF/tree/main

# Produce a lot more text, but correct score is OK:
# UNUSED: Meta-Llama-3-8B-Instruct-Q8_0.gguf: https://huggingface.co/mradermacher/Meta-Llama-3-8B-Instruct-GGUF/resolve/main/Meta-Llama-3-8B-Instruct.Q8_0.gguf

# phi-4.Q8_0.gguf: https://huggingface.co/mradermacher/phi-4-GGUF/resolve/main/phi-4.Q8_0.gguf
# phi-4.Q4_K_M.gguf: https://huggingface.co/mradermacher/phi-4-GGUF/resolve/main/phi-4.Q4_K_M.gguf

# Viper-Coder-v1.7-Vsm6.Q8_0.gguf: https://huggingface.co/mradermacher/Viper-Coder-v1.7-Vsm6-GGUF
# Viper-Coder-v1.7-Vsm6.Q4_0.gguf: https://huggingface.co/mradermacher/Viper-Coder-v1.7-Vsm6-GGUF

# DeepSeek-Coder-V2-Lite-Instruct-Q6_K.gguf: https://huggingface.co/bartowski/DeepSeek-Coder-V2-Lite-Instruct-GGUF/blob/main/DeepSeek-Coder-V2-Lite-Instruct-Q6_K.gguf
# wizardcoder-python-34b-v1.0.Q4_K_M.gguf: https://huggingface.co/TheBloke/WizardCoder-Python-34B-V1.0-GGUF/blob/main/wizardcoder-python-34b-v1.0.Q4_K_M.gguf

# gemma-3-27b-it-q4_0.gguf: https://huggingface.co/google/gemma-3-27b-it-qat-q4_0-gguf/tree/main

#%%+++++++++++++++++++++++++
# define scores (eval metrics) for each model. Make sure that string after "score" exists in llmModelsDict-key
llmScoresDict = {
    'Llama2-70B': {'MATH':-1, 'IFEval':-1, 'MMLU-Pro':-1, 'GPQA':-1}, # N/A - only used for illustration of performance-progress over past years
    'Llama3-8B': {'MATH':9, 'IFEval':48, 'MMLU-Pro':29, 'GPQA':6}, # from HF leaderboard bfloat16 
    'Llama3.1-8B': {'MATH':16, 'IFEval':49, 'MMLU-Pro':31, 'GPQA':9}, # from HF leaderboard bfloat16 
    'Llama3.1-70B': {'MATH':38, 'IFEval':87, 'MMLU-Pro':48, 'GPQA':14}, # from HF leaderboard bfloat16 
    'Llama3.1-405B': {'MATH':31, 'IFEval':85, 'MMLU-Pro':85, 'GPQA':51}, # from HF Modelcard bfloat16 (add footnote) - selfreported by META
    'Llama3.3-70B': {'MATH':48, 'IFEval':90, 'MMLU-Pro':69, 'GPQA':11}, # from HF leaderboard bfloat16 
    'Llama4-Scout': {'MATH':50, 'IFEval':0, 'MMLU-Pro':74, 'GPQA':57}, # from HF modelcard (not yet available in the HF leaderboard)
    'Codestral-22B': {'MATH':10, 'IFEval':58, 'MMLU-Pro':24, 'GPQA':7}, # from HF leaderboard bfloat16
    'DeepSeekCoder-33B': {'MATH':29, 'IFEval':47, 'MMLU-Pro':37, 'GPQA':37}, # from https://github.com/deepseek-ai/deepseek-coder (add footnote) - selfreported by DeepSeek # MATH estimation based on 6.7B model,  IFEval based on BBH, MMLU-Pro and GPQA based on MMLU 
    'DeepSeekCoder-16B': {'MATH':62, 'IFEval':84, 'MMLU-Pro':60, 'GPQA':-1}, # from paper: https://github.com/deepseek-ai/DeepSeek-Coder-V2/blob/main/paper.pdf (add footnote with paper citation) - selfreported by DeepSeek
    'DeepSeek-R1': {'MATH':97, 'IFEval':83, 'MMLU-Pro':84, 'GPQA':72}, # from HF Modelcard bfloat16 (add footnote) - selfreported by DeepSeek
    'Qwen2.5-32B': {'MATH':63, 'IFEval':83, 'MMLU-Pro':52, 'GPQA':12}, # from HF leaderboard bfloat16 
    'Qwen2.5-72B': {'MATH':60, 'IFEval':86, 'MMLU-Pro':51, 'GPQA':17}, # from HF leaderboard bfloat16 
    'QwenCoder-32B': {'MATH':-1, 'IFEval':-1, 'MMLU-Pro':-1, 'GPQA':-1}, # no proper evaluation metrics available! only: https://qwenlm.github.io/blog/qwen2.5-coder-family/
    'Phi4': {'MATH':46, 'IFEval':67, 'MMLU-Pro':47, 'GPQA':12}, # from HF leaderboard bfloat16 
    'Calme3.1-78B': {'MATH':39, 'IFEval':81, 'MMLU-Pro':69, 'GPQA':19}, # from HF leaderboard bfloat16 
    'Calme3.2-78B': {'MATH':40, 'IFEval':81, 'MMLU-Pro':70, 'GPQA':20}, # from HF leaderboard bfloat16 
    'Starcoder2-15B': {'MATH':6, 'IFEval':28, 'MMLU-Pro':15, 'GPQA':3}, # from HF leaderboard bfloat16 
    'ViperCoder': {'MATH':46, 'IFEval':50, 'MMLU-Pro':48, 'GPQA':20}, # from HF leaderboard bfloat16 
    'FluentlyLM': {'MATH':54, 'IFEval':81, 'MMLU-Pro':53, 'GPQA':18}, # from HF leaderboard bfloat16 
    'QwenQwQ-32B': {'MATH':-1, 'IFEval':-1, 'MMLU-Pro':-1, 'GPQA':-1}, # strange documentation and different eval-metrics found, kept to zero to prevent mistakes...
    'WizardCoderPython-34B': {'MATH':-1, 'IFEval':-1, 'MMLU-Pro':-1, 'GPQA':-1}, # not found (too old?)
    'Gemma3-27B': {'MATH':50, 'IFEval':-1, 'MMLU-Pro':52, 'GPQA':24},  # from HF modelcard bfloat 16
    'GPT-4o': {'MATH':-1, 'IFEval':-1, 'MMLU-Pro':-1, 'GPQA':-1},  # from HF modelcard bfloat 16
}

llmModelsDict = {
    'OpenAI_GPT-4o': {'type':'API', 'VRAM':-1, 'nParam':-1, 'Q':-1, 'ctxSize':-1, 'shortName':'GPT-4o', 'quality':0}, 
    'qwen2.5-coder-32b-instruct-q5_0.gguf': {'type':'gguf', 'VRAM':22.1, 'nParam':32, 'Q':5, 'ctxSize':32, 'shortName':'QwenCoder-32B-Q5', 'quality':64}, 
    'qwen2.5-coder-32b-instruct-q4_0.gguf': {'type':'gguf', 'VRAM':18.6, 'nParam':32, 'Q':4, 'ctxSize':32, 'shortName':'QwenCoder-32B-Q4', 'quality':64},
    #worse than bartowski Q8: 
    'Meta-Llama-3.1-8B-Instruct_MP.Q8_0.gguf': {'type':'gguf', 'VRAM':8.3, 'nParam':8, 'Q':8, 'ctxSize':128, 'shortName':'Llama3.1-8B-Q8-MP', 'quality':8},
    'Meta-Llama-3.1-8B-Instruct-Q8_0.gguf': {'type':'gguf', 'VRAM':8.3, 'nParam':8, 'Q':8, 'ctxSize':128, 'shortName':'Llama3.1-8B-Q8', 'quality':8},
    'Meta-Llama-3.1-8B-Instruct-128k-Q4_0.gguf':{'type':'gguf', 'VRAM':4.5, 'nParam':8, 'Q':4, 'ctxSize':128, 'shortName':'Llama3.1-8B-Q4', 'quality':8},
    #
    'Meta-Llama-3-8B-Instruct-Q8_0.gguf': {'type':'gguf', 'VRAM':8.5, 'nParam':8, 'Q':4, 'ctxSize':8, 'shortName':'Llama3-8B-Q8', 'quality':15},
    #'Meta-Llama-3-8B-Instruct.Q8_0.gguf': {'type':'gguf', 'VRAM':8.5, 'nParam':8, 'Q':4, 'ctxSize':8, 'shortName':'Llama3-8B-Q8', 'quality':15},
    #'Meta-Llama-3-8B-Instruct_QF.Q8_0.gguf': {'type':'gguf', 'VRAM':8.5, 'nParam':8, 'Q':4, 'ctxSize':8, 'shortName':'Llama3-8B-Q8-QF', 'quality':15},
    'Meta-Llama-3-8B-Instruct_LMS-Q8_0.gguf': {'type':'gguf', 'VRAM':8.5, 'nParam':8, 'Q':4, 'ctxSize':8, 'shortName':'Llama3-8B-Q8-LMS', 'quality':15},
    'Meta-Llama-3-8B-Instruct.Q4_0.gguf': {'type':'gguf', 'VRAM':4.5, 'nParam':8, 'Q':4, 'ctxSize':8, 'shortName':'Llama3-8B-Q4', 'quality':15},
    #
    'llama-2-70b-chat.Q5_K_M.gguf': {'type':'gguf', 'VRAM':48.8, 'nParam':69, 'Q':5, 'ctxSize':4, 'shortName':'Llama2-70B-Q5', 'quality':0},
    #
    'gemma-3-27b-it-q4_0.gguf': {'type':'gguf', 'VRAM':17.2, 'nParam':27, 'Q':4, 'ctxSize':128, 'shortName':'Gemma3-27B-Q4', 'quality':0},
    'Codestral-22B-v0.1-Q6_K.gguf': {'type':'gguf', 'VRAM':18, 'nParam':22, 'Q':6, 'ctxSize':32, 'shortName':'Codestral-22B-Q6', 'quality':55},
    'Llama-3.3-70B-Instruct-IQ2_XS.gguf': {'type':'gguf', 'VRAM':21.7, 'nParam':70, 'Q':2, 'ctxSize':128, 'shortName':'Llama3.3-70B-Q2', 'quality':0},
    'phi-4-Q4_0.gguf': {'type':'gguf', 'VRAM':8.2, 'nParam':14.7, 'Q':4, 'ctxSize':16, 'shortName':'Phi4-Q4', 'quality':64},
    'phi-4.Q4_K_M.gguf': {'type':'gguf', 'VRAM':8.8, 'nParam':14.7, 'Q':4, 'ctxSize':16, 'shortName':'Phi4-Q4-KM', 'quality':64},
    'phi-4.Q8_0.gguf': {'type':'gguf', 'VRAM':15, 'nParam':14.7, 'Q':4, 'ctxSize':16, 'shortName':'Phi4-Q8', 'quality':64},
    'qwq-32b-q4_k_m.gguf': {'type':'gguf', 'VRAM':19.3, 'nParam':32, 'Q':4, 'ctxSize':32, 'shortName':'QwenQwQ-32B-Q4', 'quality':0},
    'FluentlyLM-Prinum.Q4_K_M.gguf': {'type':'gguf', 'VRAM':19.3, 'nParam':32, 'Q':4, 'ctxSize':32, 'shortName':'FluentlyLM-Q4', 'quality':64},
    'Viper-Coder-v1.7-Vsm6.Q8_0.gguf': {'type':'gguf', 'VRAM':16.0, 'nParam':14.8, 'Q':8, 'ctxSize':128, 'shortName':'ViperCoder-Q8', 'quality':0},
    'Viper-Coder-v1.7-Vsm6.Q4_K_M.gguf': {'type':'gguf', 'VRAM':9.0, 'nParam':14.8, 'Q':8, 'ctxSize':128, 'shortName':'ViperCoder-Q4', 'quality':0},
    'DeepSeek-Coder-V2-Lite-Instruct-Q6_K.gguf': {'type':'gguf', 'VRAM':13.7, 'nParam':15.7, 'Q':6, 'ctxSize':128, 'shortName':'DeepSeekCoder-16B-Q6', 'quality':0},
    'wizardcoder-python-34b-v1.0.Q4_K_M.gguf': {'type':'gguf', 'VRAM':20.2, 'nParam':34, 'Q':4, 'ctxSize':128, 'shortName':'WizardCoderPython-34B-Q4', 'quality':0},


    #Qwen2.5-72B-Instruct-Q4_K_M.gguf is not usable, possibly wrong template!
    'Qwen2.5-72B-Instruct-Q4_K_M.gguf': {'type':'gguf', 'VRAM':47, 'nParam':72, 'Q':4, 'ctxSize':128, 'shortName':'Qwen2.5-72B-Q4', 'quality':0},
    'Qwen2.5-32B-Instruct-Q5_K_S.gguf': {'type':'gguf', 'VRAM':22.1, 'nParam':32, 'Q':5, 'ctxSize':128, 'shortName':'Qwen2.5-32B-Q5', 'quality':58},
    'Qwen2.5-32B-Instruct-Q4_K_L.gguf': {'type':'gguf', 'VRAM':19.9, 'nParam':32, 'Q':5, 'ctxSize':128, 'shortName':'Qwen2.5-32B-Q4', 'quality':58},
    'meta-llama_Llama-Scout-17B-16E-Instruct-Q4_K_M/meta-llama_Llama-4-Scout-17B-16E-Instruct-Q4_K_M-00001-of-00002.gguf': {'type':'gguf', 'VRAM':67.5, 'nParam':108, 'Q':5, 'ctxSize':256, 'shortName':'Llama4-Scout-Q4', 'quality':0},
    'Hermes-3-Llama-3.1-405B-Q8_0/Hermes-3-Llama-3.1-405B-Q8_0-00001-of-00011.gguf': {'type':'gguf', 'VRAM':401.62, 'nParam':405, 'Q':8, 'ctxSize':128, 'shortName':'Llama3.1-405B-Q8', 'quality':0},
    'DeepSeek-R1-Q8.gguf': {'type':'gguf', 'VRAM':676.8, 'nParam':671, 'Q':8, 'ctxSize':128, 'shortName':'DeepSeek-R1-Q8', 'quality':0},
    'deepseek-coder-33b-instruct.Q4_0.gguf': {'type':'gguf', 'VRAM':19, 'nParam':33, 'Q':4, 'ctxSize':0, 'shortName':'DeepSeekCoder-33B-Q4', 'quality':0},
    # HF (add quality for each model!)
    'google/gemma-3-27b-it':{'type':'huggingface', 'VRAM':54.81, 'nParam':27, 'Q':16, 'ctxSize':16, 'shortName':'Gemma3-27B-HF', 'quality':0},
    'meta-llama/Llama-3-8B-Instruct': {'type':'huggingface', 'VRAM':16.07, 'nParam':8, 'Q':4, 'ctxSize':8, 'shortName':'Llama3-8B-HF', 'quality':15},
    'meta-llama/Llama-3.1-8B-Instruct  ': {'type':'huggingface', 'VRAM':16.07, 'nParam':8, 'Q':4, 'ctxSize':128, 'shortName':'Llama3.1-8B-HF-Q4', 'quality':0},
    'meta-llama/Llama-3.1-8B-Instruct ': {'type':'huggingface', 'VRAM':16.07, 'nParam':8, 'Q':8, 'ctxSize':128, 'shortName':'Llama3.1-8B-HF-Q8', 'quality':0},
    'meta-llama/Llama-3.1-8B-Instruct': {'type':'huggingface', 'VRAM':16.07, 'nParam':8, 'Q':16, 'ctxSize':128, 'shortName':'Llama3.1-8B-HF', 'quality':0},
    'meta-llama/Llama-3.1-70B-Instruct': {'type':'huggingface', 'VRAM':141.06, 'nParam':70, 'Q':16, 'ctxSize':128, 'shortName':'Llama3.1-70B-HF', 'quality':0},
    'meta-llama/Llama-3.3-70B-Instruct': {'type':'huggingface', 'VRAM':141.06, 'nParam':70, 'Q':16, 'ctxSize':128, 'shortName':'Llama3.3-70B-HF', 'quality':61},
    'MaziyarPanahi/calme-3.1-instruct-78b': {'type':'huggingface', 'VRAM':206.2, 'nParam':78, 'Q':8, 'ctxSize':32, 'shortName':'Calme3.1-78B-HF', 'quality':46},
    'MaziyarPanahi/calme-3.2-instruct-78b': {'type':'huggingface', 'VRAM':206.2, 'nParam':78, 'Q':8, 'ctxSize':32, 'shortName':'Calme3.2-78B-HF', 'quality':0},
    'Qwen/Qwen2.5-72B-Instruct': {'type':'huggingface', 'VRAM':177.51, 'nParam':72, 'Q':8, 'ctxSize':32, 'shortName':'Qwen2.5-72B-HF', 'quality':0}, 
    'Qwen/Qwen2.5-72B-Instruct-GPTQ-Int8': {'type':'huggingface', 'VRAM':80.91, 'nParam':72, 'Q':8, 'ctxSize':32, 'shortName':'Qwen2.5-72B-Q8-HF', 'quality':58},   
    'deepseek-ai/DeepSeek-Coder-V2-Lite-Instruct': {'type':'huggingface', 'VRAM':31.41, 'nParam':15.7, 'Q':16, 'ctxSize':128, 'shortName':'DeepSeekCoder-16B-HF', 'quality':0},  
    'mistralai/Codestral-22B-v0.1': {'type':'huggingface', 'VRAM':44.5, 'nParam':22, 'Q':16, 'ctxSize':32, 'shortName':'Codestral-22B', 'quality':0},
    'bigcode/starcoder2-15b-instruct-v0.1': {'type':'huggingface', 'VRAM':63.9, 'nParam':22, 'Q':16, 'ctxSize':16, 'shortName':'StarCoder2-15B', 'quality':0},
    }

#%%
#now insert scores, using short names ...
if True:
    #llmScoresList = list(llmScoresDict)
    for keyModel, valueModel in llmModelsDict.items():
        if 'MATH' not in valueModel:
            foundScore = False
            for key, value in llmScoresDict.items():
                shortName = valueModel['shortName']
                if shortName.lower().startswith(key.lower()):
                    llmModelsDict[keyModel].update(value)
                    foundScore = True
                    #print('model '+shortName+', score=',key)
            if not foundScore:
                print('**************************************************')
                print('WARNING: MyLLM model '+shortName+': no score found')
                print('**************************************************')

#%%
#merge parts of .gguf models from HuggingFace:
#linux ?: cat Mixtral-8x22B-v0.1.Q4_K_M.gguf-part-* > Mixtral-8x22B-v0.1.Q4_K_M.gguf
#windows: cmd: COPY /B dolphin-2.9-llama3-70b.Q8_0.gguf.part1of2 + dolphin-2.9-llama3-70b.Q8_0.gguf.part2of2 dolphin-2.9-llama3-70b.Q8_0.gguf
# UPDATE: do NOT merge parts... just call one part and the other parts will be loaded automatically!

def GetLLMmodelNameFormShortName(shortName):
    for key, value in llmModelsDict.items():
        if value['shortName'] == shortName:
            return key
    raise ValueError('GetLLMmodelNameFormShortName: short name "'+shortName+'" does not exist!')

#%%++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
typicalLLMstopTags= ['<|im_end|>', '<|endoftext|>']
#callback for GPT4All
localGenerateTokenCount = 0
localGenerateTokenCountStr = ''
def TokenCallback(token_id, token_string):
    global localGenerateTokenCount, localGenerateTokenCountStr, typicalLLMstopTags
    localGenerateTokenCount += 1
    localGenerateTokenCountStr += token_string
   
    # print(token_string.replace('\n','\\n')+'#', end='', flush=True)          
    # print(token_string, end='', flush=True)          

    #for stop_string in ['</s>', '###', '\n\n\n', '<|im_end|>', '<|endoftext|>']:
    for stop_string in typicalLLMstopTags + ['</score>']: #stop when score received ...
        # if (localGenerateTokenCountStr.strip().endswith(stop_string) ):
        #     # print('\n********* stop generation **********\n')
        #     return False
        if stop_string in localGenerateTokenCountStr[-50:]:
            # print('\n********* stop generation2 **********\n')
            return False

    return True

#%%++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

class MyLLM:
    def __init__(self, modelName, modelQuantization=None, device=None, nThreads=None, logger=None, 
                 logPromptInput = False, 
                 contextWindowMaxSize = 2048, #for gpt4all only #for Exudyn model generation >2048
                 useTokenCallback = True, #to count tokens and to catch endstrings; needed for some models!
                 ):
        """
        Initialize the LLM model with corresponding promptTemplate. Uses either GPU(s) or CPU.

        Args:
            modelName (str): Name or path of the pre-trained model.
            nThreads (int): number of threads to be used in cpu mode.
            logger: either none or a exuai.logger class Logger
            device (Union[int, list[int]]): None (select automatically), -1 (cpu), integer (GPU device) or list of GPU devices
            verbose (bool): enable logging info 
            debug (bool): enable logging on debug level
            modelQuantization (str): Hugging Face model quantization (4bit, 8bit, fp16, bf16).
        """
        # reset global llm-parameter (these parameters track token-specific information of a LLM during runtime between initializations)
        self.numberOfTokensGlobal = 0
        self.numberOfRemovedTokensGlobal = 0
        self.tokensPerSecondGlobal = 0 
        self.durationGlobal = 0
        self.numberOfGenerateCalls = 0
        self.logPromptInput = logPromptInput
        self.contextWindowMaxSize = contextWindowMaxSize
        self.useTokenCallback = useTokenCallback

        # if (modelName.startswith('phi-4')
        #     or modelName.startswith('Viper-Coder')
        #     or modelName.startswith('FluentlyLM')
        #     or 'Qwen2.5' in modelName
        #     ):
        #     self.useTokenCallback = True #for this model, it is needed!



        self.numberOfTokensLocal = 0 
        self.localGenerateTokenCount = 0 #new in GPT4all, real tokens

        
        self.logger = logger
        if self.logger is None:
            self.logger = Logger('LLMlog')
        
        try:
            from gpt4all import GPT4All
        except:
            self.logger.LogDebug('MyLLM Warning: did not find gpt4all Python package')
            
        # Set up backend
        self.logger.LogDebug(f"Initializing MyLLM with model name: {modelName}, device: {device}, number of threads: {nThreads}")
        if modelName.endswith(".gguf") or modelName.endswith(".bin"):
            self.backend = 'GPT4All'
        else:
            self.backend = 'HFtransformers'
        self.logger.LogText(f"LLM: Used backend: {self.backend}")

        if self.useTokenCallback:
            self.logger.LogText("LLM: Using TokenCallback for gguf models")
        
        self.modelName = modelName

        ## CPU core-handling
        #  siehe exudyn RL bsp core/threads abfragen (>nthreads)
        if nThreads is None:
            #use number of cores, which always works well
            self.nThreads = max(1,int(os.cpu_count()/2)) 
        else:
            self.nThreads = nThreads
            
        #self.systemPrompt = self.GetSystemPrompt(systemPrompt)

        ## device handling
        numGPUs = 0
        self.deviceMap = None
        
        if self.backend == 'GPT4All':  
            if device is None:
                self.device = None # choose automatically (first trying to select GPU)
                if isLinux: os.environ["CUDA_VISIBLE_DEVICES"] = str(0) # default set visible device 0 
                self.logger.LogDebug("GPT4All: Selecting CPU / GPU automatically")
            elif device == -1  or device=='cpu':
                self.device = 'cpu'  # choose CPU
                self.logger.LogDebug(f"GPT4All: Using CPU with {self.nThreads} threads")
            elif isinstance(device, int) or device=='cuda' or isinstance(device, list):
                # self.device = 'Kompute' #cuda or gpu for other choices
                # self.logger.LogText(f"GPT4All: Using best GPU with Kompute backend")
                
                # always choose gpu 0 if arg 'cuda' is provided (no multiGPU implemented in GPT4All (yet))
                if isinstance(device, list) or (isinstance(device, int) and device > 0): 
                    device = 0 
                    self.logger.LogWarning('GPT4All does not support device>0 or list, using GPU 0')
                if device=='cuda': 
                    device = 0 
                if isLinux: os.environ["CUDA_VISIBLE_DEVICES"] = str(device) 
                self.device = 'cuda'
                self.logger.LogDebug("GPT4All: Using GPU with cuda backend")
            else:
                raise ValueError('MyLLM: illegal device: '+str(device))
        else: #HF transformers
            if device is None: # automatically choose GPU and CPU (if necessary)
                self.device = None
                self.deviceMap = "auto"
                self.logger.LogDebug("Selecting torch cuda device automatically and CPU (if needed)")

                # Log used GPUs
                # uses ALL CUDA-devices!!! 
                try:
                    import torch
                except:
                    self.logger.LogDebug('MyLLM Warning: did not find torch Python package')
                numGPUs = torch.cuda.device_count() # this command sets all CUDA devices visible
                if numGPUs > 0:
                    # List of visible devices
                    visibleDevices = ",".join(str(i) for i in range(numGPUs))

                    # Set the detected GPUs as visible
                    os.environ["CUDA_VISIBLE_DEVICES"] = visibleDevices
                    for i in range(numGPUs):
                        self.logger.LogText(f"Used GPU {i}: {torch.cuda.get_device_name(i)}")
                else:
                    self.logger.LogText("Attempting auto-selection of CUDA device, but none found.")
            elif device == -1 or device == 'cpu':
                self.device = -1
                self.logger.LogText(f"Using CPU with {self.nThreads} threads")
                self.deviceMap = None
            elif isinstance(device, int): # single specific gpu provided
                self.device = device
                self.deviceMap = None

                # print("VISIBLE: ", os.environ["CUDA_VISIBLE_DEVICES"])
                os.environ["CUDA_VISIBLE_DEVICES"] = str(device)
                try:
                    import torch
                except:
                    self.logger.LogDebug('MyLLM Warning: did not find torch Python package')
                self.logger.LogText(f"Selected GPU {device}: {torch.cuda.get_device_name(device)}") # changed from 0 to device for different GPUs
            elif isinstance(device, list): # list of specific gpus provided
                self.device = None
                self.deviceMap = "auto"

                visibleDevices = ",".join(map(str, device))
                os.environ["CUDA_VISIBLE_DEVICES"] = visibleDevices
                numGPUs = len(device)

                try:
                    import torch
                except:
                    self.logger.LogDebug('MyLLM Warning: did not find torch Python package')
                
                
                print("DEVICE-COUNT: ", torch.cuda.device_count())
                for i in range(numGPUs):
                    self.logger.LogText(f"Used GPU {i}: {torch.cuda.get_device_name(i)}")
            else:
                raise ValueError('MyLLM: illegal device: '+str(device)+' Provide single integer for single GPU or None for multi GPU usage')         

        ## initialize models
        if self.backend == 'GPT4All':
            # GPT4All does not support multi GPU (yet), seperately handled here to use only one GPU
            # Only uses nthreads if device is CPU
            modelLoaded = False
            
            
            if self.modelName.startswith('Qwen2.5-32B-Instruct'): #Qwen makes problems
                self.contextWindowMaxSize = min(2048, self.contextWindowMaxSize)

            # Try to initialize on GPU first if no device specified
            if self.device is None or self.device == 'cuda':
                try:
                    #on WSL, this does not work => gpt4allDevice = 'cuda'
                    gpt4allDevice = 'gpu' if isLinux else 'cuda'
                    self.model = GPT4All(
                        model_name=modelName,
                        n_threads=self.nThreads,  # Threads are only for CPU
                        device=gpt4allDevice, # cuda not possible ATM at hopper?! (CUDA 11 required?)
                        allow_download=True,
                        verbose=True,
                        n_ctx = self.contextWindowMaxSize, #Johannes; changed from 2048, as it gave errors
                    )
                    modelLoaded = True
                    self.logger.LogDebug("GPT4All: Successfully loaded model on GPU")
                    
                except Exception as e:
                    self.logger.LogWarning(f"GPT4All: GPU loading failed, falling back to CPU. Error: {str(e)}")

            # If GPU loading failed or CPU was explicitly set
            if not modelLoaded:
                self.model = GPT4All(
                    model_name=modelName,
                    n_threads=self.nThreads, # if self.device == 'cpu' else None,
                    device='cpu',
                    allow_download=True,
                    verbose=True,
                    n_ctx = self.contextWindowMaxSize, #Johannes; changed from 2048, as it gave errors
                )
                self.device = 'cpu'
                self.logger.LogDebug("GPT4All: Using CPU instead of GPU")

            self.logger.LogText(f"Using GPT4All model: {modelName} on {self.device}, n_ctx={self.contextWindowMaxSize}")
        else: # HF transformers
            # Load model config 
            try:
                from transformers import  AutoConfig, pipeline, BitsAndBytesConfig, AutoTokenizer
            except:
                self.logger.LogDebug('MyLLM Warning: did not find transformers Python package')
            config = AutoConfig.from_pretrained(modelName)
##########################################################################################
            tokenizer = AutoTokenizer.from_pretrained(modelName, trust_remote_code=True) # introduced for deepseek-coder-v2-instruct-lite (outcomment if resulting in error for other models!!!) 
##########################################################################################            
            self.logger.LogDebug(f"Loaded HF-config for {modelName}: {config}")
            
            modelKwargs = {}
            
            # Quantization setup
            if self.device != -1:
                if modelQuantization is None:
                    modelKwargs['torch_dtype'] = "auto"  # Default to auto
                    self.logger.LogText("No custom quantization provided, attempting auto-quantization ...")
                elif modelQuantization == "4bit":
                    modelKwargs["quantization_config"] = BitsAndBytesConfig(
                        load_in_4bit=True,
                        bnb_4bit_compute_dtype=torch.float16,  # Change to torch.bfloat16 if needed
                        bnb_4bit_use_double_quant=True,
                        bnb_4bit_quant_type="nf4"  # NF4 improves quantization accuracy
                    )
                    self.logger.LogText("Loaded model with 4-bit quantization.")
                elif modelQuantization == "8bit":
                    # modelKwargs['torch_dtype'] = torch.float16 # might solve slow inference for f32 or other sub-optimal model quantizations
                    modelKwargs["quantization_config"] = BitsAndBytesConfig(
                        load_in_8bit=True,
                        # llm_int8_threshold=6.0,  # Prevents too many 16-bit fallback operations
                        # llm_int8_enable_fp32_cpu_offload=False  # Ensures all operations stay on GPU
                    )
                    self.logger.LogText("Loaded model with 8-bit quantization.")
                else:
                    # Use specified torch_dtype for other quantizations (e.g., fp16, bf16)
                    modelKwargs['torch_dtype'] = modelQuantization
                    self.logger.LogText(f"Custom quantization {modelQuantization} provided.")
            # Load the pipeline
            try:
                task = None
                if 'causal' in config.architectures[0].lower():
                    task = "text-generation"
                elif 'gemma3' in config.architectures[0].lower(): # gemma specific task (test)
                    task = 'question-answering'
                # add other tasks here
                else:
                    task = 'conversation' #default

                self.pipe = pipeline(
                    task=task,
##########################################################################################
                    trust_remote_code=True, # introduced for deepseek-coder-v2-instruct-lite (outcomment if resulting in error for other models!!!) 
                    
                    ### Also you might have to change the following codelines of the models class deepseek-v2-lite: 
                        # past_length = past_key_values.seen_tokens
                        # max_cache_length = past_key_values.get_max_cache_shape()
##########################################################################################
                    model=modelName,
                    tokenizer=tokenizer,
                    model_kwargs=modelKwargs,
                    device_map=self.deviceMap  # Important for optimized GPU loading
                )
                self.logger.LogText(f"Initialized HuggingFace model: {modelName}")
            except Exception as e:
                self.logger.LogError(f"HF transformers: loading GPU failed - {str(e)}")
                
                

    def Generate(self, prompt, systemPrompt = None, max_tokens=None, temperature=None, top_p=None, top_k=None, repeat_penalty=None, doSample=False, numBeams=1,
                 streaming=False, showTiming=False, showTokensPerSecond=False, returnFullText=True, cleanUpTokenizationSpaces=False,
                 n_batch = None):
        """
        Generate text from a given prompt.

        Args:
            prompt (str): The input text to start the generation.
            systemPrompt (str): The system prompt that guides the behaviour of the LLM in answering questions.
            max_tokens (int): The maximum number of tokens to generate.
            temperature (float): Sampling temperature for Hugging Face models.
            top_p (float): Nucleus sampling probability for Hugging Face models.
            top_k (int): The top_k parameter for GPT4All (only applicable for GPT4All).
            repeat_penalty (float): Penalty for repeated tokens in GPT4All.
            doSample (bool): Whether to sample or not (greedy decoding if False).
            streaming (bool): Whether to streaming or not (only GPT4All).
            showTiming (bool): Whether to show output generation time or not.
            showTokensPerSecond (bool): Whether to show the approximation of tokens in generated output.
            returnFullText(bool): Whether to return full output (True), including the input, or only the added text (False) (only HF-transformers).
            cleanUpTokenizationSpaces (bool): Whether or not to clean up the potential extra spaces in the text output (only HF-transformers).
            n_batch (int): for GPT4All; default=8 => increase for small models to increase speed

        Returns:
            str: Generated text.
        """
        
        self.numberOfGenerateCalls += 1
        if self.logPromptInput:
            self.logger.LogDebug(f"Generating text with prompt: max_tokens: {max_tokens}, temperature: {temperature}")

        self.numberOfTokensLocal = 0     #string-based
        self.numberOfRemovedTokensLocal = 0
        if self.backend == "GPT4All":
            global localGenerateTokenCount, localGenerateTokenCountStr, typicalLLMstopTags
            localGenerateTokenCount = 0 #updated in callback function
            localGenerateTokenCountStr = ''

            # GPT4All inference with specific arguments
            opts = {}

            if max_tokens is not None: opts['max_tokens'] = max_tokens
            #if max_tokens is not None: opts['n_predict'] = max_tokens # does not incorporate the input so n_ctx = n_predict + input prompt [tokens]
            
            if n_batch is not None:
                opts['n_batch'] = n_batch 

            if self.modelName.startswith('Qwen2.5-32B-Instruct'): #Qwen makes problems
                repeat_penalty = 1.25
                opts['repeat_last_n'] = 128 #default: 64
                
            if self.modelName.startswith('FluentlyLM'): #also includes repeatings
                repeat_penalty = 1.18

            # thinking model
            if self.modelName.startswith('QwenQwQ-32B'): # testing for optimal inference args 
                repeat_penalty = 1.25
                prompt = prompt + "<think>\n"

            # default:
            # temp: float = 0.7,
            # top_k: int = 40,
            # top_p: float = 0.4,
            # min_p: float = 0.0,
            # repeat_penalty: float = 1.18,
            # repeat_last_n: int = 64,

            #if values are not given, turn into deterministic mode (temp=0, top_k=0, top_p=1.0, repeat_penalty=1.0)
            #these parameters are ideal for #ideal for Llama3.x 8B, QwenCoder32B, Phi4
            if temperature is not None:
                opts['temp'] = temperature
            else:
                opts['temp'] = 0. 
            if top_k is not None:
                opts['top_k'] = top_k
            else:
                opts['top_k'] = 0
            if top_p is not None:
                opts['top_p'] = top_p
            else:
                opts['top_p'] = 1.0
            if repeat_penalty is not None:
                opts['repeat_penalty'] = repeat_penalty
            else:
                opts['repeat_penalty'] = 1.0

            opts['streaming'] = streaming
            if self.useTokenCallback:
                opts['callback'] = TokenCallback

            try:
                with self.model.chat_session(system_prompt=systemPrompt):
                    if self.logPromptInput: 
                        self.logger.LogDebug(f"LLM-Input: {prompt}")
                    timeStamp = time.time()
                    self.numberOfTokensLocal = 0
                    if not streaming:
                        output = self.model.generate(prompt, **opts)
                    else: #slower
                        output = ''
                        for token in self.model.generate(prompt, **opts):
                            output += str(token)
                            # print(str(token),sep='',end='')
                            self.numberOfTokensLocal += 1
                            stopGeneration = False
                            for stopTag in typicalLLMstopTags:
                                if stopTag in output: #happens with Phi4; workaround
                                    print('\n********* stop generation **********\n')
                                    stopGeneration = True
                            if stopGeneration: break
                        # print()
                    # if not streaming: #in both cases, output represents the characters, not the tokens!
                    if self.useTokenCallback:
                        self.numberOfTokensLocal = localGenerateTokenCount
                        approximated = ''
                    else:
                        self.numberOfTokensLocal = max(1,int(len(output) / 4) )
                        approximated = '(4 chars/token)'

                    for stopTag in typicalLLMstopTags:
                        if stopTag in output:
                            tokensOld = int(len(output)/4)
                            output = output.split(stopTag)[0]
                            self.numberOfRemovedTokensLocal = tokensOld - int(len(output)/4)
                            if not self.useTokenCallback:
                                self.logger.LogWarning(f'remove text {stopTag}, removed '+str(self.numberOfRemovedTokensLocal)+' tokens')
                        
                    self.durationLocal = max(0.01,time.time() - timeStamp)
    
                    
                    self.tokensPerSecondLocal = round(self.numberOfTokensLocal/self.durationLocal,2)
                    timingText = f"LLM generation time={self.durationLocal} seconds\n"
                    tokensText = f"LLM generated {self.numberOfTokensLocal} tokens, {self.tokensPerSecondLocal} tokens/second {approximated}\n"
                    if showTiming or showTokensPerSecond:
                        self.logger.LogDebug(timingText*showTiming + tokensText*showTokensPerSecond)
            except KeyboardInterrupt:
                print("Keyboard interrupt requested...exiting")
                raise ValueError('Keyboard interrupt reraised')
            except:
                exceptionText = traceback.format_exc()
                self.logger.LogError(f'Generate raised exception:\n{exceptionText}')
                
                
        else:
            # Hugging Face pipeline inference
            if systemPrompt: # specific system prompt desired
                promptFormatted = [
                    {"role": "system", "content": systemPrompt},
                    {"role": "user", "content": prompt},
                ]
            else: 
                promptFormatted = [
                    {"role": "user", "content": prompt},
                ]
            
            if self.logPromptInput: 
                self.logger.LogDebug(f"LLM-Input: {promptFormatted}")
            
            self.numberOfTokensLocal = 0
            timeStamp = time.time()
            output = self.pipe(
                promptFormatted,
                #max_length=max_tokens,
                max_new_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                do_sample=doSample,
                num_beams=numBeams,
                return_full_text=returnFullText,
                clean_up_tokenization_spaces=cleanUpTokenizationSpaces,
                # add additional args here (if needed)
            )[0]['generated_text']
            
            self.durationLocal = max(0.01,time.time() - timeStamp)
            
            approximated = ''
            self.numberOfTokensLocal = max(1,int(len(output) / 4) )
            approximated = '(4 chars/token)'
            self.tokensPerSecondLocal = round(self.numberOfTokensLocal/self.durationLocal,2)

            timingText = f"LLM generation time={self.durationLocal} seconds\n"
            tokensText = f"LLM generated {self.numberOfTokensLocal} tokens, {self.tokensPerSecondLocal} tokens/second {approximated}\n"
            if showTiming or showTokensPerSecond:
                self.logger.LogDebug(timingText*showTiming + tokensText*showTokensPerSecond)

        # update global parameter
        self.numberOfTokensGlobal += self.numberOfTokensLocal
        self.numberOfRemovedTokensGlobal += self.numberOfRemovedTokensLocal
        self.durationGlobal += self.durationLocal
        self.tokensPerSecondGlobal = self.numberOfTokensGlobal / max(0.01,self.durationGlobal)
        
        self.thinkingString = ''
        thinkingStrings = ['</think>', #deepseek R1
                           #add more from other models
                          ]
        
        for thinking in thinkingStrings:
            if thinking in output:
                pos = output.rfind(thinking)+len(thinking)
                self.thinkingString = output[:pos]
                output = output[pos:]
                self.logger.LogDebug('found thinking region in ouput:\n'+self.thinkingString)
        
        return output

    def QuestionAnswerContextCheck(self, question, answer, context, exceptionIfFails = False, **kwargs):
        """
        Check if answer to question is True or False with LLM, using provided context.

        Args:
            question (str): The question to be asked.
            answer (str): The answer to be checked.
            context (str): The context to be used.
            **kwargs: options for MyLLM.Generate(...)
        Returns:
            str: string containing only True or False; otherwise, a warning is raised
        """
        
        prompt = 'Check if the following answer correctly answers the question, using the provided context.\n'
        prompt += 'Question:"'+question+'"\n'
        prompt += 'Answer:"'+answer+'"\n'
        prompt += 'Context:"'+context+'"\n'
        prompt += 'Respond only with the single words True or False, where True must be only used if it is strictly correct!'
        result = self.Generate(prompt, **kwargs).strip()
        if result != 'True' and result != 'False':
            if exceptionIfFails:
                raise ValueError('QuestionAnswerContextCheck: Invalid result: "'+result+'"')
            self.logger.LogWarning('Invalid result from QuestionAnswerContextCheck: "'+result+'"')
        return result

    def GenerateQuestionFromContext(self, context, randomWords=False, printWord=False, **kwargs):
        """
        Generate question from given context, possibly focussing on randomly selected words in text.

        Args:
            context (str): The context to be used.
            randomWords (bool): False: no randomization; True: will focus on a specific word, randomly selected from longest 25% of words given
            printWord (bool): True: print randomly selected word
            **kwargs: options for MyLLM.Generate(...)
        Returns:
            str: string containing only True or False; otherwise, a warning is raised
        """
        if not randomWords:
            prompt = 'Create an appropriate question from the following context: "'
        else:
            words = GetLongestWords(context)
            n = max(1,int(len(words)/4))
            randomWord = words[np.random.randint(n)]
            if printWord: 
                self.logger.LogText (f"randomWord={randomWord}") 
            prompt = 'Create an appropriate question, focusing on the word "'+randomWord+'", using the following context: "'
        prompt += context+'"\n\n'
        prompt += 'Respond only with the question and no other text!'
        result = self.Generate(prompt, **kwargs).strip()
        return result

    def AnswerQuestionWithContext(self, question, context, **kwargs):
        """
        Answer the question using only the context using LLM.

        Args:
            question (str): The question to be checked.
            context (str): The context to be used.
            **kwargs: options for MyLLM.Generate(...)
        Returns:
            str: answer to question
        """
        prompt = 'Answer the question "'+question+'" with the given context "'+context+'".\n'
        prompt += context+'Respond only with the answer itself, but with no other text like "the answer is:"'
        result = self.Generate(prompt, **kwargs)
        return result

    def ExchangeWord(self, word, **kwargs):
        """
        Given a word in arg word, exchange it to a similar word, not necessarily a synonym, but with a different meaning

        Args:
            word (str): Given word.
            **kwargs: options for MyLLM.Generate(...)
        Returns:
            str: New word
        """
        
        if not IsNumberOrSpecialCharacter(word):
            prompt = 'Exchange the word "'+word+'" with a single word of a similar category but with a different meaning. '
            prompt += 'Return only the single word and no other text or comments.'
        else:
            prompt = 'Read the string containg a number "'+word+'" and give me a similar single string, e.g., 1.23 => 7.45, or €40 => €12 .\n'
            prompt += 'Return only the single string and no other text or comments.'
            
        
        result = self.Generate(prompt, **kwargs).strip()
        if result.count(' ') != 0:
            print('WARNING: Incorrect result from ExchangeWord: "'+word+' <-> '+result+'"')
            result = result.split(' ')[0].strip()
        return result
    
    def GenerateMultipleChoiceQuestion(self, question, answer, context, nOptions=None, nAdditionalOptions=None, **kwargs):
        """
        Given a question, a corresponding correct answer and a context, a defined number of multiple suitable (possibly wrong) alternative answers for the given question, using the context, are generated.

        Args:
            question (str): Given question.
            answer (str): Given correct answer.
            context (str): Given context on which the question and answers is/are created.
            nOptions (int): Given number alternative answers that the MC-set contains.
            nAdditionalOptions(int): Given number of additional created alternatives of which the most suitable ones are selected.
            **kwargs: options for MyLLM.Generate(...)
        Returns:
            str: Multiple choice question and a set of answers with one being correct.
        """

        # exclude user input in llm-output and cleanup 
        kwargs['returnFullText'] = False
        kwargs['cleanUpTokenizationSpaces'] = True

        def check(checkString): # check if string is in list format
            try:
                list = ast.literal_eval(checkString)
            except:
                list = None
                print("LLM-output not in List format")
            return list
        
        # number of possible answers
        if nOptions is None:
            qa = {
                    'question': question,
                    'correct': 0,
                    'answers': answer
                }
            print("No additional (wrong) answers created.")
        else:
            # Generate alternative answers
            prompt = 'The answer:\n' 
            prompt += '"'+answer+'"'' correctly answers the question:\n'
            prompt += '"'+question+'"'' using information of the context:\n'
            prompt += '"'+context+'"''.\n'
            prompt += 'Provide a list of alternative but wrong answers. Provide only the list in list format like'
            prompt += '["answer1","answer2","answer3",...], where each answer of the list is a string.'
            prompt += 'Ensure each item is a valid Python string enclosed in double quotes (").'
            prompt += 'Do not use any single quotes/apostrophes in the answer strings of the provided list.'
            prompt += 'Generate a maximum of '+str(nOptions+nAdditionalOptions)+' alternative answers.' # to prevent list of answers exceeds maxToken
            prompt += 'Do not provide any other result aside the list of answers!'

            try:
                output = self.Generate(prompt, **kwargs)[0]['generated_text']
                print("Creating Alternative answers with HF-transformers.")
            except:
                output = self.Generate(prompt, **kwargs)
                print("Creating Alternative answers with GPT4All.")
            
            print(output)
           
            # check if output is list
            alternatives = check(output) 
            if alternatives is None:
                return None # No MC-set returned                               

            # Get close matches for alternative answers
            matches = get_close_matches(answer, alternatives, nOptions, 0.0)
            nMatches = len(matches)
            if nMatches < nOptions:
                print('*** nMatches:', nMatches)
            else:
                answers = [answer] + matches  # first one is correct
                answers = ReplaceDuplicates(answers) # replace duplicates with "N/A"
                order = list(range(nMatches))
                np.random.shuffle(order)
                rightPos = order.index(0)
                answersShuffled = [answers[order[i]] for i in range(nMatches)] # number of answers equals matches + 1

                qa = {
                    'question': question,
                    'correct': rightPos,
                    'answers': answersShuffled
                }
        return qa
    
    def AnswerMultipleChoiceQuestion(self, question, answers, **kwargs):
        """
        Given a question and multiple answers, of which just one is correct, the answer deemed correct by the LLM is returned.

        Args:
            question (str): Given question.
            answers (str): Given set of answers, containing one correct.
            **kwargs: options for MyLLM.Generate(...)
        Returns:
            str: Answer deemed correct by the LLM.
        """
        
        # exclude user input in llm-output and cleanup 
        kwargs['returnFullText'] = False
        kwargs['cleanUpTokenizationSpaces'] = True

        def check(checkString): # inner function checking the quality of the LLM-output
            return True
        
        prompt = 'The question:\n' 
        prompt += f'"{question}" has the following answers:\n' 
        prompt += f'"{answers}"\n'
        prompt += 'Of the provided answers only **one** is correct!'
        prompt += 'Which one is the correct answer? Provide only the text of the answer.'
        prompt += 'Do not provide any additional explanation or details, just the text of the correct answer.'

        try:
            output = self.Generate(prompt, **kwargs)[0]['generated_text']
            print("Creating Alternative answers with HF-transformers.")
        except:
            output = self.Generate(prompt, **kwargs)
            print("Creating Alternative answers with GPT4All.")
        
        print(output)
    
        if not check(output): # check fails
            output = None
        print("No answer found!")                              

        return output


    def FreeMemory(self):
        if self.backend == 'GPT4All':  
            self.model.close()

#testing:
if __name__ == '__main__': #only executed if myLLM is executed
    # IMPORTANT information!
    # make sure to only use one device setup (e.g. device = 0) for one script-execution. Python needs a restart after modifying CUDA_VISIBLE_DEVICES dynamically!
    # --> test single- and multi-GPU inference seperately!
    # make sure that the following modules are installed. you can either install them by running: 
    # pip install -r requirements.txt
    
    # or installing them manually with:

    # pip install torch
    # pip install transformers
    # pip install numpy
    # pip install psutil  

    prompt = """
    
The following description of a multibody model is given: 
Projectile motion of a point mass with the following properties: mass m = 15 kg, gravity g = 10.0 m/s^2, initial velocity in x/y/z-direction: vx = 0.3 m/s, vy = 3 m/s, vz = 0 m/s. The initial position is given as x=0 and y=0. Gravity acts along the negative y-axis, and there is no other external propulsion or resistance.

The following evaluation method has been chosen by the user to validate the multibody model:
Use the evaluation method "Perform a rough calculation", which states: Perform a rough calculation based on in combination with a position, velocity or acceleration sensor.

Create an according conjecture (like a hypothesis) for the multibody model based on the evaluation method, such that this conjecture can be used to validate a numerical simulation of the model hereafter.
Make sure that the assumptions of the model are compatible with the conjecture, and there must be only one conjecture.
Put xml-like tags around the conjecture text, marked by these tags: <conjecture> ... </conjecture>.

Also specify which sensor type to use, to which body the sensor is attached and at which local position (if different from [0,0,0]) the sensor is placed.
Put sensor-related information in plain text between tags: <sensor> ... </sensor>.

"""
    

    ## test 1 (single GPU)
    #llmModelName = 'Meta-Llama-3-8B-Instruct.Q4_0.gguf'
    #llmModelName = 'phi-4-Q4_0.gguf'
    llmModelName = 'Meta-Llama-3-8B-Instruct.Q4_0.gguf'
    
    logger = Logger(logDir='logsTest')
    llmModel = MyLLM(modelName=llmModelName, 
                     logger=logger,
                     device=None,
                     useTokenCallback=True,
                     )
    if False:
        max_tokens = 1024*2
        
        output = llmModel.Generate(prompt, 
                                # temperature=0.5,
                                # systemPrompt=None, 
                                max_tokens=max_tokens,
                                #doSample=False, 
                                #    numBeams=4, 
                                #streaming=True,
                                showTiming=True, 
                                showTokensPerSecond=True,
                                returnFullText=False,
                                )
        print('tokens(chars/4)=',llmModel.numberOfTokensLocal)
        print('tokens         =',localGenerateTokenCount)
        print('tokens/second  =',llmModel.tokensPerSecondLocal)
    
        logger.LogText(f"LLM-response test 1: {output}", separator=True, printToConsole=not llmModel.useTokenCallback)

    if True:
        from mbsModelLoader import ModelLoader
        from utilities import ExtractXMLtaggedString
        mbsModelLoader = ModelLoader()
        # only loading models with sample files (needed for comparison) and parameters - ATM
        mbsModelLoader.LoadStandardModelDescriptions(maxDifficultyLevel=25, 
                                                     # specificModels=['nMassOscillatorFG'],
                                                     onlyWithSampleFiles=True, 
                                                     )
        for name in mbsModelLoader.ListOfModels():
            [text, modelData, chosenParameters] = mbsModelLoader.GetModelDescriptionAndDict(name)
            output = llmModel.Generate('translate the following text into German, use "." as decimal point '+
                                       'and put the result into xml tags <german> ... </german> :\n'+
                                       text, 
                                    max_tokens=1024,
                                    returnFullText=True,
                                    )
            resultDict = ExtractXMLtaggedString(output, 'german')
            if resultDict['text'] != None:
                logger.LogText(f'- mbs model description {name}:\n'+resultDict['text']+'\n',
                                separator=True, printToConsole=True)
            else:
                logger.LogText(f'\n***** mbs model description {name} not translated *****\n\n')
    
    # # test 2 (multi-GPU)
    # llmModelName = "meta-llama/Llama-3.3-70B-Instruct"
    # llmModel = MyLLM(modelName=llmModelName, 
    #                  #modelQuantization='8bit', 
    #                  logger=logger,
    #                  device= [0,1],
    #                 #  device='cuda', #on win32/Nvidia4090 works with 'cuda' or 'None'
    #                  )
    
    # output = llmModel.Generate(prompt, 
    #                         # temperature=0.5,
    #                         systemPrompt=None, 
    #                         max_tokens=max_tokens,
    #                         doSample=False, 
    #                         #    numBeams=4, 
    #                         streaming=True,
    #                         showTiming=True, 
    #                         showTokensPerSecond=True,
    #                         returnFullText=False,
    #                         )
    
    # print(output)
