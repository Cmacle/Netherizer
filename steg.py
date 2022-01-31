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
#    byte_list_to_file(file_byte_list, "")
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
    print(f'Bit Depth: {bit_depth}')
    file_name_length = int(byte_list.pop(0).decode('UTF-8'))
    print(f'File Name Length: {file_name_length}')
    file_name = []

    for num in range(file_name_length):
        file_name.append(byte_list.pop(0).decode('UTF-8'))

    file_name = "".join(file_name)
    print(f'File Name: {file_name}')

    with open(file_name, "wb") as file:
        print("Writing bytes to file:  ")
        while byte_list:
            file.write(byte_list.pop(0))
            

def int_to_byte(x):
    #Turns an int into a string then a byte
    return str(x).encode()

def int_to_four_byte_list(x):
    byte_list = []
    binary_string = format(x, "b") #Turn the int to a binary string
    binary_string = binary_string.rjust(32, "0") #pad the string to 32
    for index in range(0, len(binary_string), 8):
        #Break the string up into 4 8 character strings
        byte_list.append(binary_string[index : index + 8])
    
    for index, string in enumerate(byte_list):
        byte_list[index] = int(byte_list[index], 2)
        byte_list[index] = int_to_byte(byte_list[index])

    return byte_list



def file_to_byte_list(file_path, bit_depth):
    """
    This will take a file and return a list of bytes so that it can be
    encoded. It will additionally append file information including
    bitdepth, file name and file type that will allow it to be decoded.
    This is for use in the encode function.
    """
    byte_list = []   #Declare the Byte list that will be returned
    byte_list.append(int_to_byte(bit_depth))   #Appends the bit depth to the list as a byte
    file_name = os.path.basename(file_path)   #Get the file name from the path
    file_name_length = len(file_name)   #Get the length of the file name
    byte_list.append(int_to_byte(file_name_length))   #Appends the length

    for letter in file_name: #Append the letters of the name to the list
        byte_list.append(letter.encode())

    file_size = os.path.getsize(file_path) #Get the file size
    #Turn the file size into a byte list with 4 bytes
    file_size_byte_list = int_to_four_byte_list(file_size)
    byte_list.append(file_size_byte_list) #Append the list
    
    

    with open(file_path, "rb") as file:
        while True:
            byte = file.read(1)
            if not byte:
                break
            byte_list.append(byte)
    return byte_list
    

if __name__ == "__main__":
    encode("C:\\Users\\cmacl\\Pictures\\test.png", "C:\\Users\\cmacl\\Pictures\\test.png", "2")
    