import plotting.image
import analysis.agipd

state = {}
state['Facility'] = 'euxfel'

# Reading from simulated data
#state['socket'] = 'tcp://10.253.0.65:4700'

# Reading from raw AGIPD data source
state['socket'] = 'tcp://10.253.0.51:4500'

# Reading from corrected AGIPD data source
#state['socket'] = 'tcp://10.253.0.51:4501'

# Reading from individual raw AGIPD data sources
#state['socket'] = 'tcp://10.253.0.52:4600'
#state['socket'] = 'tcp://10.253.0.52:4601'
#state['socket'] = 'tcp://10.253.0.52:4602'



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
