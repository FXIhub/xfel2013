#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys, os, re
import argparse
import h5py
import numpy as np
from matplotlib import pyplot as plt

#sys.path.insert(0, '/gpfs/exfel/u/usr/SPB/201701/p002013/sbobkov/xfel2013/offline')
import combine_modules

BASE_EXP_FOLDER = '/gpfs/exfel/u/scratch/SPB/201701/p002013/ayyerkar/xfel2013/offline/data/'
SCRATCH_FIG_FOLDER = '/gpfs/exfel/u/scratch/SPB/201701/p002013/sellberg/figures/'
SCRATCH_FOLDER = '/gpfs/exfel/u/scratch/SPB/201701/p002013/sellberg/hit_statistics/'

runs = ['hits_r0071.h5', 'hits_r0072.h5', 'hits_r0073.h5', 'hits_r0074.h5', 'hits_r0075.h5', 'hits_r0076.h5', 'hits_r0079.h5', 'hits_r0080.h5', 'hits_r0081.h5', 'hits_r0082.h5', 'hits_r0083.h5', 'hits_r0086.h5', 'hits_r0089.h5', 'hits_r0090.h5', 'hits_r0091.h5', 'hits_r0092.h5', 'hits_r0093.h5', 'hits_r0094.h5', 'hits_r0095.h5', 'hits_r0096.h5', 'hits_r0097.h5', 'hits_r0098.h5', 'hits_r0099.h5', 'hits_r0100.h5', 'hits_r0101.h5', 'hits_r0102.h5', 'hits_r0103.h5', 'hits_r0104.h5', 'hits_r0105.h5', 'hits_r0106.h5', 'hits_r0107.h5', 'hits_r0108.h5', 'hits_r0109.h5', 'hits_r0110.h5', 'hits_r0111.h5', 'hits_r0112.h5', 'hits_r0113.h5', 'hits_r0114.h5']
run_numbers = np.array([int(re.sub('hits_r', '', s).split('.')[0]) for s in runs])

