from imagekit.specs import ImageSpec 
from imagekit import processors 

# first we define our thumbnail resize processor 
class ResizeThumb(processors.Resize): 
    width = 218
    height = 218 
    crop = False

class ResizeThumbnail_110x110(processors.Resize): 
    width = 110
    height = 110 
    crop = False

class ResizeDisplay_170x170(processors.Resize): 
    width = 170
    height = 170 
    crop = False

# now we define a display size resize processor
class ResizeDisplay(processors.Resize):
    width = 670
    height = 342

class ResizeBanner(processors.Resize):
    width = 670
    height = 342

# now we can define our thumbnail spec 
class Thumbnail(ImageSpec):
    access_as = 'thumbnail_image'
    pre_cache = True
    processors = [ResizeThumb]

# now we can define our thumbnail spec 
class Thumbnail218x218(ImageSpec): 
    access_as = 'thumbnail_218x218' 
    pre_cache = True 
    processors = [ResizeThumb] 

class Thumbnail_110x110(ImageSpec): 
    access_as = 'thumbnail_110x110'
    pre_cache = True 
    processors = [ResizeThumbnail_110x110] 

# and our display spec
class Display(ImageSpec):
    pre_cache = True
    increment_count = False
    processors = [ResizeDisplay]

class Display_170x170(ImageSpec): 
    access_as = 'display_170x170' 
    pre_cache = True 
    processors = [ResizeDisplay_170x170] 

class Banner670x342(ImageSpec):
    access_as = 'banner_670x342'
    pre_cache = True
    processors = [ResizeBanner]
