import tkinter as tk
from ResizingCanvasObject import ResizingCanvas
from tkinter import filedialog, Scrollbar, Canvas, ttk
from tkinter.messagebox import showerror, askyesno
from tkinter import colorchooser
from PIL import Image, ImageOps, ImageTk, ImageFilter, ImageGrab
import os
import PDFtoImages
from ImageProcces import ImageProcessing

global image_index

def TODOFunc():
    pass

def open_pdf():
    global file_path, image_proccessor
    print("dirname", dirname)
    file_path = filedialog.askopenfilename(title="Open PDF File", initialdir=dirname, filetypes=[("PDF Files", "*.pdf")])#TODO initialdir
    if file_path:
        global num_pages
        num_pages = PDFtoImages.filename_to_images(file_path)
        #image_proccessor = ImageProcessing(dirname, filename, num_pages)
        open_image(image_index=0)




def open_image(image_index):
    global image, photo_image, IMAGE_HEIGHT, IMAGE_WIDTH
    if file_path:
        image = Image.open(dirname + "\\SheetsMusic\\Annotated\\annotated" + str(image_index) + ".png")
        print("image type", type(image))
        IMAGE_HEIGHT, IMAGE_WIDTH = image.size
        #new_width = int((CANVAS_WIDTH / 2))
        #image = image.resize((new_width, CANVAS_HEIGHT), Image.LANCZOS)

        image = ImageTk.PhotoImage(image)
        canvas.create_image(0, 0, anchor="nw", image=image)

def on_click(event):
    global file_path
    if file_path:
        print("x: ", event.x, "y: ", event.y)
        x, y = convert_coordinates(event.x, event.y)
        print("Converted: x:", x, " y:", y)

def scroll_vertical(event):
    canvas.yview_scroll(int(-1*(event.delta/120)), "units")

def scroll_horizontal(event):
    canvas.xview_scroll(int(-1*(event.delta/120)), "units")

def next_image(event):
    global image_index
    print("test")
    image_index = (image_index + 1) % num_pages
    open_image(image_index)

def previous_image(event):
    global image_index
    image_index = (image_index - 1) % num_pages
    open_image(image_index)

def zoom_in():
    if file_path:
        global image, photo_image, IMAGE_HEIGHT, IMAGE_WIDTH
        image = Image.open(dirname + "\\SheetsMusic\\page" + str(image_index) + ".jpg")
        IMAGE_WIDTH = int((IMAGE_WIDTH * 2))
        wpercent = (IMAGE_WIDTH / float(image.size[0]))
        IMAGE_HEIGHT = int(float(image.size[1]) * (float(wpercent)))
        image = image.resize((IMAGE_WIDTH, IMAGE_HEIGHT), Image.LANCZOS)

        image = ImageTk.PhotoImage(image)
        canvas.create_image(0, 0, anchor="nw", image=image)

def zoom_out():
    if file_path:
        global image, photo_image, IMAGE_HEIGHT, IMAGE_WIDTH
        image = Image.open(dirname + "\\SheetsMusic\\page" + str(image_index) + ".jpg")
        IMAGE_WIDTH = int((IMAGE_WIDTH / 2))
        wpercent = (IMAGE_WIDTH / float(image.size[0]))
        IMAGE_HEIGHT = int(float(image.size[1]) * (float(wpercent)))
        image = image.resize((IMAGE_WIDTH, IMAGE_HEIGHT), Image.LANCZOS)

    image = ImageTk.PhotoImage(image)
    canvas.create_image(0, 0, anchor="nw", image=image)

def convert_coordinates(x, y):
    global IMAGE_WIDTH, IMAGE_HEIGHT, image, canvas
    cavnas.yview



dirname = os.path.dirname(__file__)
print("DIR: ", dirname)
screen_size = (1280, 720)
screen_start = (0, 0)
filename = dirname + "\\Georgia on My Mind.pdf"
CANVAS_WIDTH = 750
CANVAS_HEIGHT = 560
FRAME_WIDTH = 200
FRAME_HEIGHT = 600
file_path = ""
image = 0
image_index = 0
num_notes = 0
num_accidentals = 0
IMAGE_WIDTH = 0
IMAGE_HEIGHT = 0





