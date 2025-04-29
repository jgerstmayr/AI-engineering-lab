# -*- coding: utf-8 -*-
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# This is part of the AI engineering lab project
#
# Filename: templatesAndLists.py
#
# Details:  main prompt templates (template to create the prompt for LLMs, using their prompt templates ...), 
#           further lists, and dictionaries used by agent;
#           dictOfEvaluationMethods: defines the evaluation methods with hints, needed codes and descriptions
#           
#
# Authors:  Johannes Gerstmayr, Tobias Möltner
# Date:     2025-02-10
# Notes:    Ensure that the appropriate model files are available locally or through the Hugging Face model hub.
#
# License:  BSD-3 license
#
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++
#%% Evaluation methods
#introduce type to distinguish processing lines:
class EvaluationType:
    def RequiredSensors(evalType):
        if evalType == EvaluationType.Sensor or evalType == EvaluationType.SensorBasedFunction:
            return 1
        elif evalType == EvaluationType.Sensors or evalType == EvaluationType.SensorsBasedFunction:
            return 2
        else:
            return 0
        
    def IsAnalysisType(evalType):
        return evalType == EvaluationType.SystemAnalysis
    def IsPureSensorType(evalType):
        return (evalType == EvaluationType.Sensor) or (evalType == EvaluationType.Sensors)

EvaluationType.SystemAnalysis = 0 #eigenvalues, DOF, ...

EvaluationType.Sensor = 1 #Position sensor, Acceleration sensor, ...
EvaluationType.SensorBasedFunction = 2 #Check if planar, ...

EvaluationType.Sensors = 3 #Position sensor, Acceleration sensor, ...
EvaluationType.SensorsBasedFunction = 4 #Check distance

#templates for evaluation:
sensorBasedFunctionHintTemplate = 'After the line with mbs.SolveDynamic : for the given sensor "sensorNumber" add exactly the following commands with adjusted sensorNumber:\n```python\ndata = GetSensorData(mbs, sensorNumber)\noutput = {functionName}(data)\n```\nMake sure to exactly call the variable "output" as this variable is used afterwards.'
systemAnalysisHintTemplate = 'After mbs.Assemble() add exactly the commands:\noutput = {command}\n\nMake sure to exactly call the variable "output" as this variable is used afterwards. You do not need to add other solve commands like mbs.SolveDynamic(...).'

#++++++++++++++++
#now included in ConvertResultsToPlainText:
notePointMass = '; note that a point mass has 3 DOF and a rigid body has 6 DOF (equivalent to the number of eigenvalues)'
notePointMass2 = '; note that a point mass has 3 DOF and a rigid body has 6 DOF as long as no constraint is applied'
notePointMass3 = '; note that without constraints, a point mass has 3 DOF and a rigid body has 6 DOF'
#++++++++++++++++

