import PIL

def encode(image, file, bit_depth):
    """
    This will take the input image and file to be hidden within
    the input image. It will then overwrite LSB pixel data in
    ascending order according to the bit_depth. With lower values
    having less impact on the image and having less data capacity.
    """
    pass

def decode(image, output_location):
    """
    This will take an image that has been encoded previously and
    output the file that was encoded into the image to the output_location.
    """
    pass

def file_to_byte_array(file, bit_depth):
    """
    This will take a file and return a byte array so that it can be 
    encoded. It will additionally append file information including
    bitdepth, file name and file type that will allow it to be decoded.
    This is for use in the encode function.
    """
    pass
