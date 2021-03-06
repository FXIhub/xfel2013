import os
import socket
import analysis.agipd
this_dir = os.path.dirname(os.path.realpath(__file__))

# ===================== #
# Read calibration data #
# ===================== #

run_at_desy = socket.getfqdn().split('.')[0].startswith('exflonc')
run_online = run_at_desy

def init_calib(dark_run_nr=None):
    # Read calibration data (one file per panel)        
    if run_at_desy:
        if dark_run_nr is None:
            calib_dir = '/gpfs/exfel/exp/SPB/201701/p002013/usr/Shared/calib/latest'
        else:
            calib_dir = '/gpfs/exfel/exp/SPB/201701/p002013/usr/Shared/calib/r%04i' % dark_run_nr
    else:
        calib_dir = "%s/calib" % this_dir
    fn_agipd_calib_list = ['%s/Cheetah-AGIPD%02i-calib.h5' % (calib_dir, panelID) for panelID in range(0, 16)]
    analysis.agipd.init_calib(filenames=fn_agipd_calib_list)

def init_geom(rot180=False):
    # Read geometry data
    if run_at_desy:
        geom_dir = '/gpfs/exfel/exp/SPB/201701/p002013/usr/Shared/geometry'
    else:
        geom_dir = "%s/geometry" % this_dir
    fn_agipd_geom = '%s/agipd_taw9_oy2_1050addu_hmg5.geom' % (geom_dir)
    analysis.agipd.init_geom(filename=fn_agipd_geom, rot180=rot180)


def get_agipd_source(agipd_format, agipd_panel, do_assemble, do_calibrate, do_precalibrate=False):
    # Determine the data source
    agipd_panel_to_port = {3: 0, 4: 1, 15: 2}
    if not run_online:
        tcp_prefix = 'tcp://127.0.0.1'
    else:
        if agipd_format == 'panel':
            tcp_prefix = 'tcp://10.253.0.52'
        elif agipd_format == 'combined':
            tcp_prefix = 'tcp://10.253.0.51'
        elif agipd_format == 'synced':
            tcp_prefix = 'tcp://10.253.0.68'
    if agipd_format == 'panel':
        # Reading from individual raw AGIPD data source
        if not run_online:
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
    elif agipd_format == 'synced':
        # Reading from raw AGIPD data source
        if do_precalibrate:
            agipd_socket = '%s:5101' % tcp_prefix
        else:
            agipd_socket = '%s:5100' % tcp_prefix
        agipd_key = 'synced'
    

    # Output calibration to console
    print("AGIPD socket:\t%s" % agipd_socket)
    print("AGIPD key:\t%s" % agipd_key)
    print("AGIPD format: %s" % agipd_format)
    print("AGIPD do assemble: %i" % do_assemble)
    print("AGIPD do calibrate: %i" % do_calibrate)

    return agipd_socket, agipd_key

