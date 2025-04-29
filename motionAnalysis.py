# -*- coding: utf-8 -*-
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# This is part of the AI engineering lab project
#
# Filename: motionAnalysis.py
#
# Details:  main functionality to process sensor output and perform special multibody analysis;
#           postprocessing of data, error and warning handling and conversion in AI-text-readable format
#           
# Author:   Johannes Gerstmayr
# Date:     2025-03-23
#
# License:  BSD-3 license
#
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


import sys
import re
import numpy as np
import os
from utilities import ConvertValueArray2Text, ConvertResultsToPlainText

#resamble data, directly read from sensor, using numberOfSamples and number of digits
#UNUSED IN new framework!
def ResampleSensorOutput(data, numberOfSamples, nDigits = None):
    """
    Parameters
    ----------
    data : numpy array
        one data sample per row
    numberOfSamples : int
        total number of samples to be created (should be > 1)
    nDigits : int, optional
        if not None, this is the number of digits used for rounding data

    Returns
    -------
    rData : numpy array
        resampled and rounded data
    """
    #from scipy.signal import resample, decimate
    #note resample uses FFT and only works for periodic signals!
    #use numpy interp, which only works for 1D signals!

    original_indices = np.linspace(0, len(data) - 1, len(data))
    new_indices = np.linspace(0, len(data) - 1, numberOfSamples)

    if data.ndim == 2:
        rData = np.zeros((numberOfSamples, data.shape[1]))
    
        for col in range(data.shape[1]):
            rData[:, col] = np.interp(new_indices, original_indices, data[:, col])
    elif data.ndim == 1:
        rData = np.interp(new_indices, original_indices, data)
    else:
        raise ValueError('ResampleSensorOutput: data must be a 1D or 2D numpy array')
        

    if nDigits is not None:
        rData = np.round(rData,nDigits)
    return rData 

#%%+++++++++++++++++++++++++++++++++++++++++++++++++++
#return true if trajectory has only one point, which is same for all times
def CheckIfTrajectoryIsPoint(data):
    positions = data[:, 1:].astype(np.float64)
    pos0 = positions[0]
    for pos in positions[1:]:
        if np.linalg.norm(pos0-pos) != 0:
            return False
    return True

#check if trajectory is linear (all points lie on the same line);
#  calculate the maximum distance from the line, using start point and point which is furthest away from start point
def CheckLinearTrajectory(data):
    # Extract positions (x, y, z)
    positions = data[:, 1:].astype(np.float64)
    
    # Get the start and end points
    startPoint = positions[0]
    endPoint = positions[-1]

    # Possibly search other end point (e.g., if trajectory starts and ends at same point)
    dist = 0
    
    for pos in positions[1:]:
        if np.linalg.norm(startPoint - pos) > dist:
            dist = np.linalg.norm(startPoint - pos)
            endPoint = pos
            
    # Compute the direction vector from start to end point
    normalizedLineVector = endPoint - startPoint
    
    # Check if the start and end points are identical
    if np.linalg.norm(normalizedLineVector) == 0:
        return {'maxDistanceFromLine': sys.float_info.max,
                'normalizedLineVector': normalizedLineVector, 
                'startPoint': startPoint,
                'success': False}
    
    # Normalize the line vector
    normalizedLineVector /= np.linalg.norm(normalizedLineVector)
    
    # Compute the vector from the start point to all other points
    vectorsToPoints = positions - startPoint
    
    # Project these vectors onto the line vector to find their closest points on the line
    projections = np.dot(vectorsToPoints, normalizedLineVector)[:, None] * normalizedLineVector
    
    # Compute the deviation vectors (from points to their projections on the line)
    deviations = vectorsToPoints - projections
    
    # Calculate the distances of the deviations
    distances = np.linalg.norm(deviations, axis=1)
    
    #evaluate maxLineVectorLength
    scalarProjections = np.dot(vectorsToPoints, normalizedLineVector)
    maxLineVectorLength = np.max(scalarProjections) - np.min(scalarProjections)
    
    # Check if the maximum deviation is within the tolerance
    maxDistanceFromLine = np.max(distances)
    return {'maxDistanceFromLine':maxDistanceFromLine,
            'normalizedLineVector':normalizedLineVector, 
            'maxLineVectorLength':maxLineVectorLength,
            'startPoint':startPoint,
            'timespan':data[-1,0]-data[0,0],
            'success': True}


