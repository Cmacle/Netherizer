from PIL import Image

def encode(image_path, file_path, bit_depth):
    """
    This will take the input image and file to be hidden within
    the input image. It will then overwrite LSB pixel data in
    ascending order according to the bit_depth. With lower values
    having less impact on the image and having less data capacity.
    """
    file_array = file_to_byte_list(file_path, 1)
    print(file_array)
    image = Image.open(image_path)
    pixels = image.getdata()
    print(pixels[1])


def decode(image, output_path):
    """
    This will take an image that has been encoded previously and
    output the file that was encoded into the image to the output_path.
    """
    pass

def file_to_byte_list(file_path, bit_depth):
    """
    This will take a file and return a list of bytes so that it can be
    encoded. It will additionally append file information including
    bitdepth, file name and file type that will allow it to be decoded.
    This is for use in the encode function.
    """
    byte_list = []
    with open(file_path, "rb") as file:
        while True:
            byte = file.read(1)
            if not byte:
                break
            byte_list.append(byte)
    return(byte_list)
    

if __name__ == "__main__":
    encode("C:\\Users\\cmacl\\Pictures\\test.png", "C:\\Users\\cmacl\\Pictures\\test.png", "")