import logging
import math
import os
import sys
from typing import List, Optional, Tuple, Union
from PIL import Image

CHUNK_SIZE = 10000

# Make a variable for updating the app UI
state = "Done"
# These two variables will be used to track progress throughout loops
# so it can be displayed to the UI periodically
progress = 0
target = 0

logger = logging.getLogger(__name__)

Image.MAX_IMAGE_PIXELS = None


def encode(image_path: str,
           file_path: str,
           bit_depth: int,
           output_path: str) -> None:
    """
    Take the input image and file to be hidden within
    the input image, output the encoded image to the output path.

    Args:
        image_path (str): The path to the image that will be encoded
        file_path (str): The path to the file that will be encoded
        bit_depth (int): How many bits of each RGB value will be overwritten
        lower values will make less impact on the image but have less data
        capacity. bit_depth 0 only writes to tranparent pixels.
        output_path (str): The output path of the resulting encoded image
    """
    # CHUNK_SIZE will control how large each chunk of data from the input
    # file will be while encoded, the value will be made made divisible by 8
    # then multiplied by the bit_depth so later loops can be simplified
    global state
    global progress
    global target
    print(f'BitDepth = {bit_depth}')
    write_to_transparent = False
    try:
        # Set the state so that a new process cannot be started
        update_state(f'Encoding with Bit Depth: {bit_depth}')
        update_state("Processing Input File")
        # Turn the input file into a bytearray that can be encoded
        file_byte_list = file_to_byte_list(file_path, bit_depth)
        # Check if encoder is set to tranparent only
        if bit_depth == 0:
            write_to_transparent = True
            bit_depth = 8
        update_state("Opening Image")
        image = Image.open(image_path)
        # Get the pixel data from the image
        update_state("Extracting Pixel Data")
        pixels = image.getdata()
        image_mode = image.mode
        image_size = image.size
        # Delete the image as it is no longer needed
        del(image)
        # Check if the image has a transparency value
        transparency = False
        if len(pixels[0]) > 3:
            transparency = True
        update_state("Processing Pixel Data")
        # Get the length of the byte_list so pixels_to_colors
        # will only get as many colors as necessary to save memory
        byte_list_len = len(file_byte_list)
        # Get a bytearray of color values from the pixels
        colors, transparency_values = pixels_to_colors(pixels,
                                                       bit_depth,
                                                       byte_list_len,
                                                       write_to_transparent,
                                                       transparency)
        # Write the file data to the colors
        update_state("Writing File Data to Image")
        write_file_to_colors(bit_depth,
                             colors,
                             file_byte_list,)
        del(file_byte_list)

        # Reconstruct the pixels from the colors
        update_state("Reconstructing Pixels")
        new_im_data = colors_to_pixels(colors,
                                       pixels,
                                       transparency_values,
                                       write_to_transparent,
                                       transparency)
        del(colors)
        # Add the remaining unaltered pixels
        update_state("Appending unaltered pixels")
        target = len(pixels)
        for i in range(len(new_im_data), len(pixels)):
            progress = i
            new_im_data.append(pixels[i])
        del(pixels)
        target = 0
        update_state("Writing Output File")
        output_image(new_im_data, image_mode, image_size, output_path)
        update_state("Done")

    except Exception as err:
        target = 0
        exception_type, exception_object, exception_traceback = sys.exc_info()
        filename = exception_traceback.tb_frame.f_code.co_filename
        line_number = exception_traceback.tb_lineno

        logger.log(logging.CRITICAL,
                   f'Critical Error Process Aborted: \n {err}')
        logger.log(logging.CRITICAL, f'Exception type: {exception_type}')
        logger.log(logging.CRITICAL, f'File name: {filename}')
        logger.log(logging.CRITICAL, f'Line number: {line_number}')
        state = "Done"


