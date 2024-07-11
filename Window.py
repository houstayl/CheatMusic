import tkinter as tk
import cv2 as cv
from tkinter import filedialog, Canvas, Scale, ttk
from PIL import Image, ImageTk, ImageDraw
import os
import PDFtoImages
from ImageProcces import ImageProcessing
from FeatureObject import Feature
import multiprocessing
import cv2 as cv
import numpy as np


"""
TODO
Better drawing. Drawing that isnt region dependent
Removing adjacent matches
Save pdf
Better note detection: use png
#TODO when deleting, delete from region and imageProcessor list
only use top and bottom staffline
adding and editing staff lines
barline detection
Clear out annotated and images folder at start
On click release starting even though no rect
when opening a new file, reset everything
image rotation
save not only as pdf, but binary file for later editing
multiprocessing generate regions
key: regions and no regions

"""

class ImageEditor(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Image Editor")
        self.dirname = os.path.dirname(__file__)

        #Left frame
        self.left_frame = tk.Frame(self, width=300, height=800)
        self.left_frame.pack(side="left", fill="y")

        #Generate stafflines label
        self.generate_stafflines_label = tk.Label(self.left_frame, text="Generate Regions")
        self.generate_stafflines_label.pack(pady=5)
        self.generate_stafflines_label.bind("<Button-1>", self.generate_regions)

        #TODO set key
        #Show selected feature label
        self.selected_label_text = tk.StringVar()
        self.current_feature_type = "treble_clef"
        self.current_feature = None
        self.selected_label_text.set("Current Feature Selected: \n " + self.current_feature_type)
        self.feature_mode_add = True #fasle for remove
        self.selected_label = tk.Label(self.left_frame, textvariable=self.selected_label_text)#"Current Feature Selected: \n " + self.current_feature_type)
        self.selected_label.pack(pady=5)
        self.selected_label.bind("<Button-1>", lambda e:self.todofunc)

        #Staff line error scale
        self.staff_line_error_scale = Scale(self.left_frame, from_=0, to=42, label="Staff line error", command=self.generate_staff_lines)#todo regenerate and redraw staff lines
        self.staff_line_error_scale.set(5)
        self.staff_line_error_scale.pack()

        #Feature Error Scale
        self.feature_error_scale = Scale(self.left_frame, from_=0, to=42, label="Current feature error")
        self.feature_error_scale.set(5)
        self.feature_error_scale.pack()

        #Setting how the features will be added to just the current page, all pages, or the current and next pages
        self.add_mode_label = tk.Label(self.left_frame, text="Feature add mode:")
        self.add_mode_label.pack()
        self.add_mode_combobox_values = ["Current page and next pages", "Current Page", "All pages", "Single"]
        self.add_mode_combobox = ttk.Combobox(self.left_frame, state="readonly", values=self.add_mode_combobox_values)
        self.add_mode_combobox.current(0)
        self.add_mode_combobox.pack()

        #Setting the key
        self.key_label = tk.Label(self.left_frame, text="Key:")
        self.key_label.pack()
        self.key_combobox_values = ["None","1 sharp", "2 sharps", "3 sharps", "4 sharps", "5 sharps", "6 sharps", "1 flat", "2 flats", "3 flats", "4 flats", "5 flats", "6 flats"]
        self.key_combobox = ttk.Combobox(self.left_frame, state="readonly", values=self.key_combobox_values)
        self.key_combobox.current(0)
        self.key_combobox.pack()

        #Setting the add mode
        #editing_mode stores current state of edit
        self.editing_mode_label = tk.Label(self.left_frame, text="Editing Mode: ")
        self.editing_mode_label.pack()
        self.editing_modes = ["add", "edit"]
        self.editing_mode = tk.StringVar()
        self.editing_mode.set(self.editing_modes[0])
        self.add_mode_radio_button = ttk.Radiobutton(self.left_frame, text="Add", variable=self.editing_mode, value=self.editing_modes[0], command=self.set_mode)
        self.add_mode_radio_button.pack()
        self.edit_mode_radio_button = ttk.Radiobutton(self.left_frame, text="Edit", variable=self.editing_mode, value=self.editing_modes[1], command=self.set_mode)
        self.edit_mode_radio_button.pack()

        self.editing_mode_corner = tk.StringVar()
        self.editing_mode_corner_values = ["topleft", "bottomright", "topright", "bottomleft"]
        self.editing_mode_corner.set(self.editing_mode_corner_values[0])
        self.topleft_corner_radio_button = ttk.Radiobutton(self.left_frame, text="TopLeft corner", variable=self.editing_mode_corner, value=self.editing_mode_corner_values[0], command=self.set_corner)
        self.topleft_corner_radio_button.pack()
        self.bottomright_corner_radio_button = ttk.Radiobutton(self.left_frame, text="Bottomright corner", variable=self.editing_mode_corner, value=self.editing_mode_corner_values[1], command=self.set_corner)
        self.bottomright_corner_radio_button.pack()
        self.topright_corner_radio_button = ttk.Radiobutton(self.left_frame, text="Topright corner",variable=self.editing_mode_corner,value=self.editing_mode_corner_values[2],command=self.set_corner)
        self.topright_corner_radio_button.pack()
        self.bottomleft_corner_radio_button = ttk.Radiobutton(self.left_frame, text="Bottomleft corner",variable=self.editing_mode_corner,value=self.editing_mode_corner_values[3],command=self.set_corner)
        self.bottomleft_corner_radio_button.pack()

        #TODO editing mode: position of size editing


        #Filtering what is displayted
        self.filter_label = tk.Label(self.left_frame, text="Filter: ")
        self.filter_label.pack()
        self.filter_list = []
        for i in range(9):
            self.filter_list.append(tk.IntVar())
            self.filter_list[i].set(1)
        self.staff_line_check_button = tk.Checkbutton(self.left_frame, text="Staff Lines", onvalue=1, offvalue=0,
                                                       variable=self.filter_list[0], command=self.set_filter)
        self.staff_line_check_button.pack()
        self.implied_line_check_button = tk.Checkbutton(self.left_frame, text="Implied Lines", onvalue=1, offvalue=0,
                                                      variable=self.filter_list[1], command=self.set_filter)
        self.implied_line_check_button.pack()
        self.bass_clef_check_button = tk.Checkbutton(self.left_frame, text="Bass Clefs", onvalue=1, offvalue=0, variable=self.filter_list[2], command=self.set_filter)
        self.bass_clef_check_button.pack()
        self.treble_clef_check_button = tk.Checkbutton(self.left_frame, text="Treble Clefs", onvalue=1, offvalue=0,
                                                     variable=self.filter_list[3], command=self.set_filter)
        self.treble_clef_check_button.pack()
        self.barline_check_button = tk.Checkbutton(self.left_frame, text="Barlines", onvalue=1, offvalue=0,
                                                       variable=self.filter_list[4], command=self.set_filter)
        self.barline_check_button.pack()
        self.note_check_button = tk.Checkbutton(self.left_frame, text="Notes", onvalue=1, offvalue=0,
                                                       variable=self.filter_list[5], command=self.set_filter)
        self.note_check_button.pack()
        self.accidental_check_button = tk.Checkbutton(self.left_frame, text="Accidentals", onvalue=1, offvalue=0,
                                                       variable=self.filter_list[6], command=self.set_filter)
        self.accidental_check_button.pack()
        self.region_borders_check_button = tk.Checkbutton(self.left_frame, text="Region Borders", onvalue=1, offvalue=0,
                                                      variable=self.filter_list[7], command=self.set_filter)
        self.region_borders_check_button.pack()

        self.colored_note_check_button = tk.Checkbutton(self.left_frame, text="Colored Notes", onvalue=1, offvalue=0,
                                                      variable=self.filter_list[7], command=self.set_filter)
        self.colored_note_check_button.pack()






        #Image canvas
        self.canvas = Canvas(self, bg="gray")
        self.canvas.pack(fill="both", expand=True)

        #Scrollbars form image canvas
        self.vbar = tk.Scrollbar(self.canvas, orient=tk.VERTICAL, command=self.canvas.yview)
        self.vbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.hbar = tk.Scrollbar(self.canvas, orient=tk.HORIZONTAL, command=self.canvas.xview)
        self.hbar.pack(side=tk.BOTTOM, fill=tk.X)

        #Canvas Inputs
        self.canvas.config(yscrollcommand=self.vbar.set, xscrollcommand=self.hbar.set)
        self.canvas.bind("<ButtonPress-1>", self.on_button_press)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_button_release)
        self.canvas.bind("<MouseWheel>", self.scroll_vertical)
        self.canvas.bind("<Shift-MouseWheel>", self.scroll_horizontal)

        #Changing the current image
        self.bind("<Left>", self.left_key_press)
        self.bind("<Right>", self.right_key_press)
        self.bind("<Up>", self.up_key_press)
        self.bind("<Down>", self.down_key_press)

        self.bind("<Key>", self.keypress)
        #self.bind("<Key>", self.keypress)


        self.image_processor = None
        self.num_pages = 0
        self.image = None
        self.image_index = 0
        self.image_height = 0
        self.image_width = 0
        self.photo = None
        self.rect = None
        self.rect_start = None
        self.scale = 1.0

        #Menu bar
        self.menu = tk.Menu(self)
        self.config(menu=self.menu)

        #File menu TODO save as pdf
        file_menu = tk.Menu(self.menu, tearoff=0)
        self.menu.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Open", command=self.open_pdf)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.quit)

        #View menu for zoom in and out
        view_menu = tk.Menu(self.menu, tearoff=0)
        self.menu.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Zoom In", command=self.zoom_in)
        view_menu.add_command(label="Zoom Out", command=self.zoom_out)

        #Staff line menu
        staff_line_menu = tk.Menu(self.menu, tearoff=0)
        self.menu.add_cascade(label="Staff Lines", menu=staff_line_menu)
        staff_line_menu.add_command(label="Staff line", command=lambda :self.set_feature_type("staff_line"))
        staff_line_menu.add_command(label="Show implied lines", command=self.todofunc)

        #Bass clef menu
        bass_clef_menu = tk.Menu(self.menu, tearoff=0)
        self.menu.add_cascade(label="Bass Clef", menu=bass_clef_menu)
        bass_clef_menu.add_command(label="Bass Clef", command=lambda :self.set_feature_type("bass_clef"))#TODO bass clef or b

        #Treble clef menu
        treble_clef_menu = tk.Menu(self.menu, tearoff=0)
        self.menu.add_cascade(label="Treble Clef", menu=treble_clef_menu)
        treble_clef_menu.add_command(label="Treble Clef", command=lambda :self.set_feature_type("treble_clef"))

        #Barline menu
        barline_menu = tk.Menu(self.menu, tearoff=0)
        self.menu.add_cascade(label="Barline", menu=barline_menu)
        barline_menu.add_command(label="Barline", command=lambda :self.set_feature_type("barline"))

        #Note menu
        note_menu = tk.Menu(self.menu, tearoff=0)
        self.menu.add_cascade(label="Notes", menu=note_menu)
        note_menu.add_command(label="Note", command=lambda :self.set_feature_type("note"))

        #Accidental menu
        accidental_menu = tk.Menu(self.menu, tearoff=0)
        self.menu.add_cascade(label="Accidentals", menu=accidental_menu)
        accidental_menu.add_command(label="Double Flat", command=lambda :self.set_feature_type("double_flat"))
        accidental_menu.add_command(label="Flat", command=lambda :self.set_feature_type("flat"))
        accidental_menu.add_command(label="Natural", command=lambda :self.set_feature_type("natural"))
        accidental_menu.add_command(label="Sharp", command=lambda :self.set_feature_type("sharp"))
        accidental_menu.add_command(label="Double Sharp", command=lambda :self.set_feature_type("double_sharp"))


    def set_filter(self):
        print("Filter values: ", end =" ")
        for i in self.filter_list:
            print(i.get(), end=" ")
        print()
        self.draw_image_with_filters()

    def set_mode(self):
        print("current mode: ", self.editing_mode.get())

    def set_corner(self):
        print("current corner: ", self.editing_mode_corner.get())

    def get_loop_array_based_on_feature_mode(self):
        if self.add_mode_combobox.get() == self.add_mode_combobox_values[0]:#current page and next
            return range(self.image_index, self.num_pages, 1)
        if self.add_mode_combobox.get() == self.add_mode_combobox_values[1]:#Current page
            return [self.image_index]
        if self.add_mode_combobox.get() == self.add_mode_combobox_values[2]:#all pages
            return range(self.num_pages)
        if self.add_mode_combobox.get() == self.add_mode_combobox_values[3]:#single feature, no match_template
            return

    def generate_staff_lines(self, event):
        value = self.staff_line_error_scale.get()
        for i in self.get_loop_array_based_on_feature_mode():
            self.image_processor.get_stafflines(page_index=i, error=value)
            self.image_processor.draw_stafflines(page_index=i)
            #TODO replace with self.draw_image_with_filters(self.filters)

    def generate_regions(self, event):
        print("Generating Regions")
        for i in self.get_loop_array_based_on_feature_mode():
            self.image_processor.sort_clefs(i, error=100)
            self.image_processor.get_clef_regions(i)
            self.image_processor.remove_adjacent_matches(self.image_processor.barlines[i], error=300)
            self.image_processor.sort_barlines(i, error=30)
            self.image_processor.split_regions_by_bar(i)
            self.image_processor.find_notes_and_accidentals_in_region(i)
            if self.image_processor.regions[i] != None:
                for region in self.image_processor.regions[i]:
                    region.fill_implied_lines(self.image_processor.staff_lines[i])
                    region.autosnap_notes_and_accidentals()
                    region.find_accidental_for_note()
                    #print("region: ", region)
            #self.image_processor.draw_regions(i)
            self.draw_image_with_filters()
        self.display_image()

    def set_feature_type(self, feature_name):
        self.current_feature_type = feature_name
        self.selected_label_text.set("Current Feature Selected: \n " + self.current_feature_type)
        print("Feature: ", self.current_feature_type, "Mode: ", self.editing_mode.get())



    def keypress(self, event):
        #TODO wasd to move rectancle
        print("char: ", event)
        c = event.char
        #if self.editing_mode.get() == self.editing_modes[0]:#add mode
        if c == 'i' or c == 'I':
            self.zoom_in()
        if c == 'o' or c == "O":
            self.zoom_out()
        if self.editing_mode.get() == "edit":
            if self.current_feature is not None:
                if c == 'a' or c == "A":
                    self.current_feature.set_letter('a')
                if c == 'b' or c == "B":
                    self.current_feature.set_letter('b')
                if c == 'c' or c == "C":
                    self.current_feature.set_letter('c')
                if c == 'd' or c == "D":
                    self.current_feature.set_letter('d')
                if c == 'e' or c == "E":
                    self.current_feature.set_letter('e')
                if c == 'f' or c == "F":
                    self.current_feature.set_letter('f')
                if c == 'g' or c == "G":
                    self.current_feature.set_letter('g')
                if c == 'x' or c == "X":#DELETE
                    self.image_processor.remove_feature(self.current_feature, self.image_index)
                    print("deleted feature")
                    self.current_feature = None
                    self.draw_image_with_filters()
                    self.display_image()
                if c == 'm' or c == "M":#CHANGE mode BETWEEN position and size
                    pass
                if c == '1':
                    self.current_feature.set_accidental("double_sharp")
                if c == '2':
                    self.current_feature.set_accidental("sharp")
                if c == '3':
                    self.current_feature.set_accidental("natural")
                if c == '4':
                    self.current_feature.set_accidental("flat")
                if c == '5':
                    self.current_feature.set_accidental("double_flat")

        if self.editing_mode.get() == "add":
            if c == 'b' or c == "B":
                self.set_feature_type("bass_clef")
            if c == 't' or c == "T":
                self.set_feature_type("treble_clef")
            if c == 'n' or c == "N":
                self.set_feature_type("note")
            if c == 'v' or c == "V":
                self.set_feature_type("barline")
            if c == '1':
                self.set_feature_type("double_sharp")
            if c == '2':
                self.set_feature_type("sharp")
            if c == '3':
                self.set_feature_type("natural")
            if c == '4':
                self.set_feature_type("flat")
            if c == '5':
                self.set_feature_type("double_flat")
            if c == 'l' or c == "L":
                #TODO staff line
                pass


        #TODO button to change mode



    def todofunc(self, event):
        print("event", event)

    def scroll_vertical(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def scroll_horizontal(self, event):
        self.canvas.xview_scroll(int(-1 * (event.delta / 120)), "units")

    def open_pdf(self):
        file_path = filedialog.askopenfilename(title="Open PDF File", initialdir=self.dirname, filetypes=[("PDF Files", "*.pdf")])  # TODO initialdir
        if file_path:
            self.num_pages = PDFtoImages.filename_to_images(file_path)
            self.image_processor = ImageProcessing(self.dirname, file_path, self.num_pages)
            self.display_image()
    def save_pdf(self):
        pass

    def display_image(self):
        self.image = Image.open(self.dirname + "\\SheetsMusic\\Annotated\\annotated" + str(self.image_index) + ".png")
        self.photo = ImageTk.PhotoImage(
            self.image.resize((int(self.image.width * self.scale), int(self.image.height * self.scale))))
        self.canvas.create_image(0, 0, image=self.photo, anchor="nw")
        self.canvas.config(scrollregion=self.canvas.bbox(tk.ALL))

    def left_key_press(self, event):
        print("left key pressed")
        if self.editing_mode.get() == self.editing_modes[0]:#add
            self.previous_image()
        elif self.editing_mode.get() == self.editing_modes[1]:#edit
            if self.current_feature is not None:
                if self.editing_mode_corner.get() == self.editing_mode_corner_values[0]: #topleft
                    if self.current_feature.topleft[0] > 0:
                        self.current_feature.topleft = (self.current_feature.topleft[0] - 1, self.current_feature.topleft[1])
                if self.editing_mode_corner.get() == self.editing_mode_corner_values[1]:  # bottomright
                    if self.current_feature.bottomright[0] > 0 and self.current_feature.bottomright[0] > self.current_feature.topleft[0]:
                        self.current_feature.bottomright = (self.current_feature.bottomright[0] - 1, self.current_feature.bottomright[1])
                if self.editing_mode_corner.get() == self.editing_mode_corner_values[2]:  # topright
                    if self.current_feature.bottomright[0] > 0 and self.current_feature.bottomright[0] > self.current_feature.topleft[0]:
                        self.current_feature.bottomright = (self.current_feature.bottomright[0] - 1, self.current_feature.bottomright[1])
                if self.editing_mode_corner.get() == self.editing_mode_corner_values[3]:  # bottomleft
                    if self.current_feature.topleft[0] > 0:
                        self.current_feature.topleft = (self.current_feature.topleft[0] - 1, self.current_feature.topleft[1])
                print("Updated feature: ", self.current_feature)
                self.draw_image_with_filters()
                self.display_image()




    def right_key_press(self, event):
        print("right key pressed")
        if self.editing_mode.get() == self.editing_modes[0]:  # add
            self.next_image()
        elif self.editing_mode.get() == self.editing_modes[1]:  # edit
            if self.current_feature is not None:
                image_width = self.image_processor.image_widths[self.image_index]
                if self.editing_mode_corner.get() == self.editing_mode_corner_values[0]:  # topleft
                    if self.current_feature.topleft[0] < self.current_feature.bottomright[0] and self.current_feature.topleft[0] < image_width:
                        self.current_feature.topleft = (self.current_feature.topleft[0] + 1, self.current_feature.topleft[1])
                if self.editing_mode_corner.get() == self.editing_mode_corner_values[1]:  # bottomright
                    if self.current_feature.bottomright[0] < image_width:
                        self.current_feature.bottomright = (self.current_feature.bottomright[0] + 1, self.current_feature.bottomright[1])
                if self.editing_mode_corner.get() == self.editing_mode_corner_values[2]:  # topright
                    if self.current_feature.bottomright[0] < image_width:
                        self.current_feature.bottomright = (self.current_feature.bottomright[0] + 1, self.current_feature.bottomright[1])
                if self.editing_mode_corner.get() == self.editing_mode_corner_values[3]:  # bottomleft
                    if self.current_feature.topleft[0] < self.current_feature.bottomright[0] and self.current_feature.topleft[0] < image_width:
                        self.current_feature.topleft  = (self.current_feature.topleft[0] + 1, self.current_feature.topleft[1])
                print("Updated feature: ", self.current_feature)
                self.draw_image_with_filters()
                self.display_image()

    def up_key_press(self, event):
        if self.editing_mode.get() == self.editing_modes[0]:  # add
            pass
        elif self.editing_mode.get() == self.editing_modes[1]:  # edit
            if self.current_feature is not None:
                if self.editing_mode_corner.get() == self.editing_mode_corner_values[0]:  # topleft
                    if self.current_feature.topleft[1] > 0:
                        self.current_feature.topleft = (self.current_feature.topleft[0], self.current_feature.topleft[1] - 1)
                if self.editing_mode_corner.get() == self.editing_mode_corner_values[1]:  # bottomright
                    if self.current_feature.bottomright[1] > 0 and self.current_feature.bottomright[1] > self.current_feature.topleft[1]:
                        self.current_feature.bottomright = (self.current_feature.bottomright[0], self.current_feature.bottomright[1] - 1)
                if self.editing_mode_corner.get() == self.editing_mode_corner_values[2]:  # topright
                    if self.current_feature.bottomright[1] > 0 and self.current_feature.bottomright[1] > self.current_feature.topleft[1]:
                        self.current_feature.topleft = (self.current_feature.topleft[0], self.current_feature.topleft[1] - 1)
                if self.editing_mode_corner.get() == self.editing_mode_corner_values[3]:  # bottomleft
                    if self.current_feature.topleft[1] > 0:
                        self.current_feature.bottomright = (self.current_feature.bottomright[0], self.current_feature.bottomright[1] - 1)
                print("Updated feature: ", self.current_feature)
                self.draw_image_with_filters()
                self.display_image()

    def down_key_press(self, event):
        if self.editing_mode.get() == self.editing_modes[0]:  # add
            pass
        elif self.editing_mode.get() == self.editing_modes[1]:  # edit
            if self.current_feature is not None:
                image_height = self.image_processor.image_heights[self.image_index]
                if self.editing_mode_corner.get() == self.editing_mode_corner_values[0]:  # topleft
                    if self.current_feature.topleft[1] < self.current_feature.bottomright[1] and self.current_feature.topleft[1] < image_height:
                        self.current_feature.topleft = (self.current_feature.topleft[0], self.current_feature.topleft[1] + 1)
                if self.editing_mode_corner.get() == self.editing_mode_corner_values[1]:  # bottomright
                    if self.current_feature.bottomright[1] < image_height:
                        self.current_feature.bottomright = (self.current_feature.bottomright[0], self.current_feature.bottomright[1] + 1)
                if self.editing_mode_corner.get() == self.editing_mode_corner_values[2]:  # topright
                    if self.current_feature.bottomright[1] < image_height:
                        self.current_feature.topleft = (self.current_feature.topleft[0], self.current_feature.topleft[1] + 1)
                if self.editing_mode_corner.get() == self.editing_mode_corner_values[3]:  # bottomleft
                    if self.current_feature.topleft[1] < self.current_feature.bottomright[1] and self.current_feature.topleft[1] < image_height:
                        self.current_feature.bottomright = (self.current_feature.bottomright[0], self.current_feature.bottomright[1] + 1)
                print("Updated feature: ", self.current_feature)
                self.draw_image_with_filters()
                self.display_image()

    def next_image(self):
        #print("test")
        self.image_index = (self.image_index + 1) % self.num_pages
        self.draw_image_with_filters()
        self.display_image()

    def previous_image(self):
        self.image_index = (self.image_index - 1) % self.num_pages
        self.draw_image_with_filters()
        self.display_image()

    def zoom_in(self):
        self.scale *= 1.1
        self.display_image()

    def zoom_out(self):
        self.scale /= 1.1
        self.display_image()

    def draw_image_with_filters(self):
        self.image_processor.draw_image(self.filter_list, self.image_index)
        self.display_image()

    def on_button_press(self, event):
        #Has to have image loaded onto the canvas
        if self.image is not None:
            if self.editing_mode.get() == "add":
                self.rect_start = (self.canvas.canvasx(event.x), self.canvas.canvasy(event.y))
                if self.rect:
                    self.canvas.delete(self.rect)
                self.rect = None
            elif self.editing_mode.get() == "edit":
                x = self.canvas.canvasx(event.x)
                y = self.canvas.canvasx(event.y)
                x_img = int(x / self.scale)
                y_img = int(y / self.scale)
                feature = self.image_processor.find_closest_feature(self.current_feature_type, self.image_index, x_img, y_img)
                if feature is not None:
                    print("feature found: ", feature)
                    self.current_feature = feature
                    draw = ImageDraw.Draw(self.image)
                    draw.rectangle([feature.topleft[0], feature.topleft[1], feature.bottomright[0], feature.bottomright[1]], outline='red')#TODO color
                    self.display_image()
                else:
                    print("No feature in click area")

                

    def on_mouse_drag(self, event):
        curX, curY = (self.canvas.canvasx(event.x), self.canvas.canvasy(event.y))
        if self.rect:
            self.canvas.coords(self.rect, self.rect_start[0], self.rect_start[1], curX, curY)
        else:
            self.rect = self.canvas.create_rectangle(self.rect_start[0], self.rect_start[1], curX, curY, outline='red')

    def on_button_release(self, event):
        print("released")
        if self.rect:
            curX, curY = (self.canvas.canvasx(event.x), self.canvas.canvasy(event.y))
            x0, y0 = self.rect_start
            x1, y1 = curX, curY

            # Convert canvas coordinates to image coordinates
            x0_img = int(x0 / self.scale)
            y0_img = int(y0 / self.scale)
            x1_img = int(x1 / self.scale)
            y1_img = int(y1 / self.scale)

            rectangle = Feature((x0_img, y0_img), (x1_img, y1_img), x1_img - x0_img, y1_img - y0_img, self.current_feature_type)

            if self.editing_mode.get() == "add":
                template = self.image_processor.images[self.image_index][rectangle.topleft[1]:rectangle.bottomright[1],
                           rectangle.topleft[0]:rectangle.bottomright[0]]

                match_template_params = (
                    template,
                    (0, 255, 0),
                    rectangle.type,
                    10,  # error
                    True  # draw
                )
                # Prepare the arguments for each task
                tasks = [
                    (i, self.image_processor.images[i], self.image_processor.gray_images[i], match_template_params)
                    for i in self.get_loop_array_based_on_feature_mode()
                ]
                # Create a pool of worker processes
                with multiprocessing.Pool() as pool:
                    results = pool.map(ImageEditor.process_feature, tasks)
                for i in self.get_loop_array_based_on_feature_mode():
                    if self.image_processor.array_types_dict[rectangle.type][i] is None:
                        self.image_processor.array_types_dict[rectangle.type][i] = results[i]
                    else:
                        self.image_processor.array_types_dict[rectangle.type][i] = self.image_processor.array_types_dict[rectangle.type][i] + results[i]
                    self.image_processor.sort_features(self.image_processor.array_types_dict[rectangle.type][i])

                self.draw_image_with_filters()


                #TODO if staffline

                # Draw the rectangle on the actual image
                draw = ImageDraw.Draw(self.image)
                draw.rectangle([x0_img, y0_img, x1_img, y1_img], outline='red')
                self.display_image()
            elif self.editing_mode.get() == "edit":
                #todo find all features in rectangle
                pass


        else:#if rect wasnt started
            pass

    @staticmethod
    def get_distance(p1, p2):
        x2 = (p1[0] - p2[0]) * (p1[0] - p2[0])
        y2 = (p1[1] - p2[1]) * (p1[1] - p2[1])
        return (x2 + y2) ** .5

    @staticmethod
    def match_template_parallel(image, gray_image, template, color, type,
                                error=10, draw=True):
        gray_template = cv.cvtColor(template, cv.COLOR_BGR2GRAY)
        gray_template_width, gray_template_height = gray_template.shape[::-1]
        res = cv.matchTemplate(gray_image, gray_template, cv.TM_CCOEFF_NORMED)
        threshold = 0.8
        loc = np.where(res >= threshold)
        features = []
        # print("start")
        first_iteration = True
        point = 0
        for pt in zip(*loc[::-1]):
            if first_iteration == True:
                point = pt
                first_iteration = False
                f = Feature(pt, (pt[0] + gray_template_width, pt[1] + gray_template_height), gray_template_width,
                            gray_template_height, type)
                features.append(f)
                if draw == True:
                    cv.rectangle(image, pt,
                                 (pt[0] + gray_template_width, pt[1] + gray_template_height), color, 2)

            # if points are too close, skip
            # print("distance", get_distance(point, pt))
            if ImageEditor.get_distance(point, pt) < error:
                # print("skip")
                continue
            else:
                point = pt

            # print("point", pt)
            f = Feature(pt, (pt[0] + gray_template_width, pt[1] + gray_template_height), gray_template_width,
                        gray_template_height, type)
            features.append(f)
            if draw == True:
                cv.rectangle(image, pt, (pt[0] + gray_template_width, pt[1] + gray_template_height),
                             color, 2)

        return features

    @staticmethod
    def process_feature(args):
        i, image, gray_image, match_template_params = args
        print("Process ", i, "started")
        # Unpack the match_template parameters
        template, color, rect_type, error, draw = match_template_params
        features = ImageEditor.match_template_parallel(image, gray_image, template, color, rect_type, error=error,
                                                  draw=draw)
        if features is not None:
            #TODO remove adjacent matches based on feature size
            print("num features: ", len(features), "on page: ", i)

        print("Process ", i, "ended")
        return features





if __name__ == "__main__":
    app = ImageEditor()
    app.mainloop()

