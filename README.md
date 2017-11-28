## Getting started (online analysis)
Login to the Maxwell cluster and source ```source_this_at_xfel```. This should provide all the dependencies and include the Hummingbird executable in your path. For testing purposes, one can start the AGIPD simulator to provide data over ZMQ, e.g. on port 4500:

```
cd scripts
python3 agipd_zmq_server.py 4500
```

Now, one can test Hummingbird in the XFEL configuration by running the backend with

```
hummingbird.py -b conf.py
```

and the frontend with 

```
hummingbird.py -i
```

## How to contribute
You can always check the issue tracker on this repository and/or the Hummingbird repository in order look for things to do or bugs to be fixed...

## Meeting notes

### AGIPD detector

__Data of the entire detector (all panels) can be received from:__

       - Raw: tcp://10.253.0.51:4500
       - Corrected: tcp://10.253.0.51:4501

       Note: Stream of only events with FEL on!

__Data of the central (working) three modules can be received from:__

       - Module 0: tcp://10.253/0.52:4600
       - Module 1: tcp://10.253/0.52:4601
       - Module 2: tcp://10.253/0.52:4602

       Stream of all events: frame 0: garbage / frame 1: garbage / frame 2: FEL on / frame 3: FEL off / frame 4: FEL on / frame 5: FEL off ...)