def decode(image_path: str, output_path: str) -> None:
    """
    Take an image that has previously been encoded and output
    the encoded file to the output_path.

    Args:
        image_path (str): Path to the image to be decoded
        output_path (str): Path to the directory where the file will be output
    """
    try:
        global state
        global progress
        global target

        update_state("DECODING")
        update_state(f'Opening {image_path}')
        image = Image.open(image_path)
        update_state("Extracting Pixel Data")
        pixels = image.getdata()
        # Delete the image as it is no longer needed
        del(image)
        colors = bytearray()
        # Get the color data from the first 3 pixels to retrieve the bit_depth
        for x in range(3):
            for i in range(3):
                colors.append(pixels[x][i])
        bit_depth = []
        # Get the Bit Depth from the first 8 color values
        for i in range(8):
            color = colors.pop(0)
            if len(bit_depth) < 8:
                if color % 2 == 0:
                    bit_depth.append("0")
                else:
                    bit_depth.append("1")
        bit_depth = bit_list_to_bytes(bit_depth)
        bit_depth = int(bit_depth.decode('UTF-8'))
        update_state(f'Bit Depth: {bit_depth}')

        # If bit_depth is 0 we will only read from tranparent pixels
        update_state("Processing Pixel Data")
        target = len(pixels)
        if bit_depth == 0:
            bit_depth = 8
            for x in range(3, len(pixels)):
                progress = x
                # For each pixel check if the transparency value is 0
                # If it is append those colors to colors[]
                if pixels[x][3] == 0:
                    for i in range(3):
                        colors.append(pixels[x][i])
        else:
            # If bit_depth is not 0 read data from all pixels
            for num in range(3, len(pixels)):
                progress = num
                for i in range(3):
                    colors.append(pixels[num][i])
        target = 0
        del(pixels)
        update_state("Reading Data")
        color_index = 0
        remaining_bits = bytearray()
        file_name_length, remaining_bits = read_data_from_colors(colors,
                                                                 remaining_bits,
                                                                 bit_depth,
                                                                 color_index,
                                                                 3)
        print(file_name_length)
        file_name_length = int(file_name_length.decode('UTF-8'))
        color_index += math.ceil(3*8/bit_depth)
        update_state(f'File Name Length: {file_name_length}')

        file_name, remaining_bits = read_data_from_colors(colors,
                                                          remaining_bits,
                                                          bit_depth,
                                                          color_index,
                                                          file_name_length)
        file_name = file_name.decode('UTF-8')
        color_index += math.ceil(file_name_length*8/bit_depth)
        update_state(f'File Name: {file_name}')

        file_length, remaining_bits = read_data_from_colors(colors,
                                                            remaining_bits,
                                                            bit_depth,
                                                            color_index,
                                                            11)
        file_length = int(file_length.decode('UTF-8'))
        color_index += math.ceil(11*8/bit_depth)
        update_state(f'File Length: {file_length}')

        update_state("Reading File Data")
        target = math.ceil(file_length*8/bit_depth)
        file_data, remaining_bits = read_data_from_colors(colors,
                                                          remaining_bits,
                                                          bit_depth,
                                                          color_index,
                                                          file_length)
        target = 0
        # Write the data to a file
        output_location = os.path.join(output_path, file_name)
        with open(output_location, "wb") as file:
            update_state("Writing bytes to file:  ")
            file.write(file_data)
        update_state("Done")

    except Exception as err:
        exception_type, exception_object, exception_traceback = sys.exc_info()
        filename = exception_traceback.tb_frame.f_code.co_filename
        line_number = exception_traceback.tb_lineno

        logger.log(logging.CRITICAL,
                   f'''Critical Error, Process Aborted:
Are you sure this image has been encoded? \n{err}''')
        logger.log(logging.CRITICAL, f'Exception type: {exception_type}')
        logger.log(logging.CRITICAL, f'File name: {filename}')
        logger.log(logging.CRITICAL, f'Line number: {line_number}')
        state = "Done"


def output_image(image_data: List[Tuple[int, ...]],
                 image_mode: str,
                 image_size: Tuple[int, int],
                 output_path: str
                 ) -> None:
    """
    Take a list of pixel data, creates a new image using 
    image_mode and image_size then outputs to the output path

    Args:
        image_data (List[Tuple[int, ...]]): The RGB data of the image
        image_mode (str): The mode of the new image
        image_size (Tuple[int,int]): The size of the new image
        output_path (str): The output path of the new image
    """
    new_image = Image.new(image_mode, image_size)
    new_image.putdata(image_data)
    new_image.save(output_path, format="PNG",)


