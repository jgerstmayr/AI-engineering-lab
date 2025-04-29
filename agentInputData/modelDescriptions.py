# -*- coding: utf-8 -*-
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# This is part of the AI engineering lab project
#
# Filename: modelDescriptions.py
#
# Details:  Lists, dictionaries and lists used by agend
#
# Authors:  Tobias Möltner
# Date:     2025-02-25
# Notes:    Collection of modeldescriptions and according possible parametrizations.
#
# License:  BSD-3 license
#
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
import numpy

import exudyn as exu
exu.RequireVersion('1.9.76') #if according version is not available, tests will fail.

import re

#replace camel case strings to strings with spaces
def AddSpacesToCamelCaseLocal(text):
    return re.sub(r'(?<=[a-z])([A-Z])', r' \1',text).lower()

#create list of numbers, return int types, as numpy makes problems with saving!
def Arange(start, final):
    newList = []
    for x in numpy.arange(start, final+1):
        newList.append(int(x))
    return newList


#join paths or path and file name
#prefer over path.join as it allows more consistent handling
def JoinPathLocal(path, subpath, subpath2=None):
    path = path.replace('\\','/')
    subpath = subpath.replace('\\','/')
    
    if path != '' and subpath != '' and path[-1] != '/':
        path += '/'
    if subpath != '' and subpath[0] == '/':
        subpath = subpath[1:]
    path = path+subpath
    
    #further subpath
    if subpath2 is not None:
        path = JoinPathLocal(path, subpath2)
    
    return path


########################################################
# improvements:
#   - elastic chain: boundaries are mass points on spherical joints
#   - rolling disc: prescribe angular velocity as -v/r
#   - artifact: several "L" as lengths are removed, as they are never replaced by Phi4
#   - remove errors such as missing gravity
#   - avoid spherical joints
#   - avoid specification of COM
#   - point mass: strongly recommend [0,0,0] as localPosition in helper files
#   - double pendulum: avoid saying arm2 relative to arm1

########################################################
# potential future features:
# list of models that has nDOF represented. These are used for that kind of "validation"
# --> 3 levels of validation
# 1) executable code
# 2) nDOF (mind, only possible for some models) - Contact models not suitable for that kind of "validation"; use this for "constrained" joint systems
# 3) closing conjecturesLoop
####################################################################################

gravityList = [3.73, 9.81, 11.15]

#TODO: modelled and modeled / modelling => choose AE variant

