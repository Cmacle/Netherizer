import io
import os
import shutil
import unittest
import steg
from PIL import Image
from os.path import exists

class StegTests(unittest.TestCase):

    def test_color_to_bit_list(self):
        self.assertEqual(steg.color_to_bit_list(0), 
                        ["0","0","0","0","0","0","0","0"])
        self.assertEqual(steg.color_to_bit_list(100), 
                        ["0","1","1","0","0","1","0","0"])
        self.assertEqual(steg.color_to_bit_list(255), 
                        ["1","1","1","1","1","1","1","1"])
        self.assertRaises(ValueError, steg.color_to_bit_list, 256)
        self.assertRaises(ValueError, steg.color_to_bit_list, -1)

    def test_max_input_size(self):
        self.assertEqual(steg.max_input_size(100,100,1), 3750)
        self.assertEqual(steg.max_input_size(59,73,4), 6460)
    
    def test_bit_list_to_bytes(self):
        self.assertEqual(steg.bit_list_to_bytes(["0","0","0","0","0","0","0","0"]),
        b'\x00')
        self.assertEqual(steg.bit_list_to_bytes(["0","1","0","0","0","0","1","1"]),
        b'C')
    
    def test_int_to_byte(self):
        self.assertEqual(steg.int_to_byte(255), b'255')
        self.assertEqual(steg.int_to_byte(153), b'153')

    def test_bytes_to_bit_list(self):
        self.assertEqual(steg.bytes_to_bit_list([b'A']),
        [0,1,0,0,0,0,0,1])
        self.assertEqual(steg.bytes_to_bit_list([b'\x00']),
        [0,0,0,0,0,0,0,0])

class EncodeDecodeTest(unittest.TestCase):
    temp_directory = ""
    temp_directory_output = ""
    def setUp(self):
        FILE_TEXT = "This is a temporary test file."
        #Create a temporary folder with a file and image to test encode and decode
        current_directory = os.getcwd()
        directory_name = "testing_temp"
        output_directory_name = "output"
        self.temp_directory = os.path.join(current_directory, directory_name)
        try:
            os.mkdir(self.temp_directory)
        except OSError:
            pass
        self.temp_directory_output = os.path.join(self.temp_directory, output_directory_name)
        try:
            os.mkdir(self.temp_directory_output)
        except OSError:
            pass
        temp_img = Image.new("RGB", (100, 100), (255, 255, 255))
        temp_img.save(os.path.join(self.temp_directory, "temp_png.png"), "PNG")

        with open(os.path.join(self.temp_directory, "temp_txt.txt"), "w") as temp_file:
            temp_file.write(FILE_TEXT)
        

    def test_encode_decode(self):
        file_path = os.path.join(self.temp_directory, "temp_txt.txt")
        image_path = os.path.join(self.temp_directory, "temp_png.png")
        output_image_path = os.path.join(self.temp_directory_output, "temp_output.png")
        output_file_path = os.path.join(self.temp_directory_output, "temp_txt.txt")
        #Run the test for each bit_depth value
        for i in range(1,9):
            #Create the encoded image
            steg.encode(image_path, file_path, i, output_image_path)
            #Decode that image
            steg.decode(output_image_path, self.temp_directory_output)
            #Compare the two output files
            with open(file_path, "r") as file1, open(output_file_path, "r") as file2:
                self.assertListEqual(
                    list(file1),
                    list(file2)
                )

    
    def tearDown(self):
        #Delete any existing temporary files
        shutil.rmtree(self.temp_directory)

        



if __name__ == '__main__':
    unittest.main()