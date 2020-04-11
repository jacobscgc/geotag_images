from scripts.tagging_functions import GeotaggingFunctions, Logging
from timezonefinder import TimezoneFinder


class GeotagImages:

    def __init__(self, settings):
        self.input_location = settings.input_location
        self.gpx_location = settings.gpx_location
        # Initialize logging
        self.logger = Logging('Geotag_Images', 'DEBUG')
        self.gf = GeotaggingFunctions(self.logger)
        self.correction = self.gf.parse_correction_delta(settings.correction)
        self.source = settings.gpx_source
        self.tz = TimezoneFinder()

    def apply(self):
        self.logger.log_info('Geotagging Images Started')
        self.logger.log_info('The input location = {0}'.format(self.input_location))
        image_list = self.gf.retrieve_image_filelist(self.input_location)
        gpx = None
        if self.source == 'gpslogger':
            gpx = self.gf.gpslogger_gpx_to_dictionary(self.gpx_location)
        if self.source == 'strava':
            gpx = self.gf.strava_gpx_to_dictionary(self.gpx_location)
        if gpx is None:
            self.logger.log_error('GPX file not loaded, choose "strava" or "gpslogger" as GPX source, exiting..')
            exit()
        else:
            # Identify the timezone, IMPORTANT, the script assumes that all images are taken in a single timezone!
            # Get a single entry from the gpx dictionary:
            latitude, longitude, altitude, speed, satellites, gpstime = gpx[list(gpx.keys())[0]]
            timezone = self.tz.timezone_at(lng=float(longitude), lat=float(latitude))
            self.logger.log_info('{0} points loaded from the GPX file'.format(len(gpx)))
            for entry in image_list:
                self.gf.geotag_image(entry, self.correction, gpx, timezone)
