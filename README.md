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