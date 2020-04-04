import unittest
from datetime import datetime, timedelta

from scripts.tagging_functions import Logging, GeotaggingFunctions


class TestTryThis(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super(TestTryThis, self).__init__(*args, **kwargs)
        logger = Logging('Geotag_Images_Tests', 'ERROR')
        self.gtf = GeotaggingFunctions(logger)

    def test_parse_correction_delta(self):
        #TODO: fix this test, the function works properly now but the test seems wrong
        test_list = [
            "+01:01:01:01",
            "-01:01:01:01",
            "+00:01:00:00",
            "-00:01:00:00",
            "+00:00:00:00"
        ]

        expected_output = [
            timedelta(days=1, hours=1, minutes=1, seconds=1),
            timedelta(days=-1, hours=-1, minutes=-1, seconds=-1),
            timedelta(days=0, hours=1, minutes=0, seconds=0),
            timedelta(days=0, hours=-1, minutes=0, seconds=0),
            timedelta(days=0, hours=0, minutes=0, seconds=0)
        ]

        output = [self.gtf.parse_correction_delta(i) for i in test_list]

        self.assertEqual(output, expected_output)

    def test_decimal_degrees_to_dms(self):
        test_list = [
            (52.04561, 4.45885)
        ]
        expected_ouput = [
            (((52, 1), (2, 1), (441960000, 10000000)), ((4, 1), (27, 1), (318599999, 10000000)))
        ]
        output = [self.gtf.decimal_degrees_to_dms(i) for i in test_list]

        self.assertEqual(output, expected_ouput)


if __name__ == '__main__':
    unittest.main()