def color_to_bit_list(color: int) -> List[str]:
    """
    Take a color value as an int and convert it to a
    list of strings 8 characters long of its binary
    string representation.

    Args:
        color (int): The color value as an int

    Returns:
        List[str]: Returns a list of strings 8 characters long containing
        the binary representation of the color
    """

    color_bit_list = format(color, "b")
    # Pad the string to 8 characters
    color_bit_list = color_bit_list.rjust(8, "0")
    color_bit_list = list(color_bit_list)
    return color_bit_list


def max_input_size(path: str, bit_depth: int) -> int:
    """
    Calculate the maximum input file size from the provided image path
    as well as the bit_depth.

    Args:
        path (str): The path to the image.
        bit_depth (int): The bit_depth value to calculate max
        size for.

    Returns:
        int: The maximum input file size in bytes
    """
    image = Image.open(path)
    width, height = image.size
    if bit_depth == 0:
        num_transparent = num_pixels_transparent(image)
        max_size = num_transparent*3
    else:
        max_size = (width*height*3*bit_depth)/8
    return max_size


def bit_list_to_bytes(bit_list: Union[List[str], List[int]]) -> bytes:
    """
    Take a list of bit values as ints or strings and return
    bytes. len(bit_list) must be divisible by 8

    Args:
        bit_list (List[str]): A list of bit values as strings("0" or "1")

    Returns:
        bytes: bit_list converted to bytes
    """
    global progress
    byte_array = bytearray()
    progress = 0
    for _ in range(math.ceil(len(bit_list)/8)):
        hold = []
        for _ in range(8):
            hold.append(str(bit_list[progress]))
            progress += 1
        hold = "".join(hold)
        byte_array.append(int(hold, 2))
    return byte_array


def int_to_byte(x: int) -> str:
    """
    Take an int and return a UTF-8 encoded str of the int

    Args:
        x (int): integer value

    Returns:
        str: UTF-8 encoded string
    """
    return str(x).encode()


def bytes_to_bit_list(byte_list: List[str],
                      start_index: Optional[int] = None,
                      end_index: Optional[int] = None
                      ) -> List[int]:
    """
    Take a list of bytes and return a list of ints with
    values of 1 or 0. If there is an end_index given it will only
    return the bits for the bytes within the range provided.

    Args:
        byte_list (List[str]): A list of byte values
        start_index (Optional[int], optional): Where to start in byte_list.
        Defaults to None.
        end_index (Optional[int], optional): Where to stop in byte_list
        if longer than len(byte_list) is changed to len(byte_list).
        Defaults to None.

    Returns:
        List[int]: A list of ints with value 0 or 1
    """
    bit_list = []
    if end_index:
        # Make sure the start_index is in range if not return an empty list
        if start_index >= len(byte_list):
            return bit_list
        # Make sure the end_index is in range
        # if not set it to the end of the list
        if end_index > len(byte_list):
            end_index = len(byte_list)
        # Now we will iterate over the selected elements and return them
        for i in range(start_index, end_index):
            byte = byte_list[i]
            byte = str(bin(byte))[2:]
            byte = byte.zfill(8)
            byte = list(byte)
            hold = []
            for i in range(8):
                next_bit = byte[i]
                hold.append(next_bit)
            for bit in hold:
                bit_list.append(int(bit))
    else:
        for byte in byte_list:
            byte = str(bin(byte))[2:]
            print(byte)
            byte = byte.zfill(8)
            print(byte)
            byte = list(byte)
            hold = []
            for i in range(8):
                next_bit = byte[i]
                hold.append(next_bit)
            for bit in hold:
                bit_list.append(int(bit))
    return bit_list