#check initial values: pos/vel sensor + values at time=0
#check final values: pos/vel sensor + values at last time step
dictOfEvaluationMethods = {
'Perform a rough calculation':{'description':'Performs a rough calculation using e.g. a position, velocity or acceleration sensor.','type':EvaluationType.Sensor,'code':'','evaluationCodeHints':''},
'Evaluate analytical formulas':{'description':'Evaluate analytical formulas for (e.g. parts of the) given multibody system using position, velocity or acceleration sensor.','type':EvaluationType.Sensor,'code':'','evaluationCodeHints':''},
'Evaluate position trajectory':{'description':'Evaluates the trajectory of a specific body for the whole motion or at a specific instant in time, using a position sensor.','type':EvaluationType.Sensor,'code':'','evaluationCodeHints':''},
'Evaluate initial position':{'description':'Evaluates initial position of a point mass or rigid body with a position sensor.','type':EvaluationType.Sensor,'code':'','evaluationCodeHints':''},
'Evaluate static equilibrium for damped systems':{'description':'Evaluates the static equilibrium position of a point mass or body for a damped system with a according sensor.','type':EvaluationType.Sensor,'code':'','evaluationCodeHints':''},

'Evaluate eigenfrequencies of undamped system':{'description':'Evaluates the eigenvalues of the constrained second order system, in initial configuration, converted in Hz.','type':EvaluationType.SystemAnalysis,'code':'',
                        'evaluationFunction':'mbs.ComputeODE2Eigenvalues()'},
'Evaluate complex eigenvalues':{'description':'Evaluates the complex eigenvalues (in rad/s) of the first order ODE system, in initial configuration.','type':EvaluationType.SystemAnalysis,'code':'',
                        'evaluationFunction':'mbs.ComputeODE2Eigenvalues(computeComplexEigenvalues=True,useAbsoluteValues=False)'},
'Evaluate system degree of freedom':{'description':'Computes numerically the system degree of freedom, including the constraints on the system and all potential free motions (see specific notes on point masses and rigid bodies for their DOF).','type':EvaluationType.SystemAnalysis,'code':'',
                        'evaluationFunction':'mbs.ComputeSystemDegreeOfFreedom()'},
'Evaluate number of system constraints':{'description':'Computes numerically the number of constraints, including redundant constraints (see specific notes on point masses and rigid bodies for their DOF).','type':EvaluationType.SystemAnalysis,'code':'',
                        'evaluationFunction':'mbs.ComputeSystemDegreeOfFreedom(verbose=False)'}, #verbose=True is used to distinguish from DOF method
#
'Check if straight-line motion':{'description':'Evaluates the motion of a certain system component with a position sensor and checks if the motion follows a straight line.','type':EvaluationType.SensorBasedFunction,'code':'',
                          'evaluationFunction':'CheckLinearTrajectory'},
'Check if planar motion':{'description':'Evaluates the motion of a certain system component with a position sensor and checks if it lies inside a plane.','type':EvaluationType.SensorBasedFunction,'code':'',
                          'evaluationFunction':'CheckPlanarTrajectory'},
'Check if spherical motion':{'description':'Evaluates the motion of a certain system component with a position sensor and checks if it is spherical.','type':EvaluationType.SensorBasedFunction,'code':'',
                            'evaluationFunction':'CheckSphericalMotion'},
'Check if circular motion':{'description':'Evaluates the motion of a certain system component with a position sensor and checks if it is circular.','type':EvaluationType.SensorBasedFunction,'code':'',
                              'evaluationFunction':'CheckCircularMotion'},
'Check if parabolic motion':{'description':'Evaluates the motion space of a certain object with a position sensor and checks if the trajectory is parabolic.','type':EvaluationType.SensorBasedFunction,'code':'',
                                'evaluationFunction':'CheckParabolicMotion'},
'Evaluate motion space':{'description':'Evaluates the motion space (min and max coordinates) of a certain object with a position sensor.','type':EvaluationType.SensorBasedFunction,'code':'',
                          'evaluationFunction':'CheckMotionSpace'},
'Evaluate velocity space':{'description':'Evaluates the velocity space (min and max velocities) of a certain object.','type':EvaluationType.SensorBasedFunction,'code':'',
                            'evaluationFunction':'CheckVelocitySpace'},
'Evaluate acceleration space':{'description':'Evaluates the acceleration space (min and max acceleration) of a certain object.','type':EvaluationType.SensorBasedFunction,'code':'',
                                'evaluationFunction':'CheckAccelerationSpace'},

#'Evaluate distance of two points':{'description':'Evaluate the distance of points, e.g. point masses, point on ground, or point on a rigid body.','type':EvaluationType.SensorBasedFunction,'code':'',
#                               'evaluationCodeHints':''},

#'Evaluate velocity direction':{'description':'Check the direction of the velocity, for the whole motion or at a specific instant in time.','type':EvaluationType.Sensor,'code':'','evaluationCodeHints':''},
#'Evaluate velocity size':{'description':'Check the size of the velocity, for the whole motion, at a specific instant in time, or the range of velocities.','type':EvaluationType.Sensor,'code':'','evaluationCodeHints':''},
#'Evaluate acceleration direction':{'description':'Check the direction of the acceleration vector, for the whole motion or at a specific instant in time.','type':EvaluationType.Sensor,'code':'','evaluationCodeHints':''},
#'Evaluate acceleration size':{'description':'Check the size of the acceleration vector, for the whole motion, at a specific instant in time, or the range of accelerations.','type':EvaluationType.Sensor,'code':'','evaluationCodeHints':''},
#'Evaluate final position':{'description':'Evaluate final values of a position sensor.','type':EvaluationType.Sensor,'code':''},
#'Evaluate specific coordinates':{'description':'Check the size of specific position coordinates over time or at a specific time instant.','type':EvaluationType.Sensor,'code':'','evaluationCodeHints':''},

#for that, we would need to add functionality to compute total energy of the system:
#'Evaluate energy conservation':{'description':'Verify that the total energy (kinetic + potential) is conserved over time for conservative systems.','type':EvaluationType.Sensor,'code':'','evaluationCodeHints':''},

#for this case, the LLM would need to add a frequency sweep, but this would change the model
#'Evaluate resonance behavior':{'description':'Test the system’s response under periodic forcing to identify possible resonances.','type':EvaluationType.Sensor,'code':'','evaluationCodeHints':''},
'Evaluate angular momentum conservation':{'description':'Evaluate whether angular momentum is conserved in the absence of external torques by evaluation of an angular velocity sensor (for a point mass, you have to use translational velocity, as angular velocity gives an error).','type':EvaluationType.Sensor,'code':'','evaluationCodeHints':''},
'Evaluate linear momentum conservation':{'description':'Check if linear momentum is conserved in the absence of external forces by evaluation of velocity sensor.','type':EvaluationType.Sensor,'code':'','evaluationCodeHints':''},
#'Constraint satisfaction':{'description':'Verify that the system satisfies all kinematic constraints at every time step.','type':EvaluationType.Sensor,'code':'','evaluationCodeHints':''},

# 'Evaluate linearized system':{'description':'Check if system mass, stiffness and damping matrices have expected structure or values','type':EvaluationType.SystemAnalysis,'code':'',
#                         'evaluationFunction':'mbs.ComputeLinearizedSystem()'},

#'Check collision detection':{'description':'Identify unintended collisions between bodies, particularly in constrained multibody systems.','type':EvaluationType.Sensor,'code':'','evaluationCodeHints':''},
'Evaluate damping effects':{'description':'Evaluate the damping behavior by evaluating certain position coordinates over time, and check if it matches expected analytical values.','type':EvaluationType.Sensor,'code':'','evaluationCodeHints':''},
#'Check reaction forces at joints':{'description':'Check whether reaction forces at constraints are within expected ranges.','type':EvaluationType.Sensor,'code':'','evaluationCodeHints':''},
'Evaluate symmetry':{'description':'Evaluate the symmetry of motion by evaluating the position coordinates over time.','type':EvaluationType.Sensor,'code':'','evaluationCodeHints':''},
#'Frequency analysis':{'description':'Perform a Fourier transform on motion data to identify dominant oscillatory modes.','type':EvaluationType.Sensor,'code':'','evaluationCodeHints':''},
}

