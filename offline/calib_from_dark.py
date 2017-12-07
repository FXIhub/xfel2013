#!/usr/bin/env python

import os
import sys
import shutil
import h5py
import numpy as np
import glob
import multiprocessing as mp

'''
Short script to update calibration files with high gain darks using
a specified dark run number.

Authors: Kartik Ayyer, Filipe Maia
'''

if len(sys.argv) < 2:
    print('Format: %s <run_number>' % sys.argv[0])
    sys.exit(1)

run = int(sys.argv[1])
num_cells = 64

folder = '/gpfs/exfel/exp/SPB/201701/p002013/scratch/calib'
os.makedirs('%s/r%.4d'%(folder, run), exist_ok=True)

def worker(m):
    shutil.copyfile('%s/Cheetah-AGIPD%.2d-calib.h5'%(folder, m), '%s/r%.4d/Cheetah-AGIPD%.2d-calib.h5'%(folder, run, m))
    dark_sum = np.zeros((num_cells,512,128))
    dark_sumsq = np.zeros((num_cells,512,128))
    
    flist = sorted(glob.glob('/gpfs/exfel/exp/SPB/201701/p002013/raw/r%.4d/RAW-R%.4d-AGIPD%02d-S*.h5' % (run,run,m)))
    num_trains = 0
    for fname in flist:
        f = h5py.File(fname, 'r')
        dset = f['/INSTRUMENT/SPB_DET_AGIPD1M-1/DET/%dCH0:xtdf/image/data' % (m)]    
        num_trains += dset.shape[0] // num_cells

        for i in range(dset.shape[0] // num_cells):
            for j in range(num_cells):
                data = dset[num_cells*i+j,0,:,:].astype('f8')
                dark_sum[j,:,:] += data[j]
                dark_sumsq[j,:,:] += data[j]**2

            if m == 0:
                sys.stderr.write('\r%s: %.4d' % (os.path.basename(fname), i))
        f.close()

    dark_sum /= num_trains
    dark_sumsq /= num_trains

    with h5py.File('%s/r%.4d/Cheetah-AGIPD%.2d-calib.h5'%(folder, run, m), 'a') as f:
        f['AnalogOffset'][0,:,:,:] = dark_sum
        f['DarkVariance'] = dark_sumsq - dark_sum**2

pool = mp.Pool(16)
pool.map(worker, range(16))
sys.stderr.write('\n')

