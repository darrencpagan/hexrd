import copy
import os
import sys
import time

import shelve, cPickle
import numpy as np

from scipy.optimize import leastsq
from scipy.linalg import solve

from ConfigParser import SafeConfigParser

from hexrd.xrd import experiment      as expt
from hexrd.xrd import transforms      as xf
from hexrd.xrd import transforms_CAPI as xfcapi

from hexrd.xrd.detector import ReadGE


# #################################################
# PARAMETERS
d2r = np.pi/180.
r2d = 180./np.pi

bVec_ref = xf.bVec_ref
vInv_ref = xf.vInv_ref
# #################################################

# #################################################
# LEGACY FUCTIONS FOR WORKING WITH OLD HEXRD PAR
def tVec_d_from_old_detector_params(old_par, det_origin):
    """
    calculate tVec_d from old [xc, yc, D] parameter spec

    as loaded the params have 2 columns: [val, bool]
    """
    rMat_d = xf.makeDetectorRotMat(old_par[3:6, 0])
    #
    P2_d   = np.c_[ old_par[0, 0] - det_origin[0],
                    old_par[1, 0] - det_origin[1],
                    0.].T
    P2_l   = np.c_[ 0.,
                    0.,
                   -old_par[2, 0]].T
    return P2_l - np.dot(rMat_d, P2_d)

def old_detector_params_from_new(new_par, det_origin):
    """
    calculate beam position in old parameter spec

    *) may need to consider distortion...
    """
    rMat_d = xf.makeDetectorRotMat(new_par[:3])
    tVec_d = new_par[3:6].reshape(3, 1)
    #
    A = np.eye(3); A[:, :2] = rMat_d[:, :2]
    #
    return solve(A, -tVec_d) + np.vstack([det_origin[0], det_origin[1], 0])

def make_old_detector_parfile(results, det_origin=(204.8, 204.8), filename=None):
    tiltAngles = np.array(results['tiltAngles'])
    rMat_d     = xf.makeDetectorRotMat(tiltAngles)
    tVec_d     = results['tVec_d'] - results['tVec_s']
    #
    beamXYD = old_detector_params_from_new(np.hstack([tiltAngles.flatten(), tVec_d.flatten()]), det_origin)
    #
    det_plist = np.zeros(12)
    det_plist[:3]  = beamXYD.flatten()
    det_plist[3:6] = tiltAngles
    det_plist[6:]  = results['dParams']
    if filename is not None:
        if isinstance(filename, file):
            fid = filename
        elif isinstance(filename, str) or isinstance(filename, unicode):
            fid = open(filename, 'w')
        print >> fid, "# DETECTOR PARAMETERS (from new geometry model fit)"
        print >> fid, "# \n# <class 'hexrd.xrd.detector.DetectorGeomGE'>\n#"
        for i in range(len(det_plist)):
            print >> fid, "%1.8e\t%d" % (det_plist[i], 0)
        fid.close()
    return det_plist

def convert_detector_params(old_par, det_origin, chi=0., tVec_s=np.zeros(3), filename=None):
    """
    takes old ge detector parfile from hexrd and converts to the new 10
    parameters
    """
    tVec_d = tVec_d_from_old_detector_params(old_par, det_origin)
    detector_params = np.hstack([old_par[3:6, 0], tVec_d.flatten(), chi, tVec_s.flatten()])
    if filename is not None:
        if isinstance(filename, file):
            fid = filename
        elif isinstance(filename, str) or isinstance(filename, unicode):
            fid = open(filename, 'w')
        print >> fid, "# DETECTOR PARAMETERS"
        print >> fid, \
            "%1.7e\t# tiltAngles[0]\n" % (detector_params[0]) + \
            "%1.7e\t# tiltAngles[1]\n" % (detector_params[1]) + \
            "%1.7e\t# tiltAngles[2]\n" % (detector_params[2]) + \
            "%1.7e\t# tVec_d[0]    \n" % (detector_params[3]) + \
            "%1.7e\t# tVec_d[1]    \n" % (detector_params[4]) + \
            "%1.7e\t# tVec_d[2]    \n" % (detector_params[5]) + \
            "%1.7e\t# chi          \n" % (detector_params[6]) + \
            "%1.7e\t# tVec_s[0]    \n" % (detector_params[7]) + \
            "%1.7e\t# tVec_s[1]    \n" % (detector_params[8]) + \
            "%1.7e\t# tVec_s[2]    \n" % (detector_params[9])
        fid.close()
    return detector_params

