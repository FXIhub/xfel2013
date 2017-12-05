import os, sys
import numpy as np
import ipc
import plotting.image
import plotting.line
import plotting.correlation
import analysis.agipd
import analysis.hitfinding
import analysis.pixel_detector
import analysis.event
import imp
import spimage
import h5py
from backend import add_record


this_dir = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, this_dir)
import conf_xfel2013
imp.reload(conf_xfel2013)
from conf_xfel2013 import *

# Do testing with another panel
do_testing = False

# Do radial averaging
do_radial = True

# Do radial fitting and sizing
do_sizing = do_radial

# Do slow data
do_slow_data = False

# =================== #
# AGIPD configuration #
# =================== #

#agipd_format = 'combined'
agipd_format = 'panel'

# The central 3 working panels have the IDs 3, 4, 15
if do_testing:
    #agipd_panel = 3
    agipd_panel = 4
else:
    agipd_panel = 15

# Do per-asic common mode correction
do_asic_cmc = False

# For the combined format precalibrated data can be selected from Karabo
do_precalibrate = False
#do_calibrate = not do_precalibrate
do_calibrate = True

# Apply geometry (only effective if agipd_format='combined')
do_assemble = False

# Get socket and key depending on operation mode
agipd_socket, agipd_key = get_agipd_source(agipd_format=agipd_format, 
                                           agipd_panel=agipd_panel, 
                                           do_assemble=do_assemble, 
                                           do_calibrate=do_calibrate, 
                                           do_precalibrate=do_precalibrate)

init_calib(dark_run_nr=None) # reads the latest dark
init_geom(rot180=True)

# Manually generated bad pixel map
mask_file = os.path.join(this_dir, "mask/mask_panel15.h5")
with h5py.File(mask_file, "r") as file_handle:
    mask = np.bool8(file_handle["data"][...])

# Mask out 3x3 neighborhood around specific bad pixels
bad_pos = [(493, 21), (491, 35), (493, 37), (498, 34), (499, 38), (492, 31)]
for y, x in bad_pos:
    mask[y-1:y-1+3, x-1:x-1+3] = False

# =============== #
# State variables #
# =============== #

state = {}
state['Facility'] = 'euxfel'
state['euxfel/agipd'] = {}
state['euxfel/agipd']['socket'] = agipd_socket
state['euxfel/agipd']['source'] = agipd_key
state['euxfel/agipd']['format'] = agipd_format

if do_slow_data and run_online:
    # exflonc05: 10.253.0.63
    # exflonc09: 10.253.0.67
    # exflonc10: 10.253.0.68
    # exflonc11: 10.253.0.69
    state['euxfel/agipd']['slow_data_socket'] = "tcp://10.253.0.69:4700"
    print("Slow data socket: %s" % state['euxfel/agipd']['slow_data_socket'])

aduThreshold = 40
hitscoreThreshold = 120

# ============ #
# onEvent call #
# ============ #

# counter = 0
# image_array = np.zeros((1000, 512, 128))

