from imagekit.specs import ImageSpec 
from imagekit import processors 

# first we define our thumbnail resize processor 
class ResizeThumb(processors.Resize): 
    width = 100 
    height = 75 
    crop = False

class ResizeCategoryImage(processors.Resize):
    width = 150
    height = 150
    crop = False

# now we define a display size resize processor
class ResizeDisplay(processors.Resize):
    width = 322
    height = 218

class ResizeBanner(processors.Resize):
    width = 988
    height = 300

class ResizeStealNow(processors.Resize):
    width = 142
    height = 31

class ResizeRelated(processors.Resize):
    width = 125

class ResizeFilmstrip(processors.Resize):
    width = 48

# now we can define our thumbnail spec 
class Thumbnail(ImageSpec): 
    access_as = 'thumbnail_image' 
    pre_cache = True 
    processors = [ResizeThumb] 

class Category(ImageSpec):
    access_as = 'category_thumbnail'
    pre_cache = True
    processors = [ResizeCategoryImage]

class Filmstrip(ImageSpec):
    processors = [ResizeFilmstrip]

# and our display spec
class Display(ImageSpec):
    increment_count = False
    processors = [ResizeDisplay]

class Related(ImageSpec):
    increment_count = False
    processors = [ResizeRelated]

class Banner(ImageSpec):
    quality = 100
    pre_cache = True
    increment_count = False
    processors = [ResizeBanner]

class StealNow(ImageSpec):
    increment_count = False
    processors = [ResizeStealNow]
