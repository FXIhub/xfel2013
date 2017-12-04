#!/usr/bin/env python

import os
import sys
import shutil
import h5py
import numpy as np
import glob

'''
Short script to update calibration files with high gain darks using
a specified dark run number.

(Currently only uses 250 trains (251-500) to calculate mean signal)
Authors: Kartik Ayyer, Filipe Maia
'''

if len(sys.argv) < 2:
    print('Format: %s <run_number>' % sys.argv[0])
    sys.exit(1)

run = int(sys.argv[1])
num_cells = 64

folder = '/gpfs/exfel/exp/SPB/201701/p002013/scratch/calib'
os.makedirs('%s/r%.4d'%(folder, run), exist_ok=True)

for m in range(16):    
    shutil.copyfile('%s/Cheetah-AGIPD%.2d-calib.h5'%(folder, m), '%s/r%.4d/Cheetah-AGIPD%.2d-calib.h5'%(folder, run, m))
    dark_sum = np.zeros((num_cells,512,128))
    
    #dark_file = '/gpfs/exfel/exp/SPB/201701/p002013/raw/r%.4d/RAW-R%.4d-AGIPD%02d-S00001.h5' % (run,run,m)
    flist = sorted(glob.glob('/gpfs/exfel/exp/SPB/201701/p002013/raw/r%.4d/RAW-R%.4d-AGIPD%02d-S*.h5' % (run,run,m)))
    num_trains = 0
    for fname in flist:
        with h5py.File(fname, 'r') as f:
            dset = f['/INSTRUMENT/SPB_DET_AGIPD1M-1/DET/%dCH0:xtdf/image/data' % (m)]    
            num_trains += dset.shape[0] // num_cells
            for i in range(dset.shape[0] // num_cells):
                for j in range(num_cells):
                    index = num_cells*i+j
                    dark_sum[j,:,:] += dset[num_cells*i + j,0,:,:]
                    sys.stderr.write('\r%s: (%.4d, %.4d)' % (os.path.basename(fname), i, m))
        sys.stderr.write('\n')
    dark_sum /= num_trains
    print('Processed %d trains'%num_trains)

    with h5py.File('%s/r%.4d/Cheetah-AGIPD%.2d-calib.h5'%(folder, run, m), 'a') as f:
        f['AnalogOffset'][0,:,:,:] = dark_sum