modelDescriptions = {
    # 0) Johannes
    "flyingMassPoint": {
        #"description": "Projectile motion of a point mass with the following properties: mass m = {mass} kg, gravity g = {gravity} m/s^2, initial velocity in x/y/z-direction: vx = {vx} m/s, vy = {vy} m/s, vz = 0 m/s. The initial position is given as x=0 and y=0. Gravity acts along the negative y-axis, and there is no other external propulsion or resistance.",
        "description": "Projectile motion of a point mass with the following properties: mass m = {mass} kg, gravity g = {gravity} m/s^2, initial velocity in x/y/z-direction: vx = {vx} m/s, vy = {vy} m/s, vz = 0 m/s. The initial position is given as x=0 and y=0. Gravity acts along the negative y-axis, and there is no other external propulsion or resistance. The motion shall be evaluated for 1 s. Contact with ground is not modelled, so the projectile can go below y=0. Except the action of gravity, no forces act on the point mass.",
        "parameters": {
            "mass": {"default": 10, "range": [5, 15]},
            "gravity": {"default": 9.81, "list": gravityList},
            "vx": {"default": 5, "range": [0, 20]},
            "vy": {"default": 10, "range": [10, 25]},
        },
        "difficulty": 5, 
        "sampleFileName": "flyingMassPoint.py",
    },

    # 1) Johannes
    "freeFallMassPoint": {
        #"description": "Free-fall motion of an object with the following properties: point mass m = {mass} kg, gravity g = {gravity} m/s^2 (in negative z-direction). The object starts from rest and is dropped from a height hz = {height} m. Air resistance and contact with ground are neglected.",
        "description": "Free-fall motion of an object with the following properties: point mass m = {mass} kg, gravity g = {gravity} m/s^2 (in negative z-direction). The object starts from rest and is dropped from a height hz = {height} m. The free fall shall be analyzed for 1 s. Air resistance is neglected and except the action of gravity, no forces act on the point mass..",
        #"Contact with ground is not modelled, so the projectile can go below y=0.",
        #an initial height: remove initial to avoid choosing initial displacements
        "alternativeDescription": "{model}: {pointMass} m = {mass} kg, gravity g = {gravity} m/s^2 (in negative z-direction). The object starts from rest and is dropped from a height hz = {height} m. Air resistance and contact with ground are neglected.",
        "alternativeDescriptionParameters": {
            "model": ["Free-fall motion of an object with the following properties",
                      "Free-fall of a mass point",
                      "Mass point which is freely falling"],
            "pointMass": ["point mass",
                          "mass point",
                          "mass point with mass",
                          ],
            },
        "parameters": {
            "mass": {"default": 1.5, "range": [1, 3]},
            "gravity": {"default": 9.81, "list": gravityList},
            "height": {"default": 20, "range": [10, 50]},
        },
        "difficulty": 5, 
        "sampleFileName": "freeFallMassPoint.py",
    },


    # 2)
    "singleMassOscillator": {
        "description": "Mass-spring-damper with the following properties: The mass point with mass m = {mass} kg lies at [{length} cm,0,0], stiffness k = {stiffness} N/m, and damping d = {damping} Ns/m. The force applied to the mass in x-direction is f = {force} N. The spring-damper between mass point and ground at [0,0,0] is aligned with the x-axis, the spring has a length of {length} cm and is initially relaxed. Gravity is neglected.",
        "parameters": {
            "mass": {"default": 1, "range": [5, 15]},
            "stiffness": {"default": 2000, "range": [1000, 8000]},
            "damping": {"default": 20, "range": [10, 80]},
            "force": {"default": 10, "range": [5, 40]},
            "length": {"default": 5, "range": [5, 20]}, #cm
        },
        "difficulty": 5,
        "sampleFileName": "singleMassOscillatorFG.py",
    },
    
    # 3)
    "singleMassOscillatorGravity": {
        "description": "Mass-spring-damper with the following properties: The mass point with mass m = {mass} kg lies at [{length} cm,0,0], stiffness k = {stiffness} N/m, and damping d = {damping} Ns/m. The force applied to the mass in x-direction is f = {force} N. The spring-damper between mass point and ground at [0,0,0] is aligned with the x-axis, the spring has a length of {length} cm and is initially relaxed. The system is subject to gravity g = {gravity} m/s^2 in positive x-direction.",
        #"description": "Mass-spring-damper with the following properties: mass m = {mass} kg, stiffness k = {stiffness} N/m, and damping d = {damping} Ns/m. The force applied to the mass is f = {force} N. The spring-damper is aligned with the x-axis and the spring has a length of {length} cm and is relaxed in the initial position. The system is subject to gravity g = {gravity} m/s^2 in positive x-direction.",
        #Joh: 25-03-15: improves if positive added: gravity ... in positive x-direction.
        "parameters": {
            "mass": {"default": 1, "range": [5, 15]},
            "stiffness": {"default": 2000, "range": [1000, 8000]},
            "damping": {"default": 20, "range": [10, 80]},
            "force": {"default": 10, "range": [5, 40]},
            "gravity": {"default": 9.81, "list": gravityList},
            "length": {"default": 5, "range": [5, 20]}, #cm
        },
        "difficulty": 6,
        "sampleFileName": "singleMassOscillatorFG.py",
        "_readableName":"single mass oscillator with gravity",
    },
    
    # 4) Johannes
    "sliderCrankSimple": {
        "description": "Simple slider-crank mechanism modelled with two mass points that are connected with"
        " distance constraints. The crank is modelled with a point mass m1 = {massCrank} kg, located at "
        "radius r = {radius} m (initially located at x=0, y=r) and constrained to ground with a distance r; "
        "the slider is a point mass m2 = {massSlider} kg, initially located at xSlider = {xSlider} m and "
        "ySlider = 0. The connecting rod is only represented as distance constraint between crank mass and "
        "slider mass. Add a spherical joint between mass 1 and ground and only constrain the z-axis motion and a "
        "second spherical joint to constrain the y- and z-axes motion of mass 2. "
        "A force fx = {forceSlider} acts on the slider in positive x-direction. "
        "The system is initially at rest, and no gravity is applied.",
        "parameters": {
            "massCrank": {"default": 0.5, "range": [0.5, 5]},
            "massSlider": {"default": 2, "range": [0.5, 5]},
            "radius": {"default": 0.5, "range": [0.5, 2]},
            "xSlider": {"default": 2, "range": [1.5, 4]},
            "forceSlider": {"default": 10, "range": [5, 20]},
        },
        "difficulty": 9, # masses + distance
        "sampleFileName": "sliderCrankSimple.py",
        "_readableName":"slider crank / point masses",
    },

    # 5) Johannes
    "singlePendulumElasticSpring": {
        "description": "Simple mathematical pendulum with the following properties: point mass m = {mass} kg, elastic string length = {length} m, string stiffness k = {stiffness} N/m, and gravity g = {gravity} m/s^2 which is applied in negative y-direction. The pendulum's reference configuration is such that the string has an angle {angle} degrees from the vertical (negative y-axis), thus the mass being on a positive x-coordinate for positive angles. The initial velocities of the mass point are v_x = {vx} m/s and v_y = {vy} m/s, applied in x resp. y direction.",
        #chooses initialDisplacement instead of referencePosition: "description": "Simple mathematical pendulum with the following properties: point mass m = {mass} kg, length of the elastic string L = {length} m, string stiffness k = {stiffness} N/m, and gravity g = {gravity} m/s^2 which is applied in negative y-direction. The pendulum is initialized with an angle of {angle} degrees from vertical (negative y-axis) equilibrium position, thus the mass being displaced in x-direction. The initial velocities of the mass point are v_x = {vx} m/s and v_y = {vy} m/s, applied in x resp. y direction.",
        "parameters": {
            "mass": {"default": 2, "range": [1, 5]},
            "length": {"default": 1, "range": [0.5, 2]},
            "gravity": {"default": 9.81, "list": gravityList},
            "angle": {"default": 60, "range": [10, 120]},
            "stiffness": {"default": 2000, "range": [500, 2000]},
            "vx": {"default": 0, "range": [-1, 1]}, 
            "vy": {"default": 1, "range": [-1, 1]}, 
        },
        "difficulty": 7, #masses + spring
        "sampleFileName": "singlePendulumElasticString.py",
        "_readableName":"pendulum with elastic string",
    },
        
    # 6) Johannes
    "singleMassOscillatorUserFunction": {
        "description": "Mass-spring-damper with the following properties: mass m = {mass} kg, stiffness k = {stiffness} N/m, and damping d = {damping} Ns/m. The force applied to the mass only in x-direction is given by the time-dependent function f(t) = {forceFunction}. The spring-damper is aligned with the x-axis and the spring has a length of {length} m and is relaxed in the initial position. Gravity is neglected.",
        "parameters": {
            "mass": {"default": 1, "range": [5, 15]},
            "stiffness": {"default": 2000, "range": [1000, 8000]},
            "damping": {"default": 20, "range": [10, 80]},
            "length": {"default": 0.2, "range": [0.2, 1]},
            "forceFunction": {"default": "400.*math.sin(math.pi*t)", "list": ["400.*math.sin(math.pi*t)","200.*math.sin(3.14*t)","500.","80.*t**2"]},
        },
        "difficulty": 10,
        "sampleFileName": "singleMassOscillatorUserFunction.py",
        "_readableName":"mass oscillator with user function",
    },
    
    # 7) Johannes
    "spinningDisc": {
        "description": "Rotational motion of a spinning disc (around z-axis) with the following properties: mass m = {mass} kg, disc radius r = {radius} m, disc width w = {width}, and initial angular velocity omega_z = {angular_velocity} rad/s. The disc is mounted on a frictionless revolute joint and experiences a constant torque T_z = {torque}. No gravity acts on the disc.",
        #Joh:NOTE: without "No gravity acts on the disc." it adds gravity, which changes solution due to Lagrange multipliers
        "parameters": {
            "mass": {"default": 20, "range": [10, 30]},
            "radius": {"default": 0.2, "range": [0.2, 0.75]},
            "width": {"default": 0.025, "range": [0.025, 0.2]},
            "angular_velocity": {"default": 50, "range": [10, 50]},
            "torque": {"default": 2, "range": [0.25, 2]},
        },
        "difficulty": 15, 
        "sampleFileName": "spinningDisc.py",
    },

    #%%
    #NOTE: up to here, models are sorted by descending average correctness of all models
    #      average correctness > 50%



    
    # 8) 
    "doubleMassOscillator": {
        "description": "Two-mass-spring-damper system consisting of two masses with the following properties: mass m1 = m2 = {mass} kg, stiffness k1 = k2 = {stiffness} N/m, and damping d1 = d2 = {damping} Ns/m. The first mass is placed at [{length} cm,0,0] and the second mass at [2*{length} cm,0,0]. The first spring is connected to ground at [0,0,0], and the second spring connects the two masses. Each spring has a reference length of {length} cm and is relaxed in the initial configuration. A force {force} is applied in x-direction to mass 2. No gravity is applied to the system.",
        "parameters": {
            "mass": {"default": 1, "range": [5, 15]},
            "stiffness": {"default": 2000, "range": [1000, 8000]},
            "damping": {"default": 20, "range": [10, 80]},
            "force": {"default": 10, "range": [5, 40]},
            "length": {"default": 5, "range": [5, 20]}, #cm !!!
        },
        "difficulty": 6,
        "sampleFileName": "doubleMassOscillatorFG.py",
    },

    # 9)
    "nMassOscillator": {
        "description": "A serial chain of {nMasses} masses connected with springs-dampers. Each mass has m = {mass} kg, the stiffnesses are k = {stiffness} N/m, and the damping coefficients are d = {damping} Ns/m. A force f = {force} N is applied to the last mass (with highest index). The first mass is connected to ground via the first spring-damper. The relaxed length of each spring is {distance} m, and the first mass is located at {axis} = {distance} m. The serial chain is oriented along the global {axis}-axis. Gravity acts in positive {axis}-direction, with g = {gravity} m/s^2.",
        #Joh: 25-03-15: direction of gravity was missing initially!
        "parameters": {
            "nMasses": {"default": 2, "list": Arange(2, 5)},
            "mass": {"default": 10, "range": [5, 15]},
            "stiffness": {"default": 5000, "range": [3000, 7000]},
            "damping": {"default": 50, "range": [30, 70]},
            "force": {"default": 100, "range": [50, 150]},
            "gravity": {"default": 9.81, "list": gravityList},
            "distance": {"default": 0.5, "range": [0.2, 1]},
            "axis": {"default": "x", "list": ["x", "y", "z"]}, 
        },
        "difficulty": 8,
        "sampleFileName": "nMassOscillatorFG.py",
    },
     
    # 10) Johannes
    "singlePendulum": {
        "description": "Simple mathematical pendulum with the following properties: point mass m = {mass} kg, inelastic string length = {length} m (fixed distance between ground and mass point), and gravity g = {gravity} m/s^2 which acts in negative y-direction, while the pendulum moves in the x-y plane. The reference configuration of the pendulum is such that the string has an angle (positive rotation sense) of {angle} degrees relative to the negative y-axis. Air resistance is neglected.",
        #Joh:NOTE: without point mass, it often choses a rigid body: "description": "Simple mathematical pendulum with the following properties: mass m = {mass} kg, length of the rigid string L = {length} m, and gravity g = {gravity} m/s^2 which acts in negative y-direction, while the pendulum moves in the x-y plane. The pendulum from vertical equilibrium position with an angle of {angle} degrees (positive rotation sense). Air resistance is neglected.",
        #Joh: 25-03-15: avoid initial for the angle, as it will choose initialDisplacements
        #Joh: 25-03-16: uses frequently revolute joint due to keyword rigid:  "Simple mathematical pendulum with the following properties: point mass m = {mass} kg, length of the rigid string L = {length} m, and gravity g = {gravity} m/s^2 which acts in negative y-direction, while the pendulum moves in the x-y plane. The reference configuration of the pendulum is such that the string has an angle (positive rotation sense) of {angle} degrees relative to the negative y-axis. Air resistance is neglected.",
        "parameters": {
            "mass": {"default": 2, "range": [1, 5]},
            "length": {"default": 1, "range": [0.5, 2]},
            "gravity": {"default": 9.81, "list": gravityList},
            "angle": {"default": 15, "range": [10, 30]},
            # "velocity": {"default": 0, "range": [0, 1]}, #The pendulum has initial angular velocity of {velocity} rad/s, being positive around z-axis. 
        },
        "difficulty": 8, #masses + distance
        "sampleFileName": "singlePendulum.py",
    },
        
    # 11) Johannes
    "doublePendulum": {
        "description": "Double pendulum system consisting of two mass points which are connected with inextensible strings with the following properties: mass m1 = {mass1} kg, mass m2 = {mass2} kg, length of the strings L1 = {length1} m, L2 = {length2} m, and gravity g = {gravity} m/s^2 which acts in negative y-direction. The first arm of the pendulum points in positive x direction and the second arm in positive y-direction. The strings are massless, inelastic and the length shall be constrained. Air resistance is neglected.",
        #Joh: 25-03-16: uses sometimes elastic strings: "Double pendulum system consisting of two mass points which are connected with inextensible strings with the following properties: mass m1 = {mass1} kg, mass m2 = {mass2} kg, length of the strings L1 = {length1} m, L2 = {length2} m, and gravity g = {gravity} m/s^2 which acts in negative y-direction. The first arm of the pendulum points in positive x direction and the second arm in positive y-direction (relative to mass1). Air resistance is neglected.",
        "parameters": {
            "mass1": {"default": 2, "range": [0.5, 5]},
            "mass2": {"default": 3, "range": [0.5, 5]},
            "length1": {"default": 0.8, "range": [0.5, 2]},
            "length2": {"default": 0.5, "range": [0.5, 2]},
            "gravity": {"default": 9.81, "list": gravityList},
        },
        "difficulty": 8, # masses + distance
        "sampleFileName": "doublePendulum.py",
        "_infoHasMultpleMasses":2,
    },
    
    # 12) Johannes
    "nPendulum": {
        "description": "Multibody n-pendulum system consisting of {nMasses} point masses with the following properties: masses m = {mass} kg, length of inextensible strings l_single = {length} m, and gravity g = {gravity} m/s^2. The pendulum starts from horizontal configuration, where all masses are aligned along the x-axis (the first mass starting at x={length}) and all masses have an initial velocity of {initialVelocity} m/s in negative y-direction. Gravity acts in negative y-direction and air resistance is neglected. The strings between the consecutive masses (and the string between first mass and ground) shall be modelled as constrained distances.",
        #"description": "Multibody n-pendulum system consisting of {nMasses} masses with the following properties: masses m = {mass} kg, length of inextensible strings L = {length} m, and gravity g = {gravity} m/s^2. The pendulum starts from horizontal configuration, where all masses are coaxially aligned along the x-axis and all masses have an initial velocity of {initialVelocity} m/s in negative y-direction. Gravity acts in negative y-direction and air resistance is neglected.",
        #Joh: without "Do not use springs for the strings, but use constraints." it uses springs
        "parameters": {
            "nMasses": {"default": 2, "list": Arange(2, 8)},
            "mass": {"default": 0.5, "range": [0.5, 5]},
            "length": {"default": 0.25, "range": [0.25, 2]},
            "gravity": {"default": 9.81, "list": gravityList},
            "initialVelocity": {"default": 0.5, "range": [0, 1]},
        },
        "difficulty": 9, # n * (masses + distance)
        "sampleFileName": "nPendulum.py",
    },
    
    # 13) Johannes
    "fourBarMechanismPointMasses": {
        "description": "A planar four-bar mechanism modelled with 2 points masses and the 3 moving bars modeled as massless distance constraints. The origin point of the mechanism on ground is located at [0,0,0], mass 1 with m1 = {mass1} kg is located at [0,{a},0], mass 2 with m2 = {mass2} kg is located at [{b},{a},0] and the final additional ground point is at [{b},-{c},0]. Gravity g = {gravity} m/s^2 acts in negative y-direction and mass 1 has an initial velocity of [{vx},0,0]. There is no friction or other resistance.",
        #NOTE: uses a 3rd mass (mass=0) on ground: #"description": "A planar four-bar mechanism modelled with 2 points masses and the 4 bars modeled as massless distance constraints. The origin point of the mechanism fixed to ground is located at [0,0,0], mass 1 with m1 = {mass1} kg is located at [0,{a},0], mass 2 with m2 = {mass2} kg is located at [{b},{a},0] and the final point is located at [{b},-{c},0]. Gravity acts in negative y-direction and mass 1 has an initial velocity of [{vx},0,0]. There is no friction or other resistance.",
        "parameters": {
            "mass1": {"default": 0.5, "range": [0.5, 4]},
            "mass2": {"default": 0.5, "range": [1, 4]},
            "a": {"default": 0.1, "range": [0.1, 0.5]},
            "b": {"default": 0.8, "range": [0.8, 2.5]},
            "c": {"default": 0.1, "range": [0.1, 0.5]},
            "vx": {"default": 1.25, "range": [0.1, 1.25]},
            "gravity": {"default": 9.81, "list": gravityList},
        },
        "difficulty": 9,
        "sampleFileName": "fourBarMechanismPointMasses.py",
        "_readableName":"four-bar mechanism / point masses",
    },

    
    # 14) Johannes
    "springCoupledFlyingRigidBodies": {
        "description": "Two free flying rigid elements, each modeled as a rigid body with brick-shape "
        "(density = {density} kg/m^3, lx={lx} m, wy={wy} m, hz={hz} m). Rigid body 1 is globally placed at [lx/2,0,0] "
        "and rigid body 2 at [3*lx/2,0,0], both bodies' COMs being at their origin. A Cartesian spring-damper with stiffness [{k},{k},{k}] N/m and damping "
        "[{d},{d},{d}] Ns/m is attached between rigid body 1 "
        "at [lx/2,0,0] (local position) and rigid body 2 at [-lx/2,0,0] (also local position). "
        "Body1 has initial velocity [0,{vy},0] and body2 has initial velocity [0,-{vy},0] and gravity is zero.",
        "parameters": {
            "density": {"default": 1000, "range": [1000, 2000]},
            "lx": {"default": 1., "range": [0.4, 1.]},
            "wy": {"default": 0.2, "range": [0.1, 0.2]},
            "hz": {"default": 0.1, "range": [0.05, 0.1]},
            "vy": {"default": 4., "range": [1, 4]},
            "k": {"default": 20000., "range": [10000, 20000]},
            "d": {"default": 100., "range": [100, 400]},
            #"gravity": {"default": 9.81, "list": gravityList},
        },
        "difficulty": 15, # rigid bodies + spring-dampers
        "sampleFileName": "springCoupledFlyingRigidBodies.py",
        "_infoHasMultpleRigidBodies":2,
    },
    
    
    # 15) Johannes (=spinning Disc)
    "torsionalOscillator": {
        "description": "Torsional oscillator consisting of a cylindrical disc with rotational motion around z-axis and a torsional spring-damper with the following properties: mass m = {mass} kg, disc radius r = {radius} m, disc width w = {width}, torsional stiffness k = {stiffness} Nm/rad, torsional damping coefficient d = {damping} Nms/rad and initial angular velocity omega_z = {angular_velocity} rad/s. The disc is mounted on a frictionless revolute joint and experiences a constant torque T_z = {torque}. No gravity acts on the disc.",
        #Joh:NOTE: without "No gravity acts on the disc." it adds gravity, which changes solution due to Lagrange multipliers
        "parameters": {
            "mass": {"default": 20, "range": [10, 30]},
            "radius": {"default": 0.2, "range": [0.2, 0.75]},
            "width": {"default": 0.025, "range": [0.025, 0.2]},
            "angular_velocity": {"default": 50, "range": [10, 50]},
            "torque": {"default": 2, "range": [0.25, 2]},
            "stiffness": {"default": 2000, "range": [500, 2000]},
            "damping": {"default": 5, "range": [5, 20]},
        },
        "difficulty": 15, 
        "sampleFileName": "torsionalOscillator.py",
    },

    # 16) Johannes
    "invertedSinglePendulum": {
        "description": "An inverted pendulum on a cart modelled with two mass points, where the cart is attached to ground with a spherical joint where the x-coordinate is not constrained, such that it can move along the x-direction. The pendulum is modelled with a distance constraint between cart and pendulum mass: cart mass m1 = {mass1} kg, pendulum mass m2 = {mass2} kg, pendulum length = {length} m, and gravity g = {gravity} m/s^2 which acts in negative y-direction. The pendulum starts from the upright position, where m2 is located at the positive y-axis. A disturbance force f = {force} N acts in x-direction at the pendulum and no control is applied on the cart.",
        "parameters": {
            "mass1": {"default": 4, "range": [0.5, 5]},
            "mass2": {"default": 0.5, "range": [0.5, 5]},
            "length": {"default": 0.8, "range": [0.8, 2]},
            "force": {"default": 0.1, "range": [0.01, 0.1]},
            "gravity": {"default": 9.81, "list": gravityList},
        },
        "difficulty": 15, # masses + spherical joint
        "sampleFileName": "invertedSinglePendulum.py",
    },
    
    # 17) Johannes
    "discRollingOnGround": {
        "description": "Rolling motion of a solid disc rolling on a x/y plane with the following properties: mass m = {mass} kg, radius r = {radius} m, width w = {width} m, and gravity g = {gravity} m/s^2 (in negative z-direction). The disc's axis is initially aligned with the x-axis. The COM of the disc has an initial position of p0 = [{px},{py},{radius}], translational velocity of v_y = {initialVelocity} m/s and an initial angular velocity omega_x=-v_y/radius. Rolling shall be modelled ideal and without slipping.",
        #LLMs do not choose right sign of initial ang vel, corresponding to vel
        #Joh: 25-03-16: added "(consider correct sign)"
        "parameters": {
            "mass": {"default": 4, "range": [2, 10]},
            "radius": {"default": 0.3, "range": [0.1, 0.5]},
            "width": {"default": 0.05, "range": [0.02, 0.1]},
            "px": {"default": 1, "range": [-1., 1.]},
            "py": {"default": 1, "range": [-1., 1.]},
            "initialVelocity": {"default": 1, "range": [0.5, 2.]},
            "gravity": {"default": 9.81, "list": gravityList},
        },
        "difficulty": 20, # rigid body + RollingDisc #requires exudyn 1.9.69
        "sampleFileName": "discRollingOnGround.py",
    },

    
    # 18) Johannes
    "doublePendulumElasticSpring": {
        "description": "Double pendulum consisting of two mass points which are connected with elastic springs with the following properties: mass m1 = {mass1} kg, mass m2 = {mass2} kg, length of the strings L1 = {length1} m, L2 = {length2} m, stiffnesses k1 = {stiffness1} and k2 = {stiffness2}, and gravity g = {gravity} m/s^2 which acts in negative y-direction. The first arm of the pendulum points in {arm1direction}-direction and the second arm in {arm2direction}-direction.",
        "parameters": {
            "mass1": {"default": 1, "range": [0.5, 5]},
            "mass2": {"default": 0.5, "range": [0.5, 5]},
            "length1": {"default": 0.5, "range": [0.5, 2]},
            "length2": {"default": 0.3, "range": [0.3, 2]},
            "stiffness1": {"default": 1000., "range": [1000., 10000.]},
            "stiffness2": {"default": 500., "range": [500., 5000.]},
            "gravity": {"default": 9.81, "list": gravityList},
            "arm1direction": {"default": 'positive x', "list": ['positive x', 'negative x', 'positive y']},
            "arm2direction": {"default": 'positive y', "list": ['positive y', 'positive x', 'negative x']},
        },
        "difficulty": 8, # masses + distance
        "sampleFileName": "doublePendulumElasticString.py",
    },
    
    # 19) Johannes
    "nPendulumElasticSpring": {
        "description": "Multibody n-pendulum system consisting of {nMasses} point masses connected with spring-dampers with the following properties: masses m = {mass} kg, lengths of single elastic strings l_single = {length} m, stiffness k = {stiffness} and damping d = {damping} of strings, and gravity g = {gravity} m/s^2 which acts in negative y-direction. The pendulum starts from horizontal configuration, where all masses are aligned with the x-axis, the first mass located at x={length}, with a spring-damper connected to ground.",
        "parameters": {
            "nMasses": {"default": 2, "list": Arange(2, 8)},
            "mass": {"default": 0.5, "range": [0.5, 5]},
            "length": {"default": 0.25, "range": [0.25, 2]},
            "gravity": {"default": 9.81, "list": gravityList},
            "stiffness": {"default": 1000., "range": [1000., 10000.]},
            "damping": {"default": 50., "range": [50., 500.]},
        },
        "difficulty": 9, # n * (masses + distance)
        "sampleFileName": "nPendulumElasticString.py",
    },
    
    # 20) Johannes
    "elasticChain": {
        "description": "Straight elastic chain modelled with {nMasses} mass points connected with spring-dampers with the following properties: masses m = {mass} kg, lengths of each chain element l_single = {length} m, stiffness k = {stiffness} and damping d = {damping} of chain elements, and gravity g = {gravity} m/s^2 which acts in negative y-direction. The chain starts from horizontal configuration, where all masses are aligned with the x-axis, the first mass located at x=0. The left-most and right-most spring-dampers are fixed to ground using spherical joints.",
        #problems with last support position: the last mass lies {length} m left from the last support.
        "parameters": {
            "nMasses": {"default": 20, "list": Arange(5, 20)},
            "mass": {"default": 5, "range": [0.5, 5]},
            "length": {"default": 4, "range": [1, 4]},
            "gravity": {"default": 9.81, "list": gravityList},
            "stiffness": {"default": 2000., "range": [2000., 10000.]},
            "damping": {"default": 100., "range": [100., 500.]},
        },
        "difficulty": 9, # n * (masses + distance)
        "sampleFileName": "elasticChain.py",
    },

    # 21) Johannes
    "singlePendulumRigidBody": {
        "description": "Pendulum modeled with a brick-shape rigid body and a revolute joint. "
        "The body has density = {density} kg/m^3, and xyz-dimensions lx={lx}m, wy={wy}m, hz={hz}m. "
        "The center of mass is equal to the reference point and initially located at [lx/2,0,0], "
        "while the revolute joint (rotation around z-axis) is located at [0,0,0] (global coordinates). "
        "Gravity g = {gravity} m/s^2 acts in negative y-direction, and no further force acts.",
        "parameters": {
            "density": {"default": 1000, "range": [500, 8000]},
            "lx": {"default": 1.2, "range": [0.75, 5]},
            "wy": {"default": 0.4, "range": [0.1, 0.5]},
            "hz": {"default": 0.2, "range": [0.1, 0.5]},
            "gravity": {"default": 9.81, "list": gravityList},
        },
        "difficulty": 15, # rigid bodies + revolute joint
        "sampleFileName": "singlePendulumRigidBody.py",
        "_readableName":"single pendulum / rigid body",
    },

    # 22) Johannes
    "massPointOnStringRigid": {
        "description": "A 3D mass point with mass m = {mass} kg is attached to a string with length {length} m, with a predominant rotation around the z-axis due to centrifugal forces.  Gravity g = {gravity} m/s^2 acts in negative z-direction. The mass point is placed initially at [{length},0,0] and the initial velocity is [0,{vy},0], given in m/s. The string shall be modelled as rigid distance between the mass point and the ground position at [0,0,0].",
        "parameters": {
            "mass": {"default": 2, "range": [0.5, 5]},
            "length": {"default": 0.5, "range": [0.2, 0.75]},
            "vy": {"default": 5, "range": [4, 10]},
            "gravity": {"default": 9.81, "list": gravityList},
        },
        "difficulty": 10,
        "sampleFileName": "massPointOnString.py",
        "_readableName":"mass point on rigid string",
    },   
    
    # 23) Johannes
    "massPointOnStringElastic": {
        "description": "A 3D mass point with mass m = {mass} kg is attached to a string with length {length} m, with a predominant rotation around the z-axis due to centrifugal forces. Gravity g = {gravity} m/s^2 acts in negative z-direction. The mass point is placed initially at [{length},0,0] and the initial velocity is [0,{vy},0], given in m/s. The elastic string shall be modelled as spring-damper with stiffness k = {stiffness} N/m and damping d = {damping} Ns/m, which connects the mass point and the ground position at [0,0,0].",
        "parameters": {
            "mass": {"default": 2, "range": [0.5, 5]},
            "length": {"default": 0.5, "range": [0.2, 0.75]},
            "vy": {"default": 5, "range": [4, 10]},
            "gravity": {"default": 9.81, "list": gravityList},
            "stiffness": {"default": 2000, "range": [2000, 5000]},
            "damping": {"default": 20, "range": [20, 50]},
        },
        "difficulty": 10,
        "sampleFileName": "massPointOnString.py",
        "_readableName":"mass point on elastic string",
    },   
    # 24) Johannes
    "linkOnTwoPrismaticJoints": {
        "description": "A system consisting of two mass points connected by a distance constraint. The first mass m1 = {mass1} kg is initially located at x0 = {x0} m (other coordinates are 0) and can freely move only along the x-axis, while y-axis and z-axis are constrained by a spherical joint. The second mass m2 = {mass2} kg is initially located at {axis}0 = {y0} m (other coordinates are 0) and can move only freely along the {axis}-axis, while the other two axes are constrained by a spherical joint. Furthermore, a distance constraint is added between the two mass points and the length shall be computed automatically. A spring with stiffness = {stiffness} N/m is used to connect mass m1 and ground at [0,0,0]. Gravity g = {gravity} m/s^2 acts in positive {gAxis}-direction, and no further forces or damping are applied.",
        "parameters": {
            "mass1": {"default": 2, "range": [1, 15]},
            "mass2": {"default": 3, "range": [1, 15]},
            "x0": {"default": 0.5, "range": [0.5, 2]},
            "y0": {"default": 0.5, "range": [0.5, 2]},
            "stiffness": {"default": 500, "range": [300, 900]},
            "axis": {"default": "y", "list": ["y", "z"]}, 
            "gAxis": {"default": "x", "list": ["x", "y", "z"]}, 
            "gravity": {"default": 9.81, "list": gravityList},
        },
        "difficulty": 10,
        "sampleFileName": "xyLinkage.py",
    },
    
    # 25) Johannes
    "flyingRigidBody": {
        "description": "A free flying rigid body with brick-shape, density = {density} kg/m^3, and xyz-dimensions of the cuboid lx={lx}m, wy={wy}m, hz={hz}m is investigated. The COM of the body is initially located at [0,0,0]. The initial velocity shall be [{vx},{vy},{vz}] and the initial angular velocity is [{avx},{avy},{avz}]. Gravity g = {gravity} m/s^2 acts in negative {gAxis}-direction. Contact with ground is not considered and no further forces act on the point mass.",
        "parameters": {
            "density": {"default": 200, "range": [100, 200]},
            "lx": {"default": 4, "range": [3, 5]},
            "wy": {"default": 0.8, "range": [0.5, 1.3]},
            "hz": {"default": 1.5, "range": [1, 2]},
            "vx": {"default": 5, "range": [1., 5.]},
            "vy": {"default": 5, "range": [1., 5.]},
            "vz": {"default": 5, "range": [1., 5.]},
            "avx": {"default": 0.5, "range": [0.25, 2.]},
            "avy": {"default": 2,   "range": [0.25, 2.]},
            "avz": {"default": 0.5, "range": [0.25, 2.]},
            "gravity": {"default": 9.81, "list": gravityList},
            "gAxis": {"default": "y", "list": ["x", "y", "z"]}, 
        },
        "difficulty": 12,
        "sampleFileName": "flyingRigidBody.py",
    },
    
    # 26) Johannes
    "suspendedRigidBody": {
        "description": "A rigid body is suspended by 4 Cartesian spring-dampers. The rigid body has a brick-shape with density = {density} kg/m^3, and xyz-dimensions lx={lx}m, ly={ly}m, lz={lz}m. The reference point of the body, which is equal to the COM, is located initially at [0,{ly}/2,0]. The Cartesian spring-dampers are located at the x/z positions of the vertices of the body. The y-local-position of the spring-dampers at the body is -{ly}/2 and the local position for ground is y=0. All spring-dampers have equal parameters: stiffness = [{kx},{ky},{kz}] N/m and damping = [{dx},{dy},{dz}] Ns/m. Gravity g = {gravity} m/s^2 acts in negative y-direction, and no further forces or damping are applied and contact with ground is ignored.",
        "parameters": {
            "density": {"default": 400, "range": [400, 500]},
            "lx": {"default": 4, "range": [3, 5]},
            "ly": {"default": 0.75, "range": [0.75, 1.25]},
            "lz": {"default": 1.5, "range": [1, 2]},
            "kx": {"default": 10000, "range": [10000, 20000]},
            "ky": {"default": 100000, "range": [100000, 200000]},
            "kz": {"default": 10000, "range": [10000, 20000]},
            "dx": {"default": 200, "range": [200, 400]},
            "dy": {"default": 2000, "range": [2000, 4000]},
            "dz": {"default": 200, "range": [200, 400]},
            "gravity": {"default": 9.81, "list": gravityList},
        },
        "difficulty": 20,
        "sampleFileName": "suspendedRigidBody.py",
    },

    # 27)
    "gyroscopeOnSphericalJoint": {
        "description": "A gyro is modelled with a rigid body and a spherical joint. The gyro is modelled as cylindrical disc with mass m = {mass} kg, disc radius r = {radius} m, and disc width w = {width}. The axis of the disc is initially oriented along positive x-axis and the disc is positioned at [{offsetX},0,0] (which is also the COM). The disc is connected to ground with a spherical joint at position [0,0,0]. The initial angular velocity of the disc is [{angularVelocity},0,0]. Gravity g = {gravity} m/s^2 acts in negative {gAxis}-direction, and no further forces or damping are applied.",
        "parameters": {
            "mass": {"default": 20, "range": [15, 20]},
            "radius": {"default": 0.2, "range": [0.2, 0.3]},
            "width": {"default": 0.025, "range": [0.025, 0.04]},
            "offsetX": {"default": 0.25, "range": [0.15, 0.25]},
            "angularVelocity": {"default": 200, "range": [100., 200.]}, #take care of step size and enough speed for precession
            "gAxis": {"default": "y", "list": ["y", "z"]}, 
            "gravity": {"default": 9.81, "list": gravityList},
        },
        "difficulty": 20,
        "sampleFileName": "gyroscopeOnSphericalJoint.py",
    },
    # 28)
    "prismaticJointSystem": {
        "description": "A system consisting of a brick-shaped rigid body freely moving on a prismatic joint in {axis}-direction. The COM of the rigid body is placed at [0,0,0]. The rigid body has a mass of m = {mass} kg and the side lengths of the body are all equal with s = {s} m. A force f = {force} N acts on the rigid body's COM in {axis}-direction. Gravity is neglected.",
        "parameters": {
            "mass": {"default": 10, "range": [5, 15]},
            "s": {"default": 0.5, "range": [0.25, 0.8]},
            "axis": {"default": "x", "list": ["x", "y", "z"]}, 
            "force": {"default": 20, "range": [5, 20]},
        },
        "difficulty": 15, 
        "sampleFileName": "prismaticJointSystem.py",
    },
    
    # 29) Johannes
    "twoMassPointsWithSprings": {
        "description": "Two mass points connected by springs. The mass points both have mass m1 = m2 = {mass} kg, are initially located at p1 = [-{ax},0,0] and p2 = [{ax},0,0], positions given in m. Mass m1 has initial velocity {velStr} = {vel} m/s and m2 has initial velocity {velStr} = -{vel} m/s while all other initial velocity components are zero. The spring between the two mass points is initially relaxed and has stiffness k = {stiffness} N/m. No gravity nor forces are present.",
        "parameters": {
            "mass": {"default": 1, "range": [0.5, 2]},
            "ax": {"default": 0.5, "range": [0.25, 0.8]},
            "vel": {"default": 4, "range": [0.5, 4]},
            "velStr": {"default": "vy", "list": ["vy","vz"]},
            "stiffness": {"default": 2000, "range": [500, 2000]},
        },
        "difficulty": 6,
        "sampleFileName": "twoMassPointsConnected.py",
    },
    
    # 30) Johannes
    "twoMassPointsWithDistances": {
        "description": "Two mass points connected by distance constraint. The mass points both have mass m1 = m2 = {mass} kg, are initially located at p1 = [-{ax},0,0] and p2 = [{ax},0,0], positions given in m. Mass m1 has initial velocity {velStr} = {vel} m/s and m2 has initial velocity {velStr} = -{vel} m/s while all other initial velocity components are zero. No gravity nor forces are present.",
        "parameters": {
            "mass": {"default": 1, "range": [0.5, 2]},
            "ax": {"default": 0.5, "range": [0.25, 0.8]},
            "vel": {"default": 4, "range": [0.5, 4]},
            "velStr": {"default": "vy", "list": ["vy","vz"]},
        },
        "difficulty": 6,
        "sampleFileName": "twoMassPointsConnected.py",
    },

    # 31) Rigid Rotor, simply supported, initial angular velocity, unbalance by shifting COM
    "rigidRotorSimplySupported": {
        "description": "A rotor is modelled with a rigid body mounted on ground with Cartesian spring-dampers. "
        "The rotor is modelled as cylinder with mass m = {mass} kg, disc radius r = {radius} m, and length = {length} m. "
        "The axis of the rotor is initially oriented along the x-axis and the reference point of the rotor lies at [0,0,0] (which is also the COM). "
        "The rotor is connected to ground with two Cartesian spring-dampers at global position [-{length}/2,0,0] resp. [{length}/2,0,0], "
        "the positions being identical with the local positions of the spring-dampers on the rotor. "
        "The Cartesian spring-dampers have stiffness values [{kx},{ky},{ky}] N/m and damping values [{dx},{dy},{dy}] Ns/m. "
        "The initial angular velocity of the rotor is [{angularVelocity},0,0]. "
        "Gravity g = {gravity} m/s^2 acts in negative {gAxis}-direction, and no further forces or damping are applied.",
        "parameters": {
            "mass": {"default": 5, "range": [2, 5]},
            "radius": {"default": 0.2, "range": [0.1, 0.2]},
            "length": {"default": 0.5, "range": [0.5, 1]},
            "kx": {"default": 1000, "range": [1000, 1500]},
            "ky": {"default": 2000, "range": [2000, 4000]},
            "dx": {"default": 5, "range": [5, 8]},
            "dy": {"default": 10, "range": [10, 20]},
            "angularVelocity": {"default": 500, "range": [200., 500.]},
            "gAxis": {"default": "y", "list": ["y", "z"]}, 
            "gravity": {"default": 9.81, "list": gravityList},
        },
        "difficulty": 20,
        "sampleFileName": "rigidRotorSimplySupported.py",
    },


    # 32) Rigid Rotor, simply supported, unbalance by shifting COM; torque added to simulate runup
    "rigidRotorUnbalanced": {
        "description": "A rotor is modelled with a rigid body mounted on ground with Cartesian spring-dampers. "
        "The rotor is modelled as cylinder with mass m = {mass} kg, disc radius r = {radius} m, and length = {length} m. "
        "The axis of the rotor is initially oriented along the x-axis and the reference point of the rotor lies at [0,0,0]. "
        "The COM of the rigid body lies at [0,{comY},0], representing an unbalance U={mass}*{comY} kgm. "
        "The rotor is connected to ground with two Cartesian spring-dampers at global position [-{length}/2,0,0] resp. [{length}/2,0,0], "
        "the positions being identical with the local positions of the spring-dampers on the rotor. "
        "The Cartesian spring-dampers have stiffness values [{kx},{ky},{ky}] N/m and damping values [{dx},{dy},{dy}] Ns/m. "
        "The rotor starts from zero velocity, and is driven by a torque [1,0,0] Nm. "
        "Gravity g = {gravity} m/s^2 acts in negative {gAxis}-direction. Simulate the rotor for 2s and use a stepSize of 0.2ms to meet the accuracy limits.",
        "parameters": {
            "mass": {"default": 2, "range": [2, 3]},
            "radius": {"default": 0.1, "range": [0.1, 0.12]},
            "length": {"default": 0.5, "range": [0.5, 1]},
            "comY": {"default": 0.002, "range": [0.001, 0.002]},
            "kx": {"default": 1500, "range": [1000, 1500]},
            "ky": {"default": 4000, "range": [2000, 4000]},
            "dx": {"default": 5, "range": [5, 8]},
            "dy": {"default": 10, "range": [10, 20]},
            "gAxis": {"default": "y", "list": ["y", "z"]}, 
            "gravity": {"default": 9.81, "list": gravityList},
        },
        "difficulty": 20,
        "sampleFileName": "rigidRotorSimplySupported.py",
    },
    
    # 33) Double pendulum with rigid bodies
    "doublePendulumRigidBodies": {
        "description": "Double pendulum modeled with brick-shape rigid bodies and revolute joints. "
        "Both bodies have density = {density} kg/m^3, and xyz-dimensions lx={lx} m, wy={wy} m, hz={hz} m. "
        "The first body's center is located initially at [lx/2,0,0] and the second body at [3*lx/2,0,0], both bodies having their COM locally at [0,0,0] (not translated). "
        "The first revolute joint between ground and body 1 is located at [0,0,0] (global coordinates), "
        "and the second revolute joint between body 1 and body 2 is located at [lx,0,0] (global coordinates). "
        "Both revolute joints' have a free rotation around the z-axis."
        "Gravity g = {gravity} m/s^2 acts in negative y-direction, and no further force acts.",
        "parameters": {
            "density": {"default": 1000, "range": [500, 8000]},
            "lx": {"default": 1.2, "range": [0.75, 5]},
            "wy": {"default": 0.4, "range": [0.1, 0.5]},
            "hz": {"default": 0.2, "range": [0.1, 0.5]},
            "gravity": {"default": 9.81, "list": gravityList},
        },
        "difficulty": 16, # rigid bodies + revolute joint
        "sampleFileName": "doublePendulumRigidBodies.py",
        "_readableName":"double pendulum / rigid bodies",
    },
    
    # 34) Slider-crank mechanism with rigid bodies
    "sliderCrankRigidBodies": {
        "description": "A slider-crank mechanism is given with a crank rotating about the z-axis. "
        "The crank is modelled as rigid body with cylinder shape (axis=z) with mass m = {mass} kg, radius r = {radius} m, and width = {width} m, "
        "and it is initially located at [0,0,-{width}]. "
        "The brick-shaped conrod and piston have identical parameters: density = {density} kg/m^3, "
        "and xyz-dimensions lx={lx} m, wy={wy} m, hz={hz} m, initially not rotated (straight configuration of slider-crank). "
        "The conrod's center is located initially at [r+0.5*lx,0,0] and the piston is initially located at [r+1.5*lx,0,0]. "
        "A torque [0,0,T] shall act on the crank, employing a user-function with T={torque} Nm until 1 s and 0 thereafter. "
        "The revolute joint between ground and crank is located at [0,0,0] (global coordinates), "
        "the revolute joint between crank and conrod is located at [r,0,0] (global coordinates), "
        "and the revolute joint between conrod and piston is located at [r+lx,0,0] (global coordinates). "
        "The prismatic joint (axis=x) between ground and piston is located at [r+1.5*lx,0,0] (global coordinates). "
        "No gravity acts on the system. Simulate the system for 2 s.",
        "parameters": {
            "mass": {"default": 2, "range": [2, 3]},
            "radius": {"default": 0.25, "range": [0.2, 0.25]},
            "width": {"default": 0.1, "range": [0.05, 0.1]},
            "density": {"default": 7850, "list": [2800,7850]},
            "lx": {"default": 0.4, "range": [0.4, 0.6]},
            "wy": {"default": 0.05, "range": [0.05, 0.1]},
            "hz": {"default": 0.05, "range": [0.05, 0.1]},
            "torque": {"default": 2, "range": [1, 2]},
        },
        "difficulty": 16, # rigid bodies + revolute joint
        "sampleFileName": "sliderCrankRigidBodies.py",
        "_readableName":"slider crank / rigid bodies",
    },
    
    
    # # NN) Johannes
    # "XXX": {
    #     "description": "",
    #     "parameters": {
    #     },
    #     "difficulty": 0,
    #    # "sampleFileName": ".py",
    # },
    
    # # NN) Johannes
    # "XXX": {
    #     "description": "",
    #     "parameters": {
    #     },
    #     "difficulty": 0,
    #    # "sampleFileName": ".py",
    # },
    
        
}