def make_grain_params(quat, tVec_c=np.zeros(3), vInv=vInv_ref, filename=None):
    phi      = 2*np.arccos(quat[0])
    n        = xf.unitVector(quat[1:, :])
    expMap_c = phi*n
    if filename is not None:
        if isinstance(filename, file):
            fid = filename
        elif isinstance(filename, str) or isinstance(filename, unicode):
            fid = open(filename, 'w')
        print >> fid, \
            "%1.7e\t# expMap_c[0]\n" % (expMap_c[0]) + \
            "%1.7e\t# expMap_c[1]\n" % (expMap_c[1]) + \
            "%1.7e\t# expMap_c[2]\n" % (expMap_c[2]) + \
            "%1.7e\t# tVec_c[0]  \n" % (tVec_c[0])   + \
            "%1.7e\t# tVec_c[1]  \n" % (tVec_c[1])   + \
            "%1.7e\t# tVec_c[2]  \n" % (tVec_c[2])   + \
            "%1.7e\t# vInv_s[0]  \n" % (vInv[0])     + \
            "%1.7e\t# vInv_s[1]  \n" % (vInv[1])     + \
            "%1.7e\t# vInv_s[2]  \n" % (vInv[2])     + \
            "%1.7e\t# vInv_s[3]  \n" % (vInv[3])     + \
            "%1.7e\t# vInv_s[4]  \n" % (vInv[4])     + \
            "%1.7e\t# vInv_s[5]  \n" % (vInv[5])
        fid.close()
    return np.hstack([expMap_c.flatten(), tVec_c.flatten(), vInv.flatten()])
# #################################################

# #################################################


def initialize_experiment(cfg, verbose=False):
    """takes a yml configuration file as input"""
    # make experiment
    ws = expt.Experiment()

    cwd = cfg['base'].get('working_dir', os.getcwd())

    materials_fname = cfg['material']['definitions']
    material_name = cfg['material']['active']
    detector_fname = cfg['detector']['parameters_old']

    # MATERIALS
    ws.loadMaterialList(os.path.join(cwd, materials_fname))
    ws.activeMaterial = material_name
    if verbose:
        print "setting active material to '%s'" % (material_name)

    pd = ws.activeMaterial.planeData

    # assemble the image series
    image_dir = cfg['image_series']['directory']
    file_stem = cfg['image_series']['file']['stem']
    file_ids = cfg['image_series']['file']['ids']
    image_start = cfg['image_series']['images']['start']
    file_info = []
    for fid in file_ids:
        file_info.append(
            (os.path.join(image_dir, file_stem % fid), image_start)
            )
    ome_start = cfg['image_series']['ome']['start'] * d2r
    ome_delta = cfg['image_series']['ome']['step'] * d2r
    dark = cfg['image_series'].get('dark', None)
    flip = cfg['image_series'].get('flip', None)

    # make frame reader
    reader = ReadGE(file_info, ome_start, ome_delta,
                    subtractDark=dark is not None, # TODO: get rid of this
                    dark=dark,
                    doFlip=flip is not None,
                    flipArg=flip, # TODO: flip=flip
                    )

    # DETECTOR
    ws.loadDetector(os.path.join(cwd, detector_fname))

    return pd, reader, ws.detector


def merge_dicts(a, b):
    "Returns a merged dict, updating values in `a` with values from `b`"
    a = copy.deepcopy(a)
    for k,v in b.iteritems():
        if isinstance(v, dict):
            merge_dicts(a[k], v)
        else:
            a[k] = v
    return a