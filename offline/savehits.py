import mpi4py
from mpi4py import MPI
import numpy as np
import h5py
import combine_modules
import sys
import geom

if len(sys.argv) < 2:
    print('Format: %s <run_number>'%sys.argv[0])
    sys.exit()
run = int(sys.argv[1])

good_cells = range(2,62,2)
num_h5cells = 64
comm = MPI.COMM_WORLD
num_proc = comm.size
rank = comm.rank

with h5py.File('data/hits_r%.4d.h5'%run, 'r', driver='mpio', comm=comm) as f:
    litpix = f['hitFinding/litPixels'][:]

# 2 sigma cutoff for each cell
#thresh = np.array([litpix[i::len(good_cells)].mean() + litpix[i::len(good_cells)].std()*2 for i in range(len(good_cells))])
# Fixed threshold
thresh = np.ones(len(good_cells))*140
indices = np.where((litpix.reshape(-1, len(good_cells)) > thresh).flatten())[0]
c = combine_modules.AGIPD_Combiner(run)
frame_shape = c.get_frame(0).shape
unassembled_shape = c.get_frame(0, assemble=False).shape

if rank == 0:
    with h5py.File('data/hits_r%.4d.h5'%run, 'a') as f:
        if 'hits' in f:
            del f['hits']
        f['hits/numLitPixelThreshold'] = thresh
        f['hits/indices'] = indices
        f['hits/litPixels'] = litpix[indices]

with h5py.File('data/hits_r%.4d.h5'%run, 'a', driver='mpio', comm=comm) as f:
    f.create_dataset('hits/unassembled', shape=(len(indices),)+unassembled_shape, chunks=(1,)+unassembled_shape)
    f.create_dataset('hits/assembled', shape=(len(indices),)+frame_shape, chunks=(1,)+frame_shape)
    for i in np.arange(rank, len(indices), num_proc):
        shift = c.get_frame_id(indices[i])['shift'][15] // num_h5cells * len(good_cells)
        if shift > indices[i]:
            f['hits/unassembled'][i] = np.zeros(unassembled_shape, dtype='f4')
        else:
            f['hits/unassembled'][i] = c.get_frame(indices[i]-shift, calibrate=True, assemble=False)
        f['hits/assembled'][i] = geom.apply_geom_ij_yx((c.x, c.y), f['hits/unassembled'][i])
        f['hits/indices'][i] = indices[i] - shift
        if rank == 0:
            sys.stderr.write('\r%d/%d'%(i+1, len(indices)))
if rank == 0:
    sys.stderr.write('\n')
