import os
import plotting.image
import analysis.agipd

from conf_xfel2013 import *

do_offline = True

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
#do_assemble = False

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


# ============ #
# onEvent call #
# ============ #

def onEvent(evt):

    native_cellId = evt['eventID']['Timestamp'].cellId
    
    cellId = native_cellId // 2 - 1
    pulseId = evt['eventID']['Timestamp'].pulseId
    if cellId not in cellId_allowed_range:
        print("WARNING: Skip event pulseId=%i. cellId=%i out of allowed range." %  (pulseId, cellId))
        return
    else:
        print("pulseId=%i\tcellId=%i" %  (pulseId, cellId))
    
    # Available keys
    #print("Available keys: " + str(evt.keys()))

    # Shape of AGIPD array
    #print(evt['photonPixelDetectors'][agipd_key].data.shape)
    
    # Calibrate AGIPD data
    agipd_data = analysis.agipd.getAGIPD(evt, evt['photonPixelDetectors'][agipd_key],
                                         cellID=cellId, panelID=agipd_panel,
                                         calibrate=do_calibrate, assemble=do_assemble)
    print(agipd_data.data.mean())
    
    # Plotting the AGIPD panel
    plotting.image.plotImage(agipd_data)
    #plotting.image.plotImage(evt['photonPixelDetectors'][agipd_key])

    # TODO: Add more ......
    # ....
