import plotting.image
import analysis.agipd

state = {}
state['Facility'] = 'euxfel'
state['socket'] = 'tcp://127.0.0.1:4501'


def onEvent(evt):

    # Available keys
    print("Available keys: " + str(evt.keys()))

    # Shape of AGIPD array
    print(evt['photonPixelDetectors']['AGIPD1'].data.shape)

    # Get individual panels from the AGIPD
    agipd_0 = analysis.agipd.get_panel(evt, evt['photonPixelDetectors']['AGIPD1'], 0)

    # Shape of the AGIPD panel
    print(agipd_0.data.shape)

    # Plotting the AGIPD panel
    plotting.image.plotImage(agipd_0)

    # TODO: Add more ......
    # ....