#%%+++++++++++++++++++++++++++++++++++++++++++++++++++
#Check if a motion is planar (all points lie in the same plane) and calculate the maximum distance from the best-fit plane.
def CheckPlanarTrajectory(data):
    # Extract positions (x, y, z)
    positions = data[:, 1:]
    
    foundPlaneSuccess = True
    
    # Calculate the centroid of the points
    planeMidpoint = np.mean(positions, axis=0)
    
    # Shift the points by subtracting the centroid
    shiftedPositions = positions - planeMidpoint
    
    # Perform singular value decomposition (SVD)
    _, _, vh = np.linalg.svd(shiftedPositions)
    
    # The normal vector to the best-fit plane is given by the last row of vh
    planeNormal = vh[-1]

    L = np.linalg.norm(planeNormal)
    if L == 0:
        foundPlaneSuccess = False
        maxPlaneDistance = sys.float_info.max
    else:
        planeNormal /= L
        
        # Calculate the distances of all points from the plane
        distances = np.dot(shiftedPositions, planeNormal)
        maxPlaneDistance = np.max(np.abs(distances))

    if CheckIfTrajectoryIsPoint(data):
        planeNormal = np.array([0,0,0])
        foundPlaneSuccess = False

    return {'maxPlaneDistance':maxPlaneDistance, 
            'planeNormal':planeNormal, 
            'planeMidpoint':planeMidpoint,
            'timespan':data[-1,0]-data[0,0],
            'success': foundPlaneSuccess}

#%%+++++++++++++++++++++++++++++++++++++++++++++++++++
#Check if a motion is spherical (all points lie approximately on a sphere) 
#and calculate the maximum deviation from the best-fit sphere.
def CheckSphericalMotion(data):

    if CheckIfTrajectoryIsPoint(data):
        return {'maxDeviation':sys.float_info.max,
                'center':[0,0,0],
                'radius':0,
                'success':False}
    
    # Extract positions (x, y, z)
    positions = data[:, 1:]
    
    # Number of points
    n_points = positions.shape[0]

    # Set up the system of equations to solve for the sphere center and radius
    A = np.hstack((positions, np.ones((n_points, 1))))  # [x, y, z, 1]
    b = np.sum(positions**2, axis=1)  # x^2 + y^2 + z^2

    # Solve the linear system using least squares
    coeffs, _, _, _ = np.linalg.lstsq(A, b, rcond=None)

    # Extract the sphere center and radius
    center = coeffs[:3] / 2
    radius = np.sqrt(np.sum(center**2) + coeffs[3])

    # Compute the distances of all points from the sphere center
    distances = np.linalg.norm(positions - center, axis=1)

    # Compute the deviations from the sphere radius
    deviations = np.abs(distances - radius)

    # Find the maximum deviation
    maxDeviation = np.max(deviations)

    return {'maxDeviation':maxDeviation,
            'center':center, 
            'radius':radius,
            'timespan':data[-1,0]-data[0,0],
            'success':True}


#%%+++++++++++++++++++++++++++++++++++++++++++++++++++
#Check if a motion is circular
def CheckCircularMotion(data):
    dictSpherical = CheckSphericalMotion(data)
    dictPlanar = CheckPlanarTrajectory(data)
    maxPlaneDeviation = 0
    if dictPlanar['success']:
        maxPlaneDeviation = dictPlanar['maxPlaneDistance']
    
    return {'maxDeviation':dictSpherical['maxDeviation'] + maxPlaneDeviation,
            'center':dictSpherical['center'], 
            'radius':dictSpherical['radius'],
            'circularPlaneNormal':dictPlanar['planeNormal'],
            'timespan':data[-1,0]-data[0,0],
            'success':dictPlanar['success'] and dictSpherical['success']
            }
    
#%%+++++++++++++++++++++++++++++++++++++++++++++++++++
#Check max and min values of motion space
#motionTypeStr shall be Position, Velocity, Acceleration, ...
def CheckMinMaxValues(data, motionTypeStr):
    positions = data[:, 1:]
    minPos = np.array(positions[0]) #copy!! - otherwise, min=max
    maxPos = np.array(positions[0]) #copy!!
    for pos in positions:
        for i in range(3):
            minPos[i] = min(minPos[i],pos[i])
            maxPos[i] = max(maxPos[i],pos[i])
    return {'minimum'+motionTypeStr+'XyzComponents':minPos,
            'maximum'+motionTypeStr+'XyzComponents':maxPos,
            'simulatedTimespan':data[-1,0]-data[0,0],
            'success':True
            }

#check position motion space (min/max)
def CheckMotionSpace(data):
    return CheckMinMaxValues(data, motionTypeStr='Position')

#check velocity space (min/max)
def CheckVelocitySpace(data):
    return CheckMinMaxValues(data, motionTypeStr='Velocity')

#check accerlation space (min/max)
def CheckAccelerationSpace(data):
    return CheckMinMaxValues(data, motionTypeStr='Acceleration')

