import logging
import math
import os
import sys
from tkinter import StringVar
from typing import List, Optional, Tuple, Type
from PIL import Image


#Make a variable for updating the app UI 

state = "Ready"
#These two variables will be used to track progress throughout loops within the code
#so it can be displayed to the UI periodically
progress = 0
target = 0
logger = ""

def encode(image_path: str, file_path: str, bit_depth: int, output_path: str):
    """
    This will take the input image and file to be hidden within
    the input image. It will then overwrite LSB pixel data in
    ascending order according to the bit_depth. With lower values
    having less impact on the image and having less data capacity.
    """
    #CHUNK_SIZE will control how large each chunk of data from the input
    #file will be while encoded, the value will be made made divisible by 8
    #then multiplied by the bit_depth so later loops can be simplified
    CHUNK_SIZE = 10000
    global state
    global progress
    global target
    try:

        state = "ENCODING"

        logger.log(logging.INFO, "Encoding")
        logger.log(logging.INFO, "Processing Input File")

        file_byte_list = file_to_byte_list(file_path, bit_depth)

        logger.log(logging.INFO, "Opening Image")

        image = Image.open(image_path)
        #Get the pixel data from the image
        logger.log(logging.INFO, "Extracting Pixel Data")

        pixels = image.getdata()
        print(len(pixels))
        print(pixels[0])
        width, height = image.size
        image_mode = image.mode
        image_size = image.size
        #Delete the image as it is no longer needed
        del(image)

        if os.path.getsize(file_path) <= max_input_size(width, height, bit_depth, len(os.path.basename(file_path))):
            new_im_data = []

            byte_list_len = len(file_byte_list)
            color_stop = 0

            #Check if the image is a png and if so create a list for transparency values
            #this is so we can add those values back later
            transparency = False

            if len(pixels[0]) > 3:
                    transparency = True
                    transparency_values = []
            colors = bytearray()
            #Turn the pixels into a list of color values and a list for transparency values if a png

            logger.log(logging.INFO, "Processing Pixel Data")

            target = byte_list_len * 8 / 3 + 56
            if transparency:
                print("Byte List Len: ",byte_list_len*8)
                for x, pixel in enumerate(pixels):
                    progress = x * bit_depth
                    if x*bit_depth > byte_list_len * 8 / 3 + 56:
                        color_stop = x
                        break
                    for i in range(3):
                        colors.append(pixel[i])
                    transparency_values.append(pixel[3])
            else:
                for x, pixel in enumerate(pixels):
                    progress = x
                    if x*bit_depth > byte_list_len * 8 / 3 + 56:
                        color_stop = x
                        break
                    for color in pixel:
                        colors.append(color)
            target = 0
            #Encode the file into chunks to reduce memory usage
            #Make chunk_size divisible by 8 and bit_depth
            chunk_size = (CHUNK_SIZE//8)* 8 * bit_depth
            num_chunks = math.ceil(len(file_byte_list)/chunk_size)


            if bit_depth == 1:
                #For every chunk
                color_index = 0
                for i in range(num_chunks):
                    print(f'Chunk: {i+1} of {num_chunks}')
                    logger.log(logging.INFO, f'Chunk: {i+1} of {num_chunks}')
                    bit_list = bytes_to_bit_list(file_byte_list, 
                                                start_index=i*chunk_size, 
                                                end_index=i*chunk_size+chunk_size)
                    #Edit Pixel Data until all file bits have been written
                    for bit in bit_list:                  
                        color_value_even = colors[color_index]%2==0

                        if bit and color_value_even: 
                            #if the next bit and last value of the color are different
                            #edit the color
                            colors[color_index] = colors[color_index] + 1
                    
                        elif not bit and not color_value_even:
                            colors[color_index] = colors[color_index] - 1
                        color_index+=1

            else:
                color_index = 0
                #out_of_bits = False
                logger.log(logging.INFO, "Writing File Data to Image")

                bit_list = bytes_to_bit_list(file_byte_list, start_index=0, end_index=1)
                for bit in bit_list:
                    #check if there are any bits left to write                   
                    color_value_even = colors[color_index]%2==0
                    if bit and color_value_even: 
                            #if the next bit and last value of the color are different
                            #edit the color
                        colors[color_index] = colors[color_index] + 1
                    
                    elif not bit and not color_value_even:
                        colors[color_index] = colors[color_index] - 1
                    color_index+=1
                #Now handle the rest of the pixels and data with the new method
                for i in range(num_chunks):
                    logger.log(logging.INFO, f'Chunk: {i+1} of {num_chunks}')
                    bit_list = bytes_to_bit_list(file_byte_list, 
                                                start_index=i*chunk_size+1, 
                                                end_index=i*chunk_size+chunk_size+1)
                    bit_list_len = len(bit_list)
                    bit_list_index = 0
                    for x in range(bit_list_len//bit_depth):

                        #Get the color as a string in binary
                        color_bit_list = format(colors[color_index], "b")
                        color_bit_list = color_bit_list.rjust(8,"0") #Pad string to 8 bits
                        color_bit_list = list(color_bit_list) #Make it a list
                        #rewrite bits in values equal to bitdepth starting with LSB
                        for x in range(bit_depth):
                            next_bit = bit_list[bit_list_index]
                            bit_list_index+=1
                            #check for remaining bits
                            #if bit_list_index+1 < bit_list_len:
                            #    next_bit = bit_list[bit_list_index]
                            #    bit_list_index+=1
                            #else:
                            #    out_of_bits = True
                            #    break
                            color_bit_list[(x+1)*-1] = int(next_bit)
                        #Make a list of th evalues as strings
                        bit_list_strings = [str(int) for int in color_bit_list]
                        #Join the new bit_list_strings can cast to int
                        hold = "".join(bit_list_strings)
                        colors[color_index] = int(hold , 2)
                        color_index+=1

            #Reconstruct the pixels from the colors
            logger.log(logging.INFO, "Reconstructing Pixels")
            target = len(colors)//3
            if transparency:
                color_index = 0
                for num in range(len(colors)//3):
                    progress = num
                    new_pixel = []
                    #Append 3 Color Values
                    for i in range(3):
                        new_pixel.append(colors[color_index])
                        color_index+=1
                    #Append the transparency Value
                    new_pixel.append(transparency_values[num])
                    #Append to new_im_data as a tuple
                    new_im_data.append(tuple(new_pixel))
            #Same but without the transparency append, split up for branching performance        
            else:
                color_index = 0
                print(len(colors))
                for num in range(len(colors)//3):
                    progress = num
                    new_pixel = []
                    #Append 3 Color Values
                    for i in range(3):
                        new_pixel.append(colors[color_index])
                        color_index+=1
                    new_im_data.append(tuple(new_pixel))
            target = 0
            del(colors)
            #Add the remaining unaltered pixels
            print("Appending unaltered pixels")
            logger.log(logging.INFO, "Appending unaltered pixels")
            target = len(pixels) - color_stop
            for i in range(color_stop, len(pixels)):
                progress = i - color_stop
                new_im_data.append(pixels[i])
            del(pixels)
            target = 0

            logger.log(logging.INFO, "Writing Output File")
            output_image(new_im_data, image_mode, image_size, output_path)

            logger.log(logging.INFO, "Done")
        else:
            print("File too large")
            logger.log(logging.ERROR, "INPUT FILE TOO LARGE")
        state = "Ready"
    except Exception as err:
        exception_type, exception_object, exception_traceback = sys.exc_info()
        filename = exception_traceback.tb_frame.f_code.co_filename
        line_number = exception_traceback.tb_lineno

        logger.log(logging.CRITICAL, f'Critical Error Process Aborted: \n {err}')
        logger.log(logging.CRITICAL, f'Exception type: {exception_type}')
        logger.log(logging.CRITICAL, f'File name: {filename}')
        logger.log(logging.CRITICAL, f'Line number: {line_number}')
        state = "Ready"

def decode(image_path: str, output_path: str):
    """
    This will take an image that has been encoded previously and
    output the file that was encoded into the image to the output_path.
    """
    try:
        global state
        global progress
        global target
        state = "DECODING"

        logger.log(logging.INFO, "DECODING")
        logger.log(logging.INFO, f'Opening {image_path}')
        image = Image.open(image_path)
        logger.log(logging.INFO, "Extracting Pixel Data")
        pixels = image.getdata()
        #Delete the image as it is no longer needed
        del(image)
        logger.log(logging.INFO, "Processing Pixel Data")
        colors = bytearray()
        #create a list for the color values from every pixel
        target = len(pixels)
        for x, pixel in enumerate(pixels):
            progress = x
            for i in range(3):
                colors.append(pixel[i])
        target = 0
        del(pixels)
        bit_depth = []

        logger.log(logging.INFO, "Reading Data")
        #Get the Bit Depth from the first 8 color values
        for i in range(8):
            color = colors.pop(0)
            if len(bit_depth) < 8:
                if color%2==0:
                    bit_depth.append("0")
                else:
                    bit_depth.append("1")
        bit_depth = bit_list_to_bytes(bit_depth)
        bit_depth = int(bit_depth.decode('UTF-8'))
        logger.log(logging.INFO, f'Bit Depth: {bit_depth}')
        
        if bit_depth == 1:
            file_name_length = []#Make a list for the file name length
            colors_offset = 0 #Keep track of what color we are on
            for i in range(24):
                color = colors[colors_offset]
                colors_offset+=1
                if color%2==0:
                    file_name_length.append("0")
                else:
                    file_name_length.append("1")
            file_name_length = bit_list_to_bytes(file_name_length)
            file_name_length = int(file_name_length.decode('UTF-8'))
            logger.log(logging.INFO, f'File Name Length: {file_name_length}')
            #Get the file name from the data
            file_name = []
            #Get 8 bits for each character starting from the 16th
            for i in range(file_name_length*8):
                color = colors[colors_offset]
                colors_offset+=1
                if color%2==0:
                    file_name.append("0")
                else:
                    file_name.append("1")
            file_name = bit_list_to_bytes(file_name)
            file_name = file_name.decode('UTF-8')
            logger.log(logging.INFO, f'File Name: {file_name}')
            #Get the file length
            file_length = []
            for i in range(88):
                color = colors[colors_offset]
                colors_offset+=1
                if color%2==0:
                    file_length.append("0")
                else:
                    file_length.append("1")
            file_length = bit_list_to_bytes(file_length)
            file_length = int(file_length.decode('UTF-8'))
            logger.log(logging.INFO, f'File Length: {file_length} Bytes')
            #Get the file information
            bit_list = bytearray()
            hold = file_length*8
            logger.log(logging.INFO, f'Getting File Information')

            for i in range(file_length*8):
                color = colors[i+colors_offset]
                bit_list.append(color%2)
                #print(f'{i} : {i/hold*100}%')

            logger.log(logging.INFO, f'Converting File Data')
            file_data = bytearray()
            bit_list_index = 0

            target = range(file_length)
            for i in range(file_length):
                progress = i
                hold = []
                for x in range(8):
                    hold.append(str(bit_list[bit_list_index]))
                    bit_list_index += 1
                file_data.append(int("".join(hold), 2))
            target = 0

            #Write the data to a file
            output_location = os.path.join(output_path, file_name)
            with open(output_location, "wb") as file:
                logger.log(logging.INFO, "Writing bytes to file:  ")
                file.write(file_data)
            logger.log(logging.INFO, "Done")
        else:
            bit_list = bytearray()
            #get the bit list for the first 8112 bits to ensure we have all file information
            colors_offset = 0

            for i in range(math.ceil(8112/bit_depth)):
                #get the color as a bitstring then turn it into a list
                color_bit_list = color_to_bit_list(colors[i])
                colors_offset+=1
                #Now read values equal to the bit_depth
                for x in range(bit_depth):
                    bit_list.append(int(color_bit_list[(x+1)*-1]))

            #Now we start parsing the data
            bit_list_index = 0
            file_name_length = [] #Make a list for the file_name_length
            #get 3 bytes of data
            for i in range(24):
                file_name_length.append(str(bit_list[bit_list_index]))
                bit_list_index += 1
            file_name_length = bit_list_to_bytes(file_name_length)
            file_name_length = int(file_name_length.decode('UTF-8'))
            logger.log(logging.INFO, f'File Name Length: {file_name_length}')

            #Get the file name from the data
            file_name = []
            #Get 8 bits for each character starting from the 16th
            for i in range(file_name_length*8):
                file_name.append(str(bit_list[bit_list_index]))
                bit_list_index += 1
            file_name = bit_list_to_bytes(file_name)
            file_name = file_name.decode('UTF-8')
            logger.log(logging.INFO, f'File Name: {file_name}')

            #Get the file length
            file_length = []
            for i in range(88):
                file_length.append(str(bit_list[bit_list_index]))
                bit_list_index += 1
            file_length = bit_list_to_bytes(file_length)
            file_length = int(file_length.decode('UTF-8'))
            logger.log(logging.INFO, f'File Length: {file_length} Bytes')

            #Get data until we have enough to satisfy the file length 
            logger.log(logging.INFO, "Reading File Data")

            target = math.ceil(8112/bit_depth + file_length*8/bit_depth)
            for i in range(math.ceil(8112/bit_depth + file_length*8/bit_depth)):
                progress = i
                #get the color as a bitstring then turn it into a list
                color_bit_list = color_to_bit_list(colors[i+colors_offset])
                #Now read values equal to the bit_depth
                for x in range(bit_depth):
                    bit_list.append(int(color_bit_list[(x+1)*-1]))
            target = 0
            #Delete Colors
            del(colors)
            #Get the file information
            file_data = bytearray()
            logger.log(logging.INFO, "Converting File Data")
            target = file_length
            for i in range(file_length):
                progress = i
                hold = []
                for x in range(8):
                    hold.append(str(bit_list[bit_list_index]))
                    bit_list_index += 1
                file_data.append(int("".join(hold), 2))
            target = 0
            #Delete bit_list
            del(bit_list)
            #Turn the file_data into a list of bytes
            logger.log(logging.INFO, "Changing bit_list to byte_list")

            #Write the data to a file
            output_location = os.path.join(output_path, file_name)
            with open(output_location, "wb") as file:
                logger.log(logging.INFO, "Writing bytes to file:  ")
                file.write(file_data)
            logger.log(logging.INFO, "Done")

            state = "Ready"
    except Exception as err:
        exception_type, exception_object, exception_traceback = sys.exc_info()
        filename = exception_traceback.tb_frame.f_code.co_filename
        line_number = exception_traceback.tb_lineno

        logger.log(logging.CRITICAL, 
        f'Critical Error, Process Aborted: Are you sure this image has been encoded? \n{err}')
        logger.log(logging.CRITICAL, f'Exception type: {exception_type}')
        logger.log(logging.CRITICAL, f'File name: {filename}')
        logger.log(logging.CRITICAL, f'Line number: {line_number}')
        state = "Ready"



def output_image(image_data: List[Tuple[int, ...]], image_mode: str, image_size: Tuple[int,int], output_path: str) -> None:
    """
    Takes a list of pixel data, creates a new image using 
    image_mode and image_size then outputs to the output path
    """
    new_image = Image.new(image_mode, image_size)
    new_image.putdata(image_data)
    new_image.save(output_path, format="PNG")


def color_to_bit_list(color: int) -> List[str]:
    """
    Takes a color value as an int and converts it to a
    list of strings 8 characters long of its binary
    string representation.
    """
    color_bit_list = format(color, "b")
    color_bit_list = color_bit_list.rjust(8, "0") #Pad the string to 8 characters
    color_bit_list = list(color_bit_list)
    return color_bit_list

def max_input_size(width: int, height: int, bit_depth: int, file_name_length: int = None) -> int:
    """
    Calculates the maximum input file size based on the provided
    width, height and bit_depth. If file_name_length is provided
    it will be subtracted from the total.
    """
    max_size = (width*height*3*bit_depth)/8
    if file_name_length:
        max_size -= file_name_length
    return max_size

def max_input_size_from_path(path: int, bit_depth: int) -> int:
    """
    Calculates the maximum input file size from the provided image path
    as well as the bit_depth.
    """
    image = Image.open(path)
    width, height = image.size
    max_size = (width*height*3*bit_depth)/8
    max_size = max_size - len(os.path.basename(path))
    return max_size

def bit_list_to_bytes(bit_list: List[str]) -> bytes:
    """
    Takes a list of bit values as strings ("0" or "1") and returns
    bytes. len(bit_list) must be divisible by 8
    """
    bit_string = "".join(bit_list)
    return int(bit_string, 2).to_bytes(len(bit_string) // 8, byteorder='big')
            
def int_to_byte(x: int) -> str:
    """
    Takes an int and returns a utf-8 encoded str of the int
    """
    return str(x).encode()

def bytes_to_bit_list(byte_list: List[str], start_index: Optional[int] = None, end_index: Optional[int] = None):
    """
    This function takes a list of bytes and returns a list of bits
    that can be encoded. If there is an end_index given it will only
    return the bits for the bytes within the range provided. 
    """
    bit_list = []
    if end_index:
        #Make sure the start_index is in range if not return an empty list
        if start_index >= len(byte_list):
            return bit_list
        #Make sure the end_index is in range if not set it to the end of the list
        if end_index > len(byte_list):
            end_index = len(byte_list)
        #Now we will iterate over the selected elements and return them
        for i in range(start_index,end_index):

            byte = byte_list[i]
            hold = []
            for i in range(8):
                    next_bit = (byte[0] >> i) & 1
                    hold.insert(0, bool(next_bit))
            for bit in hold:
                bit_list.append(bit)
    else:
        for byte in byte_list:
            hold = []
            for i in range(8):
                    next_bit = (byte[0] >> i) & 1
                    hold.insert(0, bool(next_bit))
            for bit in hold:
                bit_list.append(bit)
    return bit_list

def file_to_byte_list(file_path: str, bit_depth: int) -> List[str]:
    """
    This will take a file and return a list of UTF-8 encoded strings. 
    """
    byte_list = []   #Declare the Byte list that will be returned
    byte_list.append(int_to_byte(bit_depth))   #Appends the bit depth to the list as a byte
    file_name = os.path.basename(file_path)   #Get the file name from the path
    file_name_length = len(file_name) #Get the length of the file name
    file_name_length = str(file_name_length).rjust(3, "0") #Change to a string and pad to 3 characters
    for character in file_name_length:
        byte_list.append(character.encode())

    for letter in file_name: #Append the letters of the name to the list
        byte_list.append(letter.encode())

    file_size = os.path.getsize(file_path) #Get the file size
    #Turn the file size into a string and pad it to 11 characters
    file_size = str(file_size).rjust(11, "0")
    print(file_size)
    for letter in file_size: #Append the list
        byte_list.append(letter.encode())
 
    with open(file_path, "rb") as file:
        while True:
            byte = file.read(1)
            if not byte:
                break
            byte_list.append(byte)
    return byte_list
    

if __name__ == "__main__":
    print("Run app.py")