from datetime import datetime, timedelta
import os
import piexif
import logging
import pytz
from xml.dom import minidom


class GeotaggingFunctions:

    def __init__(self, logger):
        self.logger = logger

    def retrieve_image_filelist(self, directory_location):
        """
        This function retrieves the path of all image files from the input directory. It only considers jpg and tiff
        image files.

        :param directory_location: full path to the directory containing the images
        :return: filelist containing the full path to each image in the directory
        """
        extensions = ['JPG', 'jpg', 'TIFF', 'tiff']
        files = [os.path.join(directory_location, f) for f in os.listdir(directory_location) if
                 os.path.isfile(os.path.join(directory_location, f)) and f[-3:] in extensions]
        self.logger.log_info('Found {0} image files.'.format(len(files)))
        return files

    def gpslogger_gpx_to_dictionary(self, gpx_location):
        """
        This function parses the GPX as generated by the GPS Logger app. It returns a dictionary with the datetime
        object as key and a tuple containing the other info as value (latitude, longitude, altitude, speed, satellites)

        :param gpx_location: location of the GPX file generated by GPS logger
        :return: dictionary linking the datetime object to the attributes linked to that.
        """
        # Load the GPX file:
        xmldoc = minidom.parse(gpx_location)
        # Extract the name from the GPX to get the time from that, it can be used to see whether there is a difference
        # between the phone time and the logged time (due to wintertime or not). If there is a difference, correct the
        # extracted times automatically.
        name_xml = xmldoc.getElementsByTagName('name')[0].firstChild.nodeValue
        gpx_date, gpx_time = name_xml.split(' ')[-1].split('-')
        year = int(gpx_date[:4])
        month = int(gpx_date[4:6])
        day = int(gpx_date[6:])
        hour = int(gpx_time[:2])
        minute = int(gpx_time[2:4])
        seconds = int(gpx_time[4:])
        phone_time = datetime(year, month, day, hour, minute, seconds)

        # Extract the tracepoints from the GPX file, for the first entry, check whether the time is the same as the
        # phone_time or whether they differ, correct if needed:
        first = True
        itemlist = xmldoc.getElementsByTagName('trkpt')
        timedif = None
        trace_dict = {}
        for entry in itemlist:
            latitude = entry.attributes['lat'].value
            longitude = entry.attributes['lon'].value
            altitude = entry.getElementsByTagName('ele')[0].firstChild.nodeValue
            dtime = self.gpx_time_to_datetime(entry.getElementsByTagName('time')[0].firstChild.nodeValue)
            if timedif is not None:
                dtime = dtime - timedif
            speed = entry.getElementsByTagName('speed')[0].firstChild.nodeValue
            satellites = entry.getElementsByTagName('sat')[0].firstChild.nodeValue
            if first:
                first = False
                timedif = dtime - phone_time
                dtime = dtime - timedif
            trace_dict[dtime] = (latitude, longitude, altitude, speed, satellites)
            self.logger.log_debug('lat={0}, lon={1}, alt={2}, datetime={3}, speed={4}, sat={5}'.format(latitude,
                                                                                                       longitude,
                                                                                                       altitude,
                                                                                                       dtime, speed,
                                                                                                       satellites))

        return trace_dict

    def strava_gpx_to_dictionary(self, gpx_location):
        """
        This function parses the GPX as generated by the Strava app. It returns a dictionary with the datetime
        object as key and a tuple containing the other info as value (latitude, longitude, altitude, None, None)
        (The None values are to make it camparable with GPS logger).

        :param gpx_location: location of the GPX file generated by Strava
        :return: dictionary linking the datetime object to the attributes linked to that.
        """
        # Load the GPX file:
        xmldoc = minidom.parse(gpx_location)
        # Extract the tracepoints from the GPX file
        itemlist = xmldoc.getElementsByTagName('trkpt')
        speed, satellites = None, None
        trace_dict = {}
        for entry in itemlist:
            latitude = entry.attributes['lat'].value
            longitude = entry.attributes['lon'].value
            altitude = entry.getElementsByTagName('ele')[0].firstChild.nodeValue
            gpstime = entry.getElementsByTagName('time')[0].firstChild.nodeValue
            dtime = self.gpx_time_to_datetime(gpstime)
            trace_dict[dtime] = (latitude, longitude, altitude, speed, satellites, gpstime)
            self.logger.log_debug('lat={0}, lon={1}, alt={2}, datetime={3}, speed={4}, sat={5}'.format(latitude,
                                                                                                       longitude,
                                                                                                       altitude,
                                                                                                       dtime, speed,
                                                                                                       satellites))

        return trace_dict

    @staticmethod
    def gpx_time_to_datetime(dtime):
        """
        Creates a datetime object from the datetime extracted from the GPX file.

        :param dtime: datetime string extracted from the GPX file.
        :return: datetime object
        """
        gpx_date, gpx_time = dtime.split('T')
        year, month, day = gpx_date.split('-')
        hour, minute, seconds = gpx_time[:-1].split(':')

        return datetime(int(year), int(month), int(day), int(hour), int(minute), int(seconds))

    @staticmethod
    def match_to_gpx(gpx_dict, img_datetime):
        """
        This function uses the img_datetime object to identify with which datetime from the GPX trace it has the
        smallest time difference. It then returns the GPX datetime and the time difference.

        :param img_datetime: datetime object of the image.
        :param gpx_dict: a gpx dictionary with the gpx datetime as key (as generated by gpx_to_dictionary())
        :return: smallest time difference found (seconds) and the coordinates belonging to that time.
        """
        min_datetime, min_timediff = None, None
        for key, value in gpx_dict.items():
            timediff = abs(key - img_datetime)
            if min_timediff is None or timediff.total_seconds() < min_timediff:
                min_datetime = key
                min_timediff = timediff.total_seconds()

        return min_datetime, min_timediff

    @staticmethod
    def correct_datetime(datetime_object, correction_delta):
        """
        This function corrects the input datetime object using a correction delta.

        :param datetime_object: datetime object to be corrected
        :param correction_delta: timedelta object used for correction
        :return: corrected datetime object
        """
        # Correct the values:
        return datetime_object + correction_delta

    @staticmethod
    def string_to_datetime(datetime_string):
        """
        This function transforms a string 'YYYY:DD:MM HH:MM:SS' to a datetime object and returns it.

        :param datetime_string: a datetime string in the form 'YYYY:DD:MM HH:MM:SS'
        :return: datetime object
        """
        input_date, input_time = datetime_string.split(' ')
        year, month, day = input_date.split(':')
        hour, minute, second = input_time.split(':')
        return datetime(int(year), int(month), int(day), int(hour), int(minute), int(second))

    @staticmethod
    def decode_byte_object(byte_object):
        """
        This function decodes byte objects to strings (UTF-8) and returns the string.

        :param byte_object: a byte object (b'NIKON D3200')
        :return: a string ('NIKON D3200')
        """
        return byte_object.decode("utf-8")  # the .decode('utf-8') transforms the bytes object to a string

    @staticmethod
    def encode_string_object(string_object):
        """
        This function encodes a string intop a byte object and returns this byte object.

        :param string_object: A string ('NIKON D3200')
        :return: a byte object (b'NIKON D3200')
        """
        return str.encode(string_object)

    @staticmethod
    def parse_correction_delta(correction):
        """
        This function parses the +DD:HH:MM:SS correction input to a timedelta format so it can be used to correct the
        image time. This is used if the time setting on the camera was wrong but known.
        If the date needs to be moved forward / in the future, start with a plus sign: +DD:HH:MM:SS
        If the date needs to be moved back / in the past, start with a minus sign: -DD:HH:MM:SS

        :param correction: The time difference between the time information on the image and when it was really taken
        in the format +DD:HH:MM:SS (string)
        :return: correction as timedelta
        """
        sign = correction[1]
        day, hour, minute, second = correction[2:-1].split(':')
        if sign == '-':
            day = -1 * int(day)
            hour = -1 * int(hour)
            minute = -1 * int(minute)
            second = -1 * int(second)
        else:
            day = int(day)
            hour = int(hour)
            minute = int(minute)
            second = int(second)
        correction = timedelta(days=day, hours=hour, minutes=minute, seconds=second)
        return correction

    @staticmethod
    def generate_float_tuple(input_float):
        """
        piexif only accepts integers or tuples of integers, so if we have a float convert it to a tuple where the first
        integer is divided by the second to get the float again.

        For example:
            52.34678 would be the tuple (5234678, 100000)

        :param input_float: a float
        :return: a float tuple
        """
        val1, val2 = str(input_float).split('.')

        # piexif cannot deal with numbers larger than 4294967295, so make sure that the coordinate is always a maximum
        # of 9 digits:
        if len(val1) + len(val2) > 9:
            # if the length is more than 9 digits, remove all digits after the 9th digit:
            remove = 9 - (len(val1) + len(val2))
            val2 = val2[:remove]
        int_value = int('{0}{1}'.format(val1, val2))
        multiplier_list = ['0' for i in range(0, len(str(val2)))]
        multiplier_list.insert(0, '1')  # insert a 1 in the front
        return_tup = (int_value, int("".join(multiplier_list)))
        return return_tup

    def add_gps_to_exif(self, exif_dict, latitude, longitude, altitude, gps_timestamp, number_of_satellites):
        """
        This function adds GPS data to the exif dictionary.
        It returns the exif_dictionary with the new GPS information included. It will overwrite previous GPS info if
        exists. (usefull reference to GPS tags: https://exiftool.org/TagNames/GPS.html)

        :param exif_dict: a exif dictionary as loaded using piexif.load()
        :param latitude: the latitude to be added (WGS84)
        :param longitude: the longitude to be added (WGS84)
        :param altitude: the altitude to be added (WGS84)
        :param gps_timestamp: the Unix timestamp of the GPS measurement (seconds)
        :param number_of_satellites: the number of satellites of the GPS measurement
        :return: the exif dictionary with the GPS data included
        """
        latitude, longitude, altitude = float(latitude), float(longitude), float(altitude)
        # First, get the N/S/E/W hemisphere abbreviation:
        if int(latitude) >= 0:
            lat_hemisphere = 'N'
        else:
            lat_hemisphere = 'S'
        if int(longitude) >= 0:
            lon_hemisphere = 'E'
        else:
            lon_hemisphere = 'W'
        # Several software suites (windows / iNaturalist) only recognize GPS exif data if in DMS notation:
        # N52 2' 44.2104'' E4 27' 31,8599''
        # Which should be given as tuples in the form (lat, lon):
        # (((52, 1), (2, 1), (442104, 10000)), ((4, 1), (27, 1), (318599, 10000)))
        # Convert the decimal degrees to DMS in the proper tuple format:
        latitude, longitude = self.decimal_degrees_to_dms((latitude, longitude))

        # Check the altitude, if it below sealevel, GPSAltitudeRef should be 1, otherwise it should be 0.
        if altitude < 0:
            altituderef = 1
            altitude = -1 * altitude  # remove negative notation for the tuple creation
        else:
            altituderef = 0

        # Set the GPSDateStamp and GPSTimeStamp, where the datastamp is a string and the GPSTimeStamp a rational:
        gps_date, gps_time = gps_timestamp[:-1].split('T')
        gps_hour, gps_minute, gps_second = gps_time.split(':')
        gps_time = ((int(gps_hour), 1), (int(gps_minute), 1), (int(gps_second), 1))

        # Check whether the number of satellites is given or is None, if None, give empty string:
        if number_of_satellites is None:
            number_of_satellites = ''

        # Create the GPS information dictionary:
        gps_ifd = {
            piexif.GPSIFD.GPSLatitudeRef: lat_hemisphere,
            piexif.GPSIFD.GPSLatitude: latitude,
            piexif.GPSIFD.GPSLongitudeRef: lon_hemisphere,
            piexif.GPSIFD.GPSLongitude: longitude,
            piexif.GPSIFD.GPSAltitudeRef: altituderef,
            piexif.GPSIFD.GPSAltitude: self.generate_float_tuple(altitude),
            piexif.GPSIFD.GPSTimeStamp: gps_time,
            piexif.GPSIFD.GPSDateStamp: gps_date,
            piexif.GPSIFD.GPSSatellites: number_of_satellites
        }

        # Create a exif dictionary containing only the GPS data:
        gps_exif = {"GPS": gps_ifd}

        # Update the original exif_dict to include the GPS data (original GPS data will be overwrittten):
        exif_dict.update(gps_exif)

        return exif_dict

    def geotag_image(self, image_location, correction, gpx_dict, timezone):
        exif_dict = piexif.load(image_location)
        # Extract the datetime from the exif data, transform byte to string and create a datetime object from it:
        img_datetime = self.string_to_datetime(
            self.decode_byte_object(exif_dict["0th"][piexif.ImageIFD.DateTime]))
        # Correct the image datetime:
        corrected_datetime = self.correct_datetime(img_datetime, correction)
        exif_dict["0th"][piexif.ImageIFD.DateTime] = corrected_datetime.strftime("%Y:%m:%d %H:%M:%S")
        # Convert the time to UTC:
        local_time = pytz.timezone(timezone)
        local_datetime = local_time.localize(corrected_datetime, is_dst=None)  # add the local timezone to the datetime
        utc_datetime = local_datetime.astimezone(pytz.utc)  # convert to utc
        # Create it as a naive datetime object again so it can be used to find differences between objects:
        utc_datetime = datetime.strptime(utc_datetime.strftime("%Y:%m:%d %H:%M:%S"), "%Y:%m:%d %H:%M:%S")
        # Match datetime to the GPX trace using the utc_time:
        min_datetime, min_timediff = self.match_to_gpx(gpx_dict, utc_datetime)
        # If a match was found, add the data to the image:
        if min_timediff < 300:  # less than 5 minutes difference
            latitude, longitude, altitude, speed, satellites, gpstime = gpx_dict[min_datetime]
            # Set coordinates in exif data:
            exif_dict = self.add_gps_to_exif(exif_dict, latitude, longitude, altitude, gpstime, satellites)
            # Convert the exif_dict to a bytes object:
            exif_bytes = piexif.dump(exif_dict)
            piexif.insert(exif_bytes, image_location)  # write to image, will overwrite exif data in original file
            self.logger.log_info('Image {} was matched and a coordinate has been added to the exif data'
                                 .format(image_location))

    def decimal_degrees_to_dms(self, decimal_degrees):
        """
        This function converts a decimal degree coordinate to a degrees, minutes, seconds (DMS) coordinate which can
        be used in exif data: ((52, 1), (2, 1), (442104, 10000))
        The decimal degrees coordinate contains the number of degrees and a fraction. Minutes is 1/60th of the fraction,
        seconds in 1/60th of the remaining fraction after the minutes.
        So for example:
        N52.04561 E4.45885

        0.04561*60 => 2.7366
        0.7366*60 => 44.196
        N52 2' 44,196''

        0.45885*60 => 27.531
        0.531*60 => 31.86
        E4 27' 31,86''

        :param decimal_degrees: decimal degrees notation of the coordinate
        :return: DMS notation of the coordinate as it can be used for exif data (lat, lon) tuple.
        """
        lat, lon = decimal_degrees
        lat_degrees = int(lat)  # takes the whole integer, always rounds down as needed
        lon_degrees = int(lon)
        lat_fraction = lat - lat_degrees  # extract the remaining fraction
        lon_fraction = lon - lon_degrees
        lat_minutes = int(lat_fraction * 60)
        lat_seconds = ((lat_fraction * 60) - lat_minutes) * 60
        lon_minutes = int(lon_fraction * 60)
        lon_seconds = ((lon_fraction * 60) - lon_minutes) * 60
        # Convert to a format that can be used in exif data:
        dms_lat = ((lat_degrees, 1), (lat_minutes, 1), self.generate_float_tuple(lat_seconds))
        dms_lon = ((lon_degrees, 1), (lon_minutes, 1), self.generate_float_tuple(lon_seconds))
        return_tuple = (dms_lat, dms_lon)
        return return_tuple


class Logging:

    def __init__(self, name, level):
        # Initiate logging:
        self.logger = logging.getLogger(name)
        format_str = '%(asctime)s.%(msecs)03d | %(levelname)-7s | %(message)s'
        date_str = '%Y-%m-%d %H:%M:%S'
        if level == 'NOTSET':
            logging.basicConfig(level=logging.NOTSET, format=format_str, datefmt=date_str)
        elif level == 'DEBUG':
            logging.basicConfig(level=logging.DEBUG, format=format_str, datefmt=date_str)
        elif level == 'INFO':
            logging.basicConfig(level=logging.INFO, format=format_str, datefmt=date_str)
        elif level == 'WARNING':
            logging.basicConfig(level=logging.WARNING, format=format_str, datefmt=date_str)
        elif level == 'ERROR':
            logging.basicConfig(level=logging.ERROR, format=format_str, datefmt=date_str)
        elif level == 'CRITICAL':
            logging.basicConfig(level=logging.CRITICAL, format=format_str, datefmt=date_str)

    def log_error(self, error):
        self.logger.error(error)

    def log_info(self, info):
        self.logger.info(info)

    def log_debug(self, debug):
        self.logger.debug(debug)

    def log_warning(self, warning):
        self.logger.warning(warning)