###########################################################################################################################################################################

# NOTE: discussed modeldescriptions are added to the dict modelDescriptionsAlternative if they are under development. 
# Add them to modelDescriptions if first version of model description completed!   

modelDescriptionsAlternative = {        

    # # 23)
    # "nPendulumRigidBodies": {
    #     "description": "Multibody pendulum system consisting of {nBodies} rigid bodies (3D) connected with {nBodies} revolute joints with the following properties: mass m = {mass} kg, length of the string L = {length} m, and gravity g = {gravity} m/s^2 in negative y-direction. Each link of the pendulum has a cylindrical shape with radius r = {radius}. Air resistance is neglected. The bodies are initially aligned with the x-axis, and the pendulum moves in the x-y plane and the axis of the revolute joint is pointing in z-direction.",
    #     "parameters": {
    #         "nBodies": {"default": 2, "list": Arange(2, 5)},
    #         "mass": {"default": 2, "range": [1, 5]},
    #         "length": {"default": 1, "range": [0.5, 2]},
    #         "gravity": {"default": 9.81, "list": gravityList},
    #         "radius": {"default": 0.1, "range": [0.02, 0.1]},
    #     },
    #     "difficulty": 15, 
    #     # "sampleFileName": "",
    # },

    # # 23)
    # "scottRussellLinkage": #rigid body, distance constraint and spring

    # "wattLinkage": #rigid body, 2 x distance constraint, prismatic joint, and spring

    # xx1) contact of two mass points of different mass, initialized with specific velocities, aligned along specific axis
    # xx2) contact of several mass points - billiard like, no rolling; initialized with 1 velocity (vx,vy)
    # xx3) mass point on spring, pre-stressed and smashed against other mass
    # xx4) Newton's cradle with two pendulums
    # xx5) Newton's cradle with n pendulums

    # # NN) Johannes
    # "triangleWithMassPointsAndSprings": {
    #     "description": "",
    #     "parameters": {
    #     },
    #     "difficulty": 0,
    #    # "sampleFileName": ".py",
    # },
    
    # # NN) Johannes
    # "triangleWithMassPointsAndDistances": {
    #     "description": "",
    #     "parameters": {
    #     },
    #     "difficulty": 0,
    #    # "sampleFileName": ".py",
    # },
    

    
    # 28) Johannes
    "doubleWheelOnGround": {
        "description": "",
        "parameters": {
            "difficulty": 0,
        },
    },
    
    # 32) Michael
    "crane": {
        "description": "",
        "parameters": {
            "difficulty": 0,
        },
    },
    
    # 34) Johannes
    "fourWheelerOnGround": {
        "description": "",
        "parameters": {
            "difficulty": 0,
        },
    },
    
    # 37) Peter
    "simpleRobotArm": {
        "description": "",
        "parameters": {
            "difficulty": 0,
        },
    },
    
    # 38) Peter
    "scara": {
        "description": "",
        "parameters": {
            "difficulty": 0,
        },
    },

    # 39) Peter
    "duffingOscillator": { #requires nonlinear spring
        "description": "",
        "parameters": {
            "difficulty": 0,
        },
    },
        
}