def onEvent(evt):

    # analysis.event.printProcessingRate()

    # global counter, image_array
    cellId = evt['eventID']['Timestamp'].cellId
    pulseId = evt['eventID']['Timestamp'].pulseId
    #if cellId > 3:
    #    return
    #else:
    #     print("pulseId=%i\tcellId=%i" %  (pulseId, cellId))

    # Available keys
    #print("Available keys: " + str(evt.keys()))

    # Shape of AGIPD array
    #print(evt['photonPixelDetectors'][agipd_key].data.shape)
    
    # Calibrate AGIPD data
    agipd_data = analysis.agipd.getAGIPD(evt, evt['photonPixelDetectors'][agipd_key],
                                         cellID=cellId, panelID=agipd_panel,
                                         calibrate=do_calibrate, assemble=False)

    if do_asic_cmc:
        CM = np.zeros_like(agipd_data.data)
        for ix in range(128//64):
            for iy in range(512//64):
                sel = agipd_data.data[iy*64:(iy+1)*64, ix*64:(ix+1)*64] < aduThreshold
                if sel.any():
                    CM[iy*64:(iy+1)*64, ix*64:(ix+1)*64] = np.median(agipd_data.data[iy*64:(iy+1)*64, ix*64:(ix+1)*64][sel])
        agipd_data.data -= CM

    # image_array[counter, :, :] = agipd_data.data
    # counter += 1
    # if counter >= 100:
    #     import pickle
    #     pickle.dump(image_array, open("mask_data.p", "wb"))
    #     import sys
    #     sys.exit(0)
    #print(agipd_data.data.shape)
    roi_15 = agipd_data.data[512-22:,:]
    roi_nosignal = agipd_data.data[:300,:]
    cm = np.median(roi_nosignal)

    roi_15_record = add_record(evt['analysis'], 'analysis', 'raw_gain_panel_15', roi_15-cm)
    #print(roi_15_record.data.shape)

    agipd_data = add_record(evt['analysis'], 'analysis', 'agipd (cm corected)', agipd_data.data - cm)
    agipd_data.data[~mask] = 0

    plotting.image.plotImage(agipd_data, name="All events no floor correction")#, group='Diagnostics')
    plotting.line.plotHistogram(agipd_data, hmin=-50, hmax=150, bins=100, vline=aduThreshold, name='Detector histogram')#, group='Diagnostics')
    
    # cm corrected agipd
    #agipd_mask = evt['analysis']['AGIPD_panel_15_mask']

    # Reject noisy pixels
    dark_pix = agipd_data.data < aduThreshold
    if dark_pix.any():
        agipd_data.data[dark_pix] = 0
    agipd_data = add_record(evt['analysis'], 'analysis', 'agipd (floor corrected)', agipd_data.data)

    # Plotting the AGIPD panel
    plotting.image.plotImage(agipd_data)#, group='Diagnostics')
    
    #plotting.image.plotImage(roi_15_record, name='ROI')
    #plotting.image.plotImage(evt['photonPixelDetectors'][agipd_key])

    analysis.hitfinding.countLitPixels(evt, roi_15_record, aduThreshold=aduThreshold, hitscoreThreshold=hitscoreThreshold)
    hit = evt['analysis']['litpixel: isHit']
    hitscore = evt['analysis']['litpixel: hitscore']
    plotting.line.plotHistory(hitscore, history=1000, label='Hitscore', hline=hitscoreThreshold)#, group='Hitfinding') 
    plotting.line.plotHistory(hit, history=1000, label='isHit')#, group='Hitfinding') 

    #analysis.pixel_detector.totalNrPhotons(evt, roi_15_record, aduPhoton=1, aduThreshold=50, outkey='roi_integrated')
    #roi_integrated_record = evt['analysis']['roi_integrated']
    
    #plotting.line.plotHistory(roi_integrated_record, history=1000, label='ROI integrated')
    #plotting.line.plotHistogram(roi_15_record, log10=True, hmin=-100, hmax=15000, bins=100, name='ROI histogram')

    analysis.hitfinding.hitrate(evt, hit.data, history=1000)
    if ipc.mpi.is_main_worker():
        plotting.line.plotHistory(evt['analysis']['hitrate'], history=10000)#, group='Hitfinding')

    # AGIPD noise level as a function of Cell ID
    cellId_rec = add_record(evt['analysis'], 'analysis', 'cellID', cellId)
    noiseLevel_rec = add_record(evt['analysis'], 'analysis', 'noiseLevel', agipd_data.data.std())    
    plotting.correlation.plotScatter(cellId_rec, noiseLevel_rec, name='Noise vs. Cell ID', history=10000, xlabel='Cell ID', ylabel='Noise')#, group='Diagnostic')

    if hit.data:

        d1 = 2*8*1.4*2
        d2 = 2*8*2.4*2
        d3 = 2*8*3.4*2
        center = (21,512+13)
        plotting.image.plotImage(agipd_data, name='Agipd panel 15 (only hits)', roi_center=center, roi_diameters=[d1,d2,d3])#, group='Hitfinding')

        # Radial average
        r, I = analysis.pixel_detector.radial(evt, agipd_data, mask=None, cx=21, cy=512+21-8)
        plotting.line.plotTrace(I, r)
        
        # Radial fit
        if do_radial:
            if agipd_panel == 15:
                cx = 21
                cy = 512+21-8
            else:# agipd_panel == 4:
                cx = -100
                cy = 512+200
            # Radial average
            r, I = analysis.pixel_detector.radial(evt, agipd_data, mask=None, cx=cx, cy=cy)
            r.data = r.data[:100]
            I.data = I.data[:100]

            plotting.line.plotTrace(I, r)
            
            if do_sizing:
                # Radial fit
                diameter, infodict = spimage.fit_sphere_diameter_radial(r.data, I.data, 
                                                                        diameter=400.E-9, intensity=1., wavelength=0.13E-9,
                                                                        pixel_size=190E-6, detector_distance=5.465,
                                                                        full_output=True, detector_adu_photon=1, detector_quantum_efficiency=1, 
                                                                        material='water', maxfev=1000, do_brute_evals=0, dlim=None)
                err = infodict['error'] 
                r_fit = infodict['img_r'] 
                I_fit = infodict['I_fit_m']
                I_fit_rec = add_record(evt['analysis'], 'analysis', 'Fit', I_fit)
                r_fit_rec = add_record(evt['analysis'], 'analysis', 'Fit', r_fit)
                plotting.line.plotTrace(I_fit_rec, r) 
    
    if 'slowData' in evt.keys():
        if 'injposX' in evt['slowData']:

            # Hitscore vs. injector position X
            plotting.correlation.plotScatter(evt['slowData']['injposX'], hitscore, name='Hitscore vs. inj X')#, group='Hitfinding')

            # isHit vs. injector position X
            plotting.correlation.plotScatter(hit, evt['slowData']['injposX'], name='inj X isHit')#, group='Hitfinding')

        if 'cam_ehc_scr' in evt['slowData']:
            cam_ehc = evt['slowData']['cam_ehc_scr']
            if cam_ehc is not None:
            
                # Filter out bad frames, this criteria is somewhat dangerous as we might melt the cam without even noticing
                if cam_ehc.data.max() != 65535:
                    plotting.image.plotImage(cam_ehc)#, group='Diagnostics')
                #else:
                #    if np.random.rand() < 0.01:
                #        print('EHC camera frame is crap!!')

        if 'cam_inline' in evt['slowData']:
            cam_inline = evt['slowData']['cam_inline']
            if cam_inline is not None:
                cam_inline.data = cam_inline.data.reshape((cam_inline.data.shape[1], cam_inline.data.shape[0]))

                # Filter out bad frames, this criteria is somewhat dangerous as we might melt the cam without even noticing
                if cam_inline.data.max() != 65535:
                    plotting.image.plotImage(cam_inline)#, group='Diagnostics')
