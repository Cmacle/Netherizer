import os
from PIL import Image

def encode(image_path, file_path, bit_depth, output_path):
    """
    This will take the input image and file to be hidden within
    the input image. It will then overwrite LSB pixel data in
    ascending order according to the bit_depth. With lower values
    having less impact on the image and having less data capacity.
    """
    file_byte_list = file_to_byte_list(file_path, bit_depth)
    #byte_list_to_file(file_byte_list, "")
    image = Image.open(image_path)
    pixels = image.getdata()
    print(len(pixels))
    print(pixels[0])
    width, height = image.size
    if os.path.getsize(file_path) <= max_input_size(width, height, bit_depth, len(os.path.basename(file_path))):
        new_im_data = []
        bit_list = bytes_to_bit_list(file_byte_list)

        if bit_depth == 1:
            index = 0
            bit_list_len = len(bit_list)
            bit_list_index = 0
            transparency = False
            pixel_index = 0
            if len(pixels[0]) > 3:
                transparency = True
            while bit_list_index+1 < bit_list_len:
                pixel = pixels[pixel_index]
                pixel_index+=1
                new_pixel = []
                for num in range(3):
                    color = pixel[num]
                    #check if there are any bits left to write
                    if bit_list_index+1 < bit_list_len:
                        next_bit = bit_list[bit_list_index]
                        bit_list_index+=1
                    else:
                        break
                    next_bit_even = next_bit%2==0
                    color_value_even = color%2==0
                    if next_bit_even == color_value_even: 
                        #if both the next bit and color value are even
                        #add the number as is
                        new_pixel.append(color)
                    elif next_bit_even:
                        new_pixel.append(color-1)
                    else:
                        new_pixel.append(color+1)
                if transparency:
                    new_pixel.append(pixel[3])
                new_im_data.append(tuple(new_pixel))
                
            #Add all the pixels that don't need to be changed to the list
            last_pixel = len(new_im_data)
            for i in range(last_pixel,len(pixels)):
                new_im_data.append(pixels[i])
                #print(f'{i}::{pixels_length}')
        else:
            index = 0
            bit_list_len = len(bit_list)
            bit_list_index = 0
            transparency = False
            #Start with the 4th pixel, the first 3 are used for bitdepth
            pixel_index = 3
            out_of_bits = False

            if len(pixels[0]) > 3:
                transparency = True
            #Append the first 8 bits the same way as with a bit depth of 1
            for x in range(3):
                pixel = pixels[x]
                new_pixel = []
                for num in range(3):
                    color = pixel[num]
                    if bit_list_index < 8:
                        next_bit = bit_list[bit_list_index]
                        bit_list_index+=1
                    else:
                        new_pixel.append(color)
                        break
                    next_bit_even = next_bit%2==0
                    color_value_even = color%2==0
                    if next_bit_even == color_value_even: 
                        #if both the next bit and color value are even
                        #add the number as is
                        new_pixel.append(color)
                    elif next_bit_even:
                        new_pixel.append(color-1)
                    else:
                        new_pixel.append(color+1)
                if transparency:
                    new_pixel.append(pixel[3])
                new_im_data.append(tuple(new_pixel))
            #Now handle the rest of the pixels and data with the new method
            while bit_list_index+1 < bit_list_len:
                pixel = pixels[pixel_index]
                pixel_index+=1
                new_pixel = []
                for num in range(3):
                    #check if out of bits
                    if out_of_bits:
                        break
                    #get the color
                    color = pixel[num]
                    #get the color as a bitstring then turn it into a list
                    color_bit_list = format(color, "b")
                    color_bit_list = color_bit_list.rjust(8, "0") #Pad the string to 8 characters
                    color_bit_list = list(color_bit_list)
                    #rewrite bits in values equal to bitdepth starting with LSB
                    for x in range(bit_depth):
                        #check for remaining bits
                        if bit_list_index+1 < bit_list_len:
                            next_bit = bit_list[bit_list_index]
                            bit_list_index+=1
                        else:
                            out_of_bits = True
                            break
                        color_bit_list[(x+1)*-1] = next_bit
                    #Make a list of the values as strings
                    bit_list_strings = [str(int) for int in color_bit_list]
                    #Join the new bit_list into a string then cast to an int
                    color = "".join(bit_list_strings)
                    color = int(color , 2)
                    new_pixel.append(color)
                if transparency:
                    new_pixel.append(pixel[3])
                new_im_data.append(tuple(new_pixel))        
                        
            #Add all the pixels that don't need to be changed to the list
            last_pixel = len(new_im_data)
            for i in range(last_pixel,len(pixels)):
                new_im_data.append(pixels[i])

        output_image(new_im_data, image, output_path)
        print("Done")