if True: #for final agent tests, we exclude the following methods due to low performance:
    del dictOfEvaluationMethods['Evaluate system degree of freedom']
    del dictOfEvaluationMethods['Evaluate number of system constraints']
    del dictOfEvaluationMethods['Evaluate acceleration space']


for key, value in dictOfEvaluationMethods.items():
    if value['type'] == EvaluationType.SensorBasedFunction:
        value['evaluationCodeHints'] = sensorBasedFunctionHintTemplate.format(functionName=value['evaluationFunction'])
    if value['type'] == EvaluationType.SystemAnalysis:
        value['evaluationCodeHints'] = systemAnalysisHintTemplate.format(command=value['evaluationFunction'])
    if 'evaluationFunction' not in value:
        value['evaluationFunction'] = '' #to have it in all dicts
    if 'evaluationCodeHints' not in value:
        value['evaluationCodeHints'] = '' #to have it in all dicts
    value['method_'] = key #to have it inside as well


#for paper    
cntEvaluationMethods=0
for key, v in dictOfEvaluationMethods.items(): 
    dictOfEvaluationMethods[key]['ID'] = cntEvaluationMethods
    cntEvaluationMethods+=1
    if False: 
        print(f'('+str(cntEvaluationMethods)+') '+key+', ')


#Evaluation method table:
if False:
    n = int((len(dictOfEvaluationMethods)+1)/2)
    EL = "\n"
    s = ''
    s += r"\begin{tabular}{p{0.25cm}|p{5cm}||p{0.25cm}|p{5cm}}"+EL
    s += r"\toprule"+EL
    s += r"  ID & Evaluation method & ID & Evaluation method \\"+EL
    s += r"  \hline "+EL
    
    listOfEvaluationMethods = list(dictOfEvaluationMethods)
    for i in range(n): 
        itemL = listOfEvaluationMethods[i]
        s += '  '+str(dictOfEvaluationMethods[itemL]['ID']+1)+' & '
        s += itemL + ' & '
        if n+i < len(listOfEvaluationMethods):
            itemR = listOfEvaluationMethods[n+i]
            s += '  '+str(dictOfEvaluationMethods[itemR]['ID']+1)+' & '
            s += itemR
        else:
            s += ' & '
          
        s += r'\\'+EL
    s += r"\hline"+EL
    s += r"\end{tabular}"+EL
    
    print('evaluation methods table:')
    print(s)

