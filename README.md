# Netherizer - Image Steganography

The Netherizer is a python based image steganography tool used for concealing files within RGB color data. Netherizer utilizes Pillow for image processing and tKinter for the GUI.
## Features
**Variable Bit Depth:** Control how much color data is overwritten starting with LSB (Least Significant Bit). Higher values allow for larger files but cause more changes to the image.  
**Transparency Write:** Only write data to transparent pixels causing no visual change in the image.  
**Auto Bit Depth:** Automatically choose the bit depth that will make the least possible change in the image.  

## How To Use
### Setup:
1. Download the Zip file [here.](https://github.com/Cmacle/Netherizer/releases/latest)
2. Extract the files and run the exe

### Encode:
1. Choose Encode
2. Select Choose Image and select the image you want to have encoded (png or jpg)
![chooseencode](https://user-images.githubusercontent.com/36272771/169583063-94aadc9d-9d16-4ce3-9477-e4e3c9f06f49.png)
3. (Optional) Change Bit Depth, This will change how much data is overwritten with file data. If unsure leave on auto and the minimum option will be chosen.
4. Choose input file by selecting Choose File, maximum input size is shown below your input image.  
![chooseinput](https://user-images.githubusercontent.com/36272771/169585975-791a0185-2f5d-469d-8848-48df2550989c.png)
5. Choose the output location and file name for the resulting encoded image.
![encodechooselocation](https://user-images.githubusercontent.com/36272771/169854403-26fb4a7a-e7c9-4184-8e79-bba926666271.png)
6. Hit encode

### Decode:
1. Choose Decode
2. Select Choose Image and select the image that has been previously encoded
![decodeselectimage](https://user-images.githubusercontent.com/36272771/169863054-5be3bfa4-716c-4575-a796-0a2967dbdd43.png)
3. Select Choose Folder and select the output folder for the encoded file
![decodechoosefolder](https://user-images.githubusercontent.com/36272771/169863655-3cc4fa13-6a5c-4d44-9a1c-b30da8759286.png)
4. Hit DECODE and the resulting file will be placed in the output folder with the original file name.
