#!/usr/bin/env python

import mpi4py
from mpi4py import MPI
import numpy as np
import h5py
import combine_modules
import sys
import geom
import argparse

parser = argparse.ArgumentParser(description='Save hits according to threshold')
parser.add_argument('run', help='Run number', type=int)
parser.add_argument('-d', '--dark', help='Dark run if not latest', type=int, default=None)
parser.add_argument('-t', '--threshold', help='Lit pixel threshold to be considered a hit', type=float, default=240)
args = parser.parse_args()

good_cells = range(2,62,2)
num_h5cells = 64
world_comm = MPI.COMM_WORLD
world_rank = world_comm.rank

with h5py.File('data/hits_r%.4d.h5'%args.run, 'r', driver='mpio', comm=world_comm) as f:
    litpix = f['hitFinding/litPixels'][:]

# 2 sigma cutoff for each cell
#thresh = np.array([litpix[i::len(good_cells)].mean() + litpix[i::len(good_cells)].std()*2 for i in range(len(good_cells))])
# Fixed threshold
thresh = np.ones(len(good_cells))*args.threshold

indices = np.where((litpix.reshape(-1, len(good_cells)) > thresh).flatten())[0]
if world_rank == 0:
    sys.stderr.write('%d hits in run %d\n' % (len(indices), args.run))
c = combine_modules.AGIPD_Combiner(args.run, calib_run=args.dark)
frame_shape = c.get_frame(0).shape
unassembled_shape = c.get_frame(0, assemble=False).shape

# Split comm if number of hits < number of procs
comm = world_comm.Split(world_rank<len(indices), world_rank)
rank = comm.rank
num_proc = comm.size

if world_rank == 0:
    with h5py.File('data/hits_r%.4d.h5'%args.run, 'a') as f:
        if 'hits' in f:
            del f['hits']
        f['hits/numLitPixelThreshold'] = thresh
        f['hits/indices'] = indices
        f['hits/litPixels'] = litpix[indices]

if world_rank < len(indices):
    with h5py.File('data/hits_r%.4d.h5'%args.run, 'a', driver='mpio', comm=comm) as f:
        f.create_dataset('hits/unassembled', shape=(len(indices),)+unassembled_shape, chunks=(1,)+unassembled_shape)
        f.create_dataset('hits/assembled', shape=(len(indices),)+frame_shape, chunks=(1,)+frame_shape)
        for i in np.arange(rank, len(indices), num_proc):
            try:
                shift = c.get_frame_id(indices[i])['shift'][15] // num_h5cells * len(good_cells)
            except ValueError:
                shift = 0
            if shift > indices[i]:
                f['hits/unassembled'][i] = np.zeros(unassembled_shape, dtype='f4')
            else:
                try:
                    f['hits/unassembled'][i] = c.get_frame(indices[i]-shift, calibrate=True, assemble=False)
                except ValueError:
                    f['hits/unassembled'][i] = np.zeros(unassembled_shape, dtype='f4')
            f['hits/assembled'][i] = geom.apply_geom_ij_yx((c.x, c.y), f['hits/unassembled'][i])
            f['hits/indices'][i] = indices[i] - shift
            if rank == 0:
                sys.stderr.write('\r%d/%d'%(i+1, len(indices)))
if world_rank == 0:
    sys.stderr.write('\n')