############################################################################################################################################################################
############################################################################################################################################################################
#add readable name automatically...
for key, value in modelDescriptions.items():
    #print('process: '+key)
    # if key == 'singlePendulum': break
    if '_readableName' not in value:
        value['_readableName'] = AddSpacesToCamelCaseLocal(key)
        if value['_readableName'].startswith('n '):
            value['_readableName'] = 'n-'+value['_readableName'][2:]

#assign IDs and add two-way conversion dicts
modelName2mbsID = {}
mbsID2modelName = {}
cntID = 1 # needs to start with 1 to match formalism
for key, value in modelDescriptions.items():
    value['_ID'] = cntID
    modelName2mbsID[key] = cntID
    mbsID2modelName[cntID] = key
    cntID += 1


############################################################################################################################################################################
############################################################################################################################################################################

# returns the dict of available simulation elements and if they exist in a file (strin-basis)
def CheckModeledElementsInFile(filePath, modelName, readableName, elementsToCheck, elements2Code):
    try:
        with open(filePath, 'r', encoding='utf-8') as f:
            fileContent = f.read()
    except FileNotFoundError:
        print(f"File not found: {filePath}")
        
    foundElements = {}
    
    isMultibodySystem = False 
    nBodies = 0

    for element in elementsToCheck:
        # print(''+elements2Code[element])
        if elements2Code[element] in fileContent:
            #print('  '+element)
            foundElements[element] = True
            # print('   yes')
        else:
            foundElements[element] = False

    if fileContent.count('CreateMassPoint') + fileContent.count('CreateRigidBody') > 1:
        isMultibodySystem = True
        # print('  is multibody')
    
    if readableName.startswith('n-') or readableName.startswith('two mass') or 'chain' in readableName:
        isMultibodySystem = True

    
    if modelName in ['twoMassPointsWithSprings','massPointOnStringElastic']:
        foundElements['distance constraint'] = False
    if modelName in ['twoMassPointsWithDistances','massPointOnStringRigid']:
        foundElements['spring damper'] = False
    
    return [isMultibodySystem, foundElements]

