import os
import plotting.image
import analysis.agipd

do_offline = True

# =================== #
# AGIPD configuration #
# =================== #

cellId_allowed_range = range(0, 30)

#agipd_format = 'combined'
agipd_format = 'panel'

# For the combined format precalibrated data can be selected from Karabo
do_precalibrate = False
do_calibrate = not do_precalibrate

# Apply geometry (only effective if agipd_format='combined')
#do_assemble = True
do_assemble = False

# The central 3 working panels have the IDs 3, 4, 15
agipd_panel = 3
#agipd_panel = 4
#agipd_panel = 15

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
        agipd_socket = '%s:460%i' % (tcp_prefix, agipd_panel)
    agipd_key = 'SPB_DET_AGIPD1M-1/DET/3CH0:xtdf'
elif agipd_format == 'combined':
    # Reading from raw AGIPD data source
    if do_precalibrate:
        agipd_socket = '%s:4501' % tcp_prefix
    else:
        agipd_socket = '%s:4500' % tcp_prefix
    agipd_key = 'SPB_DET_AGIPD1M-1/DET'

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

# ===================== #
# Read calibration data #
# ===================== #

this_dir = os.path.dirname(os.path.realpath(__file__))

# Read calibration data (one file per panel)
calib_dir = "%s/calib" % this_dir
fn_agipd_calib_list = ['%s/Cheetah-AGIPD%02i-calib.h5' % (calib_dir, panelID) for panelID in range(0, 16)]
analysis.agipd.init_calib(filenames=fn_agipd_calib_list)

# Read geometry data
geom_dir = "%s/geometry" % this_dir
fn_agipd_geom = '%s/agipd_taw9_oy2_1050addu_hmg5.geom' % (geom_dir)
analysis.agipd.init_geom(filename=fn_agipd_geom)

# ============ #
# onEvent call #
# ============ #

def onEvent(evt):

    cellId = evt['eventID']['Timestamp'].cellId
    pulseId = evt['eventID']['Timestamp'].pulseId
    if cellId not in cellId_allowed_range:
        print("WARNING: Skip event pulseId=%i. cellId=%i out of allowed range." %  (pulseId, cellId))
        return
    
    # Available keys
    #print("Available keys: " + str(evt.keys()))

    # Shape of AGIPD array
    #print(evt['photonPixelDetectors'][agipd_key].data.shape)
    
    # Calibrate AGIPD data
    agipd_data = analysis.agipd.getAGIPD(evt, evt['photonPixelDetectors'][agipd_key],
                                         cellID=cellId, panelID=agipd_panel,
                                         calibrate=do_calibrate, assemble=do_assemble)
    
    # Plotting the AGIPD panel
    plotting.image.plotImage(agipd_data)

    # TODO: Add more ......
    # ....
