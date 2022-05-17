# Netherizer - Image Steganography

The Netherizer is a python based image steganography tool used for concealing files within RGB color data. Netherizer utilizes Pillow for image processing and tKinter for the GUI.
## Features
**Variable Bit Depth:** Control how much color data is overwritten starting with LSB (Least Significant Bit). Higher values allow for larger files but cause more changes to the image. If uncertain leave on Auto and the program will use the lowest possible bit depth.
**Transparency Write:** Only write data to transparent pixels causing no noticeable change in the image.
