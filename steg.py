import logging
import math
import os
import sys
from typing import List, Optional, Tuple
from PIL import Image


#Make a variable for updating the app UI 
state = "Ready"
#These two variables will be used to track progress throughout loops within the code
#so it can be displayed to the UI periodically
progress = 0
target = 0

logger = logging.getLogger(__name__)

def encode(image_path: str, file_path: str, bit_depth: int, output_path: str) -> None:
    """
    This will take the input image and file to be hidden within
    the input image. It will then overwrite LSB pixel data in
    ascending order according to the bit_depth. With lower values
    having less impact on the image and having less data capacity.
    Outputs the encoded image to the output_path.
    """
    #CHUNK_SIZE will control how large each chunk of data from the input
    #file will be while encoded, the value will be made made divisible by 8
    #then multiplied by the bit_depth so later loops can be simplified
    CHUNK_SIZE = 10000
    global state
    global progress
    global target
    print(f'BitDepth = {bit_depth}')
    write_to_transparent = False
    try:
        
        state = "ENCODING"

        logger.log(logging.INFO, f'Encoding with Bit Depth: {bit_depth}')
        logger.log(logging.INFO, "Processing Input File")

        file_byte_list = file_to_byte_list(file_path, bit_depth)
        #Check if encoder is set to tranparent only
        if bit_depth == 0:
            write_to_transparent = True
            bit_depth = 8
        print(file_byte_list[0])

        logger.log(logging.INFO, "Opening Image")

        image = Image.open(image_path)
        #Get the pixel data from the image
        logger.log(logging.INFO, "Extracting Pixel Data")

        pixels = image.getdata()
        width, height = image.size
        image_mode = image.mode
        image_size = image.size
        #Delete the image as it is no longer needed
        del(image)
        logger.log(logging.DEBUG, f'Num Pixels: {len(pixels)}')

        new_im_data = []

        byte_list_len = len(file_byte_list)

        #Check if the image is a png and if so create a list for transparency values
        #this is so we can add those values back later
        transparency = False

        if len(pixels[0]) > 3:
                transparency = True
                transparency_values = []
        colors = bytearray()
        #Turn the pixels into a list of color values 
        #and a list for transparency values if a png

        logger.log(logging.INFO, "Processing Pixel Data")
        state = "Processing Pixel Data"

        target = math.ceil(byte_list_len * 8 / 3 / bit_depth + 56)
        #If writing to transparent only get the color values from transparent pixels
        if write_to_transparent:
            progress = 0
            #Append the colors of the first 3 pixels regardless of transparency
            for x in range(3):
                for i in range(3):
                    colors.append(pixels[x][i])
                transparency_values.append(pixels[x][3])

            for x in range(3, len(pixels)):
                #Check if any more colors are needed
                if progress*8 > byte_list_len * 8 / 3 + 56:
                        break
                #check if the pixel is transparent
                elif pixels[x][3] == 0:
                    progress += 1
                    #if the pixel is transparent append the colors
                    for i in range(3):
                        colors.append(pixels[x][i])
                transparency_values.append(pixels[x][3])
        else:
            if transparency:
                for x, pixel in enumerate(pixels):
                    progress = x
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
        print(len(colors))
        target = 0
        #Encode the file into chunks to reduce memory usage
        #Make chunk_size divisible by 8 and bit_depth
        chunk_size = (CHUNK_SIZE//8)* 8 * bit_depth
        num_chunks = math.ceil(len(file_byte_list)/chunk_size)

        if bit_depth == 1:
            #For every chunk
            color_index = 0
            target = num_chunks
            for i in range(num_chunks):
                state = f'Writing Chunk {i} of {num_chunks}'
                progress = i
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
            state = "Encoding"
        elif bit_depth == 8:
            color_index = 0
            logger.log(logging.INFO, "Writing File Data to Image")
            state = "Writing File Data to Image"
            #Write the bit_depth to the first 3 color values with bit_depth of 1
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
            target = len(file_byte_list) - 1
            for i in range(1, len(file_byte_list)):
                progress = i
                colors[color_index] = ord(file_byte_list[i])
                color_index += 1
        else:
            color_index = 0
            logger.log(logging.INFO, "Writing File Data to Image")
            #Write the bit_depth to the first 3 color values with bit_depth of 1
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
            target = num_chunks
            for i in range(num_chunks):
                state = f'Writing Chunk {i} of {num_chunks}'
                progress = i
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
                        color_bit_list[(x+1)*-1] = int(next_bit)
                    #Make a list of th evalues as strings
                    bit_list_strings = [str(int) for int in color_bit_list]
                    #Join the new bit_list_strings can cast to int
                    hold = "".join(bit_list_strings)
                    colors[color_index] = int(hold , 2)
                    color_index+=1
            state = "Encoding"
            #If the last chunk had a length that was not divisible by the
            #bit_depth we will pull one final color and append those bits
            remaining_bits = bit_list_len % bit_depth
            if remaining_bits:
                #Get the color as a string in binary
                color_bit_list = format(colors[color_index], "b")
                color_bit_list = color_bit_list.rjust(8,"0") #Pad string to 8 bits
                color_bit_list = list(color_bit_list) #Make it a list
                #rewrite bits in values equal to bitdepth starting with LSB
                for x in range(remaining_bits):
                    next_bit = bit_list[bit_list_index]
                    bit_list_index+=1
                    color_bit_list[(x+1)*-1] = int(next_bit)
                #Make a list of th evalues as strings
                bit_list_strings = [str(int) for int in color_bit_list]
                #Join the new bit_list_strings can cast to int
                hold = "".join(bit_list_strings)
                colors[color_index] = int(hold , 2)
                color_index+=1

        #Reconstruct the pixels from the colors
        logger.log(logging.INFO, "Reconstructing Pixels")
        state = "Reconstructing Pixels"
        target = len(colors)//3
        if write_to_transparent:
            color_index = 0
            #First append the first 3 pixels regardless of transparency
            for num in range(3):
                new_pixel = []
                #Append 3 Color Values
                for i in range(3):
                    new_pixel.append(colors[color_index])
                    color_index+=1
                #Append the transparency Value
                new_pixel.append(transparency_values[num])
                #Append to new_im_data as a tuple
                new_im_data.append(tuple(new_pixel))

            #Add pixels until all the new data has been added
            num = 3
            while color_index < len(colors):
                progress = color_index
                #If pixel is tranparent write new color data
                if pixels[num][3] == 0:
                    new_pixel = []
                    #Append 3 Color Values
                    for i in range(3):
                        new_pixel.append(colors[color_index])
                        color_index+=1
                    #Append the transparency Value
                    new_pixel.append(transparency_values[num])
                    #Append to new_im_data as a tuple
                    new_im_data.append(tuple(new_pixel))    
                #If pixel is not transparent append the pixel from original image
                else:
                    new_im_data.append(pixels[num])
                num+=1
        else:
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
            #Same but without the transparency append, split up for performance       
            else:
                color_index = 0
                for num in range(len(colors)//3):
                    progress = num
                    new_pixel = []
                    #Append 3 Color Values
                    for i in range(3):
                        new_pixel.append(colors[color_index])
                        color_index+=1
                    new_im_data.append(tuple(new_pixel))
        target = 0

        #Add the remaining unaltered pixels
        logger.log(logging.INFO, "Appending unaltered pixels")
        state = "Appending unaltered pixels"
        target = len(pixels) - len(new_im_data)
        for i in range(len(new_im_data), len(pixels)):
            progress = i - len(new_im_data)
            new_im_data.append(pixels[i])
        del(pixels)
        del(colors)
        target = 0
        logger.log(logging.INFO, "Writing Output File")
        output_image(new_im_data, image_mode, image_size, output_path)
        logger.log(logging.INFO, "Done")
        state = "Ready"

    except Exception as err:
        target = 0
        exception_type, exception_object, exception_traceback = sys.exc_info()
        filename = exception_traceback.tb_frame.f_code.co_filename
        line_number = exception_traceback.tb_lineno

        logger.log(logging.CRITICAL, f'Critical Error Process Aborted: \n {err}')
        logger.log(logging.CRITICAL, f'Exception type: {exception_type}')
        logger.log(logging.CRITICAL, f'File name: {filename}')
        logger.log(logging.CRITICAL, f'Line number: {line_number}')
        state = "Ready"

def decode(image_path: str, output_path: str) -> None:
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
        state = "Processing Pixel Data"
        colors = bytearray()

        #Get the color data from the first 3 pixels to retrieve the bit_depth
        for x in range(3):
            for i in range(3):
                colors.append(pixels[x][i])
        
        print(colors)
        bit_depth = []

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
        print(len(colors))
        logger.log(logging.INFO, f'Bit Depth: {bit_depth}')

        #If bit_depth is 0 we will only read from tranparent pixels
        target = len(pixels)
        transparency = False
        if bit_depth == 0:
            transparency = True
            bit_depth = 8
            for x in range(3, len(pixels)):
                progress = x
                #For each pixel check if the transparency value is 0
                #If it is append those colors to colors[]
                if pixels[x][3] == 0:
                    for i in range(3):
                        colors.append(pixels[x][i])
        else:
            #If bit_depth is not 0 read data from all pixels
            for num in range(3, len(pixels)):
                progress = num
                for i in range(3):
                    colors.append(pixels[num][i])
        target = 0
        del(pixels)
        
        logger.log(logging.INFO, "Reading Data")

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

            logger.log(logging.INFO, f'Converting File Data')
            state = "Converting File Data"
            file_data = bytearray()
            bit_list_index = 0

            target = file_length
            for i in range(file_length):
                progress = i
                hold = []
                for x in range(8):
                    hold.append(str(bit_list[bit_list_index]))
                    bit_list_index += 1
                file_data.append(int("".join(hold), 2))
            target = 0
            del(bit_list)

        elif bit_depth == 8:
            byte_list = bytearray()
            colors_offset = 0
            byte_list_index = 0

            #Get enough data to get all file information
            for i in range(1014):
                byte_list.append(colors[colors_offset])
                colors_offset += 1  
            #Read that data

            #Get the length of the file name from the first 3 bytes
            file_name_length = bytearray()
            for i in range(3):
                file_name_length.append(byte_list[byte_list_index])
                byte_list_index += 1
            file_name_length = bytes(file_name_length)
            file_name_length = int(file_name_length.decode("UTF-8"))
            logger.log(logging.INFO, f'File Name Length: {file_name_length}')

            #Read the file name
            file_name = bytearray()
            for i in range(file_name_length):
                file_name.append(byte_list[byte_list_index])
                byte_list_index += 1
            file_name = bytes(file_name)
            file_name = file_name.decode("UTF-8")
            logger.log(logging.INFO, f'File Name: {file_name}')

            #Get the file length from the next 11 bytes
            file_length = bytearray()
            for i in range(11):
                file_length.append(byte_list[byte_list_index])
                byte_list_index += 1
            file_length = bytes(file_length)
            file_length = int(file_length.decode("UTF-8"))
            logger.log(logging.INFO, f'File Length: {file_length} Bytes')

            #Get the file data from the image
            file_data = bytearray()
            #Save how many bytes we have used so far
            colors_used = 3 + file_name_length + 11
            state = "Reading File Data"
            target = file_length
            for i in range(colors_used, colors_used + file_length):
                progress = i - colors_used
                file_data.append(colors[i])
            target = 0
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
            print(file_name_length)
            file_name_length = bit_list_to_bytes(file_name_length)
            print(file_name_length)
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
            state = "Reading File Data"

            target = math.ceil(8112/bit_depth + file_length*8/bit_depth)
            for i in range(math.ceil(8112/bit_depth + file_length*8/bit_depth)+1):
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
            state = "Converting File Data"
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

def output_image(image_data: List[Tuple[int, ...]], 
                image_mode: str, 
                image_size: Tuple[int,int], 
                output_path: str
                ) -> None:
    """
    Takes a list of pixel data, creates a new image using 
    image_mode and image_size then outputs to the output path
    """
    new_image = Image.new(image_mode, image_size)
    new_image.putdata(image_data)
    new_image.save(output_path, format="PNG",)

def color_to_bit_list(color: int) -> List[str]:
    """
    Takes a color value as an int and converts it to a
    list of strings 8 characters long of its binary
    string representation.
    """
    if color > 255 or color < 0:
        raise ValueError("Input out of range: 0-255")

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
    max_size = (width*height*3*bit_depth)//8
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
    if bit_depth == 0:
        num_transparent = num_pixels_transparent(image)
        max_size = num_transparent*3
    else:
        max_size = (width*height*3*bit_depth)/8
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

def bytes_to_bit_list(byte_list: List[str], 
                    start_index: Optional[int] = None, 
                    end_index: Optional[int] = None
                    ) -> List[int]:
    """
    This function takes a list of bytes and returns a list of ints with
    values of 1 or 0. If there is an end_index given it will only
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
                    hold.insert(0, next_bit)
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
    for letter in file_size: #Append the list
        byte_list.append(letter.encode())
 
    with open(file_path, "rb") as file:
        while True:
            byte = file.read(1)
            if not byte:
                break
            byte_list.append(byte)
    return byte_list

def num_pixels_transparent(img: Image) -> int:
    """
    Takes an image and returns the number of transparent pixels
    contained within it.
    """
    pixels = img.getdata()
    num_transparent = 0
    if len(pixels[0]) < 4:
        return 0
    for pixel in pixels:
        if pixel[3] == 0:
            num_transparent+=1
    return num_transparent


if __name__ == "__main__":
    print("Run app.py")