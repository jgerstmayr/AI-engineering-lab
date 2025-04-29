# -*- coding: utf-8 -*-
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# This is part of the AI engineering lab project
#
# Filename: logger.py
#
# Details:  This script defines a class for logging different information of agent-functionalities.
#           It logs the information both in human- and machinereadable format depending on the information provided.
#
# Authors:  Tobias Moeltner, Johannes Gerstmayr
# Date:     2024-12-20
#
# License:  BSD-3 license
#
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

import logging
import os
from datetime import datetime
from utilities import JoinPath, IsScalar

class NoNewlineFormatter(logging.Formatter):
    """Custom formatter that prevents automatic newlines."""
    def format(self, record):
        formatted_message = super().format(record)
        return formatted_message.rstrip("\n")  # Remove trailing newlines

#set up logger
#debugLogger: logs everything, incl. time stamps, using logging package
#humanLogger: creates human readable file
class Logger:
    def __init__(self, logDir, suffix=''):
        self.limitConsoleText = 120 #can be adapted from outside
        self.errorCount = 0 #increased with LogError
        self.warningCount = 0 #increased with LogWarning
        
        def Clear_log_file(fileName):
            """Clear the log file when the logger is initialized."""
            with open(fileName, 'w', encoding='utf-8') as file:
                file.write("")  # Overwrite with an empty file
    
        def ResetLogger(logger):
            # Reset logger if needed
            if logger.hasHandlers():
                for handler in logger.handlers[:]:
                    logger.removeHandler(handler)
                    handler.close()
        
        if len(logDir) > 0 and logDir[-1] != '/':
            logDir += '/'
        self.logDir = logDir

        humanLogFile = JoinPath(logDir,'humanReadableLog'+suffix+'.md')
        infoLogFile = JoinPath(logDir,'quickinfo'+suffix+'.md')
        debugFile = JoinPath(logDir,'debug'+suffix+'.txt')
        
        #create directory if it does not exist
        try:
            os.makedirs(os.path.dirname(humanLogFile), exist_ok=True)
        except:
            pass #makedirs may fail on some systems, but we keep going
        
        self.humanLoggerFileName = humanLogFile
        Clear_log_file(humanLogFile)
        self.infoLoggerFileName = infoLogFile
        Clear_log_file(infoLogFile)
        self.debugLoggerFileName = debugFile
        Clear_log_file(debugFile)

    def ResetCounters(self):
        self.errorCount = 0
        self.warningCount = 0
        

    def WriteFile(self, fileName, text, newLine=True):
        """Write a text to the file in append mode."""
        with open(fileName, 'a', encoding='utf-8') as file:
            file.write(str(text)+'\n'*newLine)  # Append mode     
            file.flush()


    def GetTimeStamp(self):
        # Get the current timestamp
        timestamp = datetime.now()
        
        # Extract milliseconds properly
        milliseconds = timestamp.microsecond // 1000  # Convert microseconds to milliseconds
        
        # Format the timestamp correctly
        timestamp_str = timestamp.strftime(f"%Y-%m-%d %H:%M:%S.{milliseconds:03d}")
        
        return timestamp_str
    

    #write debug messages
    def LogDebug(self, debugMessage, printToConsole=False):
        debugMessage = str(debugMessage)
        self.WriteFile(self.debugLoggerFileName, self.GetTimeStamp() + ' - '+debugMessage)
        if printToConsole:
            print(debugMessage)

    #write plain text to debug, quick and human readable
    def LogText(self, text, quickinfo=False, timestamp=True, style=0, separator=False, 
                newLine=True, printToConsole=False, limitConsoleText=-1):
        timeStr = self.GetTimeStamp()
        text = str(text) #if None, etc. => string operations would not work
        
        if separator:
            self.WriteFile(self.humanLoggerFileName, '\n***\n')
            if quickinfo:
                self.WriteFile(self.infoLoggerFileName, '\n***\n')
            self.WriteFile(self.debugLoggerFileName, '\n=======================================')

        if timestamp:
            self.WriteFile(self.debugLoggerFileName, '\n'+timeStr+':')

        if timestamp == 2:
            self.WriteFile(self.humanLoggerFileName, '\n*time stamp: '+timeStr+'*\n')
            if quickinfo:
                self.WriteFile(self.infoLoggerFileName, '\n*time stamp: '+timeStr+'*\n')

        self.WriteFile(self.debugLoggerFileName, text, newLine=newLine)
        # if not newLine:
        #     self.debugLogger.handlers[0].stream.write(text)
        #     self.debugLogger.handlers[0].stream.flush()  # Ensure it's written immediately
        # else:
        #     self.debugLogger.debug(text)
        
        
        if printToConsole:
            textConsole = text
            if limitConsoleText > 0 and len(text)>limitConsoleText:
                textConsole = text[:limitConsoleText]+'...'
            print(textConsole)


        if style == STYLE.bold:
            text = '**'+text.strip()+'** '
        elif style == STYLE.italics:
            text = '*'+text.strip()+'* '
        elif style == STYLE.python:
            copyText = text.replace('```python','').replace('```','')
            text = '\n```\n'+copyText+'\n```\n'

        self.WriteFile(self.humanLoggerFileName, text, newLine=newLine)
        if quickinfo:
            self.WriteFile(self.infoLoggerFileName, text, newLine=newLine)


    def LogError(self, errorMessage, printToConsole=True):
        self.errorCount += 1
        errorMessage = str(errorMessage)
        self.LogText('***\nERROR:', style=STYLE.bold, printToConsole=printToConsole, separator=True, quickinfo=True)
        self.LogText(errorMessage+'\n***', style=STYLE.python, printToConsole=printToConsole, quickinfo=True,
                     limitConsoleText=self.limitConsoleText, timestamp=False)
        
    def LogWarning(self, warningMessage, printToConsole=False):
        self.warningCount += 1
        warningMessage = str(warningMessage)
        self.LogText('WARNING:', style=STYLE.bold, printToConsole=printToConsole, separator=True)
        self.LogText(warningMessage, style=STYLE.python, printToConsole=printToConsole, timestamp=False)
        

    #log dictionary as list
    def LogDict(self, infoDict, inline=False, header='', timestamp=True, quickinfo=False, excludeCodeLLM=False,
                level1Inline=None, separator=False):
        
        if header != '':
            self.LogText(header+':'*(inline), style=STYLE.bold, separator=separator, timestamp=timestamp, quickinfo=quickinfo, 
                         newLine=(not inline))

        if level1Inline is None:
            level1Inline = inline

        itemSymbol = ' - '
        endLine = '\n\n'
        if inline:
            itemSymbol = ''
            endLine = ''
        endLine2 = endLine
        if level1Inline:
            endLine2 = ''
        
        for key, value in infoDict.items():
            if type(value) == dict:
                self.LogText(itemSymbol+key+': '+endLine2, timestamp=False, 
                             newLine=False, quickinfo=quickinfo)
                itemSymbol1 = '   + '
                if level1Inline:
                    itemSymbol1 = '['
                for key1, value1 in value.items():
                    if excludeCodeLLM:
                        if ('code' in key1
                            or 'LLM prompt' in key1
                            or 'LLM response' in key1
                            ): continue

                    sValue1 = '"'+value1+'"' if type(value1)==str else str(value1)
                    self.LogText(itemSymbol1+key1+': '+sValue1+endLine2, timestamp=False, 
                                 newLine=False, quickinfo=quickinfo)
                    if level1Inline: 
                        itemSymbol1 = ', '
                if level1Inline: 
                    self.LogText(']'+'\n\n'*(not inline), timestamp=False, newLine=False, quickinfo=quickinfo)
            else:
                if excludeCodeLLM:
                    if ('general exudyn model' in key 
                        or key.startswith('evaluation model')
                        or 'LLM prompt' in key 
                        or 'LLM response' in key 
                        ):
                        continue
                sValue = '"'+value+'"' if type(value)==str else str(value)
                self.LogText(itemSymbol+key+': '+sValue+endLine, timestamp=False, newLine=False, quickinfo=quickinfo)
            if inline: itemSymbol = ', '
        
        if inline or level1Inline:
            self.LogText('\n', newLine=False, timestamp=False, quickinfo=quickinfo)
            
    #print scalar quantities of first level in dict:
    def PrintScalarQuantities(self, title, dataDict, separator=True, quickinfo=True, printToConsole=True):
        text = title+'\n'
        for key, value in dataDict.items():
            if IsScalar(value):
                text+=' - '+str(key)+' = '+str(value)+'\n'
                
        text+='\n'
        if separator: print('\n=======================================')
        self.LogText(text, separator=separator, quickinfo=quickinfo, printToConsole=printToConsole)

    def PrintAndLogCounters(self, separator=True, quickinfo=True, printToConsole=True):
        self.LogText(f'A total of:\n  {self.errorCount} errors and\n  {self.warningCount} warnings\nwere logged!', 
                separator=separator, quickinfo=quickinfo, printToConsole=printToConsole)


