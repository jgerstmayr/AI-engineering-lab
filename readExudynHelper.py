# -*- coding: utf-8 -*-
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# This is part of the AI engineering lab project
#
# Filename: readExudynHelper.py
#
# Details:  Read and parse exudynHelper.py and evalHelper and provide information as dictionary with tags
#
# Author:   Johannes Gerstmayr
# Date:     2025-01-05
#
# License:  BSD-3 license
#
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

import sys
import re
import numpy as np
import os
import copy

listSystemTags = ['general',
                  'general import',
                  'assemble',
                  ]

listSimulationTags = [
                  'simulation settings',
                  'dynamic solver'
                  ]

#parse Exudyn helper and fill into parsedDict
#maxDifficultyLevel: max level up to which tags are included
#parsedDictInit = {}: used to extend existing dict
def ParseExudynHelper(filePath, maxDifficultyLevel=10000, excludeTags=[], 
                      parsedDictInit = {}):
    """
    Parse a file with special comments and organize information into a dictionary.

    Args:
        filePath (str): Path to the file to be parsed.
        maxDifficultyLevel (int): Maximum allowed difficulty level for including a tag.

    Returns:
        dict: A dictionary containing structured information.
    """
   
    with open(filePath, 'r') as file:
        lines = file.readlines()

    parsedDict = copy.deepcopy(parsedDictInit)
    tagCounterStart = 0
    for key, value in parsedDict.items():
        if value['INDEX'] > tagCounterStart:
            tagCounterStart = value['INDEX']

    currentTag = None
    currentCode = []
    tagCounter = tagCounterStart
    skipCurrentTag = False  # Flag to determine if the tag should be skipped

    for linePure in lines:
        line = linePure.strip()

        if line.startswith("#TAG:"):
            # If a new tag is found, finalize the previous one (if not skipped)
            if currentTag and not skipCurrentTag:
                if currentTag in parsedDict:  # Ensure the tag exists before modifying
                    parsedDict[currentTag]['CODE'] = "\n".join(currentCode).strip()

            # Reset and start a new tag
            currentTag = line.split("#TAG:")[1].strip()
            tagCounter += 1

            # Ensure the currentTag exists in parsedDict before any modification
            if currentTag in parsedDict:
                # print('overwrite tag:',parsedDict[currentTag],'with new tag index:', tagCounter)
                del parsedDict[currentTag] #erase it to get a new position in dict
                
            parsedDict[currentTag] = {
                'INDEX': tagCounter,
                'DIFFICULTY': "",
                'REQUIRES': "",
                'NOTES': "",
                'INFO': "",
                'CODE': "",  # Initialize CODE to avoid KeyError
            }
            currentCode = []
            skipCurrentTag = False  # Reset skip flag

        else:
            if line.startswith("#DIFFICULTY:"):
                difficulty = line.split("#DIFFICULTY:")[1].strip()
                parsedDict[currentTag]['DIFFICULTY'] = difficulty
                
                # Check if difficulty exceeds maxDifficultyLevel and set skip flag
                try:
                    if int(difficulty) > maxDifficultyLevel:
                        skipCurrentTag = True
                        parsedDict.pop(currentTag, None)  # Remove the current tag
                except ValueError:
                    pass  # Ignore if difficulty is not a valid integer
                
            elif line.startswith("#REQUIRES:") and not skipCurrentTag:
                parsedDict[currentTag]['REQUIRES'] = line.split("#REQUIRES:")[1].strip()

            elif line.startswith("#INFO:") and not skipCurrentTag:
                parsedDict[currentTag]['INFO'] = line.split("#INFO:")[1].strip()

            elif line.startswith("#NOTES:") and not skipCurrentTag:
                parsedDict[currentTag]['NOTES'] = line.split("#NOTES:")[1].strip()

            elif line.startswith("#%%") and not skipCurrentTag:
                continue  # Skip the section separators

            else:
                if not skipCurrentTag:  # Only collect code if tag is not skipped
                    currentCode.append(linePure.replace('\n', ''))

        # Finalize the last tag if it was not skipped
        if currentTag and not skipCurrentTag:
            parsedDict[currentTag]['CODE'] = "\n".join(currentCode).strip()

    #we need to check if there are tags which cannot be found safely with ExtractElementsInResponse
    # print('extracted tags:')
    listTags = list(parsedDict)
    for i, tag in enumerate(listTags):
        # print('   '+tag)
        for tag2 in listTags[i+1:]:
            if tag2.startswith(tag):
                raise ValueError('invalid sorting of tags: subsequent tags may not start with same string as previous tags')



    return parsedDict



def GetRequiredTags(parsed_dict, tag_name):
    """
    Get a list of all required tags for a given tag, including hierarchical dependencies.

    Args:
        parsed_dict (dict): The dictionary containing parsed tag information.
        tag_name (str): The name of the tag to find requirements for.

    Returns:
        list: A list of all required tags, avoiding duplicates.
    """
    required_tags = set()
    stack = [tag_name]

    while stack:
        current_tag = stack.pop()
        if current_tag not in parsed_dict:
            continue

        requires = parsed_dict[current_tag]['REQUIRES']
        if requires:
            dependencies = [req.strip() for req in requires.split(',')]
            for dep in dependencies:
                if dep not in required_tags:
                    required_tags.add(dep)
                    stack.append(dep)

    return list(required_tags)

def CreateSampleCode(parsed_dict, tag_list):
    """
    Assemble code snippets based on a list of tags, sorted by their INDEX in parsed_dict.

    Args:
        parsed_dict (dict): The dictionary containing parsed tag information.
        tag_list (list): A list of tag names to include in the assembled code.

    Returns:
        str: The assembled code as a single string.
    """

    # print('create sample code tag list:',tag_list)
    #remove duplicated items:
    tag_list = list(dict.fromkeys(tag_list))
    # print('create sample code, unique tag list:',tag_list)

    # Filter tags that exist in the dictionary
    valid_tags = [tag for tag in tag_list if tag in parsed_dict]
    
    # Sort tags by their INDEX
    sorted_tags = sorted(valid_tags, key=lambda tag: parsed_dict[tag]['INDEX'])
    # print('** sorted tags=',sorted_tags)
    # Collect the code snippets in order
    assembled_code = []
    for tag in sorted_tags:
        # for seperation of short-tag info and comment section with longer description of the code snippet, 
        # delete parsed_dict[tag]['IFNO'] since we do not want to use that as description for the code snippet 
        assembled_code.append(f"#{parsed_dict[tag]['INFO']}\n{parsed_dict[tag]['CODE']}")

    return "\n\n".join(assembled_code)



#%%+++++++++++++++++++++++++++++++++++++++++++++++++++
if __name__ == "__main__":
    if True:
        # file_path = "evalHelper.py"
        filePath = "exudynHelper.py"
        parsed_dict = ParseExudynHelper(filePath, 5)
        
        # for key, value in parsed_dict.items():
        #     if key not in listSystemTags:
        #         print(f"{key}: {value['INFO']}")
        
        # selectedTag = 'body sensor'
        # selectedTag = ['body sensor' , 'retrieve sensor data']
        # selectedTag = 'distance constraint' # requires ground and point mass 
        selectedTag = ['general', 'visualization', # should not be printed, since it is ommited in the parsed_dict
                    'revolute joint', # 15 
                    'distance constraint', # 5
                    ] 
        
        l = GetRequiredTags(parsed_dict, 'distance constraint')
        print("Required tags: ", l)
        
        
        code = CreateSampleCode(parsed_dict, selectedTag+l)#selectedTag+l+listSystemTags)
        print(code)
        #sys.exit()
