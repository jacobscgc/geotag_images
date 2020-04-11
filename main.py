# Modules included in our package
from scripts.settings import Settings
from scripts.geotag_images import GeotagImages
from scripts.plot_images import PlotImages

if __name__ == '__main__':
    settings = Settings().add_options()
    f = GeotagImages(settings)
    f.apply()
    if settings.generate_map == 'yes':
        f = PlotImages(settings)
        f.apply()
