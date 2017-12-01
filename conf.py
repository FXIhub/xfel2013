import os
import numpy as np
import plotting.image
import plotting.line
import analysis.agipd
import analysis.hitfinding
from backend import add_record

from conf_xfel2013 import *

do_offline = True
#do_offline = False

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


agipd_socket, agipd_key = get_agipd_source(agipd_format=agipd_format, agipd_panel=agipd_panel, do_offline=do_offline, do_precalibrate=do_precalibrate)

# =============== #
# State variables #
# =============== #

state = {}
state['Facility'] = 'euxfel'
state['euxfel/agipd'] = {}
state['euxfel/agipd']['socket'] = agipd_socket
state['euxfel/agipd']['source'] = agipd_key
state['euxfel/agipd']['format'] = agipd_format
state['euxfel/agipd']['slow_data_socket'] = "tcp://10.253.0.64:4700"

aduThreshold = 400
hitscoreThreshold = 1000

# ============ #
# onEvent call #
# ============ #

def onEvent(evt):

    native_cellId = evt['eventID']['Timestamp'].cellId
    
    cellId = native_cellId // 2 - 1
    pulseId = evt['eventID']['Timestamp'].pulseId
    if cellId != 0:
        return
    if cellId not in cellId_allowed_range:
        print("WARNING: Skip event pulseId=%i. cellId=%i out of allowed range." %  (pulseId, cellId))
        return
    else:
        print("pulseId=%i\tcellId=%i" %  (pulseId, cellId))
    
    # Available keys
    #print("Available keys: " + str(evt.keys()))
    #print("Available slow data keys: " + str(evt['slowData'].keys()))
    print("Available slow data keys: " + str(evt['slowData'].keys()))
    #print("Available slow data keys: ",(evt['slowData']['injposX']))
    #import pickle, sys
    #pickle.dump(evt['slowData']['full_dict'].data, open('./slowdata.p', 'wb'))
    #sys.exit(1)
    
    # Shape of AGIPD array
    #print(evt['photonPixelDetectors'][agipd_key].data.shape)

    # Raw gain values
    raw_15_gain = evt['photonPixelDetectors'][agipd_key].data[1,15]
    raw_15_gain = add_record(evt['analysis'], 'analysis', 'raw_gain_panel_15', raw_15_gain)

    # Calibrate AGIPD data (assembled)
    agipd_data = analysis.agipd.getAGIPD(evt, evt['photonPixelDetectors'][agipd_key],
                                         cellID=cellId, panelID=agipd_panel,
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
    # Plotting the raw gain for panel 15
    plotting.image.plotImage(agipd_15_data)#, vmin=0, vmax=3000)
    plotting.image.plotImage(raw_15_gain)#, vmin=0, vmax=3000)

    # Filtering on AGIPD panel 03, reject events which have negative maximima
    if (agipd_03_data.data.max() <= 0):
        return
    # Plotting the AGIPD panel 03
    plotting.image.plotImage(agipd_03_data)#, vmin=0, vmax=3000)

    # Filtering on AGIPD panel 04, reject events which have negative maximima
    if (agipd_04_data.data.max() <= 0):
        return
    # Plotting the AGIPD panel 04
    plotting.image.plotImage(agipd_04_data)#, vmin=0, vmax=3000)

    # Plotting the full AGIPD (assembled)
    plotting.image.plotImage(agipd_data)#, vmin=0, vmax=3000)
    # Plotting the full AGIPD (assembled) Log scale
    plotting.image.plotImage(agipd_data, log=True, name="AGIPD_assembled (Log)")#, vmin=0, vmax=3000)

    # Do hitfinding on the AGIPD panel 04
    analysis.hitfinding.countLitPixels(evt, agipd_04_data, aduThreshold=aduThreshold, hitscoreThreshold=hitscoreThreshold)
    hitscore = evt['analysis']['litpixel: hitscore']
    hit = evt['analysis']['litpixel: isHit'].data

    # Plotting the hitscore
    plotting.line.plotHistory(hitscore, history=1000, label='Hitscore', hline=hitscoreThreshold) 
    
    # Filter on hits
    if hit:
        print("We have a hit")

        # Plotting the full AGIPD (assembled) for hits only
        #plotting.image.plotImage(agipd_data, name='AGIPD assembled (hits)')#, vmin=0, vmax=3000)

