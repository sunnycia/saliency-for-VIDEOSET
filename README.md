# Private research, not open yet...



##TODO list (2017-6-1)

### Data collection phase
* Make tobiicontroller_apply.py beautiful. (low priority)
	* Remove useless code
	* Functional decomposition if needed

### Data processing phase
* Gaze->Fixation & fixation duration
	* Induce filter
		* I-VT filter
			* Gap fill-in
			* Noise reduction
		* Tobii fixation filter
		* ClearView Fixation filter
		* Raw Data
* Generate heatmap
* Do some combination for those code
* use argparse to parameterize the python code
	* Input directory of tester's data
	* Output directory of synthetic video
	* Output directory of fixation/frame images
	*
* Wash tester's data
	* out of boundary
	* still point
	* outlier point
	* ...
 
* User friendly data access interface
	* A demo program is necessary.
	* Dataset documentation