def PrintMBSmodelOverview(latexFilePath, mbsReadableNames, isMultibodySystemDistribution, 
                          simElementsDistribution, filteredElements):
    # defining headers
       
    # putting desired columns into row format 
    dataRows = []

    for i in range(len(mbsIDs)):
        row = [
            #'$\model{' + str(mbsIDs[i]) + '}{1}$',
            str(mbsIDs[i]),
            mbsReadableNames[i],
            isMultibodySystemDistribution[i],
        ]

        # Unpack the element values into the row
        listDistribution = []
        for key in filteredElements:
            listDistribution.append(simElementsDistribution[i][key])
        row += list(listDistribution)
        dataRows.append(row)

    latexCode = []

    numColumns = len(filteredElements)
    columnDef = r"p{0.27cm}" + r"|p{4.45cm}" + r"|p{0.17cm}"*(1+numColumns)
    latexCode.append(r"\begin{tabular}{" + columnDef + "}")
    latexCode.append(r"\toprule")
    #latexCode.append(r"\cline{4-" + str(numColumns-1) + "}")
    latexCode.append(r"$k$ & modelname & \rotatebox{90}{multibody system} & ")
    latexCode.append(" & ".join([f"\\rotatebox{{90}}{{{col}}}" for col in filteredElements]) + r" \\")
    latexCode.append(r"\hline")

    for row in dataRows:
        rowEntries = []
        for idx, cell in enumerate(row):
            if idx == 0:
                rowEntries.append(str(cell))
            else:
                if cell == True:
                    rowEntries.append(r"\blackcheck")
                elif cell == False:
                    rowEntries.append(r"\blackhyphen")
                else:
                    rowEntries.append(str(cell))
        latexCode.append(" & ".join(rowEntries) + r" \\")

    latexCode.append(r"\hline")
    latexCode.append(r"\end{tabular}")

    with open(latexFilePath, "w") as f:
        f.write("\n".join(latexCode))

    print(f"LaTeX table written to: {latexFilePath}")
    