generateEvalMethodsListTemplate = [
'''
The following description of a multibody model is given: 
{modelDescription}

The following evaluation methods can be applied to a simulation model of the multibody system, either by evaluating sensors during simulation or making specific system analysis:
{possibleOutputVariables}

Choose a list of {nEvalMethods} (or less if not appropriate) evaluation methods which fit to the given model. Use precisely the phrases for the methods as given above.
Return the list of strings in the format ['evaluation method name1", "evaluation method name2", ...] such that it can be interpreted like a Python list.
'''
]

evaluationTypeDependentStringsDict = {
    EvaluationType.Sensor : 'Also specify which sensor type to use, to which body the sensor is attached and at which local position (if different from [0,0,0]) the sensor is placed.',
    EvaluationType.Sensors: 'Also specify which sensor types to use, to which bodies the sensors are attached and at which local positions (if different from [0,0,0]) the sensors are placed.',
    EvaluationType.SensorBasedFunction : 'Also specify which sensor type to use, to which body the sensor is attached and at which local position (if different from [0,0,0]) the sensor is placed.',
    EvaluationType.SensorsBasedFunction: 'Also specify which sensor types to use, to which bodies the sensors are attached and at which local positions (if different from [0,0,0]) the sensors are placed.',
    EvaluationType.SystemAnalysis : '',
    }
    
generateConjectureFromEvaluationMethod = [
'''
The following description of a multibody model is given: 
{modelDescription}

The following evaluation method has been chosen by the user to validate the multibody model:
{evaluationMethodDescription}

Create an according conjecture (like a hypothesis) for the multibody model based on the evaluation method, such that this conjecture can be used to validate a numerical simulation of the model hereafter.
Make sure that the assumptions of the model are compatible with the conjecture, and there must be only one conjecture.
Put xml-like tags around the conjecture text, marked by these tags: <conjecture> ... </conjecture>.

{evaluationTypeDependentString}
'''
]

chooseItemsForModel = [
'''
The following Exudyn elements are available:
{exudynItems}

Which of the Exudyn elements are required to build the following multibody model, including any necessary reference points or grounds? Please just list the items (without repetition) that represent the model's mechanical behavior best.
Given multibody model:
{modelDescription}
''' 
]

chooseEvalItemsForModel = [chooseItemsForModel[0]+
'''
Also list the Exudyn elements (in particular sensors) for generating outputs according to the following evaluation method:
{evaluationDescription}
''' 
]
    