#%%+++++++++++++++++++++++++++++++++++++++++++++++++++
#Check if a motion is parabolic by analyzing the second derivatives of position with respect to time.
#returns the maxDeviations from the parabolic motion, which is the deviation from mean accelerations
def CheckParabolicMotion(data):
    t = data[:, 0]
    positions = data[:, 1:]
    accelerations = []

    for dim in range(positions.shape[1]):  # For x, y, z
        pos = positions[:, dim]
        
        #fit quadratic polynomial: pos(t) ≈ a*t^2 + b*t + c
        coeffs = np.polyfit(t, pos, deg=2)  # returns [a, b, c]

        a = coeffs[0] #this coefficient remains after 2x diff
        acc = 2 * a   #pos=a*t^2 => pos'' = 2*a
        accelerations.append(acc)

    accelerations = np.array(accelerations)

    #now calculate deviation from polynomial
    residuals = []
    for dim in range(positions.shape[1]):
        poly = np.poly1d(np.polyfit(t, positions[:, dim], deg=2))
        predicted = poly(t)
        residual = np.linalg.norm(predicted - positions[:, dim])
        residuals.append(residual)

    totalResidual = np.sum(residuals)
   
    return {'maxParabolicDeviation':totalResidual,
            'meanAccelerationXyzComponents':accelerations, 
            'simulatedTimespan':data[-1,0]-data[0,0],
            'success':True
            }

#WARNING: this approach only works for small time steps (numerical differentiation!)
# def CheckParabolicMotion(data):
#     # Extract time and positions
#     t = data[:, 0]
#     positions = data[:, 1:]
    
#     # Calculate velocities (first derivative)
#     velocities = np.gradient(positions, t, axis=0)
    
#     # Calculate accelerations (second derivative)
#     accelerations = np.gradient(velocities, t, axis=0)
    
#     # Check if the accelerations are approximately constant
#     meanAcceleration = np.mean(accelerations, axis=0)
#     deviations = np.linalg.norm(accelerations - meanAcceleration, axis=1)
#     maxDeviation = np.max(deviations)
   
#     return {'maxDeviation':maxDeviation,
#             'meanAcceleration':meanAcceleration, 
#             'success':True
#             }

#%%+++++++++++++++++++++++++++++++++++++++++++++++++++
#harmonic motion
#helical motion
#motion ?orbits? => repeated motion trajectories
#  =>periodic motion
#damped motion (check decreasing velocity; check monotonically decreasing velocity)
#look at min/max, pos/neg edge (relative to mean value),
#look at sequences of min/max peaks
#look at frequency due to pos edge
#look at impacts (sudden change of velocity)
#look at linear decay of velocity (friction) or exponential decay (viscous)
#chaotic motion (would mean, we simulate several times by slightly changing (1e-14) initial conditions)
#Epicycloidal and Hypocycloidal Motion
#Lissajous Motion
#scara (double pendulum) motion? is this possible?
#Diverging or Converging Motion (The velocity vector points outward (divergent) or inward (convergent) from a central point.)
#Fourier analysis


    
#%%+++++++++++++++++++++++++++++++++++++++++++++++++++
if __name__ == "__main__":
    if True:
        # Example usage:
        # Simulation data (time, x, y, z)
        data = np.array([
            [0, -0.2, 0, 0],
            [1, 0.25, 0, 0],
            [2, 0.5, 0, 0.001], #deviation of 0.001
            [3, 1.25, 0, 0]
        ])
        
        print('** test linear=\n', CheckLinearTrajectory(data))  # Output: True

    if True:
        data = np.array([
            [0, 0.25, 0, 0],
            [1, 0.25, 0, 0],
            [2, 0.25, 0, 0],
            [3, 0.25, 0, 0] ])
        print('** test point=\n', CheckIfTrajectoryIsPoint(data))  # Output: True
        print('** test planar=\n', CheckPlanarTrajectory(data))  # Output: True
        print('** test spherical=\n', CheckSphericalMotion(data))  # Output: True
        print('** test circular=\n', CheckCircularMotion(data))  # Output: True
        print()
    if True:
        data = np.array([
                        [0, 0, 0, 0],
                        [1, 1, 0, 0],
                        [2, 0, 1, 0],
                        [3, 2, 2, 0*1e-8]  # Slight deviation from the plane
                    ])
        print('** test planar=\n',CheckPlanarTrajectory(data))

    if True:
        #circle with center=[1,0,0], radius=1
        data = np.array([
                        [0, 2, 0, 0],
                        [1, 1, 1, 0],
                        [2, 1, 0, 1],
                        [3, 1, -1, 0],
                        [4, 1.707, 0.707, 0],  # Slight deviation
                        [4, 1.57, 0.57735, 0.57735]  # Slight deviation
                    ])
        print('** test spherical=\n',CheckSphericalMotion(data))
        print('** test planar=\n',CheckPlanarTrajectory(data))
        print('** test circular=\n',CheckCircularMotion(data))

        d = CheckCircularMotion(data)
        
        print('\nresults=\n'+ConvertResultsToPlainText(d, 'CheckCircularMotion', nDigits=3)['text'])

        d = {'maxDeviation':sys.float_info.max,
                'center':[0,0,0],
                'radius':0,
                'success':False}
        
        print('\nresults=\n'+ConvertResultsToPlainText(d, 'CheckCircularMotion', nDigits=3)['text'])
        
        