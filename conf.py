import os
import numpy as np
import plotting.image
import plotting.line
import analysis.agipd
import analysis.hitfinding

do_offline = False

# =================== #
# AGIPD configuration #
# =================== #

cellId_allowed_range = range(0, 30)

agipd_format = 'combined'
#agipd_format = 'panel'

# For the combined format precalibrated data can be selected from Karabo
do_precalibrate = False
#do_calibrate = not do_precalibrate
do_calibrate = True

# Apply geometry (only effective if agipd_format='combined')
do_assemble = True

# The central 3 working panels have the IDs 3, 4, 15
#agipd_panel = 3
#agipd_panel = 4
agipd_panel = 15
agipd_panel_to_port = {3: 0, 4: 1, 15: 2}

# Determine the data source
if do_offline:
    tcp_prefix = 'tcp://127.0.0.1'
else:
    if agipd_format == 'panel':
        tcp_prefix = 'tcp://10.253.0.52'
    elif agipd_format == 'combined':
        tcp_prefix = 'tcp://10.253.0.51'
if agipd_format == 'panel':
    # Reading from individual raw AGIPD data source
    if do_offline:
        agipd_socket = '%s:4600' % (tcp_prefix)
    else:
        agipd_socket = '%s:460%i' % (tcp_prefix, agipd_panel_to_port[agipd_panel])
    agipd_key = 'SPB_DET_AGIPD1M-1/DET/%iCH0:xtdf' % agipd_panel
elif agipd_format == 'combined':
    # Reading from raw AGIPD data source
    if do_precalibrate:
        agipd_socket = '%s:4501' % tcp_prefix
    else:
        agipd_socket = '%s:4500' % tcp_prefix
    agipd_key = 'SPB_DET_AGIPD1M-1/DET'
    agipd_panel = None

# Output calibration to console
print("AGIPD socket:\t%s" % agipd_socket)
print("AGIPD key:\t%s" % agipd_key)
print("AGIPD format: %s" % agipd_format)
print("AGIPD do assemble: %i" % do_assemble)
print("AGIPD do calibrate: %i" % do_calibrate)

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

# ===================== #
# Read calibration data #
# ===================== #

this_dir = os.path.dirname(os.path.realpath(__file__))

# Read calibration data (one file per panel)
calib_dir = "%s/calib" % this_dir
if not os.path.exists(calib_dir):
    calib_dir = "/gpfs/exfel/exp/SPB/201701/p002013/usr/Shared/calib/r0030"
fn_agipd_calib_list = ['%s/Cheetah-AGIPD%02i-calib.h5' % (calib_dir, panelID) for panelID in range(0, 16)]
analysis.agipd.init_calib(filenames=fn_agipd_calib_list)

# Read geometry data
geom_dir = "%s/geometry" % this_dir
fn_agipd_geom = '%s/agipd_taw9_oy2_1050addu_hmg5.geom' % (geom_dir)
analysis.agipd.init_geom(filename=fn_agipd_geom, rot180=True)


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
    
    # Calibrate AGIPD data (assembled)
    agipd_data = analysis.agipd.getAGIPD(evt, evt['photonPixelDetectors'][agipd_key],
                                         cellID=cellId, panelID=agipd_panel,
                                         calibrate=do_calibrate, assemble=do_assemble)
    
    # Calibrate AGIPD data (panel 04)
    agipd_04_data = analysis.agipd.getAGIPD(evt, evt['photonPixelDetectors'][agipd_key],
                                            cellID=cellId, panelID=4,
                                            calibrate=do_calibrate, assemble=False)
    
    # Filtering on AGIPD panel 04, reject events which have negative maximima
    if (agipd_04_data.data.max() < 0):
        return

    # Plotting the AGIPD panel
    plotting.image.plotImage(agipd_04_data)#, vmin=0, vmax=3000)

    # Plotting the full AGIPD (assembled)
    plotting.image.plotImage(agipd_data)#, vmin=0, vmax=3000)

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
        plotting.image.plotImage(agipd_data, label='AGIPD assembled (hits)')#, vmin=0, vmax=3000)

