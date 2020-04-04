# geotag_images
Tool to add GPS data to images from a GPSlogger or Strava gps trace.

# Run:
python main.py --input_location C:\for_example\image_folder --gpx_location C:\for_example\Strava_trace.gpx --gpx_source strava --correction '+00:01:00:00'

where:
--input_location gives the directory containing the images
--gpx_location gives the filepath to the gpx trace file (from strava or GPSlogger)
--gpx_source gives the source of the gpx (strava or gpslogger)
--correction gives the offset of the image timestamp as +DD:HH:MM:SS
The correction is used if the camera time was incorrect and needs to be adjusted to match the images to the gps trace. 
The first character is + if the time needs to move forward and - if the time needs to move back, it will move the time as much as is 
given in the rest of the string. '+00:01:00:00' will move the time 1 hour forward for example.
'-03:02:15:23' would move the time 3 days, 2 hours, 15 minutes and 23 seconds back.
