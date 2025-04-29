# -*- coding: utf-8 -*-
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# This is part of the AI engineering lab project
#
# Filename: misc.py
#
# Details:  Special functions like string operations, etc. used for AI agents
#
# Authors:  Johannes Gerstmayr, Tobias Möltner
# Date:     2024-09-18
# Notes:    Ensure that the appropriate model files are available locally or through the Hugging Face model hub.
#
# License:  BSD-3 license
#
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

import re

def GetLongestWords(s):
    """
    Takes a string 's' and returns a list of words sorted by length (longest first),
    without any punctuation, unusual characters, or numbers.
    Used to find words that are potentially significant for a text,
    such that using these words to generate appropriate questions.
    """
    # Remove punctuation and numbers using regular expressions
    cleaned_string = re.sub(r'[^\w\s]', '', s)  # Remove punctuation and special characters
    cleaned_string = re.sub(r'\d', '', cleaned_string)  # Remove numbers

    if len(cleaned_string) == 0: #probably a number
        return [s]

    # Split the cleaned string into words
    words = cleaned_string.split()

    # Sort the words by length in descending order
    sorted_words = sorted(words, key=len, reverse=True)

    return sorted_words


def IsNumberOrSpecialCharacter(s):
    """
    Takes a string 's' and returns True if it only contains numbers and special characters
    """
    allowed_chars = r'^[0-9.,;:!*+%$€£¥₹\- ]+$'
    
    # Use regex to check if the string matches the allowed pattern
    if re.match(allowed_chars, s):
        return True
    else:
        return False


def IsNumber(s):
    """
    Takes a string 's' and returns True if it only contains regular numbers, like int, 
    float and any notation that usually appears in internet ...
    """
    # Remove leading/trailing spaces
    s = s.strip()

    # Regular expression patterns to match the different formats
    
    # Match basic integer format
    int_pattern = r'^[+-]?\d+$'
    
    # Match numbers like "1.200,34" (with thousands separator and comma as decimal)
    float_comma_thousands_pattern = r'^[+-]?\d{1,3}(?:\.\d{3})*(?:,\d+)?$'
    
    # Match regular floating-point numbers like "+1,234" or "-1.234" (comma or period as decimal separator)
    float_comma_or_dot_pattern = r'^[+-]?\d+(?:[.,]\d+)?$'
        
    # Match numbers like "1 000 000" (space-separated large numbers)
    space_separated_pattern = r'^[+-]?\d{1,3}(?: \d{3})*(?:,\d+)?$'
    
    # sci_notation_pattern = r'^[+-]?\d+(?:\.\d+)?[eE][+-]?\d+$'
    # Match scientific notation numbers like "1.23e-45" or "1 e13"
    sci_notation_pattern = r'^[+-]?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?$'
    
    # Match numbers like "-2000,56e+7" (with comma as decimal and scientific notation)
    comma_sci_notation_pattern = r'^[+-]?\d+(?:,\d+)?[eE][+-]?\d+$'

    
    # Check if the string matches any of the patterns
    if (re.match(int_pattern, s) or
        re.match(float_comma_thousands_pattern, s) or
        re.match(float_comma_or_dot_pattern, s) or
        re.match(space_separated_pattern, s) or
        re.match(sci_notation_pattern, s) or
        re.match(comma_sci_notation_pattern, s)):
        return True
    
    return False

def ReplaceDuplicates(list):
        """
        Replaces duplicated in a list and replaces them with an underscore "N/A".
        
        Args:
            answers (list): A list of answers which may contain duplicates.
            
        Returns:
            list: The list of answers with duplicates replaced by underscores.
        """
        seen = {}
        addedAlternative = False

        for i in range(len(list)):
            if list[i] in seen:
                list[i] = "N/A"  # Replace duplicate
            else:
                seen[list[i]] = i
        return list

#testing:
if __name__ == '__main__': #only executed if myLLM is executed
    # Example usage
    test_strings = [
        "123",
        "+123",
        "-123",
        "1.200,34",
        "+1.200,34",
        "-1.200,34",
        "+1.234",
        "-1.234",
        "1.23e-45",
        "1 000 000",
        "1 e13",
        "+3.14",
        "-2,000.56e+7",
        "-2,3e+7",
        "+2,3e7",
        "invalid123",
        "123a",
        "123e",
        "123e0"
    ]
    
    for s in test_strings:
        if IsNumber(s):
            print(f"'{s}' is a valid number.")
        else:
            print(f"'{s}' is not a valid number.")
