import os, sys
import numpy as np
import plotting.image
import plotting.line
import plotting.correlation
import analysis.agipd
import analysis.hitfinding
import imp
from backend import add_record

this_dir = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, this_dir)
import conf_xfel2013
imp.reload(conf_xfel2013)
from conf_xfel2013 import *

# =================== #
# AGIPD configuration #
# =================== #

cellId_allowed_range = range(0, 30)

agipd_format = 'combined'
#agipd_format = 'panel'

# The central 3 working panels have the IDs 3, 4, 15
agipd_panel = 3
#agipd_panel = 4
#agipd_panel = 15

# For the combined format precalibrated data can be selected from Karabo
do_precalibrate = False
#do_calibrate = not do_precalibrate
do_calibrate = True

# Apply geometry (only effective if agipd_format='combined')
do_assemble = True

# Get socket and key depending on operation mode
agipd_socket, agipd_key = get_agipd_source(agipd_format=agipd_format, 
                                           agipd_panel=agipd_panel, 
                                           do_assemble=do_assemble, 
                                           do_calibrate=do_calibrate, 
                                           do_precalibrate=do_precalibrate)

init_calib()
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

if run_online:
    # exflonc05: 10.253.0.63
    # exflonc09: 10.253.0.67
    # exflonc10: 10.253.0.68
    # exflonc11: 10.253.0.69
    state['euxfel/agipd']['slow_data_socket'] = "tcp://10.253.0.67:4700"
    print("Slow data socket: %s" % state['euxfel/agipd']['slow_data_socket'])

aduThreshold = 300
hitscoreThreshold = 20

# ============ #
# onEvent call #
# ============ #

def onEvent(evt):

    # Available keys
    #print("Available keys: " + str(evt.keys()))
    #print("Available slow data keys: " + str(evt['slowData'].keys()))
    #print("Available slow data keys: " + str(evt['slowData'].keys()))
    #print("Available slow data keys: ",(evt['slowData']['injposX']))

    native_cellId = evt['eventID']['Timestamp'].cellId
    cellId = native_cellId // 2 - 1
    pulseId = evt['eventID']['Timestamp'].pulseId
    #if cellId != 0:
    #    return
    if cellId not in cellId_allowed_range:
        print("WARNING: Skip event pulseId=%i. cellId=%i out of allowed range." %  (pulseId, cellId))
        return
    else:
        print("pulseId=%i\tcellId=%i" %  (pulseId, cellId))
    
    # Shape of AGIPD array
    #print(evt['photonPixelDetectors'][agipd_key].data.shape)

    # Raw gain values
    raw_15_gain = evt['photonPixelDetectors'][agipd_key].data[1,15]
    raw_15_gain = add_record(evt['analysis'], 'analysis', 'raw_gain_panel_15', raw_15_gain)

    # Calibrate AGIPD data (assembled)
    agipd_data = analysis.agipd.getAGIPD(evt, evt['photonPixelDetectors'][agipd_key],
                                         cellID=cellId, panelID=None,
                                         calibrate=do_calibrate, assemble=do_assemble)
    
    # Calibrate AGIPD data (panel 03)
    agipd_03_data = analysis.agipd.getAGIPD(evt, evt['photonPixelDetectors'][agipd_key],
                                            cellID=cellId, panelID=3,
                                            calibrate=do_calibrate, assemble=False)
  
    # Calibrate AGIPD data (panel 04)
    agipd_04_data = analysis.agipd.getAGIPD(evt, evt['photonPixelDetectors'][agipd_key],
                                            cellID=cellId, panelID=4,
                                            calibrate=do_calibrate, assemble=False)
  
    # Calibrate AGIPD data (panel 15)
    agipd_15_data = analysis.agipd.getAGIPD(evt, evt['photonPixelDetectors'][agipd_key],
                                            cellID=cellId, panelID=15,
                                            calibrate=do_calibrate, assemble=False)

    # Filtering on AGIPD panel 15, reject events which have negative maximima
    if (agipd_15_data.data.max() <= 0):
        return

    # ROI of panel 15
    roi_15 = agipd_15_data.data[512-22:,:]
    roi_15_record = add_record(evt['analysis'], 'analysis', 'raw_gain_panel_15', roi_15)
    
    # Plotting the raw gain for panel 15
    #plotting.image.plotImage(agipd_15_data)#, vmin=0, vmax=3000)
    #plotting.image.plotImage(raw_15_gain)#, vmin=0, vmax=3000)

    # Filtering on AGIPD panel 03, reject events which have negative maximima
    #if (agipd_03_data.data.max() <= 0):
    #    return
    # Plotting the AGIPD panel 03
    #plotting.image.plotImage(agipd_03_data)#, vmin=0, vmax=3000)

    # Filtering on AGIPD panel 04, reject events which have negative maximima
    #if (agipd_04_data.data.max() <= 0):
    #    return
    # Plotting the AGIPD panel 04
    #plotting.image.plotImage(agipd_04_data)#, vmin=0, vmax=3000)

    # Plotting the full AGIPD (assembled)
    #tmp = (agipd_data.data < 0)
    #if tmp.any():
    #    agipd_data.data[tmp] = -1000
    #plotting.image.plotImage(agipd_data)#, vmin=0, vmax=3000)
    # Plotting the full AGIPD (assembled) Log scale
    #plotting.image.plotImage(agipd_data, log=True, name="AGIPD_assembled (Log)")#, vmin=0, vmax=3000)

    # Do hitfinding on the AGIPD panel 15
    analysis.hitfinding.countLitPixels(evt, roi_15_record, aduThreshold=aduThreshold, hitscoreThreshold=hitscoreThreshold)
    hitscore = evt['analysis']['litpixel: hitscore']
    hit = evt['analysis']['litpixel: isHit'].data

    # Plotting the hitscore
    plotting.line.plotHistory(hitscore, history=1000, label='Hitscore', hline=hitscoreThreshold) 
    
    # Filter on hits
    if hit:
        print("We have a hit")
        # Plotting the full AGIPD (assembled) for hits only
        plotting.image.plotImage(agipd_data, name='AGIPD assembled (hits)')#, vmin=0, vmax=3000)


    #if 'slowData' in evt.keys():
    #    SD = evt['slowData']
    #    for k in ['injposX', 'injposY', 'injposZ', 'xgm_xtd2', 'xgm_xtd9']:
    #        if k in SD:
    #            rec = evt['slowData'][k]
    #            plotting.line.plotHistory(rec, history=1000, label=k)
    #        else:
    #            print("no")
        
        #cam_inline = evt['slowData']['cam_inline']
        # Filter out bad frames, this criteria is somewhat dangerous as we might melt the cam without even noticing
        #if cam_inline.data.max() != 65535:
        #    plotting.image.plotImage(cam_inline)

        #cam_ehc = evt['slowData']['cam_ehc_scr']
        # Filter out bad frames, this criteria is somewhat dangerous as we might melt the cam without even noticing
        #if cam_inline.data.max() != 65535:
        #    plotting.image.plotImage(cam_ehc)

        plotting.correlation.plotScatter(evt['slowData']['injposY'], hitscore, name='Hitscore vs. inj Y')
