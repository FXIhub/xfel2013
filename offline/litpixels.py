import numpy as np
import h5py
import glob
import sys
import os
import multiprocessing as mp
import ctypes

if len(sys.argv) < 2:
    print('Format: %s <run_number>'%sys.argv[0])
    sys.exit(1)

# Constants
calib_file = '/gpfs/exfel/exp/SPB/201701/p002013/scratch/calib/r0059/Cheetah-AGIPD15-calib.h5'
dset_name = '/INSTRUMENT/SPB_DET_AGIPD1M-1/DET/15CH0:xtdf/image/data'
cellid_name = '/INSTRUMENT/SPB_DET_AGIPD1M-1/DET/15CH0:xtdf/image/cellId'
trainid_name = '/INSTRUMENT/SPB_DET_AGIPD1M-1/DET/15CH0:xtdf/image/trainId'
good_cells = range(2,62,2)
num_h5cells = 64
litpix_threshold = 40
num_threads = 40

run = int(sys.argv[1])
folder = '/gpfs/exfel/exp/SPB/201701/p002013/raw/r%.4d/'%run

# Calibration file for module 15
bool_cells = np.zeros(num_h5cells, dtype=np.bool)
bool_cells[good_cells] = True
with h5py.File(calib_file, 'r') as f:
    offset = f['AnalogOffset'][:, bool_cells]
    gain = f['RelativeGain'][:, bool_cells]
    gain_threshold = f['DigitalGainLevel'][:, bool_cells]
    badpix = f['Badpixel'][:, bool_cells]

litpix = np.empty((0,), dtype='i4')
trainids = np.empty((0,), dtype='u8')
cellids = np.empty((0,), dtype='u8')

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
        high_gain = (digital < gain_threshold[1])
        analog = (analog-offset[0])*gain[0]*(badpix[0]==0)
        np_litpix[start:end] += (~high_gain).sum((1,2)) + (high_gain & (analog > litpix_threshold)).sum((1,2))
        np_trainids[start:end] = fp[trainid_name][h5start:h5end][good_cells].flatten()
        np_cellids[start:end] = fp[cellid_name][h5start:h5end][good_cells].flatten()
        if rank == 0:
            sys.stderr.write('\r%s %d/%d' % (fname, i+1, num_trains))
    fp.close()

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

    '''
    old_size = litpix.shape[0]
    litpix.resize((old_size + num_trains*len(good_cells),))
    trainids.resize((old_size + num_trains*len(good_cells),))
    cellids.resize((old_size + num_trains*len(good_cells),))
    #for i in range(num_trains):
    for i in range(10):
        start = old_size + i*len(good_cells)
        end = old_size + (i+1)*len(good_cells)
        h5start = i*num_h5cells
        h5end = (i+1)*num_h5cells

        analog = f[dset_name][h5start:h5end, 0][good_cells]
        digital = f[dset_name][h5start:h5end, 1][good_cells]
        
        high_gain = (digital < gain_threshold[1])
        analog = (analog-offset[0])*gain[0]*(badpix[0]==0)
        # Any medium or low gain pixel is considered to be lit
        litpix[start:end] += (~high_gain).sum((1,2)) + (high_gain & (analog > litpix_threshold)).sum((1,2))
        trainids[start:end] = f[trainid_name][h5start:h5end][good_cells].flatten()
        cellids[start:end] = f[cellid_name][h5start:h5end][good_cells].flatten()
        sys.stderr.write('\r%s: %d/%d' % (fname, i+1, num_trains))
    '''
sys.stderr.write('\n')

os.makedirs('data', exist_ok=True)
with h5py.File('data/hits_r%.4d.h5'%run, 'w') as f:
    f['hitFinding/litPixels'] = litpix
    f['hitFinding/trainId'] = trainids
    f['hitFinding/cellId'] = cellids
