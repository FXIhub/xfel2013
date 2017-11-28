import plotting.image
import analysis.agipd

state = {}
state['Facility'] = 'euxfel'

# Reading from raw AGIPD data source
state['euxfel/agipd'] = {}
state['euxfel/agipd']['socket'] = 'tcp://10.253.0.51:4500'
state['euxfel/agipd']['source'] = 'SPB_DET_AGIPD1M-1/DET'

# Reading from calibrated AGIPD data source
#state['euxfel/agipd'] = {}
#state['euxfel/agipd']['socket'] = 'tcp://10.253.0.51:4501'
#state['euxfel/agipd']['source'] = 'SPB_DET_AGIPD1M-1/DET'

# Reading from individual raw AGIPD data source (panel 03)
#state['euxfel/agipd'] = {}
#state['euxfel/agipd']['socket'] = 'tcp://10.253.0.52:4600'
#state['euxfel/agipd']['source'] = 'SPB_DET_AGIPD1M-1/DET/3CH0:xtdf'

# Reading from individual raw AGIPD data source (panel 04)
#state['euxfel/agipd'] = {}
#state['euxfel/agipd']['socket'] = 'tcp://10.253.0.52:4601'
#state['euxfel/agipd']['source'] = 'SPB_DET_AGIPD1M-1/DET/4CH0:xtdf'

# Reading from individual raw AGIPD data source (panel 15)
#state['euxfel/agipd'] = {}
#state['euxfel/agipd']['socket'] = 'tcp://10.253.0.52:4602'
#state['euxfel/agipd']['source'] = 'SPB_DET_AGIPD1M-1/DET/15CH0:xtdf'


def onEvent(evt):

    # Available keys
    #print("Available keys: " + str(evt.keys()))

    # Shape of AGIPD array
    print(evt['photonPixelDetectors']['AGIPD1'].data.shape)

    # Get individual panels from the AGIPD
    agipd_0 = analysis.agipd.get_panel(evt, evt['photonPixelDetectors']['AGIPD1'], 0)

    # Shape of the AGIPD panel
    #print(agipd_0.data.shape)

    # Plotting the AGIPD panel
    plotting.image.plotImage(evt['photonPixelDetectors']['AGIPD1'])

    # TODO: Add more ......
    # ....
