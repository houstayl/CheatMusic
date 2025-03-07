from pdf2image import convert_from_path
import os
import sys
def filename_to_images(dirname, filename):
    print("Converting PDF to images")
    if getattr(sys, 'frozen', False):  # Running as a PyInstaller-built executable
        poppler_path = os.path.join(sys._MEIPASS, "bin")
        images = convert_from_path(filename, poppler_path=poppler_path)
        for i in range(len(images)):
            images[i].save(dirname + '/SheetsMusic/page' + str(i) + '.jpg', 'JPEG')
        return len(images)
    else:
        images = convert_from_path(filename)
        for i in range(len(images)):
            images[i].save(dirname + '/SheetsMusic/page' + str(i) + '.jpg', 'JPEG')
        return len(images)