generateExudynWithEvalModel = [
'''
The following Python example shows how to generate a multibody model in Exudyn, including most relevant features: 
```python
{generalStructure}
```
Using this example, please build a Python model and use the following description of a multibody model:
{modelDescription}

For outputting and postprocessing, follow this information:
{evaluationDescription}

Follow exactly the function names and argument names as given in the example and create the Exudyn model. 
Adjust the simulation settings to the multibody model, at least the end time.
Provide only the Python code without any additional descriptions; do not add comments like in the examples.
It is very important that you start the code with required imports and that you mark the end of code with the line "#end-of-code".
'''
]
#does not help: Follow exactly the function names and argument names as given in the example, take the given comments seriously, and create the Exudyn model. 
#Provide only the Python code without any additional descriptions; you don't need to add comments, except for special cases.


evaluateSimResults = [
'''
The following description of a multibody system is given: 
{modelDescription}

A student performed a numerical simulation with a given multibody model, together with an available evaluation method "{evaluationMethod}". 
The simulation manual states for the evaluation method: 
{evaluationDescription} 
{sensorText}The simulation results are:
{simulationResults}
    
Your task is to carefully analyze the provided simulation results with respect to the given multibody system and to provide an evaluation score in the range (0,100). 
If the numerical results are fully consistent with the expected results of the model, the score shall be high (up to 100), even if the evaluation method does not allow a full assessment of the model.
If there are clear disagreements between the model and the numerical results, e.g. errors / deviations from expected values more than 2%, the score must be 0. 
If it is clear that the numerical model is incorrect, e.g., using incorrect axes, incorrect overall results or incorrect initial conditions, the score must be 0. In other cases, scores between 0 and 100 can also be used.
Importantly, place the score inside tags <score> ... </score> to enable automatic processing and use plain text (no Python code, no Latex, no markdown).
'''
]


evaluateConjecture = [
'''
The following description of a multibody model is given: 
{modelDescription}

A student raised the following conjecture for this multibody model:
{conjecture}

Another student performed a numerical simulation with a simple multibody model.
{sensorText}The simulation results are:
{simulationResults}
    
Your task is to compare the conjecture and the system's expected behavior with the numerical results and to provide an evaluation score. 
Write the evaluation score, which is in the range (0,100), inside tags <score> ... </score>, as we need to extract the score from the text. 
Here, a score of 100 means that the numerical results fully agree with the conjecture (or at least with what is expected from the system), apart from small numerical deviations due to rounding. A score of 0 means, that conjecture and numerical results fully disagree. You can also use scores between 0 and 100, where a score above 50 means, that the conjecture is widely supported by the numerical results.
'''
]

    
chooseItemsForModel = [
'''
The following elements are available in the simulation code Exudyn:
{exudynItems}

Given is a multibody model with the following description:
{modelDescription}

Please list the elements that are required to build the given multibody model and which represent its mechanical behavior best, without repeating any element.
Provide elements in a plain list such as element1, element2, ... , using exactly the provided terms, and don't add other text or explanations.
'''
#Which of the available Exudyn elements are required to build the given multibody model?
#Don't forget elements like ground, or other elements that you will need to build the simulation.
]


generateExudynModel = [
'''
The following Python example shows how to generate a multibody model in Exudyn, including most relevant features: 
```python
{generalStructure}
```
Using this example, please build a Python model following exactly the following description of a multibody model:
{modelDescription}

Follow exactly the function names and argument names as given in the example and create the Exudyn model.
Provide only the Python code without any additional descriptions; you don't need to add comments, except for special cases.
It is very important that you start the code with required imports and that you mark the end of code with the line "#end-of-code".''' # promptIndex 0
    ] 






#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++
#%% OLD Agent methods:
#### not used any more:
exampleConjectures = {
    'constantAcceleration': 'The motion of the body has a constant acceleration.',  
    'constantVelocity': 'The motion of the body has a constant velocity.',
    'eigenFrequencyMassDependency': 'The eigenfrequency of the system changes with the mass.', 
    'eigenFrequencyStiffnessDependency': 'The eigenfrequency of the system changes with the stiffness of the spring(s).' # 'The eigenfrequency of the system does not change with the stiffness of the spring(s).' #
    # add other conjectures here
}