def main():

    parser = argparse.ArgumentParser(description='calculate hit statistics')
    parser.add_argument('-r', '--run-number', metavar='run_number', type=int)
    parser.add_argument('-s', '--frame-step', metavar='frame_steps', help="steps between frames to be processed (default: 30)", type=int, default=30)
    parser.add_argument('-g', '--gain', metavar='adu_threshold', help="photon gain to be used for single-photon detection (default: 62.5)", type=float, default=62.5)
    parser.add_argument('-t', '--threshold', metavar='photon_threshold', help="threshold in fraction of a photon to be used for single-photon detection (default: 0.7)", type=float, default=0.7)
    parser.add_argument('-n', '--number-of-frames', metavar='number_of_frames', help="number of frames to be processed (optional)", type=int)
    parser.add_argument('-p', '--plot', help="plot only", default=False, action='store_true')
    parser.add_argument('-v', '--verbose', help="print additional information", default=False, action='store_true')

    args = parser.parse_args()

    global runs, run_numbers
    if args.run_number is not None:
        runs = ['hits_r%04d.h5' % args.run_number]
        run_numbers = np.array([args.run_number])

    step_frame = args.frame_step
    nframes = 30000
    if args.number_of_frames is not None:
        nframes = args.number_of_frames*step_frame

    """
/                        Group
/hitFinding              Group
/hitFinding/cellId       Dataset {30000}
/hitFinding/goodCells    Dataset {30}
/hitFinding/litPixelThreshold Dataset {SCALAR}
/hitFinding/litPixels    Dataset {30000}
/hitFinding/trainId      Dataset {30000}
/hits                    Group
/hits/assembled          Dataset {353, 1146, 1354}
/hits/indices            Dataset {353}
/hits/litPixels          Dataset {353}
/hits/numLitPixelThreshold Dataset {30}
/hits/unassembled        Dataset {353, 16, 512, 128}
    """
    run_hits = np.zeros(len(runs))
    run_hits_per_cell = np.zeros((len(runs), 30))
    run_hit_rates = np.zeros(len(runs))
    run_hit_rates_per_cell = np.zeros((len(runs), 30))
    run_max_photons_max = np.zeros(len(runs))
    run_photons_mean = np.zeros(len(runs))
    run_photons_mean_per_cell = np.zeros((len(runs), 30))
    run_photons_max = np.zeros(len(runs))
    run_photons_std = np.zeros(len(runs))
    
    cellId_bins = np.arange(1,63,2)
    cellId_bins_center = np.array([(cellId_bins[j] + cellId_bins[j+1])/2 for j in range(len(cellId_bins) - 1)])
    if not args.plot:
    	j = 0
    	for r in runs:
    	    print(r)
    	
    	    f = h5py.File(BASE_EXP_FOLDER + r, 'r')
    	    
    	    hit_indices = np.array(f['hits']['indices'])
    	    assembled_indices_corrected = np.where(hit_indices > 0)
    	    hit_indices_corrected = hit_indices[assembled_indices_corrected]
    	    run_hits[j] = len(hit_indices_corrected)
    	    run_hit_rates[j] = run_hits[j]/np.float(len(f['hitFinding/cellId']) - 30)
    	    assert len(cellId_bins_center) == len(f['hitFinding/goodCells']), 'CellId bins not equal to number of good cells: %d' % len(f['hitFinding/goodCells'])
    	    cellId = np.array(f['hitFinding/cellId'])
    	    hist, hist_bins = np.histogram(cellId[hit_indices_corrected], bins=cellId_bins)
    	    hist_norm, hist_bins = np.histogram(cellId[30:], bins=cellId_bins)
    	    run_hits_per_cell[j] = hist
    	    run_hit_rates_per_cell[j] = hist/hist_norm.astype(np.float)
    	    
    	    photons = np.zeros(len(hit_indices_corrected))
    	    max_photons = np.zeros(len(hit_indices_corrected))
    	    for k in range(len(hit_indices_corrected)):
    	        if (args.verbose and k % (len(hit_indices_corrected)/10) == 0):
    	            print("\t\r%3d%% (%d/%d)" % (int((k+1)*100/len(hit_indices_corrected)), k, len(hit_indices_corrected)))
    	        h = np.floor(f['hits']['assembled'][assembled_indices_corrected[0][k]][:]/args.gain + 1 - args.threshold)
    	        h[h < 0] = 0
    	        photons[k] = h[300:900,500:1000].sum()
    	        max_photons[k] = h[300:900,500:1000].max()
    	    
    	    run_max_photons_max[j] = max_photons.max()
    	    run_photons_mean[j] = photons.mean()
    	    run_photons_max[j] = photons.max()
    	    run_photons_std[j] = photons.std()
    	    for k in range(len(cellId_bins_center)):
    	        run_photons_mean_per_cell[j][k] = photons[cellId[hit_indices_corrected] == cellId_bins_center[k]].mean()
    	    print("hits: %d, hitrate: %.2f%%, photons: %d +/- %.0f, max photons/hit: %d, max photons/pixel: %d" % (run_hits[j], run_hit_rates[j]*100, run_photons_mean[j], run_photons_std[j], run_photons_max[j], run_max_photons_max[j]))
    	    j += 1
    	    
    	    f.close()
        
    	print('in total: %d hits' % run_hits.sum())
        
    	filename = 'shift2_hit_statistics.h5'
    	if not os.path.exists(SCRATCH_FOLDER):
    	    os.mkdir(SCRATCH_FOLDER)
    	    print('created: %s' % SCRATCH_FOLDER)
            
    	f = h5py.File(SCRATCH_FOLDER + filename, 'w')
    	f['runs'] = run_numbers
    	f['cells'] = cellId_bins_center
    	f['hits'] = run_hits
    	f['hits_per_cell'] = run_hits_per_cell
    	f['hitrates'] = run_hit_rates
    	f['hitrates_per_cell'] = run_hit_rates_per_cell
    	f['max_photons_per_pixel'] = run_max_photons_max
    	f['mean_photons_per_hit'] = run_photons_mean
    	f['mean_photons_per_hit_per_cell'] = run_photons_mean_per_cell
    	f['max_photons_per_hit'] = run_photons_max
    	f['stdev_photons_per_hit'] = run_photons_std
    	
    	f.close()
    	print('created file: %s' % filename)
    else:
        try:
            filename = 'shift2_hit_statistics.h5'
            print("reading statistics from: %s" % filename)
            f = h5py.File(SCRATCH_FOLDER + filename, 'r')
            run_hits = f['hits'][:]
            run_hits_per_cell = f['hits_per_cell'][:]
            run_hit_rates = f['hitrates'][:]
            run_hit_rates_per_cell = f['hitrates_per_cell'][:]
            run_max_photons_max = f['max_photons_per_pixel'][:]
            run_photons_mean = f['mean_photons_per_hit'][:]
            run_photons_mean_per_cell = f['mean_photons_per_hit_per_cell'][:]
            run_photons_max = f['max_photons_per_hit'][:]
            run_photons_std = f['stdev_photons_per_hit'][:]
        except:
            print("File is missing, aborting...")
            sys.exit(1)

    # plot statistics
    fig = plt.figure(num=None, figsize=(15, 6), dpi=100, facecolor='w', edgecolor='k')
    canvas = fig.add_subplot(131)
    canvas.set_title("hitrate statistics")
    for j in range(len(cellId_bins_center)):
        #plt.plot(run_numbers, run_hit_rates_per_cell.transpose()[j]*100, label='cell %d' % cellId_bins_center[j])
        plt.plot(run_numbers, run_hit_rates_per_cell.transpose()[j]*100)
    plt.plot(run_numbers, run_hit_rates*100, color='k', linewidth=3.0, label='all')
    plt.xlabel("run")
    plt.ylabel("hitrate (%)")
    plt.legend()

    canvas = fig.add_subplot(132)
    canvas.set_title("photon/hit statistics")
    for j in range(len(cellId_bins_center)):
        #plt.plot(run_numbers, run_photons_mean_per_cell.transpose()[j], label='cell %d' % cellId_bins_center[j])
        plt.plot(run_numbers, run_photons_mean_per_cell.transpose()[j])
    canvas.errorbar(run_numbers, run_photons_mean, yerr=run_photons_std, fmt='o', color='k', markersize=4.0, label='all')
    plt.plot(run_numbers, run_photons_max, 'ks', markersize=4.0, label='max')
    plt.xlabel("run")
    plt.ylabel("photon/hit")
    plt.legend()

    canvas = fig.add_subplot(133)
    canvas.set_title("photon/pixel statistics")
    plt.plot(run_numbers, run_max_photons_max, 'ko-', label='max')
    plt.xlabel("run")
    plt.ylabel("photon/pixel")
    plt.legend()

    if os.path.exists(SCRATCH_FIG_FOLDER):
        pngname = "shift2_hit_statistics.png"
        plt.savefig(SCRATCH_FIG_FOLDER + pngname)
        print('saved image: %s' % pngname)
    plt.show()

if __name__ == '__main__':
    main()
