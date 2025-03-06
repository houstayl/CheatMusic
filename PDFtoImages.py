from pdf2image import convert_from_path

def filename_to_images(dirname, filename):
    print("Converting PDF to images")
    images = convert_from_path(filename)
    for i in range(len(images)):
        images[i].save(dirname + '/SheetsMusic/page' + str(i) + '.jpg', 'JPEG')
    return len(images)