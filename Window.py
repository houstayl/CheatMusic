import tkinter as tk
import cv2 as cv
from tkinter import filedialog, Canvas, Scale, ttk
from PIL import Image, ImageTk, ImageDraw
import os, shutil
import PDFtoImages
from ImageProcces import ImageProcessing
from FeatureObject import Feature
import multiprocessing
import cv2 as cv
import numpy as np
import pickle
import copy


"""
TODO
Big TODO
    draw notes over the accidentals
    click to expand certain notes
    for extend notes:dont do blackness scale, do until rectangles overlap
    on load binary: write annotated images
    blackness scale
    autosnap notes further: find if colored spot borders black spot and change black spot to colored spot: and black spot is not in a note rectangleii
    edit mode: get rid of corner moving and do side moving with keyboatrd only
    fix keyboard controls
    edit mode: expand rectangle
    autosnap notes corners to implied lines. single and bulk
    when adding features second time, dont allow overlap
    once note is drawn with color, wont be removed by remove overlapping squares3
    single click to add note
    edit mode select feature when zoomed in or scrolled
    remove overlaping squares loop "single"
    get_loop_array single
    2 staff lines
    find name.pkl and name.pdf
    watermark
    use blackness bar for fill in feature
    regions error catching


"""

class ImageEditor(tk.Tk):
    def __init__(self):
        super().__init__()
        self.quickload = False
        self.title("Image Editor")
        self.dirname = os.path.dirname(__file__)
        self.file_name = ""

        #clearing out SheetsMusic folder
        directory = os.path.join(self.dirname, "SheetsMusic")
        if os.path.isdir(directory):
            shutil.rmtree(directory)
        #recreating the SheetsMusic folder with Annotated folder inside it
        os.mkdir(directory)
        directory = os.path.join(directory, "Annotated")
        os.mkdir(directory)



        #Left frame
        self.left_frame = tk.Frame(self, width=300, height=800)
        self.left_frame.pack(side="left", fill="y")

        # Show selected feature label
        self.selected_label_text = tk.StringVar()
        self.current_feature_type = "treble_clef"
        self.current_feature = None
        self.selected_label_text.set("Current Feature Selected: \n " + self.current_feature_type)
        self.feature_mode_add = True  # fasle for remove
        self.selected_label = tk.Label(self.left_frame,
                                       textvariable=self.selected_label_text)  # "Current Feature Selected: \n " + self.current_feature_type)
        self.selected_label.pack(pady=5)

        #Generate regions label
        self.generate_regions_button = tk.Button(self.left_frame, text="Generate Regions", command=self.generate_regions)
        self.generate_regions_button.pack(pady=5)




        #REmove adjacent features button
        self.remove_adjacents_button = tk.Button(self.left_frame, text="Remove Overlaping Squares", command=self.remove_adjacent_matches_all)
        self.remove_adjacents_button.pack(pady=5)

        #Autosnap notes button
        self.auto_snap_notes_button = tk.Button(self.left_frame, text="Autosnap notes", command=self.autosnap_notes)
        self.auto_snap_notes_button.pack()

        #Extend notes button
        self.extend_notes_horizontal_button = tk.Button(self.left_frame, text="Extend notes horizontally", command=self.extend_notes_horizontal)
        self.extend_notes_horizontal_button.pack()

        #Extend notes verticlally
        self.extend_notes_vertical_button = tk.Button(self.left_frame, text="Extend notes vertically", command=self.extend_notes_vertical)
        self.extend_notes_vertical_button.pack()

        #Undo label
        #This stores past versions of the self.image_processor object
        self.undo_features = None
        self.undo_feature_type = None
        #self.undo_button = tk.Button(self.left_frame, text="Undo", command=self.undo)#"Current Feature Selected: \n " + self.current_feature_type)
        #self.undo_button.pack(pady=5)
        #self.undo_label.bind("<Button-1>", self.undo)

        #Redo label
        self.is_undo_mode = True
        #self.redo_features = None
        #self.redo_button = tk.Button(self.left_frame, text="Redo", command=self.redo)  # "Current Feature Selected: \n " + self.current_feature_type)
        #self.redo_button.pack(pady=5)
        #self.redo_button.bind("<Button-1>", self.redo)

        #staff line generate button
        self.generate_staff_lines_button = tk.Button(self.left_frame, text="Generate Staff lines", command=self.generate_staff_lines)
        self.generate_staff_lines_button.pack(pady=5)
        #self.generate_staff_lines_label.bind("<Button-1>", self.generate_staff_lines)

        #Staff line error scale
        self.staff_line_error_scale = tk.Scale(self.left_frame, from_=0, to=42, orient="horizontal", label="Staff line error")
        self.staff_line_error_scale.set(5)
        self.staff_line_error_scale.pack()

        #staff line blackness_threshold scale
        self.staff_line_blackness_threshold_scale = tk.Scale(self.left_frame, from_=0, to=256, orient="horizontal", label="Staff line blackness threshold")
        self.staff_line_blackness_threshold_scale.set(250)
        self.staff_line_blackness_threshold_scale.pack()

        #threshold scale
        self.threshold_scale = tk.Scale(self.left_frame, from_=0, to=99, orient="horizontal", label="Threshold")
        self.threshold_scale.set(80)
        self.threshold_scale.pack()


        #Feature Error Scale
        #self.feature_error_scale = tk.Scale(self.left_frame, from_=0, to=42, orient="horizontal", label="Current feature error")
        #self.feature_error_scale.set(5)
        #self.feature_error_scale.pack()

        #Setting how the features will be added to just the current page, all pages, or the current and next pages
        self.add_mode_label = tk.Label(self.left_frame, text="Feature add mode:")
        self.add_mode_label.pack()
        self.add_mode_combobox_values = ["Current page and next pages", "Current Page", "All pages", "Single"]
        self.add_mode_combobox = ttk.Combobox(self.left_frame, state="readonly", values=self.add_mode_combobox_values)
        self.add_mode_combobox.current(0)
        self.add_mode_combobox.pack()

        #Setting the key
        self.sharp_order = ['f', 'c', 'g', 'd', 'a', 'e', 'b']
        self.flat_order = ['b', 'e', 'a', 'd', 'g', 'c', 'f',]

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

        self.corner_label = tk.Label(self.left_frame, text="Corner selected: ")
        self.corner_label.pack()
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
        self.filter_list = []#staff line, implied line, bass, treble, barline, note, accidental, region border, colored notes
        for i in range(8):
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


        #CHeck button for whether to draw the image on the canvas or the jpg
        self.draw_jpg_label = tk.Label(self.left_frame, text="Draw jpg:")
        self.draw_jpg_label.pack()
        self.draw_jpg = tk.IntVar()
        self.draw_jpg.set(0)
        self.draw_image_on_jpg_check_button = tk.Checkbutton(self.left_frame, text="Fast editing mode", onvalue=1, offvalue=0,
                                                      variable=self.draw_jpg, command=self.draw_image_canvas_mode)
        self.draw_image_on_jpg_check_button.pack()

        #Double note check button
        self.allow_overlapping = tk.IntVar()
        self.allow_overlapping.set(0)
        self.allow_overlapping_check_button = tk.Checkbutton(self.left_frame, text="Allow overlapping squares on add", onvalue=1, offvalue=0, variable=self.allow_overlapping)
        self.allow_overlapping_check_button.pack()

        self.num_notes_label = tk.Label(self.left_frame, text="Number of notes: ")
        self.num_notes_label.pack()
        self.num_notes_values = [1, 2, 3, 4, 5, "Pb", "bP", "Pb-", "bP-", "Pb--", "bP--"]
        self.num_notes_combobox = ttk.Combobox(self.left_frame, state="readonly", values=self.num_notes_values)
        self.num_notes_combobox.current(0)
        self.num_notes_combobox.pack()








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
        file_menu.add_command(label="Open pdf", command=self.open_pdf)
        file_menu.add_command(label="Save pdf", command=self.save_pdf)
        file_menu.add_separator()
        file_menu.add_command(label="Open annotations", command=self.load_binary)
        file_menu.add_command(label="Save annotations", command=self.save_binary)
        file_menu.add_separator()
        file_menu.add_command(label="Undo", command=self.undo)
        file_menu.add_command(label="Redo", command=self.redo)


        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.quit)

        #View menu for zoom in and out
        view_menu = tk.Menu(self.menu, tearoff=0)
        self.menu.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Zoom In", command=self.zoom_in)
        view_menu.add_command(label="Zoom Out", command=self.zoom_out)
        view_menu.add_separator()
        view_menu.add_command(label="Rotate CW", command=self.rotate_cw)
        view_menu.add_command(label="Rotate CCW", command=self.rotate_ccw)
        view_menu.add_separator()
        view_menu.add_command(label="Fast editing mode", command=self.switch_fast_editing_mode)

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

        #Key menu
        key_menu = tk.Menu(self.menu, tearoff=0)
        self.menu.add_cascade(label="Key", menu=key_menu)
        key_menu.add_command(label="Key", command=lambda :self.set_feature_type("key"))


    def extend_notes_vertical(self):
        loop_list = self.get_loop_array_based_on_feature_mode()
        if loop_list == "single":
            loop_list = [self.image_index]
        for i in loop_list:
            self.image_processor.extend_notes(i, vertical=1, horizontal=0)
        self.draw_image_with_filters()

    def extend_notes_horizontal(self):
        loop_list = self.get_loop_array_based_on_feature_mode()
        if loop_list == "single":
            loop_list = [self.image_index]
        for i in loop_list:
            self.image_processor.extend_notes(i, vertical=0, horizontal=1)
        self.draw_image_with_filters()

    def autosnap_notes(self):
        loop_array = self.get_loop_array_based_on_feature_mode()
        if loop_array == "single":
            loop_array = [self.image_index]
        for i in loop_array:
            self.image_processor.autosnap_notes_to_implied_line(i)
        self.draw_image_with_filters()

    def switch_fast_editing_mode(self):
        if self.draw_jpg.get() == 1:
            self.draw_jpg.set(0)
        else:
            self.draw_jpg.set(1)
        self.draw_image_with_filters()

    def rotate_cw(self):
        image = Image.open(self.dirname + "\\SheetsMusic\\page" + str(self.image_index) + ".jpg")
        image = image.rotate(45, expand=True)
        image.save(self.dirname + '\\SheetsMusic/page' + str(self.image_index) + '.jpg')
        #self.image_processor.staff_lines = []
        self.generate_staff_lines(page_index=self.image_index)
        #self.display_image()

    def rotate_ccw(self):
        image = Image.open(self.dirname + "\\SheetsMusic\\page" + str(self.image_index) + ".jpg")
        image = image.rotate(1, expand=True)
        image.save(self.dirname + '\\SheetsMusic/page' + str(self.image_index) + '.jpg')
        #cv.imwrite(self.dirname + '\\SheetsMusic/page' + str(self.image_index) + '.jpg', image)
        self.generate_staff_lines(page_index=self.image_index)
        #self.display_image()

    def undo(self):
        #print("undo features: ", self.undo_features)
        if self.undo_features is not None and self.is_undo_mode == True:
            self.is_undo_mode = False
            self.redo_features = copy.deepcopy(self.undo_features)
            for i in range(self.num_pages):
                #print("page: ", i)
                if self.undo_features[i] is not None:
                    all_features = self.image_processor.array_types_dict[self.undo_feature_type][i]
                    for feature in list(self.undo_features[i]):
                        #print("removed feature")
                        all_features.remove(feature)
        else:
            print("Nothing to undo")
        #print("undo features2: ", self.undo_features)
        self.draw_image_with_filters()

    def redo(self):
        #print("redo features: ", self.undo_features)
        if self.redo_features is not None and self.is_undo_mode == False:
            self.is_undo_mode = True
            self.undo_features = copy.deepcopy(self.redo_features)
            for i in range(self.num_pages):
                #print("page: ", i)
                if self.redo_features[i] is not None:
                    all_features = self.image_processor.array_types_dict[self.undo_feature_type][i]
                    for feature in list(self.redo_features[i]):
                        #print("feature unreomved")
                        all_features.append(feature)
        else:
            print("nothing to redo")
        self.draw_image_with_filters()

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
            return "single"

    def generate_staff_lines(self, page_index=None):

        error_value = self.staff_line_error_scale.get()
        blackness_threshold_value = self.staff_line_blackness_threshold_scale.get()
        if page_index is None:
            for i in self.get_loop_array_based_on_feature_mode():
                self.image_processor.get_stafflines(page_index=i, error=error_value, blackness_threshold=blackness_threshold_value)
                #self.image_processor.draw_stafflines(page_index=i)
                self.draw_image_with_filters()
        else:
            self.image_processor.get_stafflines(page_index=self.image_index, error=error_value, blackness_threshold=blackness_threshold_value)
            self.draw_image_with_filters()

    def generate_regions(self):
        print("Generating Regions")
        loop_array = self.get_loop_array_based_on_feature_mode()
        if loop_array == "single":
            loop_array = [self.image_index]
        for i in loop_array:

            if self.image_processor.all_clefs[i] is not None:
                self.image_processor.all_clefs[i].clear()
            if self.image_processor.regions[i] is not None:
                self.image_processor.regions[i].clear()
            if self.image_processor.treble_clefs[i] is not None and len(self.image_processor.treble_clefs[i]) > 0:
                error = abs(self.image_processor.treble_clefs[i][0].topleft[1] - self.image_processor.treble_clefs[i][0].bottomright[1]) / 2
            else:
                error = 100
            self.image_processor.sort_clefs(i, error=error)
            self.image_processor.get_clef_regions(i)
            #self.image_processor.remove_adjacent_matches(self.image_processor.barlines[i], error=30)
            self.image_processor.sort_barlines(i, error=30)
            self.image_processor.split_regions_by_bar(i)
            #todo set key
            #self.image_processor.set_key_regions(i, self.key_combobox.get())
            self.image_processor.find_notes_and_accidentals_in_region(i)
            if self.image_processor.regions[i] is not None:
                for region in self.image_processor.regions[i]:
                    region.fill_implied_lines(self.image_processor.staff_lines[i])
                    region.autosnap_notes_and_accidentals()
                    region.find_accidental_for_note(override=0)
                    #print("region: ", region)
            #self.image_processor.draw_regions(i)
        self.draw_image_with_filters()
        #self.display_image()

    def remove_adjacent_matches_all(self):
        print("Removing adjacent matches")
        loop = self.get_loop_array_based_on_feature_mode()
        if loop != "single":
            for i in self.get_loop_array_based_on_feature_mode():
                features = self.image_processor.array_types_dict[self.current_feature_type][i]
                i = 0
                while features is not None and i < len(features):
                    j = i + 1
                    while j < len(features):
                        if features[i].letter != "":
                            continue
                        if ImageEditor.do_features_overlap(features[i], features[j]) == True:
                            features.pop(j)
                        else:
                            j += 1
                    i += 1
        else:
            "Change out of single mode to remove overlapping squares"
        self.draw_image_with_filters()

    def set_feature_type(self, feature_name):
        self.current_feature_type = feature_name
        self.selected_label_text.set("Current Feature Selected: \n " + self.current_feature_type)
        print("Feature: ", self.current_feature_type, "Mode: ", self.editing_mode.get())

    def set_key(self, topleft, bottomright):
        loop_array = self.get_loop_array_based_on_feature_mode()
        if loop_array == "single":
            loop_array = [self.image_index]
        for i in loop_array:
            key = self.key_combobox.get()
            if key == "None":
                print("key is none")
                #todo get rid of all accidentals for none key
                self.image_processor.reset_accidentals(i, topleft, bottomright)
            elif "sharp" in key:
                num_sharp = int(key[0])
                letters = self.sharp_order[0: num_sharp]
                print("Key: ", key, "letters: ", letters)
                self.image_processor.set_key(i, topleft, bottomright, "sharp", letters)
            elif "flat" in key:
                num_flat = int(key[0])
                letters = self.flat_order[0: num_flat]
                print("Key: ", key, "letters: ", letters)
                self.image_processor.set_key(i, topleft, bottomright, "flat", letters)
            else:
                print("someghing bad happened with key combobox values")
        self.draw_image_with_filters()


    def keypress(self, event):
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
                    self.draw_image_with_filters()
                if c == 'b' or c == "B":
                    self.current_feature.set_letter('b')
                    self.draw_image_with_filters()
                if c == 'c' or c == "C":
                    self.current_feature.set_letter('c')
                    self.draw_image_with_filters()
                if c == 'd' or c == "D":
                    self.current_feature.set_letter('d')
                    self.draw_image_with_filters()
                if c == 'e' or c == "E":
                    self.current_feature.set_letter('e')
                    self.draw_image_with_filters()
                if c == 'f' or c == "F":
                    self.current_feature.set_letter('f')
                    self.draw_image_with_filters()
                if c == 'g' or c == "G":
                    self.current_feature.set_letter('g')
                    self.draw_image_with_filters()
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
                    self.draw_image_with_filters()
                if c == '2':
                    self.current_feature.set_accidental("sharp")
                    self.draw_image_with_filters()
                if c == '3':
                    self.current_feature.set_accidental("natural")
                    self.draw_image_with_filters()
                if c == '4':
                    self.current_feature.set_accidental("flat")
                    self.draw_image_with_filters()
                if c == '5':
                    self.current_feature.set_accidental("double_flat")
                    self.draw_image_with_filters()
                if c == '.':
                    print('Change corner being editied')
                    if self.editing_mode_corner.get() != self.editing_mode_corner_values[0]:
                        #print("topleft", self.editing_mode_corner_values[0])
                        self.editing_mode_corner.set(self.editing_mode_corner_values[0])
                        #print(self.editing_mode_corner.get())
                    else:
                        #print("bottomright", self.editing_mode_corner_values[1])
                        self.editing_mode_corner.set(self.editing_mode_corner_values[1])
                        #print(self.editing_mode_corner.get())
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
        f = file_path.split('/')
        self.file_name = f[-1]  # extracting filename from full directory
        self.file_name = self.file_name[:-4]  # remove .pdf
        print("Filename: ", self.file_name)
        if file_path:
            self.num_pages = PDFtoImages.filename_to_images(file_path)
            self.image_processor = ImageProcessing(self.dirname, file_path, self.num_pages)
            self.display_image()

    def save_pdf(self):

        folder = os.path.join(self.dirname, "SheetsMusic\\Annotated")#annotated0.png")
        filename = os.path.join(folder, "annotated0.png")
        #directory = os.path.join(self.directory, "Annotated")
        #directory = os.path.join(directory, "page0.jpg")
        print(folder)
        #draw all notes and accidentals

        if os.path.isfile(filename):
            print("file exists")
            images = []
            for i in range(self.num_pages):
                self.image_processor.images[i] = cv.imread(self.image_processor.images_filenames[i])
                self.image_processor.draw_features(self.image_processor.notes, i, draw_rectangle=False)
                self.image_processor.draw_features(self.image_processor.accidentals, i, draw_rectangle=False)
                cv.imwrite(self.image_processor.dirname + "\\SheetsMusic\\Annotated\\annotated" + str(i) + ".png",
                           self.image_processor.images[i])

                print("test", folder + "\\annotated" + str(i) + ".png")
                images.append(Image.open(folder + "\\annotated" + str(i) + ".png"))
            # go through all the images in the folder
            print("test", folder + "\\annotated" + str(0) + ".png")
            if self.quickload is True:
                print("self.filename", self.file_name)
                pdf_path = os.path.join(self.dirname, self.file_name + "_cheatmusic.pdf")
                images[0].save(pdf_path, "PDF", resolution=100.0, save_all=True, append_images=images[1:])
            else:
                pdf_path = filedialog.asksaveasfilename(filetypes=[("PDF", "*.pdf")], defaultextension=[("PDF", "*.pdf")], initialfile=self.file_name+"_cheatmusic.pdf")
                images[0].save(pdf_path, "PDF", resolution=100.0, save_all=True, append_images=images[1:])
        else:
            print("cant save")

    def save_binary(self):
        if self.quickload is True:
            with open("binary.pkl", "wb") as file:
                pickle.dump(self.image_processor, file)
        else:
            path = filedialog.asksaveasfilename(filetypes=[("pkl", "*.pkl")], defaultextension=[("pkl", "*.pkl")], initialfile=self.file_name)
            with open(path, "wb") as file:
                pickle.dump(self.image_processor, file)
                pickle.dump(self.file_name, file)

    def load_binary(self):
        if self.quickload is True:
            with open("binary.pkl", "rb") as file:
                loaded = pickle.load(file)
                self.image_processor = pickle.load(file)
                self.num_pages = self.image_processor.num_pages
                self.image_index = 0
                self.dirname = self.image_processor.dirname
                #file = self.image_processor.filename
                #f = file.split('/')
                #self.file_name = f[-1]#extracting filename from full directory
                #self.file_name = self.file_name[:-4]#remove .pdf
                self.file_name = pickle.load()
                print("filename: ", self.file_name)
                #write the images
                for i in range(self.num_pages):
                    cv.imwrite(self.dirname + '\\SheetsMusic/page' + str(i) + '.jpg', self.image_processor.images[i])
                self.draw_image_with_filters()
        else:
            file_path = filedialog.askopenfilename(title="Open pkl File", initialdir=self.dirname, filetypes=[("pkl files", "*.pkl")])  # TODO initialdir
            with open(file_path, "rb") as file:
                self.image_processor = pickle.load(file)
                self.file_name = pickle.load(file)
                self.num_pages = self.image_processor.num_pages
                self.image_index = 0
                self.dirname = self.image_processor.dirname
                # write the images
                for i in range(self.num_pages):
                    cv.imwrite(self.dirname + '\\SheetsMusic/page' + str(i) + '.jpg', self.image_processor.images[i])
                self.draw_image_with_filters()

    def display_image(self):
        #clearing the canvas so there arent shapes drawn on top of each other making things slow
        self.canvas.delete("all")

        if self.draw_jpg.get() == 0:
            print("drawing image on jpg")
            self.image = Image.open(self.dirname + "\\SheetsMusic\\Annotated\\annotated" + str(self.image_index) + ".png")
            self.photo = ImageTk.PhotoImage(
                self.image.resize((int(self.image.width * self.scale), int(self.image.height * self.scale))))
            self.canvas.create_image(0, 0, image=self.photo, anchor="nw")
            self.canvas.config(scrollregion=self.canvas.bbox(tk.ALL))
        else:
            print("Drawing image on canvas")
            #self.image = Image.open(self.dirname + "\\SheetsMusic\\page" + str(self.image_index) + ".jpg")
            self.image = Image.open(self.dirname + "\\SheetsMusic\\Annotated\\annotated" + str(self.image_index) + ".png")

            self.photo = ImageTk.PhotoImage(
                self.image.resize((int(self.image.width * self.scale), int(self.image.height * self.scale))))
            self.canvas.create_image(0, 0, image=self.photo, anchor="nw")
            self.canvas.config(scrollregion=self.canvas.bbox(tk.ALL))
            self.draw_features_on_canvas()

    def draw_features_on_canvas(self):
        if self.image_processor.notes[self.image_index] is not None:
            for feature in self.image_processor.notes[self.image_index]:
                self.draw_cross_hairs(feature, "red")

        if self.image_processor.accidentals[self.image_index] is not None:
            for feature in self.image_processor.accidentals[self.image_index]:
                self.draw_cross_hairs(feature, "purple")


        if self.image_processor.staff_lines[self.image_index] is not None:
            for line in self.image_processor.staff_lines[self.image_index]:
                line = int(line * self.scale)
                self.canvas.create_line(0, line, self.image_processor.image_widths[self.image_index], line, fill="green")

    def draw_cross_hairs(self, feature, color):

        x_mid = int(feature.center[0] * self.scale)
        y_mid = int(feature.center[1] * self.scale)
        x0 = int(feature.topleft[0] * self.scale)
        y0 = int(feature.topleft[1] * self.scale)
        x1 = int(feature.bottomright[0] * self.scale)
        y1 = int(feature.bottomright[1] * self.scale)

        self.canvas.create_rectangle(x0, y0, x1,
                                     y1, outline=color)
        self.canvas.create_line(x0, y_mid, x1, y_mid, fill=color)
        self.canvas.create_line(x_mid, y0, x_mid, y1, fill=color)

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
                #self.display_image()

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
                #self.display_image()

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
                #self.display_image()

    def next_image(self):
        #print("test")
        self.image_index = (self.image_index + 1) % self.num_pages
        self.draw_image_canvas_mode()
        self.draw_image_with_filters()
        #self.display_image()

    def previous_image(self):
        self.image_index = (self.image_index - 1) % self.num_pages
        self.draw_image_canvas_mode()
        self.draw_image_with_filters()
        #self.display_image()

    def zoom_in(self):
        self.scale *= 1.1
        self.display_image()

    def zoom_out(self):
        self.scale /= 1.1
        self.display_image()

    def draw_image_with_filters(self):
        #if no changes:
        #if self.undo_features == self.image_processor:
        #    pass
        #else:#if there were changes
        #    pass
        if self.draw_jpg.get() == 0:
            self.image_processor.draw_image(self.filter_list, self.image_index)
            self.display_image()
        #drawing the image on the boxes on the canvas
        else:
            self.display_image()

    def draw_image_canvas_mode(self):
        if self.draw_jpg.get() == 1:
            filter_temp = []
            filter = [1, 0, 0, 0, 0, 1, 1, 0, 1]  # staff line, implied line, bass, treble, barline, note, accidental, region border, colored notes
            for i in range(len(filter)):
                filter_temp.append(tk.IntVar())
                filter_temp[i].set(filter[i])
            self.image_processor.draw_image(filter_temp, self.image_index)
            self.display_image()
        else:
            self.draw_image_with_filters()


    def on_button_press(self, event):
        #Has to have image loaded onto the canvas
        if self.image is not None:
            if self.editing_mode.get() == "add" or self.current_feature_type == "key":
                if self.current_feature_type == "staff_line":
                    y = self.canvas.canvasy(event.y)
                    y_img = int(y / self.scale)
                    self.image_processor.staff_lines[self.image_index].append(y_img)
                    self.image_processor.staff_lines[self.image_index].sort()
                    self.draw_image_with_filters()
                self.rect_start = (self.canvas.canvasx(event.x), self.canvas.canvasy(event.y))
                if self.rect:
                    self.canvas.delete(self.rect)
                self.rect = None
            elif self.editing_mode.get() == "edit":
                if self.current_feature_type == "staff_line":
                    y = self.canvas.canvasy(event.y)
                    y_img = int(y / self.scale)
                    #find closest staff line and delete it
                    min_distance = 10000000
                    closest_line = None
                    for staff_line in self.image_processor.staff_lines[self.image_index]:
                        if abs(staff_line - y_img) < min_distance:
                            min_distance = abs(staff_line - y_img)
                            closest_line = staff_line
                    if closest_line is not None:
                        self.image_processor.staff_lines[self.image_index].remove(closest_line)
                        print("removed line at y: ", closest_line)
                        self.draw_image_with_filters()
                        return
                    else:
                        print("No line found")
                        return


                x = self.canvas.canvasx(event.x)
                y = self.canvas.canvasy(event.y)
                x_img = int(x / self.scale)
                y_img = int(y / self.scale)
                feature = self.image_processor.find_closest_feature(self.current_feature_type, self.image_index, x_img, y_img)
                if feature is not None:
                    print("feature found: ", feature)
                    self.current_feature = feature
                    #cv.rectangle(self.image, feature.topleft, feature.bottomright, (200, 0, 0), 1)
                    #self.draw_image_with_filters()
                    self.rect = self.canvas.create_rectangle(feature.topleft[0], feature.topleft[1], feature.bottomright[0], feature.bottomright[1], outline='black')

                    #draw = ImageDraw.Draw(self.image)
                    #draw.rectangle([feature.topleft[0], feature.topleft[1], feature.bottomright[0], feature.bottomright[1]], outline='red')#TODO color
                    #self.rect = self.canvas.create_rectangle(feature.topleft[0], feature.topleft[1], feature.bottomright[0], feature.bottomright[1],
                    #                                         outline='red')
                    #self.display_image()

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
            if self.current_feature_type == "key":
                print("key")
                self.set_key(rectangle.topleft, rectangle.bottomright)
                return

            if self.editing_mode.get() == "add":
                if self.current_feature_type == "staff_line":
                    print("nothing to do on button release for staff_line")
                    topline = rectangle.topleft[1]
                    bottomline = rectangle.bottomright[1]
                    line_spacing = abs(bottomline - topline) / 4
                    for line in np.arange(topline + line_spacing, bottomline + line_spacing, line_spacing):
                        self.image_processor.staff_lines[self.image_index].append(int(line))
                    self.image_processor.staff_lines[self.image_index].sort()
                    self.draw_image_with_filters()
                    return
                template = self.image_processor.images[self.image_index][rectangle.topleft[1]:rectangle.bottomright[1],
                           rectangle.topleft[0]:rectangle.bottomright[0]]
                if self.get_loop_array_based_on_feature_mode() != "single":#if the add mode is in single, dont need to match template
                    match_template_params = (
                        template,
                        (0, 255, 0),
                        rectangle.type,
                        self.threshold_scale.get() / 100,
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
                    loop_list = self.get_loop_array_based_on_feature_mode()
                    index_adjustment = loop_list[0]
                    self.undo_features = [None] * self.num_pages
                    self.undo_feature_type = rectangle.type
                    self.is_undo_mode = True
                    #cutting features in half for double notes
                    if rectangle.type == "note":
                        if self.num_notes_combobox.get() != 1:
                            for i in loop_list:
                                if len(results[i - index_adjustment]) > 0:
                                    results[i - index_adjustment] = self.convert_notes(results[i - index_adjustment])

                    #remove overlapping squares:
                    if self.allow_overlapping.get() == 0:
                        print("removing overlapping squares")
                        for i in loop_list:
                            existing_features = self.image_processor.array_types_dict[rectangle.type][i]
                            if existing_features is None:
                                break
                            filtered_results = [
                                new_feature for new_feature in results[i - index_adjustment]
                                if not any(
                                    ImageEditor.do_features_overlap(new_feature, existing_feature) for existing_feature
                                    in existing_features)
                            ]
                            results[i - index_adjustment] = filtered_results
                            #if existing_features is not None and len(existing_features) > 0 and len(results[i - index_adjustment]) > 0:
                            #    for new_feature in results[i - index_adjustment][:]:
                            #        for existing_feature in existing_features:
                            #            if ImageEditor.do_features_overlap(new_feature, existing_feature) == True:
                            #                results[i - index_adjustment].remove(new_feature)

                    for i in loop_list:
                        self.undo_features[i] = results[i - index_adjustment]
                        if self.image_processor.array_types_dict[rectangle.type][i] is None:
                            self.image_processor.array_types_dict[rectangle.type][i] = results[i - index_adjustment]
                        else:
                            self.image_processor.array_types_dict[rectangle.type][i] = self.image_processor.array_types_dict[rectangle.type][i] + results[i - index_adjustment]
                        self.image_processor.sort_features(self.image_processor.array_types_dict[rectangle.type][i])

                        #self.undo_features = self.undo_features + results[i - index_adjustment]

                    self.draw_image_with_filters()


                    #TODO if staffline

                    # Draw the rectangle on the actual image
                    draw = ImageDraw.Draw(self.image)
                    draw.rectangle([x0_img, y0_img, x1_img, y1_img], outline='red')
                    self.display_image()
                else:#only add single feature
                    print("single feature")
                    if self.image_processor.array_types_dict[rectangle.type][self.image_index] is None:
                        self.image_processor.array_types_dict[rectangle.type][self.image_index] = [rectangle]
                    else:
                        self.image_processor.array_types_dict[rectangle.type][self.image_index] = self.image_processor.array_types_dict[rectangle.type][self.image_index] + [rectangle]
                    self.image_processor.sort_features(self.image_processor.array_types_dict[rectangle.type][self.image_index])
                    self.draw_image_with_filters()
            elif self.editing_mode.get() == "edit":
                print("nothing to do on_button_release when in editing mode")



        else:#if rect wasnt started
            pass

    def convert_notes(self, notes):
        new_notes = []
        num_notes = self.num_notes_combobox.get()
        if "Pb" in num_notes or "bP" in num_notes:
            for note in notes:
                tl = note.topleft
                br = note.bottomright
                x_mid = note.topleft[0] + int(abs(note.topleft[0] - note.bottomright[0]) / 2)
                y_mid_lower = note.topleft[1] + int(abs(note.topleft[1] - note.bottomright[1]) * 2 / 3)
                y_mid_upper = note.topleft[1] + int(abs(note.topleft[1] - note.bottomright[1]) / 3)
                if "--" in num_notes:
                    tl = (tl[0], tl[1] + 2)
                    br = (br[0], br[1] - 2)
                elif "-" in num_notes:
                    tl = (tl[0], tl[1] + 1)
                    br = (br[0], br[1] - 1)
                if "Pb" in num_notes:
                    new_notes.append(
                        Feature(tl, (x_mid, y_mid_lower), abs(x_mid - tl[0]), abs(tl[1] - y_mid_lower), note.type))
                    new_notes.append(
                        Feature((x_mid, y_mid_upper), br, abs(br[0] - x_mid), abs(br[1] - y_mid_upper), note.type))
                else:#bP
                    new_notes.append(
                        Feature((tl[0], y_mid_upper), (x_mid, br[1]), abs(x_mid - tl[0]), abs(br[1] - y_mid_upper), note.type))
                    new_notes.append(
                        Feature((x_mid, tl[1]), (br[0], y_mid_lower), abs(br[0] - x_mid), abs(tl[1] - y_mid_upper), note.type))
        else:
            num_notes = int(num_notes)
            for note in notes:
                for i in range(num_notes):
                    spacing = abs(note.topleft[1] - note.bottomright[1]) / num_notes
                    tl = note.topleft
                    br = note.bottomright
                    top = int(tl[1] + spacing * i)
                    bottom = int(tl[1] + spacing * (i + 1))
                    new_notes.append(Feature((tl[0], top), [br[0], bottom], note.width, abs(bottom - top), note.type))
        return new_notes


    @staticmethod
    def get_distance(p1, p2):
        x2 = (p1[0] - p2[0]) * (p1[0] - p2[0])
        y2 = (p1[1] - p2[1]) * (p1[1] - p2[1])
        return (x2 + y2) ** .5

    @staticmethod
    def do_features_overlap(one, two):
        #if one feature is to the left
        if one.bottomright[0] < two.topleft[0] or two.bottomright[0] < one.topleft[0]:
            return False
        #if one feature is above
        if one.bottomright[1] < two.topleft[1] or two.bottomright[1] < one.topleft[1]:
            return False
        return True

    @staticmethod
    def remove_adjacent_matches(features):
        #Todo remove at i not j
        i = 0
        while features is not None and i < len(features):
            j = i + 1
            while j < len(features):
                if ImageEditor.do_features_overlap(features[i], features[j]) == True:
                    features.pop(j)
                else:
                    j += 1
            i += 1

    @staticmethod
    def match_template_parallel(image, gray_image, template, color, type, threshold,
                                error=10, draw=True):
        gray_template = cv.cvtColor(template, cv.COLOR_BGR2GRAY)
        gray_template_width, gray_template_height = gray_template.shape[::-1]
        res = cv.matchTemplate(gray_image, gray_template, cv.TM_CCOEFF_NORMED)
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
        ImageEditor.remove_adjacent_matches(features)
        return features


    @staticmethod
    def process_feature(args):
        i, image, gray_image, match_template_params = args
        print("Process ", i, "started")
        # Unpack the match_template parameters
        template, color, rect_type, threshold, error, draw = match_template_params
        features = ImageEditor.match_template_parallel(image, gray_image, template, color, rect_type, threshold, error=error,
                                                  draw=draw)
        if features is not None:
            #TODO remove adjacent matches based on feature size
            print("num features: ", len(features), "on page: ", i)

        print("Process ", i, "ended")
        return features





if __name__ == "__main__":
    app = ImageEditor()
    app.mainloop()

