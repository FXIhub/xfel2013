# Offline data access

## Module combiner
AGIPD data is written in separate files for each module. The `combine_modules`
python script combines the data from different modules and applies detector
calibrations resulting in a detector image for a given run number and frame number.

## Usage

Here is some basic usage inside an `ipython` console.
```python
import combine_modules
c = combine_modules.AGIPD_combiner(35) # For run 35
frame = c.get_frame(8730, calibrate='true') # For frame number 8730
```

Note that the frame numbers are of just the cells which contain data. Thus, in 
this experiment, there are 30 frames per train, even though the detector stores
64 events. If there are 1000 trains, there should be 30000 indices.