def file_to_byte_list(file_path: str, bit_depth: int) -> List[str]:
    """
    Take a file and return a list of UTF-8 encoded strings and file
    bytes.

    Args:
        file_path (str): Path to the file
        bit_depth (int): The bit_depth to append to the beginning

    Returns:
        List[str]: A list of UTF-8 encoded strings and bytes
    """
    global target
    global progress
    # Declare the Byte list that will be returned
    byte_list = bytearray()
    # Appends the bit depth to the list as a byte
    byte_list.append(ord(str(bit_depth)))
    # Get the file name from the path
    file_name = os.path.basename(file_path)
    # Get the length of the file name
    file_name_length = len(file_name)
    # Change to a string and pad to 3 characters
    file_name_length = str(file_name_length).rjust(3, "0")
    for character in file_name_length:
        byte_list.append(ord(character))

    for letter in file_name:  # Append the letters of the name to the list
        byte_list.append(ord(letter))

    file_size = os.path.getsize(file_path)  # Get the file size
    # Turn the file size into a string and pad it to 11 characters
    file_size = str(file_size).rjust(11, "0")
    for letter in file_size:  # Append the list
        byte_list.append(ord(letter))

    target = os.path.getsize(file_path)
    progress = 0
    with open(file_path, "rb") as file:
        while True:
            byte = file.read(1)
            progress += 1
            if not byte:
                break
            byte_list.append(int.from_bytes(byte, "big"))
    target = 0
    return byte_list


def num_pixels_transparent(img: Image) -> int:
    """
    Take an image and return the number of transparent pixels
    contained within it.

    Args:
        img (Image): The Image

    Returns:
        int: The number of transparent pixels
    """
    pixels = img.getdata()
    num_transparent = 0
    if len(pixels[0]) < 4:
        return 0
    for pixel in pixels:
        if pixel[3] == 0:
            num_transparent += 1
    return num_transparent


def pixels_to_colors(pixels: bytearray,
                     bit_depth: int,
                     byte_list_len: int,
                     write_to_transparent: bool,
                     transparency: bool) -> Tuple[bytearray, bytearray]:
    """_summary_

    Args:
        pixels (bytearray): _description_
        bit_depth (int): _description_
        byte_list_len (int): _description_
        write_to_transparent (bool): _description_
        transparency (bool): _description_

    Returns:
        Tuple[bytearray, bytearray]: _description_
    """
    global target
    global progress

    colors = bytearray()
    transparency_values = bytearray()
    target = math.ceil(byte_list_len * 8 / 3 / bit_depth + 56)
    # If writing to transparent only get the color values from
    # transparent pixels
    if write_to_transparent:
        progress = 0
        # Append the colors of the first 3 pixels regardless of transparency
        for x in range(3):
            for i in range(3):
                colors.append(pixels[x][i])
            transparency_values.append(pixels[x][3])

        for x in range(3, len(pixels)):
            # Check if any more colors are needed
            if progress*8 > byte_list_len * 8 / 3 + 56:
                break
            # Check if the pixel is transparent
            elif pixels[x][3] == 0:
                progress += 1
                # if the pixel is transparent append the colors
                for i in range(3):
                    colors.append(pixels[x][i])
            transparency_values.append(pixels[x][3])
    else:
        if transparency:
            for x, pixel in enumerate(pixels):
                progress = x
                if x*bit_depth > byte_list_len * 8 / 3 + 56:
                    break
                for i in range(3):
                    colors.append(pixel[i])
                transparency_values.append(pixel[3])
        else:
            for x, pixel in enumerate(pixels):
                progress = x
                if x*bit_depth > byte_list_len * 8 / 3 + 56:
                    break
                for color in pixel:
                    colors.append(color)
    target = 0
    return colors, transparency_values


