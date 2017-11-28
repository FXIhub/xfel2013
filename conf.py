import plotting.image
import analysis.agipd


# Reading from raw AGIPD data source
#agipd_socket = 'tcp://10.253.0.51:4500'
#agipd_socket = 'tcp://127.0.0.1:4500'
#agipd_key = 'SPB_DET_AGIPD1M-1/DET'
#agipd_format = 'combined'

# Reading from calibrated AGIPD data source
#agipd_socket = 'tcp://10.253.0.51:4501'
#agipd_key = 'SPB_DET_AGIPD1M-1/DET'
#agipd_format = 'combined'

# Reading from individual raw AGIPD data source (panel 03)
#agipd_socket = 'tcp://10.253.0.52:4600'
agipd_socket = 'tcp://127.0.0.1:4600'
agipd_key = 'SPB_DET_AGIPD1M-1/DET/3CH0:xtdf'
agipd_format = 'panel'

# Reading from individual raw AGIPD data source (panel 04)
#agipd_socket = 'tcp://10.253.0.52:4601'
#agipd_key = 'SPB_DET_AGIPD1M-1/DET/4CH0:xtdf'
#agipd_format = 'panel'

# Reading from individual raw AGIPD data source (panel 15)
#agipd_socket = 'tcp://10.253.0.52:4602'
#agipd_key = 'SPB_DET_AGIPD1M-1/DET/15CH0:xtdf'
#agipd_format = 'panel'

state = {}
state['Facility'] = 'euxfel'
state['euxfel/agipd'] = {}
state['euxfel/agipd']['socket'] = agipd_socket
state['euxfel/agipd']['source'] = agipd_key
state['euxfel/agipd']['format'] = agipd_format

def onEvent(evt):

    # Available keys
    #print("Available keys: " + str(evt.keys()))

    # Shape of AGIPD array
    print(evt['photonPixelDetectors'][agipd_key].data.shape)

    # Get individual panels from the AGIPD
    if agipd_format == 'panel':
        agipd_panel = evt['photonPixelDetectors'][agipd_key]
    if agipd_format == 'combined':
        agipd_panel = analysis.agipd.get_panel(evt, evt['photonPixelDetectors'][agipd_key], 3)        

    # Plotting the AGIPD panel
    plotting.image.plotImage(agipd_panel)

    # TODO: Add more ......
    # ....