#Display images
#Change image being displayed with button pressed
#Zoom in and out: buttons and mouse wheel
#Get coordinates of mouse on click and on unclick

root = tk.Tk()
root.title("EasySheets") #TODO get name


screen_size_string = "" + str(screen_size[0]) + "x" + str(screen_size[1]) + "+" + str(screen_start[0]) + "+" + str(screen_start[1])
root.geometry(screen_size_string)
#root.resizable(0, 0)#prevents user from resizing window: TODO based of window resizing, resize canvas

#icon = tk.PhotoImage(file='icon.png') TODO add icon photo
#root.iconphoto(False, icon)

#Left frame
left_frame = tk.Frame(root, width=FRAME_WIDTH, height=FRAME_HEIGHT)
left_frame.pack(side="left", fill="y")


#Right image canvas
canvas = tk.Canvas(root, width=CANVAS_WIDTH, height=CANVAS_HEIGHT)
canvas.pack(fill="both", expand=True)


canvas.bind("<Button-1>", on_click)
canvas.bind("<MouseWheel>", scroll_vertical)
canvas.bind("<Shift-MouseWheel>", scroll_horizontal)
root.bind("<Right>", next_image)
root.bind("<Left>", previous_image)
canvas.configure(scrollregion = canvas.bbox("all"))

# Create the vertical scrollbar
scrollbar_vertical = tk.Scrollbar(root, orient=tk.VERTICAL, command=canvas.yview)
scrollbar_vertical.pack(side=tk.RIGHT, fill=tk.Y)

# Create the horizontal scrollbar
scrollbar_horizontal = tk.Scrollbar(root, orient=tk.HORIZONTAL, command=canvas.xview)
scrollbar_horizontal.pack(side=tk.BOTTOM, fill=tk.X)

# Configure the canvas to use the scrollbars
canvas.configure(yscrollcommand=scrollbar_vertical.set, xscrollcommand=scrollbar_horizontal.set)



#Drop down menu label
label = tk.Label(left_frame, text="Feature Select:", background="white")
label.pack(padx=0, pady=2)

#Drop down menu TODO change frame buttons depending on feature selection
feature_selections = ["Staff Lines", "Treble Clef", "Bass Clef", "Note", "Double Sharp", "Sharp", "Natural", "Flat", "Double Flat"]
feature_combobox = ttk.Combobox(left_frame, values=feature_selections, width=15)
feature_combobox.pack(padx=10,pady=5)
#feature_combobox.bind("<<ComboboxSelected>>", lambda event: ) TODO bind combobox to features button

#Button icons
plus_icon = tk.PhotoImage(file=dirname + "\\Icons\\plus.png").subsample(12,12)
minus_icon =tk.PhotoImage(file=dirname + "\\Icons\\minus.png").subsample(12,12)
save_icon = tk.PhotoImage(file=dirname + "\\Icons\\save.png").subsample(12,12)
open_image_icon = tk.PhotoImage(file=dirname + "\\Icons\\open_image.png").subsample(12, 12)
add_feature_icon = tk.PhotoImage(file=dirname + "\\Icons\\add_feature.png").subsample(12,12)#TODO a button for each feature
erase_icon = tk.PhotoImage(file=dirname + "\\Icons\\erase.png").subsample(12,12)
generate_icon = tk.PhotoImage(file=dirname + "\\Icons\\generate.png").subsample(12,12)

#Buttons
add_feature_button = tk.Button(left_frame, image=add_feature_icon, command=TODOFunc)
add_feature_button.pack(pady=5)

generate_button = tk.Button(left_frame, image=generate_icon, command=TODOFunc)
generate_button.pack(pady=5)

erase_button = tk.Button(left_frame, image=erase_icon, command=TODOFunc)
erase_button.pack(pady=5)

zoomin_button = tk.Button(left_frame, image=plus_icon, command=zoom_in)
zoomin_button.pack(pady=5)

zoomout_button = tk.Button(left_frame, image=minus_icon, command=zoom_out)
zoomout_button.pack(pady=5)

save_button = tk.Button(left_frame, image=save_icon)
save_button.pack(pady=5)

open_image_button = tk.Button(left_frame, image=open_image_icon,  command=open_pdf)
open_image_button.pack(pady=5)




root.mainloop()