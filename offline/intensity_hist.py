#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import argparse
import h5py
import numpy as np
from matplotlib import pyplot as plt

#sys.path.insert(0, '/gpfs/exfel/u/usr/SPB/201701/p002013/sbobkov/xfel2013/offline')
import combine_modules

BASE_EXP_FOLDER = '/gpfs/exfel/d/raw/SPB/201701/p002013/'
SCRATCH_FIG_FOLDER = '/gpfs/exfel/u/scratch/SPB/201701/p002013/sellberg/figures/'
SCRATCH_FOLDER = '/gpfs/exfel/u/scratch/SPB/201701/p002013/sellberg/intensity_histograms/'

pixels = [(629, 718), (628, 704), (646, 707), (652, 729), (635, 740), (652, 699), (679, 700), (683, 719), (681, 752), (659, 750)]

def main():

    parser = argparse.ArgumentParser(description='calculate intensity histogram')
    parser.add_argument('-r', '--run-number', metavar='run_number', type=int)
    parser.add_argument('-s', '--frame-step', metavar='frame_steps', help="steps between frames to be processed (default: 30)", type=int, default=30)
    parser.add_argument('-n', '--number-of-frames', metavar='number_of_frames', help="number of frames to be processed (optional)", type=int)
    parser.add_argument('--do-pixel', help="process individual pixels", default=False, action='store_true')
    parser.add_argument('--bg_file', metavar='background file', required=False)

    args = parser.parse_args()

    run_num = args.run_number

    if args.bg_file:
        substract_bg = True
        bgdata = h5py.File(args.bg_file, 'r')
        mean_noise = bgdata['background'][:]
        bad_pixels = bgdata['bad_pixels'][:]
    else:
        substract_bg = False

    combiner = combine_modules.AGIPD_Combiner(run_num)

    step_frame = args.frame_step
    nframes = combiner.nframes
    if args.number_of_frames is not None:
        nframes = args.number_of_frames*step_frame

    #images_data = np.zeros((nframes//step_frame, 1354, 1146))

    hist_bins = np.arange(-200, 5000 + 2) - 0.5
    hist_bins_center = [(hist_bins[j] + hist_bins[j+1])/2 for j in range(len(hist_bins) - 1)]
    if args.do_pixel:
        hist_tot = np.zeros((len(pixels), len(hist_bins) - 1))
    else:
        hist_tot = np.zeros(len(hist_bins) - 1)
    for i in range(0, nframes, step_frame):
        #sys.stderr.write("\r%3d%% (%d/%d)" % (int((i+1)*100/nframes), i, nframes))
        if (i % (nframes/100) == 0):
            print("\r%3d%% (%d/%d)" % (int((i+1)*100/nframes), i, nframes))
        try:
            image = combiner.get_frame(i, calibrate=True)
        except ValueError:
            continue
        if substract_bg:
            image -= mean_noise
            image[bad_pixels] == 0
        #image[image<0] = 0
        if args.do_pixel:
            j = 0
            for p in pixels:
                k = int(np.floor(image[p] + 0.5) + 200)
                if k < 0:
                    k = 0
                elif k > len(hist_bins) - 2:
                    k = len(hist_bins) - 2
                try:
                    hist_tot[j][k] += 1
                except IndexError:
                    print("pixel (%d, %d) has invalid value: %.0f ADU" % (p[1], p[0], image[p]))
                j += 1
        else:
            hist, hist_bins = np.histogram(image[621:766,692:817], bins=hist_bins)
            hist_tot += hist
        #images_data[i//30] = image

    filename = 'r%04d_intensity_histogram.h5' % run_num
    if not os.path.exists(SCRATCH_FOLDER):
        os.mkdir(SCRATCH_FOLDER)
        print('created: %s' % SCRATCH_FOLDER)
    f = h5py.File(SCRATCH_FOLDER + filename, 'a')
    if args.do_pixel:
        for j in range(len(pixels)):
            f['hist%d' % j] = hist_tot[j]
    else:
        f['hist'] = hist_tot
    f['bins'] = hist_bins_center
    f.close()
    print('created file: %s' % filename)
    
    # plot histogram
    fig = plt.figure()
    canvas = fig.add_subplot(111)
    canvas.set_title("r%04d histogram" % run_num)
    if args.do_pixel:
        for j in range(len(pixels)):
            plt.semilogy(hist_bins_center, hist_tot[j])
    else:
        plt.semilogy(hist_bins_center, hist_tot)
    #plt.bar(hist_bins_center, hist, align='center')
    plt.xlabel("intensity (ADU)")
    plt.ylabel("occurrences")
    #plt.xlim([0, 200])
    if os.path.exists(SCRATCH_FIG_FOLDER):
        if args.do_pixel:
            pngname = "r%04d_intensity_pixel_hist.png" % run_num
        else:
            pngname = "r%04d_intensity_hist.png" % run_num
        plt.savefig(SCRATCH_FIG_FOLDER + pngname)
        print('saved image: %s' % pngname)
    plt.show()

if __name__ == '__main__':
    main()
