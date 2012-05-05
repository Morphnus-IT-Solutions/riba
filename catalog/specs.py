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
    width = 300 
    height = 300

# now we define a display size resize processor
class ResizeDisplay_350x350(processors.Resize):
    width = 350
    height = 350
    crop = False

class ResizeDisplay_300x300(processors.Resize):
    width = 300
    height = 300

class ResizeThumb_150x150(processors.Resize):
    width = 150
    height = 150

class ResizeThumb_60x60(processors.Resize):
    width = 60
    height = 60

class ResizeRelated(processors.Resize):
    width = 125

class ResizeFilmstrip(processors.Resize):
    width = 40

class ResizeLargeImage(processors.Resize):
    width = 450
    height = 600

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
    pre_cache = True
    processors = [ResizeFilmstrip]

# and our display spec
class Display(ImageSpec):
    increment_count = False
    pre_cache = True
    processors = [ResizeDisplay]

class Related(ImageSpec):
    increment_count = False
    pre_cache = True
    processors = [ResizeRelated]

class LargeImage(ImageSpec):
    access_as = 'large_image'
    processors = [ResizeLargeImage]
    pre_cache = True

class Display_350x350(ImageSpec):
    access_as = 'display_350x350'
    pre_cache = True
    processors = [ResizeDisplay_350x350]

class Display_300x300(ImageSpec):
    access_as = 'display_300x300'
    pre_cache = True
    processors = [ResizeDisplay_300x300]

class Thumbnail_150x150(ImageSpec):
    access_as = 'thumbnail_150x150'
    pre_cache = True
    processors = [ResizeThumb_150x150]

class Thumbnail_60x60(ImageSpec):
    access_as = 'thumbnail_60x60'
    pre_cache = True
    processors = [ResizeThumb_60x60]
