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

There are two ways of streaming data:

__A) Data of the entire detector (all panels) - only events with FEL on (pulse count 64, number of frames: 30)__

       - Raw: tcp://10.253.0.51:4500 
       - Corrected: tcp://10.253.0.51:4501

       Key: SPB_DET_AGIPD1M-1

       Shape: (16, 512, 128)

       Frame sequence: 0: FEL on / 1: FEL on / ... / 29: FEL on

       Delay: ?

__B) Data of the central (working) three modules - all events (pulse count: 64, number of frames: 64)__

       - Module 3: tcp://10.253/0.52:4600 (key: SPB_DET_AGIPD1M-1/DET/3CH0:xtdf)
       - Module 4: tcp://10.253/0.52:4601 (key: SPB_DET_AGIPD1M-1/DET/3CH0:xtdf)
       - Module 15: tcp://10.253/0.52:4602 (key: SPB_DET_AGIPD1M-1/DET/3CH0:xtdf)

       Shape: (512, 128)

       Frame sequence: 0: garbage / 1: garbage / 2: FEL on / 3: FEL off / 4: FEL on / 5: FEL off / ... / 65: FEL off

       Delay: ?