#create class for styles
class STYLE :
    pass

STYLE.plain = 0
STYLE.bold = 1
STYLE.italics = 2
STYLE.python = 4


# test
if __name__ == "__main__":
    logEntry = {
    "modelName": "meta-llama/Llama-3.1-70B-Instruct",
    "testID": 1,
    "model": "springCartSystem",
    "validation": "eigenFrequencyStiffnessDependency",
    "duration": 12.34,
    "closed": 75.0,
    }
    logging.basicConfig(filemode='w')
    
    logger = Logger(logDir='logsTest')
    logger.LogDebug('simple debug message')
    logger.LogError('OMG an error!\ndef Function():\n    if True: 1/0')
    logger.LogText('this is a plain text. ', newLine=False, quickinfo=True, timestamp=2)
    logger.LogText('this is a plain text. ')
    logger.LogText('this is a bold text with separator', style=STYLE.bold, separator=True, timestamp=2)
    logger.LogDict(logEntry, header='A sample dict', inline=True, quickinfo=True)
    logger.LogDict(logEntry, header='A sample dict', inline=False)
    logEntry['test'] = {'subitem': 'Hallo subitem', 'code': 'to be erased', 'number':4}
    logEntry['test2'] = 42
    logger.LogDict(logEntry, header='A sample dict', inline=False, excludeCodeLLM=True, level1Inline=True)
    
    #del logger
    
    