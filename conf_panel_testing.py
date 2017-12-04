import os, sys
import numpy as np
import ipc
import plotting.image
import plotting.line
import plotting.correlation
import analysis.agipd
import analysis.hitfinding
import analysis.pixel_detector
import imp
import spimage
from backend import add_record

this_dir = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, this_dir)
import conf_xfel2013
imp.reload(conf_xfel2013)
from conf_xfel2013 import *

# Do testing with another panel
do_testing = True

# Floor cut
do_floor_cut = False

# Do radial averaging
do_radial = True

# Do radial fitting and sizing
do_sizing = do_radial

# Patterson analysis
do_patterson = True

# Do slow data
do_slow_data = not do_testing

# =================== #
# AGIPD configuration #
# =================== #

#agipd_format = 'combined'
agipd_format = 'panel'

# The central 3 working panels have the IDs 3, 4, 15
if do_testing:
    agipd_panel = 3
    #agipd_panel = 4
    #agipd_panel = 15
else:
    agipd_panel = 15

# For the combined format precalibrated data can be selected from Karabo
do_precalibrate = False
do_calibrate = not do_precalibrate

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
hitscoreThreshold = 140

# ============ #
# onEvent call #
# ============ #

def onEvent(evt):

    cellId = evt['eventID']['Timestamp'].cellId
    pulseId = evt['eventID']['Timestamp'].pulseId
    #~if cellId > 3:
     #   return
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
    plotting.image.plotImage(agipd_data, name="agipd (not cm corrected)")#, group='Diagnostics')
    #print(agipd_data.data.shape)
    roi_15 = agipd_data.data[512-22:,:]
    roi_nosignal = agipd_data.data[:300,:]
    
    CM = np.zeros_like(agipd_data.data)
    for ix in range(128//64):
        for iy in range(512//64):
            sel = agipd_data.data[iy*64:(iy+1)*64, ix*64:(ix+1)*64] < aduThreshold
            if sel.any():
                CM[iy*64:(iy+1)*64, ix*64:(ix+1)*64] = np.median(agipd_data.data[iy*64:(iy+1)*64, ix*64:(ix+1)*64][sel])
    #cm = np.median(roi_nosignal)

    agipd_data.data -= CM

    roi_15_record = add_record(evt['analysis'], 'analysis', 'raw_gain_panel_%i' % agipd_panel, roi_15)
    #print(roi_15_record.data.shape)

    agipd_data = add_record(evt['analysis'], 'analysis', 'agipd (cm corected)', agipd_data.data)

    plotting.line.plotHistogram(agipd_data, hmin=-50, hmax=150, bins=100, vline=aduThreshold, name='Detector histogram')#, group='Diagnostics')
    
    # cm corrected agipd
    #agipd_mask = evt['analysis']['AGIPD_panel_15_mask']

    # Reject noisy pixels
    if do_floor_cut:
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
        plotting.image.plotImage(agipd_data, name='Agipd panel %i (only hits)' % agipd_panel)#, group='Hitfinding')

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

        if do_patterson:
            #def patterson(image, mask, floor_cut=None, mask_smooth=1., darkfield_x=None, darkfield_y=None, darkfield_sigma=None, darkfield_N=1, normalize_median=False, radial_boost=False, log_boost=False, gauss_damp=False, gauss_damp_sigma=None, gauss_damp_threshold=None, subtract_fourier_kernel=False, log_min=1., mask_expand=0., full_output=False):
            P, info = spimage.patterson(
                agipd_data.data, np.ones(shape=agipd_data.data.shape, dtype='bool'), full_output=True,
                darkfield_x=420., darkfield_y=-35., darkfield_sigma=10.,
            )
            #P_rec = add_record(evt['analysis'], 'analysis', 'Patterson function', info['intensities_times_kernel'])
            P_rec = add_record(evt['analysis'], 'analysis', 'Patterson function', P)
            plotting.image.plotImage(P_rec, name='Patterson function')#, group='Hitfinding')
    
    if 'slowData' in evt.keys():
        if 'injposX' in evt['slowData']:

            # Hitscore vs. injector position X
            plotting.correlation.plotScatter(evt['slowData']['injposX'], hitscore, name='Hitscore vs. inj X')#, group='Hitfinding')

            # isHit vs. injector position X
            plotting.correlation.plotScatter(hit, evt['slowData']['injposX'], name='inj X isHit')#, group='Hitfinding')

        if 'cam_ehc_scr' in evt['slowData']:
            cam_ehc = evt['slowData']['cam_ehc_scr']
            
            # Filter out bad frames, this criteria is somewhat dangerous as we might melt the cam without even noticing
            if cam_ehc.data.max() != 65535:
                plotting.image.plotImage(cam_ehc)#, group='Diagnostics')

        if 'cam_inline' in evt['slowData']:
            cam_inline = evt['slowData']['cam_inline']
            cam_inline.data = cam_inline.data.reshape((cam_inline.data.shape[1], cam_inline.data.shape[0]))

            # Filter out bad frames, this criteria is somewhat dangerous as we might melt the cam without even noticing
            if cam_inline.data.max() != 65535:
                plotting.image.plotImage(cam_inline)#, group='Diagnostics')
