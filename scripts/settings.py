import argparse


class Settings:

    def __init__(self):
        pass

    @staticmethod
    def add_options():
        parser = argparse.ArgumentParser(description='Option parser for Geotag Images')
        parser.add_argument('--input_location', help='filepath to the directory containing the images')
        parser.add_argument('--gpx_location', help='filepath to the gpx file')
        parser.add_argument('--gpx_source', default='strava', help='Source of gpx file: strave/gpslogger')
        parser.add_argument('--correction', help='A correction factor for the image time in the format +DD:HH:MM:SS',
                            default='+00:00:00:00')

        return parser.parse_args()