#parse Exudyn helper and fill into parsedDict
#maxDifficultyLevel: max level up to which tags are included
#parsedDictInit = {}: used to extend existing dict
def ParseExudynHelperLocal(filePath, maxDifficultyLevel=10000, excludeTags=[], 
                      parsedDictInit = {}):
    """
    Parse a file with special comments and organize information into a dictionary.

    Args:
        filePath (str): Path to the file to be parsed.
        maxDifficultyLevel (int): Maximum allowed difficulty level for including a tag.

    Returns:
        dict: A dictionary containing structured information.
    """
    
    import copy
   
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



    # this is the local change, returning the tagList, not the whole dict!
    return listTags
    

if __name__ == '__main__':
   
    if True:        ## create LaTeX-table of modeloverview including model-ID, mbs model-name, list of elements and indicator (used/not used), more than one body (e.g. 2 masses)
        import os    
        filePathExudynHelper = JoinPathLocal(os.getcwd(), '../helperFiles/exudynHelper.py')
        allAvailableElements = ParseExudynHelperLocal(filePathExudynHelper)
        # since excludeTags is not implemented anymore, exclude manually
        excludeTags=['simulationPure',
                     'visualization',
                     'generalrigid',
                     'general information',
                     'general import',
                     'assemble',
                     'ground', # exclude ground?
                    ]

        #automated; used as basis:
        #filteredElements = [el for el in allAvailableElements if el not in excludeTags]

        filteredElements = [
        'point mass',
        'rigid body',
        'spring damper',
        'distance constraint',
        'spherical joint',
        'prismatic joint',
        'revolute joint',
        'rolling disc',
        #'ideal rolling disc joint',
        'torsional spr.-damp.',
        'Cartesian spr.-damp.',
        #'rigid body spring damper'
        ]
        elements2Code = {
        'point mass':'CreateMassPoint',
        'rigid body':'CreateRigidBody',
        'spring damper':'CreateSpringDamper',
        'distance constraint':'CreateDistanceConstraint',
        'spherical joint':'CreateSphericalJoint',
        'prismatic joint':'CreatePrismaticJoint',
        'revolute joint':'CreateRevoluteJoint',
        'rolling disc':'CreateRollingDisc',
        #'ideal rolling disc joint',
        'torsional spr.-damp.':'CreateTorsionalSpringDamper',
        'Cartesian spr.-damp.':'CreateCartesianSpringDamper',
            }

        mbsIDs = []
        mbsReadableNames = []
        simElementsDistribution = []
        simElementsPerMBSmodel = {}
        isMultibodySystemDistribution = []


        for key, value in modelDescriptions.items():
            #print('process: '+key)
            readableName = value['_readableName']
            mbsReadableNames.append(readableName)
            mbsIDs.append(value['_ID'])
            
            # extract modeled simulation elements
            sampleFilePath = JoinPathLocal(os.getcwd(), '../sampleFiles/' + value['sampleFileName']) # per model .py
            [isMultibodySystem, simElementsPerMBSmodel] = CheckModeledElementsInFile(sampleFilePath, key, readableName, 
                                                                                     filteredElements, elements2Code) # tags of the used simulation elements per mbs model
            simElementsDistribution.append(simElementsPerMBSmodel) # only use the distribution values (True/False) not the element keys
            
            
            isMultibodySystemDistribution.append(isMultibodySystem)
            
            
        PrintMBSmodelOverview('../../../01_paper/mbsOverview.tex', 
                              mbsReadableNames,
                              isMultibodySystemDistribution,
                              simElementsDistribution,
                              filteredElements)
        
        