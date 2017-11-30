#!/usr/bin/env python

import os
import sys
import shutil
import h5py
import numpy as np
import matplotlib.pyplot as plt

'''
Short script to update calibration files with high gain darks using
a specified dark run number.

(Currently only uses 250 trains (251-500) to calculate mean signal)
'''

if len(sys.argv) < 2:
    print('Format: %s <run_number>' % sys.argv[0])
    sys.exit(1)

run = int(sys.argv[1])
#good_cells = list(range(2,62,2))
num_cells = 64

folder = '/gpfs/exfel/exp/SPB/201701/p002013/scratch/calib'
os.makedirs('%s/r%.4d'%(folder, run), exist_ok=True)

for m in range(16):    
    shutil.copyfile('%s/Cheetah-AGIPD%.2d-calib.h5'%(folder, m), '%s/r%.4d/Cheetah-AGIPD%.2d-calib.h5'%(folder, run, m))
    #dark_sum = np.zeros((len(good_cells),512,128))
    dark_sum = np.zeros((num_cells,512,128))
    
    dark_file = '/gpfs/exfel/exp/SPB/201701/p002013/raw/r%.4d/RAW-R%.4d-AGIPD%02d-S00001.h5' % (run,run,m)
    with h5py.File(dark_file, 'r') as f:
        dset = f['/INSTRUMENT/SPB_DET_AGIPD1M-1/DET/%dCH0:xtdf/image/data' % (m)]    
        for i in range(dset.shape[0]//64):
            #for j in range(len(good_cells)):
            for j in range(64):
                index = 60*i+j
                dark_sum[j,:,:] += dset[60*i + j,0,:,:]
        sys.stderr.write('\r(%.4d, %.4d)' % (i, m))
        dark_sum /= dset.shape[0]/64
    sys.stderr.write('\n')

    with h5py.File('%s/r%.4d/Cheetah-AGIPD%.2d-calib.h5'%(folder, run, m), 'a') as f:
        f['AnalogOffset'][0,:,:,:] = dark_sum


