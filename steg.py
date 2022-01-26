import os
from PIL import Image

def encode(image_path, file_path, bit_depth):
    """
    This will take the input image and file to be hidden within
    the input image. It will then overwrite LSB pixel data in
    ascending order according to the bit_depth. With lower values
    having less impact on the image and having less data capacity.
    """
    file_byte_list = file_to_byte_list(file_path, bit_depth)
    byte_list_to_file(file_byte_list, "")
    image = Image.open(image_path)
    pixels = image.getdata()
    #print(pixels[1])


def decode(image, output_path):
    """
    This will take an image that has been encoded previously and
    output the file that was encoded into the image to the output_path.
    """
    pass

def byte_list_to_file(byte_list, output_path):
    #For testing purposes
    bit_depth = int(byte_list.pop(0).decode())
    print(bit_depth)
    file_name_length = int(byte_list.pop(0).decode('UTF-8'))
    print(file_name_length)
    file_name = []
    for num in range(file_name_length):
        file_name.append(byte_list.pop(0).decode('UTF-8'))
    print(file_name)
    file_extension_length = int(byte_list.pop(0).decode('UTF-8'))
    print(file_extension_length)
    file_extension = []
    for num in range(file_extension_length):
        file_extension.append(byte_list.pop(0).decode('UTF-8'))
    print(file_extension)
    output_name = "".join(file_name) + "".join(file_extension)
    print(output_name)

    with open(output_name, "wb") as file:
        print("Writing bytes to file:  ")
        while byte_list:
            file.write(byte_list.pop(0))
            

def int_to_byte(x):
    #Turns an int into a string then a byte
    return str(x).encode()

def get_file_extension(file_path):
    tup = os.path.splitext(file_path)
    return tup

def file_to_byte_list(file_path, bit_depth):
    """
    This will take a file and return a list of bytes so that it can be
    encoded. It will additionally append file information including
    bitdepth, file name and file type that will allow it to be decoded.
    This is for use in the encode function.
    """
    byte_list = []   #Declare the Byte list that will be returned
    byte_list.append(int_to_byte(bit_depth))   #Appends the bit depth to the list as a byte
    file_name, file_extension = get_file_extension(os.path.basename(file_path))   #Get the file name from the path
    file_name_length = len(file_name)   #Get the length of the file name
    byte_list.append(int_to_byte(file_name_length))   #Appends the length

    print(file_name)
    print(file_extension)

    for letter in file_name: #Append the letters of the name to the list
        byte_list.append(letter.encode())

    file_extension_length = len(file_extension)
    byte_list.append(int_to_byte(file_extension_length))

    for letter in file_extension:
        byte_list.append(int_to_byte(letter))

    with open(file_path, "rb") as file:
        while True:
            byte = file.read(1)
            if not byte:
                break
            byte_list.append(byte)
    return byte_list
    

if __name__ == "__main__":
    encode("C:\\Users\\cmacl\\Pictures\\test.png", "C:\\Users\\cmacl\\Pictures\\test.png", "2")
    