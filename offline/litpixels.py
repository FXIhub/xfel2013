import numpy as np
import h5py
import glob
import sys
import os
import multiprocessing as mp
import ctypes
import argparse

parser = argparse.ArgumentParser(description='Lit pixel hit finder')
parser.add_argument('run', 'Run number', type=int)
parser.add_argument('-d', '--dark', 'Dark run if not latest', type=int, default=None)
args = parser.parse_args()

folder = '/gpfs/exfel/exp/SPB/201701/p002013/raw/r%.4d/'%args.run
if args.dark is None:
    calib_file = '/gpfs/exfel/exp/SPB/201701/p002013/usr/Shared/calib/latest/Cheetah-AGIPD15-calib.h5'
else:
    calib_file = '/gpfs/exfel/exp/SPB/201701/p002013/scratch/calib/r%.4d/Cheetah-AGIPD15-calib.h5'%args.dark

# Constants
dset_name = '/INSTRUMENT/SPB_DET_AGIPD1M-1/DET/15CH0:xtdf/image/data'
cellid_name = '/INSTRUMENT/SPB_DET_AGIPD1M-1/DET/15CH0:xtdf/image/cellId'
trainid_name = '/INSTRUMENT/SPB_DET_AGIPD1M-1/DET/15CH0:xtdf/image/trainId'
good_cells = range(2,62,2)
num_h5cells = 64
adu_threshold = 40
num_threads = 80

# Calibration file for module 15
bool_cells = np.zeros(num_h5cells, dtype=np.bool)
bool_cells[good_cells] = True
with h5py.File(calib_file, 'r') as f:
    offset = f['AnalogOffset'][:, bool_cells]
    gain = f['RelativeGain'][:, bool_cells]
    gain_threshold = f['DigitalGainLevel'][:, bool_cells]
    badpix = f['Badpixel'][:, bool_cells]

def threshold(digital, cell):        
    thresh = gain_threshold[:,cell]
    high_gain = digital < thresh[1]
    low_gain = digital > thresh[2]
    medium_gain = (~high_gain) * (~low_gain)
    return low_gain*2 + medium_gain

def calibrate(data, digital, cell):        
    gain_mode = threshold(digital, cell)
    o = np.empty(gain_mode.shape)
    g = np.empty(gain_mode.shape)
    b = np.empty(gain_mode.shape)
    for i in range(3):
        o[gain_mode==i] = offset[i,cell][gain_mode==i]
        g[gain_mode==i] = gain[i,cell][gain_mode==i]
        b[gain_mode==i] = badpix[i,cell][gain_mode==i]

    data = (np.float32(data) - o)*g
    data[b != 0] = 0
    return data

def litpix_worker(rank, fname, num_trains, litpix, trainids, cellids):
    np_litpix = np.frombuffer(litpix.get_obj(), 'i4')
    np_trainids = np.frombuffer(trainids.get_obj(), 'u8')
    np_cellids = np.frombuffer(cellids.get_obj(), 'u8')
    fp = h5py.File(fname, 'r')
    for i in range(rank, num_trains, num_threads):
        start = i*len(good_cells)
        end = (i+1)*len(good_cells)
        h5start = i*num_h5cells
        h5end = (i+1)*num_h5cells

        analog = fp[dset_name][h5start:h5end, 0][good_cells]
        digital = fp[dset_name][h5start:h5end, 1][good_cells]
        for j in range(len(good_cells)):
            data = calibrate(analog[j], digital[j], j)
            np_litpix[start+j] = (data[384:]>adu_threshold).sum()
        np_trainids[start:end] = fp[trainid_name][h5start:h5end][good_cells].flatten()
        np_cellids[start:end] = fp[cellid_name][h5start:h5end][good_cells].flatten()
        if rank == 0:
            sys.stderr.write('\r%s %d/%d' % (fname, i+1, num_trains))
    fp.close()

litpix = np.empty((0,), dtype='i4')
trainids = np.empty((0,), dtype='u8')
cellids = np.empty((0,), dtype='u8')

# For all module 15 files
flist = sorted(glob.glob('%s/*AGIPD15*h5'%folder))
for fname in flist:
    with h5py.File(fname, 'r') as f:
        num_trains = f[dset_name].shape[0] // num_h5cells
    litpix_array = mp.Array(ctypes.c_int, len(good_cells)*num_trains)
    trainids_array = mp.Array(ctypes.c_ulong, len(good_cells)*num_trains)
    cellids_array = mp.Array(ctypes.c_ulong, len(good_cells)*num_trains)
    jobs = []
    for i in range(num_threads):
        p = mp.Process(target=litpix_worker, args=(i, fname, num_trains, litpix_array, trainids_array, cellids_array))
        jobs.append(p)
        p.start()
    for j in jobs:
        j.join()
    sys.stderr.write('\n')
    
    litpix = np.concatenate((litpix, np.frombuffer(litpix_array.get_obj(), 'i4')))
    trainids = np.concatenate((trainids, np.frombuffer(trainids_array.get_obj(), 'u8')))
    cellids = np.concatenate((cellids, np.frombuffer(cellids_array.get_obj(), 'u8')))

os.makedirs('data', exist_ok=True)
with h5py.File('data/hits_r%.4d.h5'%args.run, 'w') as f:
    f['hitFinding/litPixels'] = litpix
    f['hitFinding/trainId'] = trainids
    f['hitFinding/cellId'] = cellids
    f['hitFinding/ADUThreshold'] = adu_threshold
    f['hitFinding/goodCells'] = good_cells
