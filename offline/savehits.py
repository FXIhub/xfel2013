import numpy as np
import h5py
import combine_modules
import sys

if len(sys.argv) < 2:
    print('Format: %s <run_number>'%sys.argv[0])
    sys.exit()
run = int(sys.argv[1])

good_cells = range(2,62,2)
num_h5cells = 64

with h5py.File('data/hits_r%.4d.h5'%run, 'r') as f:
    litpix = f['hitFinding/litPixels'][:]

# 2 sigma cutoff for each cell
thresh = np.array([litpix[i::len(good_cells)].mean() + litpix[i::len(good_cells)].std()*2 for i in range(len(good_cells))])
indices = np.where((litpix.reshape(-1, len(good_cells)) > thresh).flatten())[0]
c = combine_modules.AGIPD_Combiner(run)
frame_shape = c.get_frame(0).shape
unassembled_shape = c.get_frame(0, assemble=False).shape
#shifts = np.array([c.get_frame_id(ind)['shift'][15] for ind in indices])

with h5py.File('data/hits_r%.4d.h5'%run, 'a') as f:
    if 'hits' in f:
        del f['hits']
    f.create_dataset('hits/assembled', shape=(len(indices),)+frame_shape, chunks=(1,)+frame_shape)
    f.create_dataset('hits/unassembled', shape=(len(indices),)+unassembled_shape, chunks=(1,)+unassembled_shape)
    f['hits/numLitPixelThreshold'] = thresh
    f['hits/indices'] = indices
    f['hits/litPixels'] = litpix[indices]
    for i, num in enumerate(indices):
        shift = c.get_frame_id(num)['shift'][15] // num_h5cells * len(good_cells)
        if shift > num:
            f['hits/assembled'][i] = np.zeros(frame_shape)
            f['hits/unassembled'][i] = np.zeros(unassembled_shape)
        else:
            f['hits/assembled'][i] = c.get_frame(num - shift, calibrate=True)
            f['hits/unassembled'][i] = c.get_frame(num - shift, calibrate=True, assemble=False)
        f['hits/indices'][i] = num - shift
        sys.stderr.write('\r%d/%d'%(i+1, len(indices)))
sys.stderr.write('\n')