def write_file_to_colors(bit_depth: int,
                         colors: bytearray,
                         file_byte_list: bytearray) -> None:
    """
    Write the bytes of file_byte_list to colors according to the
    bit_depth.

    Args:
        bit_depth (_type_): How many bits to overwrite on each color 1-8
        colors (_type_): The bytearray of color values
        file_byte_list (_type_): The bytearray of file data to
        write to the colors
    """
    global target
    global progress

    chunk_size = (CHUNK_SIZE//8) * 8 * bit_depth
    num_chunks = math.ceil(len(file_byte_list)/chunk_size)

    if bit_depth == 1:
        # color index is used to retain place in colors regardless of chunk
        color_index = 0
        target = num_chunks
        for i in range(num_chunks):
            progress = i
            bit_list = bytes_to_bit_list(file_byte_list,
                                         start_index=i*chunk_size,
                                         end_index=i*chunk_size+chunk_size)
            # Edit Pixel Data until all file bits have been written
            for bit in bit_list:
                color_value_even = colors[color_index] % 2 == 0

                if bit and color_value_even:
                    # if the next bit and last value of the color are different
                    # edit the color
                    colors[color_index] = colors[color_index] + 1

                elif not bit and not color_value_even:
                    colors[color_index] = colors[color_index] - 1
                color_index += 1
    elif bit_depth == 8:
        color_index = 0
        # Write the bit_depth to the first 8 color values with bit_depth of 1
        bit_list = bytes_to_bit_list(file_byte_list,
                                     start_index=0,
                                     end_index=1)
        for bit in bit_list:
            # check if there are any bits left to write
            color_value_even = colors[color_index] % 2 == 0
            if bit and color_value_even:
                # if the next bit and last value of the color are different
                # edit the color
                colors[color_index] = colors[color_index] + 1

            elif not bit and not color_value_even:
                colors[color_index] = colors[color_index] - 1
            color_index += 1
        target = len(file_byte_list) - 1
        for i in range(1, len(file_byte_list)):
            progress = i
            colors[color_index] = file_byte_list[i]
            color_index += 1
    else:
        color_index = 0
        # Write the bit_depth to the first 3 color values with bit_depth of 1
        bit_list = bytes_to_bit_list(file_byte_list,
                                     start_index=0,
                                     end_index=1)
        for bit in bit_list:
            # check if there are any bits left to write
            color_value_even = colors[color_index] % 2 == 0
            if bit and color_value_even:
                # if the next bit and last value of the color are different
                # edit the color
                colors[color_index] = colors[color_index] + 1

            elif not bit and not color_value_even:
                colors[color_index] = colors[color_index] - 1
            color_index += 1
        # Now handle the rest of the pixels and data with the new method
        target = num_chunks
        for i in range(num_chunks):
            progress = i
            bit_list = bytes_to_bit_list(file_byte_list,
                                         start_index=i*chunk_size+1,
                                         end_index=i*chunk_size+chunk_size+1)
            bit_list_len = len(bit_list)
            bit_list_index = 0
            for x in range(bit_list_len//bit_depth):

                # Get the color as a string in binary
                color_bit_list = format(colors[color_index], "b")
                # Pad string to 8 bits
                color_bit_list = color_bit_list.rjust(8, "0")
                color_bit_list = list(color_bit_list)  # Make it a list
                # rewrite bits in values equal to bitdepth starting with LSB
                for x in range(bit_depth):
                    next_bit = bit_list[bit_list_index]
                    bit_list_index += 1
                    color_bit_list[(x+1)*-1] = int(next_bit)
                # Make a list of th evalues as strings
                bit_list_strings = [str(int) for int in color_bit_list]
                # Join the new bit_list_strings can cast to int
                hold = "".join(bit_list_strings)
                colors[color_index] = int(hold, 2)
                color_index += 1
        # If the last chunk had a length that was not divisible by the
        # bit_depth we will pull one final color and append those bits
        remaining_bits = bit_list_len % bit_depth
        if remaining_bits:
            # Get the color as a string in binary
            color_bit_list = format(colors[color_index], "b")
            # Pad string to 8 bits
            color_bit_list = color_bit_list.rjust(8, "0")
            color_bit_list = list(color_bit_list)  # Make it a list
            # rewrite bits in values equal to bitdepth starting with LSB
            for x in range(remaining_bits):
                next_bit = bit_list[bit_list_index]
                bit_list_index += 1
                color_bit_list[(x+1)*-1] = int(next_bit)
            # Make a list of th evalues as strings
            bit_list_strings = [str(int) for int in color_bit_list]
            # Join the new bit_list_strings can cast to int
            hold = "".join(bit_list_strings)
            colors[color_index] = int(hold, 2)
            color_index += 1


def colors_to_pixels(colors: bytearray,
                     pixels: bytearray,
                     transparency_values: bytearray,
                     write_to_transparent: bool,
                     transparency: bool) -> List[Tuple]:
    """
    Take color values and return a list of pixels.

    Args:
        colors (bytearray): Color Values
        pixels (bytearray): Pixels from the original image
        transparency_values (bytearray): Transparency Values from
        the original image
        write_to_transparent (bool): Whether or not to only write
        to transparent pixels
        transparency (bool): Whether the original image had
        a transparency value

    Returns:
        List[Tuple]: A list of Tuples containing color values
    """
    global target
    global progress

    target = len(colors)//3
    new_im_data = []
    if write_to_transparent:
        color_index = 0
        # First append the first 3 pixels regardless of transparency
        for num in range(3):
            new_pixel = []
            # Append 3 Color Values
            for i in range(3):
                new_pixel.append(colors[color_index])
                color_index += 1
            # Append the transparency Value
            new_pixel.append(transparency_values[num])
            # Append to new_im_data as a tuple
            new_im_data.append(tuple(new_pixel))

        # Add pixels until all the new data has been added
        num = 3
        while color_index < len(colors):
            progress = color_index
            # If pixel is tranparent write new color data
            if pixels[num][3] == 0:
                new_pixel = []
                # Append 3 Color Values
                for i in range(3):
                    new_pixel.append(colors[color_index])
                    color_index += 1
                # Append the transparency Value
                new_pixel.append(transparency_values[num])
                # Append to new_im_data as a tuple
                new_im_data.append(tuple(new_pixel))
            # If pixel is not transparent append the pixel from original image
            else:
                new_im_data.append(pixels[num])
            num += 1
    else:
        if transparency:
            color_index = 0
            for num in range(len(colors)//3):
                progress = num
                new_pixel = []
                # Append 3 Color Values
                for i in range(3):
                    new_pixel.append(colors[color_index])
                    color_index += 1
                # Append the transparency Value
                new_pixel.append(transparency_values[num])
                # Append to new_im_data as a tuple
                new_im_data.append(tuple(new_pixel))
        # Same but without the transparency append, split up for performance
        else:
            color_index = 0
            for num in range(len(colors)//3):
                progress = num
                new_pixel = []
                # Append 3 Color Values
                for i in range(3):
                    new_pixel.append(colors[color_index])
                    color_index += 1
                new_im_data.append(tuple(new_pixel))
    target = 0
    return new_im_data


def read_data_from_colors(colors: bytearray,
                          remaining_bits: bytearray,
                          bit_depth: int,
                          start_index: int,
                          bytes_to_read: int) -> bytearray:
    """
    Read file data from the list of color values.

    Args:
        colors (bytearray): _description_
        remaining_bits (bytearray): _description_
        bit_depth (int): _description_
        start_index (int): _description_
        bytes_to_read (int): _description_

    Returns:
        bytearray: _description_
    """
    global progress
    global target

    byte_list = bytearray()
    bit_list = bytearray()
    for bit in remaining_bits:
        bit_list.append(bit)

    if bit_depth == 1:
        for i in range(start_index, start_index+bytes_to_read*8):
            progress = i - start_index + 1
            if colors[i] % 2 == 0:
                byte_list.append(0)
            else:
                byte_list.append(1)
        byte_list = bit_list_to_bytes(byte_list)

    elif bit_depth == 8:
        for i in range(start_index, start_index + bytes_to_read):
            progress = i - start_index
            byte_list.append(colors[i])

    else:
        for i in range(start_index, start_index + math.ceil(bytes_to_read*8/bit_depth)):
            progress = i - start_index + 1
            color_bit_list = color_to_bit_list(colors[i])
            for x in range(bit_depth):
                bit_list.append(int(color_bit_list[(x+1)*-1]))
        remaining_bits = bit_list[bytes_to_read*8: len(bit_list)]
        if len(bit_list) > 256 * 8:
            update_state("Converting File Data")
            target = bytes_to_read * 8
        byte_list = bit_list_to_bytes(bit_list[0: bytes_to_read*8])
    return byte_list, remaining_bits


def update_state(new_state: str) -> None:
    """
    Update the state value and logs that state

    Args:
        new_state (str): The new State
    """
    global state
    logger.log(logging.INFO, new_state)
    state = new_state


if __name__ == "__main__":
    print("Run app.py")
    