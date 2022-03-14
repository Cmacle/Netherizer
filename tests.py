import unittest
import steg

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

if __name__ == '__main__':
    unittest.main()