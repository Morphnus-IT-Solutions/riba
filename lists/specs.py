from imagekit.specs import ImageSpec 
from imagekit import processors 

# first we define our thumbnail resize processor 
class ResizeThumb(processors.Resize): 
    width = 150 
    crop = False

class ResizeCategoryImage(processors.Resize):
    width = 150
    height = 150
    crop = False

# now we define a display size resize processor
class ResizeDisplay(processors.Resize):
    width = 300 
    height = 300

class ResizeRelated(processors.Resize):
    width = 125

class ResizeFilmstrip(processors.Resize):
    width = 104

# now we can define our thumbnail spec 
class Thumbnail(ImageSpec): 
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

# now we define a display size resize processor
class ResizeBannerMain(processors.Resize):
    quality = 100
    width = 988 
    height = 300

# now we can define our thumbnail spec 
class BannerMain(ImageSpec): 
    pre_cache = True 
    quality = 100
    increment_count = False
    processors = [ResizeBannerMain] 

# now we define a display size resize processor
class ResizeBannerThumb(processors.Resize):
    width = 260 

# now we can define our thumbnail spec 
class BannerThumb(ImageSpec): 
    increment_count = False
    processors = [ResizeBannerThumb] 