def decode(image_path, output_path):
    """
    This will take an image that has been encoded previously and
    output the file that was encoded into the image to the output_path.
    """
    image = Image.open(image_path)
    pixels = image.getdata()
    colors = []
    #create a list for the color values from every pixel
    for pixel in pixels:
        for i in range(3):
            colors.append(pixel[i])
    bit_depth = []
    print("DECODING")
    #Get the Bit Depth from the first 8 color values
    for i in range(8):
        color = colors.pop(0)
        if len(bit_depth) < 8:
            if color%2==0:
                bit_depth.append("0")
            else:
                bit_depth.append("1")
    bit_depth = bit_list_to_byte_list(bit_depth)
    bit_depth = int(bit_depth.decode('UTF-8'))
    print(f'Bit Depth: {bit_depth}')
    
    if bit_depth == 1:
        file_name_length = []#Make a list for the file name length
        for i in range(24):
            color = colors.pop(0)
            if color%2==0:
                file_name_length.append("0")
            else:
                file_name_length.append("1")
        file_name_length = bit_list_to_byte_list(file_name_length)
        file_name_length = int(file_name_length.decode('UTF-8'))
        print(f'File Name Length: {file_name_length}')
        #Get the file name from the data
        file_name = []
        #Get 8 bits for each character starting from the 16th
        for i in range(file_name_length*8):
            color = colors.pop(0)
            if color%2==0:
                file_name.append("0")
            else:
                file_name.append("1")
        file_name = bit_list_to_byte_list(file_name)
        file_name = file_name.decode('UTF-8')
        print(f'File Name: {file_name}')
        #Get the file length
        file_length = []
        for i in range(88):
            color = colors.pop(0)
            if color%2==0:
                file_length.append("0")
            else:
                file_length.append("1")
        file_length = bit_list_to_byte_list(file_length)
        file_length = int(file_length.decode('UTF-8'))
        print(f'File Length: {file_length} Bytes')
        #Get the file information
        file_data = []
        hold = file_length*8
        for i in range(file_length*8):
            color = colors[i]
            file_data.append(str(color%2))
            #print(f'{i} : {i/hold*100}%')
        file_data = bit_list_to_byte_list(file_data)
        #Write the data to a file
        output_location = os.path.join(output_path, file_name)
        with open(output_location, "wb") as file:
            print("Writing bytes to file:  ")
            file.write(file_data)
        print("Done")
    else:
        bit_list = []
        #get the bit list for the entire image
        for color in colors:
            #get the color as a bitstring then turn it into a list
            color_bit_list = format(color, "b")
            color_bit_list = color_bit_list.rjust(8, "0") #Pad the string to 8 characters
            color_bit_list = list(color_bit_list)
            #Now read values equal to the bit_depth
            for x in range(bit_depth):
                bit_list.append(str(color_bit_list[(x+1)*-1]))
        #Now we start parsing the data
        bit_list_index = bit_depth #offset the index to account for the unused color in pixel 3 during encode
        
        file_name_length = [] #Make a list for the file_name_length
        #get 3 bytes of data
        for i in range(24):
            file_name_length.append(bit_list[bit_list_index])
            bit_list_index += 1
        file_name_length = bit_list_to_byte_list(file_name_length)
        file_name_length = int(file_name_length.decode('UTF-8'))
        print(f'File Name Length: {file_name_length}')

        #Get the file name from the data
        file_name = []
        #Get 8 bits for each character starting from the 16th
        for i in range(file_name_length*8):
            file_name.append(bit_list[bit_list_index])
            bit_list_index += 1
        file_name = bit_list_to_byte_list(file_name)
        file_name = file_name.decode('UTF-8')
        print(f'File Name: {file_name}')

        #Get the file length
        file_length = []
        for i in range(88):
            file_length.append(bit_list[bit_list_index])
            bit_list_index += 1
        file_length = bit_list_to_byte_list(file_length)
        file_length = int(file_length.decode('UTF-8'))
        print(f'File Length: {file_length} Bytes')

        #Get the file information
        file_data = []
        for i in range(file_length*8):
            file_data.append(bit_list[bit_list_index])
            bit_list_index += 1
        file_data = bit_list_to_byte_list(file_data)
        #Write the data to a file
        output_location = os.path.join(output_path, file_name)
        with open(output_location, "wb") as file:
            print("Writing bytes to file:  ")
            file.write(file_data)
        print("Done")

def output_image(image_data, image, output_path):
    new_image = Image.new(image.mode, image.size)
    new_image.putdata(image_data)
    new_image.save(output_path, format="PNG")

def max_input_size(width, height, bit_depth, file_name_length = None):
    #This will calculate the largest possible file that can be encoded
    #The file_name_length is optional
    max_size = (width*height*3*bit_depth)/8
    if file_name_length:
        max_size -= file_name_length
    return max_size

def max_input_size_from_path(path, bit_depth):
    image = Image.open(path)
    width, height = image.size
    max_size = (width*height*3*bit_depth)/8
    max_size = max_size - len(os.path.basename(path))
    return max_size

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

    binary_string = ""
    for index in range(4):
        #Get the next byte and turn it into a binary string
        next_byte = format(int(byte_list.pop(0).decode()), "b")
        next_byte = next_byte.rjust(8, "0") #Pad the string to 8 characters
        binary_string = binary_string + next_byte
    file_length = int(binary_string, 2)
    print(f'File Length: {file_length}')

    with open(file_name, "wb") as file:
        print("Writing bytes to file:  ")
        while byte_list:
            file.write(byte_list.pop(0))

def bit_list_to_byte_list(bit_list):
    #This takes a list of bits and returns a list of bytes
    #input length must be divisible by 8
    bit_string = "".join(bit_list)
    return int(bit_string, 2).to_bytes(len(bit_string) // 8, byteorder='big')
            
def int_to_byte(x):
    #Turns an int into a string then a byte
    return str(x).encode()

def bytes_to_bit_list(byte_list):
    bit_list = []
    for byte in byte_list:
        hold = []
        for i in range(8):
                hold.insert(0, (byte[0] >> i) & 1)
        for bit in hold:
            bit_list.append(bit)
    return bit_list

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
    print(file_name)
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
    encode("test/HighResCat.jpg", "test/200w.gif", 8, "output.png")
    decode("output.png", "")
    pass