thinkingTerms = [
    'aeroplane',
    'car',
    'machine',
    'laptop',
    'string',
    'physics course',
    'mechanics course',
    'table',
    'chair',
    ]

dictOfPossibleOutputVariables = {
    'Position':'mass points and rigid bodies', #value describes the possible items where output is available
    'Displacement':'mass points and rigid bodies',
    'Velocity':'mass points and rigid bodies',
    'Acceleration':'mass points and rigid bodies',
    'Rotation':'rigid bodies',
    'AngularVelocity':'rigid bodies',
    'Force':'connectors and joints',
    'DOF':'mbs',
    'Eigenfrequencies':'mbs',
    'Linearized System':'mbs'
    }

# prompt templates for each LLM inference/task (right now only one prompt version, add different versions and evaluate using the indizes)
taskPromptTemplates = {
    "GenerateConjectures_OLD": [
'''
The following description of a multibody model is given: 
{modelDescription}

The following outputs can be examined for a given model:
{possibleOutputVariables}

Generate a list of {nConjectures} conjectures in the format ["text of conjecture 1", "text of conjecture 2", ...] for the given model. Answer ONLY with the list of conjecture WITHOUT any additional text or information.''' # promptIndex 0
    ],
    "GenerateConjectures": [
'''
The following description of a multibody model is given: 
{modelDescription}

The following outputs can be examined for a given model:
{possibleOutputVariables}

Generate a list of {nConjectures} conjectures in the format ["text of conjecture 1", "text of conjecture 2", ...] which could be used to validate the given model. Answer ONLY with the list of conjecture WITHOUT any additional text or information.''' # promptIndex 0
    ],
    
    "GenerateConjecturesWithIdeas": [
'''
The following description of a multibody model is given: 
{modelDescription}

The following outputs can be examined for a given model:
{possibleOutputVariables}

The following ideas for conjectures can be used (if needed, you can also generate new ones):
{listOfConjectureIdeas}

Generate a list of {nConjectures} conjectures in the format ["text of conjecture 1", "text of conjecture 2", ...] which could be used to validate the given model. Answer ONLY with the list of conjecture WITHOUT any additional text or information.''' # promptIndex 0
    ],
    
    "NegateConjectures": [
'''
The following list of conjectures for a multibody model is given: 
{conjectures}

Now, please negate the given conjectures in the format ["text of negated conjecture 1", "text of negated conjecture 2", ...] for the given model. Answer ONLY with the list of conjecture WITHOUT any additional text or information.''' # promptIndex 0
    ],
        
    "GenerateModelInputsFromConjecture": [
'''
The following description of a multibody model is given: 
{modelDescription}

The following conjecture related to the multibody model is given: 
{conjecture}

Which model parameter would you choose as input parameter(s) to assess the validity of the conjecture?''' # promptIndex 0
    ],
    
    "GenerateModelOutputsFromConjecture": [
#Joh: I have no idea how it can choose outputs? which outputs?
''' 
The following description of a multibody model is given: 
{modelDescription}

The following conjecture related to the multibody model is given: 
{conjecture}

Which of the given possible outputs would you choose to assess the validity of the given conjecture?
Please write NO additional text or description. Return one single word. Write the parameter name in one word and not the symbol name.''' # promptIndex 0
    ],
        

    "ChooseItemsForModel": [
'''
The following Exudyn elements are available:
{exudynItems}

Which of the Exudyn elements are required to build the following multibody model, including any necessary reference points or grounds? Please just list the items that represent the model's mechanical behavior best in the right format.
Given multibody model:
{modelDescription}''' # promptIndex 0
    ],
    
    "GenerateExudynModel_old": [
'''
The following structure shows how to generate a multibody model in Exudyn: 
{generalStructure}

Build the whole model (starting with imports) for the described multibody model below in Exudyn using the items:
{tagSyntax}

Follow exactly the function names and the function arguments as given in the example.
Create the following multibody model:
{modelDescription}

Provide only the code without any additional indicating descriptions, but you can include comments in the code.''' # promptIndex 0
    ],
    "GenerateExudynModel": [
'''
The following structure shows how to generate a multibody model in Exudyn: 
```python
{generalStructure}
```

Build the whole model (starting with imports) for the described multibody model below in Exudyn using the items:
```python
{tagSyntax}
```

This description of the multibody model is given:
{modelDescription}

Follow exactly the function names and the function arguments as given in the example and create the Exudyn model.
Provide only the Python code without any additional indicating descriptions, but you can include comments in the code.
Use markdown format to indicate Python code in your response and mark the end of code with the line "#end-of-code".''' # promptIndex 0
    ],
    "GenerateExudynModel2": [
'''
The following Python example shows how to generate a multibody model in Exudyn, including most relevant features: 
```python
{generalStructure}
```
Using this example, please build a Python model following exactly the following description of a multibody model:
{modelDescription}

Follow exactly the function names and argument names as given in the example and create the Exudyn model.
Provide only the Python code without any additional descriptions; you don't need to add comments, except for special cases.
It is very important that you start the code with required imports and that you mark the end of code with the line "#end-of-code".''' # promptIndex 0
    ],
#Use markdown format to indicate Python code in your response and mark the end of code with the line "#end-of-code".''' # promptIndex 0
    
    "ChooseItemsForEval": [
'''
The following Exudyn elements are available:
{evalItems}

Which of the Exudyn elements are required to get the {output} for the following multibody model?  Please just list the elements that are relevant for extracting the mentioned information in the right format.
Example:
{modelDescription}''' # promptIndex 0 
#TOBIAS (noch nicht mitberücksichtigt): umschreiben, dass es die Analysemethode und Outputs berücksichtigt
    ],
    
    "GenerateEvaluationModel": [
'''
The following Exudyn code of a multibody model is given:
```python
{exudynModel}
```
Use the following evaluation example codes for writing results and evaluating the multibody model:
```python
{tagSyntax}
```
Insert the evaluation example codes into the multibody model code without modifications of the given functions and arguments.
Provide only the Python code without any additional indicating descriptions; you don't need to add comments, except for special cases.
Use markdown format to indicate Python code in your response and mark the end of code with the line "#end-of-code".''' # promptIndex 0
#You may use markdown style to indicate Python code in your response.''' # promptIndex 0
    ],
    
    "GenerateVariations": [
'''
The following description of a multibody model is given: 
{modelDescription}

The following correct Exudyn code of this multibody model is given:
```python
{evalModel}
```

The code above has the following elements implemented: 
{tagSyntax}

The following corresponding conjecture is given:
{conjecture}

Input(s) for the validation of the conjecture: 
{modelInputs}

Output(s) for the validation of the conjecture: 
{modelOutputs}

Now, adapt the provided correct Exudyn code to back up the corresponding conjecture. Do this without modifications of the functions and without inventing new Exudyn-specific functions.
Take a close look at the conjecture, and mind that for some conjectures you might need to vary the input(s) and calculate the corresponding output(s). 
To remove the system use mbs.Reset(). Remember to recreate all necessary mbs elements, including grounds, bodies, joints, sensors, etc. immediately after calling mbs.Reset(), as the reset operation will delete all existing elements and leave the system in a blank state.
Do not forget to set up the multibody system to work with with SC = exu.SystemContainer() and mbs = SC.AddSystem().
Save the input and output data in a list ("inputData", "outputData") for later evaluation and describe and save the format of what is stored in that list in a string-variable "dataFormat", such that you know how to evaluate the data later.
Provide only the code without any additional indicating descriptions, but you can include comments in the code.
Use markdown format to indicate Python code in your response and mark the end of code with the line "#end-of-code".''' # promptIndex 0
    ],
    
    "ValidateConjecture": [
'''
The following conjecture is given:
{conjecture}

The following description of a multibody model is given:
{modelDescription}

The results are presented in the following format: 
{format}

Here are the results: 
{results}

Please determine if the conjecture is True or False based on the given results. Answer only with True or False. If you cannot evaluate the conjecture based on the results, answer with N/A.''' # promptIndex 0
  ]
    # prompt lists for other prompts here...
}

    
