# Modules included in our package
from scripts.settings import Settings
from scripts.geotag_images import GeotagImages

if __name__ == '__main__':
    settings = Settings().add_options()
    f = GeotagImages(settings)
    f.apply()
