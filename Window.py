import tkinter as tk
import cv2 as cv
from tkinter import filedialog, Canvas, Scale, ttk, messagebox
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
import sys
from StaffLine import StaffLine
from Note import Note
import blosc
import concurrent.futures
import subprocess

'''
Steps: Find clefs
find staff lines
find clefs in lines
generate barlines
go through jpgs and fill in missing lines in paint
find notes
expand
remove small notes
go through and fill in manually
for small notes, turn of threshold and dont allow auto extending


'
'''
"""
TODO
Big TODOn
    confirm confirmation dialog box for all functions. display add mode, inputs
    single click key error
    on change zoom reset canvas
    only show accidentals and notes that apply to
    make f1 use horizontal erode
    make purple accidentals more visable
    on_line_detection: erode each note by width plus 2
    single click to add clef
    change buttons for accidentals
    current feature tab
    draw current feature on canvas
    interpret small click and drag as click
    ignore small notes for notes on line
    erode strength multiplier
    show staff line groups. add groups to regioins. when regions get regenerated, go through each group and add to new region
    for bijective funciton between notes and keys: for double flats, double sharps, or accidentals that result in playing white key, acutally change the image and move the note up or down a half step
    is on line detection: to see if is on space if horizontal lines pass through not near the center
    on open: extend notes in all directions, set erode to 300, determine if notes are on line, click overwrite button, calculate notes
    compress image
    piano tape
    save annotations compressed: save pdf. when reloading, regenerate bw and grayscale images. how to remember blackness scale?
    show staff line groups from distorted staff line calculation in image.
    on distorted staff lines: set overwrite to false
    2 horizontal images. one for noes the other for staff lines and detecting notes on line
    change current feature text color to match color as well
    selecting multiple features at same time
    on single click to add: dont let rect be out of bounds
    make sure rect is in bounds in fill in feature
    draw crosshairs in different color for red note
    dont allow template matching for accidentals next to start clef
    on quarter half note overlap, get color for moved note
    amethyst, bubblegum, red c, suddy d, yEllow, frog f, g
    look at note letters and display notes that have letters that are on line!!!
    for staff lines: fill in white space and find rects of evenly sized heights
    only display notes on line or notes not on line
    detect is on line for half and whole notes if is_on_line is none when opening annotations
    to change where the region border is: intentionally mess up staff lines: or just allow editing of regions 
    zoom in and out scroll bar
    drop down tab for editing current feature: set letter, accidental
    flood fill vertical image: find all notes whose center lies in the bounding rect for cord checking
    chord letter error detection
    fill in half note: check bounds to match topleft and bottomright
    take staff line angle into account for note detection
    on key set mode to single
    online detection: find pixels that appear in horizonal erode, but not vertical and are attached from flood fill
    find horizontal lines that are removed by vertical erode fo note online detection
    detect anomalies: widest notes, tallest notes, notes with wierdest dimension rations. for notes that are accidentals: notes with smallest and largest amount of pixels changes
    make sure to undo convert half notes.
    staff line error bar for staff line pixel length
    detect unused accidental, or accidental that is used far away
    transpsose notes
    find un autosnapped half note
    xmltodict: go measure by measure
    write shorcut keys 
    chord letter checking: if notes are vertically stacked then notes should be 2 apart. if horizontally stacked, then 1 apart
    use both note detection and compare to find differences
    mxl parser: get all notes in measure, and there alteration, compare with
    extract notes and compare with mxml
    save pdf for printing order
    converts all notes into sharps or all notes into flats, display double flats as fully filled
    watermark



"""

class ImageEditor(tk.Tk):
    def __init__(self):
        super().__init__()
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
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


        self.frame_location = "side"
        if len(sys.argv) > 1 and sys.argv[1] == 'v':
            self.frame_location = "top"

        #Left frame
        self.left_frame = tk.Frame(self, width=300, height=800)
        #self.left_frame.pack(side="left", fill="y")

        self.page_indicator = tk.StringVar()
        # self.page_indicator.set(str(self.image_index) + "/" + self.num_pages)
        self.page_indicator_label = tk.Label(self.left_frame, textvariable=self.page_indicator)


        # Show selected feature label
        self.selected_label_text = tk.StringVar()
        self.current_feature_type = "treble_clef"
        self.current_feature = None
        self.selected_label_text.set("Current Feature Selected: \n " + self.current_feature_type)
        #self.feature_mode_add = True  # fasle for remove
        self.selected_label = tk.Label(self.left_frame, textvariable=self.selected_label_text)  # "Current Feature Selected: \n " + self.current_feature_type)


        # Setting how the features will be added to just the current page, all pages, or the current and next pages
        self.add_mode_label = tk.Label(self.left_frame, text="Feature add mode:")
        self.add_mode_combobox_values = ["Current page and next pages", "Current Page", "All pages", "Single"]
        self.add_mode_combobox = ttk.Combobox(self.left_frame, state="readonly", values=self.add_mode_combobox_values, takefocus=0, postcommand=self.set_cursor)
        self.add_mode_combobox.current(0)
        #self.add_mode_combobox.bind("<FocusOut>", self.clear_combobox)

        # CHeck button for whether to draw the image on the canvas or the jpg
        #self.fast_editing_mode = tk.BooleanVar()
        #self.fast_editing_mode.set(False)
        #self.fast_editing_mode_checkbutton = tk.Checkbutton(self.left_frame, text="Fast editing mode", onvalue=1, offvalue=0, variable=self.fast_editing_mode)#, command=self.draw_image_canvas_mode)

        self.allow_note_to_be_auto_extended = tk.BooleanVar()
        self.allow_note_to_be_auto_extended.set(True)
        self.allow_note_to_be_auto_extended_check_button = tk.Checkbutton(self.left_frame, text="Allow note to be auto extended", onvalue=True, offvalue=False, variable=self.allow_note_to_be_auto_extended)

        # Allow overlapping featues checkbox
        self.allow_overlapping = tk.IntVar()
        self.allow_overlapping.set(0)
        #self.allow_overlapping_check_button = tk.Checkbutton(self.left_frame, text="Allow overlapping squares on add", onvalue=1, offvalue=0, variable=self.allow_overlapping)
        #self.allow_overlapping_check_button.pack()


        self.note_type = tk.StringVar()
        self.note_types = ["quarter", "half", "whole"]
        self.note_type.set(self.note_types[0])
        #self.note_type_radio_button_quarter = tk.Radiobutton(self.left_frame, text="Quarter Note", variable=self.note_type, value=self.note_types[0])
        #self.note_type_radio_button_half = tk.Radiobutton(self.left_frame, text="Half Note", variable=self.note_type, value=self.note_types[1])
        #self.note_type_radio_button_whole = tk.Radiobutton(self.left_frame, text="Whole Note", variable=self.note_type, value=self.note_types[2])

        #REmove adjacent features button
        #self.remove_adjacents_button = tk.Button(self.left_frame, text="Remove Overlaping Squares", command=self.remove_adjacent_matches_all)
        #self.remove_adjacents_button.pack(pady=5)


        #Undo label
        #This stores past versions of the self.image_processor object
        self.undo_features = None
        self.undo_feature_type = None


        #Redo label
        self.is_undo_mode = True

        #Staff line error scale
        self.staff_line_error_scale = tk.Scale(self.left_frame, from_=0, to=42, orient="horizontal", label="Staff line error(pxls)")
        self.staff_line_error_scale.set(5)

        self.note_width_ratio_scale = tk.Scale(self.left_frame, from_=50, to=200, resolution=5, orient="horizontal", label="Note height/width ratio %")
        self.note_width_ratio_scale.set(145)


        #threshold scale
        self.threshold_scale = tk.Scale(self.left_frame, from_=0, to=99, orient="horizontal", label="Threshold %")
        self.threshold_scale.set(80)

        self.blackness_scale = tk.Scale(self.left_frame,from_=0, to=255, resolution=5, orient="horizontal", label="Blackness scale", command=self.on_blackness_scale_change)
        self.blackness_scale.set(210)

        #Erode stregth scale
        self.erode_strength_scale = tk.Scale(self.left_frame, from_=50, to=300, resolution=10, orient="horizontal", label="Erode strength %", command=self.on_erode_scale_change)
        self.erode_strength_scale.set(100)

        #Used for three click staff line addition
        self.staff_line_block_coordinates = []

        #Used for two click diagonal staff line
        self.staff_line_diagonal_coordinates = []


        #Setting the key
        self.sharp_order = ['f', 'c', 'g', 'd', 'a', 'e', 'b']
        self.flat_order = ['b', 'e', 'a', 'd', 'g', 'c', 'f',]

        #self.key_label = tk.Label(self.left_frame, text="Key:")
        #self.key_combobox_values = ["None","1 sharp", "2 sharps", "3 sharps", "4 sharps", "5 sharps", "6 sharps", "1 flat", "2 flats", "3 flats", "4 flats", "5 flats", "6 flats"]
        #self.key_combobox = ttk.Combobox(self.left_frame, state="readonly", values=self.key_combobox_values, takefocus=0)
        #self.key_combobox.current(0)



        #Filtering what is displayted
        self.filter_list = []#staff line, implied line, bass, treble, barline, note, accidental, region border, colored notes
        for i in range(8):
            self.filter_list.append(tk.IntVar())
            self.filter_list[i].set(1)
        self.filter_list[1].set(0)


        #Mutltiple notes
        self.num_notes_label = tk.Label(self.left_frame, text="Number of notes: ")
        self.num_notes_values = [1, 2, 3, 4, 5, "Pb", "bP", "Pb-", "bP-", "Pb--", "bP--"]
        self.num_notes_combobox = ttk.Combobox(self.left_frame, state="readonly", values=self.num_notes_values, takefocus=0)
        self.num_notes_combobox.current(0)

        if self.frame_location == "top":
            self.left_frame.pack(side="top", fill="y", anchor="w")
            '''
            self.page_indicator_label.grid(row=0, column=0)
            self.selected_label.grid(row=1, column=0)
            self.add_mode_label.grid(row=2, column=0)
            self.add_mode_combobox.grid(row=3, column=0)
            self.allow_note_to_be_auto_extended_check_button.grid(row=5, column=0)
            self.staff_line_error_scale.grid(row=0, column=1)
            self.note_width_ratio_scale.grid(row=1, column=1)
            self.threshold_scale.grid(row=2, column=1)
            self.blackness_scale.grid(row=3, column=1)
            self.erode_strength_scale.grid(row=4, column=1)
            self.num_notes_label.grid(row=5, column=1)
            self.num_notes_combobox.grid(row=6, column=1)
            '''

            self.left_frame.pack(side="top", fill="y", anchor="w")
            self.page_indicator_label.grid(row=0, column=0)
            self.selected_label.grid(row=1, column=0)
            self.add_mode_label.grid(row=0, column=1)
            self.add_mode_combobox.grid(row=1, column=1)
            self.allow_note_to_be_auto_extended_check_button.grid(row=0, column=2)
            self.staff_line_error_scale.grid(row=1, column=2)
            self.note_width_ratio_scale.grid(row=0, column=3)
            self.threshold_scale.grid(row=1, column=3)
            self.blackness_scale.grid(row=0, column=4)
            self.erode_strength_scale.grid(row=1, column=4)
            self.num_notes_label.grid(row=0, column=5)
            self.num_notes_combobox.grid(row=1, column=5)


        else:
            self.left_frame.pack(side="left", fill="y")
            self.page_indicator_label.pack()
            self.selected_label.pack(pady=5)
            self.add_mode_label.pack()
            self.add_mode_combobox.pack()
            #self.fast_editing_mode_checkbutton.pack()
            #self.show_borders_and_crosshairs_checkbutton.pack()
            self.allow_note_to_be_auto_extended_check_button.pack()
            #self.note_type_radio_button_quarter.pack()
            #self.note_type_radio_button_half.pack()
            #self.note_type_radio_button_whole.pack()
            self.staff_line_error_scale.pack()
            self.note_width_ratio_scale.pack()
            self.threshold_scale.pack()
            self.blackness_scale.pack()
            self.erode_strength_scale.pack()
            #self.key_label.pack()
            #self.key_combobox.pack()
            self.num_notes_label.pack()
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
        self.canvas.bind("<Control-ButtonPress-1>", self.on_control_button_press)
        self.canvas.bind("<Control-Shift-ButtonPress-1>", self.on_control_shift_button_press)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_button_release)
        self.canvas.bind("<MouseWheel>", self.scroll_vertical)
        self.canvas.bind("<Shift-MouseWheel>", self.scroll_horizontal)
        self.canvas.bind("<ButtonPress-3>", self.on_right_click)
        self.canvas.bind("<B3-Motion>", self.on_right_click_drag)
        self.canvas.bind("<ButtonRelease-3>", self.on_right_click_release)

        #Changing the current image
        self.bind("<Left>", self.left_key_press)
        self.bind("<Right>", self.right_key_press)
        self.bind("<Up>", self.up_key_press)
        self.bind("<Down>", self.down_key_press)
        self.bind("<Shift-Left>", self.shift_left_key_press)
        self.bind("<Shift-Right>", self.shift_right_key_press)
        self.bind("<Shift-Up>", self.shift_up_key_press)
        self.bind("<Shift-Down>", self.shift_down_key_press)
        self.bind("<Control-Left>", self.ctrl_left_key_press)
        self.bind("<Control-Right>", self.ctrl_right_key_press)
        self.bind("<Control-Up>", self.ctrl_up_key_press)
        self.bind("<Control-Down>", self.ctrl_down_key_press)
        self.bind("<Alt-Left>", self.alt_left_key_press)
        self.bind("<Alt-Right>", self.alt_right_key_press)
        self.bind("<Alt-Up>", self.alt_up_key_press)
        self.bind("<Alt-Down>", self.alt_down_key_press)

        #filtering which letters to show
        self.bind("<Control-a>", self.ctrl_a_key_press)
        self.bind("<Control-b>", self.ctrl_b_key_press)
        self.bind("<Control-c>", self.ctrl_c_key_press)
        self.bind("<Control-d>", self.ctrl_d_key_press)
        self.bind("<Control-e>", self.ctrl_e_key_press)
        self.bind("<Control-f>", self.ctrl_f_key_press)
        self.bind("<Control-g>", self.ctrl_g_key_press)

        #filtering which features to show
        self.bind("<Control-r>", self.ctrl_r_key_press)
        self.bind("<Control-t>", self.ctrl_t_key_press)
        self.bind("<Control-y>", self.ctrl_y_key_press)
        self.bind("<Control-s>", self.ctrl_s_key_press)
        self.bind("<Control-n>", self.ctrl_n_key_press)
        self.bind("<Control-1>", self.ctrl_1_key_press)
        self.bind("<Control-2>", self.ctrl_2_key_press)
        self.bind("<Control-3>", self.ctrl_3_key_press)
        self.bind("<Control-4>", self.ctrl_4_key_press)
        self.bind("<Control-5>", self.ctrl_5_key_press)

        #filtering which images to show
        self.bind("<Control-h>", self.ctrl_h_key_press)
        self.bind("<Control-j>", self.ctrl_j_key_press)
        self.bind("<Control-k>", self.ctrl_k_key_press)
        self.bind("<Control-l>", self.ctrl_l_key_press)
        self.bind("<Control-;>", self.ctrl_semi_colon_key_press)
        self.bind("<Control-'>", self.ctrl_single_quote_key_press)

        self.bind("<Control-minus>", self.ctrl_minus_key_press)
        self.bind("<Control-=>", self.ctrl_equals_key_press)
        self.bind("<Control-0>", self.ctrl_zero_key_press)

        self.bind("<Control-9>", self.ctrl_nine_key_press)



        self.bind("<Key>", self.keypress)
        self.bind("<F1>", self.on_f1_press)#generate staff lines
        self.bind("<F2>", self.on_f2_press)#auto extend notes
        self.bind("<F3>", self.on_f3_press)#calculate notes
        self.bind("<F4>", self.on_f4_press)#calculate accidentals
        self.bind("<F5>", self.on_f5_press)#regenerate images
        self.bind("<F6>", self.on_f6_press)#open paint
        self.bind("<F7>", self.on_f7_press)#handle half and quarter overlap
        self.bind("<F9>", self.on_f9_press)  # calculate notes
        self.bind("<F10>", self.on_f10_press)  # calculate notes
        self.bind("<F11>", self.on_f11_press)  # calculate notes
        self.bind("<F12>", self.on_f12_press)  # calculate notes



        self.image_processor = None
        self.num_pages = 0
        self.image = None

        self.image_index = 0
        self.page_indicator.set("Page: " + str(self.image_index + 1) + "/" + str(self.num_pages))
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
        file_menu.add_command(label="Open uncompressed annotations", command=self.load_binary)
        file_menu.add_command(label="Save uncompressed annotations", command=self.save_binary)
        file_menu.add_separator()
        #file_menu.add_command(label="Open compressed annotations", command=self.load_binary_compressed)
        #file_menu.add_command(label="Save compressed annotations", command=self.save_binary_compressed)
        #file_menu.add_separator()
        file_menu.add_command(label="Undo", command=self.undo)
        file_menu.add_command(label="Redo", command=self.redo)
        file_menu.add_separator()
        # file_menu.add_separator()
        file_menu.add_command(label="Regenerate images(F5)", command=self.regenerate_images)
        file_menu.add_separator()
        file_menu.add_command(label="Open current image in system's default .jpg editor(F6)", command=self.open_paint)
        file_menu.add_separator()
        file_menu.add_command(label="Reduce pixels by half(For pdfs that have unnecessarily high resolution)", command=self.reduce_image_size)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.quit)

        #View menu for zoom in and out
        view_menu = tk.Menu(self.menu, tearoff=0)
        self.menu.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Zoom In", command=self.zoom_in)
        view_menu.add_command(label="Zoom Out", command=self.zoom_out)
        view_menu.add_separator()
        self.show_borders = tk.BooleanVar()
        self.show_borders.set(False)
        self.show_borders_checkbutton = tk.Checkbutton(self.left_frame, text="Show borders", onvalue=1, offvalue=0, variable=self.show_borders)
        self.show_crosshairs = tk.BooleanVar()
        self.show_crosshairs.set(False)
        self.show_crosshairs_checkbutton = tk.Checkbutton(self.left_frame, text="Show crosshairs", onvalue=1, offvalue=0, variable=self.show_crosshairs)
        view_menu.add_checkbutton(label="Show borders(Checkbutton)", onvalue=True, offvalue=False, variable=self.show_borders, command=self.draw_image_with_filters)
        view_menu.add_checkbutton(label="Show crosshairs(Checkbutton)", onvalue=True, offvalue=False, variable=self.show_crosshairs, command=self.draw_image_with_filters)

        #view_menu.add_command(label="Rotate CW", command=self.rotate_cw)
        #view_menu.add_command(label="Rotate CCW", command=self.rotate_ccw)
        view_menu.add_separator()
        self.view_mode = tk.StringVar()
        self.view_mode_values = ["color", "erode", "bw", "horizontal", "vertical", "only_vertical_erode"]
        self.view_mode.set(self.view_mode_values[0])
        view_mode_sub_menu = tk.Menu(view_menu, tearoff=0)

        view_mode_sub_menu.add_radiobutton(label="Show color image(CTRL h)", variable=self.view_mode, value=self.view_mode_values[0], command=self.draw_image_with_filters)
        view_mode_sub_menu.add_radiobutton(label="Show eroded intersection image(CTRL j)", variable=self.view_mode, value=self.view_mode_values[1], command=self.draw_image_with_filters)
        view_mode_sub_menu.add_radiobutton(label="Show black and white image(CTRL k)", variable=self.view_mode, value=self.view_mode_values[2], command=self.draw_image_with_filters)
        view_mode_sub_menu.add_radiobutton(label="Show horizontal image(CTRL l)", variable=self.view_mode, value=self.view_mode_values[3], command=self.draw_image_with_filters)
        view_mode_sub_menu.add_radiobutton(label="Show vertical image(CTRL ;", variable=self.view_mode, value=self.view_mode_values[4], command=self.draw_image_with_filters)
        view_mode_sub_menu.add_radiobutton(label="Show only vertically eroded image(CTRL '", variable=self.view_mode, value=self.view_mode_values[5], command=self.draw_image_with_filters)
        view_menu.add_cascade(label="Select image to view", menu=view_mode_sub_menu)
        view_menu.add_separator()
        #view_menu.add_command(label="Auto rotate based off of staff lines", command=self.rotate_based_off_staff_lines)
        #view_menu.add_separator()
        view_menu.add_command(label="Fill in white spots", command=self.fill_in_white_spots)
        view_menu.add_separator()
        select_features_to_view_sub_menu = tk.Menu(view_menu, tearoff=0)
        select_features_to_view_sub_menu.add_checkbutton(label="Staff Lines(CTRL s)", onvalue=1, offvalue=0, variable=self.filter_list[0], command=self.set_filter)
        select_features_to_view_sub_menu.add_checkbutton(label="Implied Lines", onvalue=1, offvalue=0, variable=self.filter_list[1], command=self.set_filter)
        select_features_to_view_sub_menu.add_checkbutton(label="Treble Clefs(CTRL t)", onvalue=1, offvalue=0, variable=self.filter_list[2], command=self.set_filter)
        select_features_to_view_sub_menu.add_checkbutton(label="Bass Clefs(CTRL r)", onvalue=1, offvalue=0, variable=self.filter_list[3], command=self.set_filter)
        select_features_to_view_sub_menu.add_checkbutton(label="Barlines(CTRL y)", onvalue=1, offvalue=0, variable=self.filter_list[4], command=self.set_filter)
        select_features_to_view_sub_menu.add_checkbutton(label="Notes(CTRL n)", onvalue=1, offvalue=0, variable=self.filter_list[5], command=self.set_filter)
        select_features_to_view_sub_menu.add_checkbutton(label="Accidentals(CTRL 1)", onvalue=1, offvalue=0, variable=self.filter_list[6], command=self.set_filter)
        select_features_to_view_sub_menu.add_checkbutton(label="Region Borders", onvalue=1, offvalue=0, variable=self.filter_list[7], command=self.set_filter)
        view_menu.add_cascade(label="Select which features to show", menu=select_features_to_view_sub_menu)
        view_menu.add_separator()
        self.only_show_this_note_type = tk.StringVar()
        self.only_show_this_note_type.set("none")
        select_color_to_view_sub_menu = tk.Menu(view_menu, tearoff=0)
        select_color_to_view_sub_menu.add_radiobutton(label="None", variable=self.only_show_this_note_type, value='none', command=self.draw_image_with_filters)
        select_color_to_view_sub_menu.add_separator()
        select_color_to_view_sub_menu.add_radiobutton(label="A(CTRL a)", variable=self.only_show_this_note_type, value='a', command=self.draw_image_with_filters)
        select_color_to_view_sub_menu.add_radiobutton(label="B(CTRL b)", variable=self.only_show_this_note_type, value='b', command=self.draw_image_with_filters)
        select_color_to_view_sub_menu.add_radiobutton(label="C(CTRL c)", variable=self.only_show_this_note_type, value='c', command=self.draw_image_with_filters)
        select_color_to_view_sub_menu.add_radiobutton(label="D(CTRL d)", variable=self.only_show_this_note_type, value='d', command=self.draw_image_with_filters)
        select_color_to_view_sub_menu.add_radiobutton(label="E(CTRL e)", variable=self.only_show_this_note_type, value='e', command=self.draw_image_with_filters)
        select_color_to_view_sub_menu.add_radiobutton(label="F(CTRL f)", variable=self.only_show_this_note_type, value='f', command=self.draw_image_with_filters)
        select_color_to_view_sub_menu.add_radiobutton(label="G(CTRL g)", variable=self.only_show_this_note_type, value='g', command=self.draw_image_with_filters)
        select_color_to_view_sub_menu.add_separator()
        select_color_to_view_sub_menu.add_radiobutton(label="Notes that are on line(CTRL -)", variable=self.only_show_this_note_type, value='on_line', command=self.draw_image_with_filters)
        select_color_to_view_sub_menu.add_radiobutton(label="Notes that are not on line(CTRL =)", variable=self.only_show_this_note_type, value='not_on_line', command=self.draw_image_with_filters)
        select_color_to_view_sub_menu.add_radiobutton(label="Notes that are undetermined if they are on line(CTRL 0)", variable=self.only_show_this_note_type, value='undetermined', command=self.draw_image_with_filters)
        select_color_to_view_sub_menu.add_separator()
        select_color_to_view_sub_menu.add_radiobutton(label="Detect chord letter errors(CTRL 9)", variable=self.only_show_this_note_type, value='chord_errors',command=self.draw_image_with_filters)

        view_menu.add_cascade(label="Only show notes of a single type for making letter corrections easily", menu=select_color_to_view_sub_menu)





        #filter_menu = tk.Menu(self.menu, tearoff=0)
        #self.menu.add_cascade(label="Filter", menu=filter_menu)




        '''
        "bass_clef": (255, 0, 0),
        "treble_clef": (0, 125, 0),
        "note": (0, 0, 255),
        "barline": (0, 255, 255),
        "double_flat": (63, 0, 127),
        "flat": (127, 0, 0),
        "natural": (255, 255, 86),
        "sharp": (0, 127, 255),
        "double_sharp": (255, 0, 255),
        "staff_line": (0, 255, 0)
        '''
        set_feature_menu = tk.Menu(self.menu, tearoff=0)
        self.menu.add_cascade(label="Set Feature Type", menu=set_feature_menu)
        set_feature_menu.add_command(label="Staff line(1 click)", command=lambda: self.set_feature_type("staff_line"))
        set_feature_menu.add_command(label="Diagonal Staff Line(2 clicks)", command=lambda: self.set_feature_type("staff_line_diagonal"))
        set_feature_menu.add_command(label="Staff line region(3 clicks)", command=lambda: self.set_feature_type("staff_line_block"))
        set_feature_menu.entryconfig(0, foreground=self.bgr_to_hex((0, 255, 0)))
        set_feature_menu.entryconfig(1, foreground=self.bgr_to_hex((0, 255, 0)))
        set_feature_menu.entryconfig(2, foreground=self.bgr_to_hex((0, 255, 0)))
        set_feature_menu.add_separator()
        set_feature_menu.add_command(label="Bass Clef (r)", command=lambda :self.set_feature_type("bass_clef"))
        set_feature_menu.add_command(label="Treble Clef (t)", command=lambda :self.set_feature_type("treble_clef"))
        set_feature_menu.entryconfig(4, foreground=self.bgr_to_hex((0, 125, 0)))
        set_feature_menu.entryconfig(5, foreground=self.bgr_to_hex((255, 0, 0)))
        set_feature_menu.add_separator()
        set_feature_menu.add_command(label="Barline (y)", command=lambda :self.set_feature_type("barline"))
        set_feature_menu.entryconfig(7, foreground=self.bgr_to_hex((0, 255, 255)))
        set_feature_menu.add_separator()
        set_feature_menu.add_command(label="Note (n)", command=lambda :self.set_feature_type("note", "quarter"))
        set_feature_menu.add_command(label="Half Note (h)", command=lambda :self.set_feature_type("note", "half"))
        set_feature_menu.add_command(label="Whole Note (w)", command=lambda :self.set_feature_type("note", "whole"))
        set_feature_menu.entryconfig(9, foreground=self.bgr_to_hex((0, 0, 255)))
        set_feature_menu.entryconfig(10, foreground=self.bgr_to_hex((0, 0, 255)))
        set_feature_menu.entryconfig(11, foreground=self.bgr_to_hex((0, 0, 255)))
        set_feature_menu.add_separator()
        set_feature_menu.add_command(label="Double Sharp (1)", command=lambda: self.set_feature_type("double_sharp"))
        set_feature_menu.add_command(label="Sharp (2)", command=lambda: self.set_feature_type("sharp"))
        set_feature_menu.add_command(label="Natural (3)", command=lambda: self.set_feature_type("natural"))
        set_feature_menu.add_command(label="Flat (4)", command=lambda: self.set_feature_type("flat"))
        set_feature_menu.add_command(label="Double Flat (5)", command=lambda: self.set_feature_type("double_flat"))
        set_feature_menu.entryconfig(13, foreground=self.bgr_to_hex((255, 0, 255)))
        set_feature_menu.entryconfig(14, foreground=self.bgr_to_hex((0, 127, 255)))
        set_feature_menu.entryconfig(15, foreground=self.bgr_to_hex((255, 255, 86)))
        set_feature_menu.entryconfig(16, foreground=self.bgr_to_hex((127, 0, 0)))
        set_feature_menu.entryconfig(17, foreground=self.bgr_to_hex((63, 0, 127)))

        set_feature_menu.add_separator()
        set_feature_menu.add_command(label="Key (k)", command=lambda :self.set_feature_type("key"))




        #Clef menu
        clef_menu = tk.Menu(self.menu, tearoff=0)
        self.menu.add_cascade(label="Clef", menu=clef_menu)
        clef_menu.add_command(label="Find page missing start clefs", command=self.find_page_with_missing_clefs)


        # Staff line menu
        staff_line_menu = tk.Menu(self.menu, tearoff=0)
        self.menu.add_cascade(label="Staff Lines", menu=staff_line_menu)
        #staff_line_menu.add_command(label="Generate staff lines horizontal", command=self.generate_staff_lines)
        staff_line_menu.add_command(label="Generate staff lines (Prerequisite: Clefs) Warning: Will overwrite manual changes (F1)", command=self.generate_staff_lines_diagonal_by_traversing_vertical_line)
        #staff_line_menu.add_command(label="Generate staff lines diagonal, Alternate method (Prerequisite: Clefs)", command=lambda :self.generate_staff_lines_diagonal(use_union_image=False))
        staff_line_menu.add_separator()
        staff_line_menu.add_command(label="Generate staff lines override(Prerequisite: Clefs)", command=lambda: self.generate_staff_lines_diagonal_by_traversing_vertical_line(override=True))
        staff_line_menu.add_separator()
        staff_line_menu.add_command(label="Generate staff lines using horizontal erode(Prerequisite: Clefs)", command=lambda: self.generate_staff_lines_diagonal_by_traversing_vertical_line_using_horizontal_erode(override=True))
        #staff_line_menu.add_command(label="Find action needed page", command=self.find_page_with_wrong_staff_lines)

        # Barline menu
        barline_menu = tk.Menu(self.menu, tearoff=0)
        self.menu.add_cascade(label="Barline", menu=barline_menu)
        barline_menu.add_command(label="Generate barlines  (Prerequisite: Staff lines) Warning: Will overwrite manual changes", command=self.get_barlines)
        # barline_menu.add_command(label="Barline", command=lambda :self.set_feature_type("barline"))


        # Note menu
        self.include_auto_extended_notes = tk.BooleanVar()
        self.include_auto_extended_notes.set(False)
        note_menu = tk.Menu(self.menu, tearoff=0)
        self.menu.add_cascade(label="Notes", menu=note_menu)
        # note_menu.add_command(label="Note", command=lambda :self.set_feature_type("note"))
        #note_menu.add_checkbutton(label="(Checkbox)Half note", variable=self.is_half_note)
        #note_menu.add_radiobutton(label="Quarter Note", variable=self.note_type, value=self.note_types[0])
        #note_menu.add_radiobutton(label="Half Note", variable=self.note_type, value=self.note_types[1])
        #note_menu.add_radiobutton(label="Whole Note", variable=self.note_type, value=self.note_types[2])
        #note_menu.add_separator()
        note_menu.add_checkbutton(label="(Checkbox)Allow note to be auto extended", variable=self.allow_note_to_be_auto_extended)
        note_menu.add_command(label="Auto extend and center notes (Prerequisite: Staff lines) (F2)", command=self.auto_extend_notes)
        note_menu.add_separator()
        extend_notes_sub_menu = tk.Menu(note_menu, tearoff=0)
        #extend_notes_sub_menu.add_checkbutton(label="(Checkbox)Include auto extended notes", variable=self.include_auto_extended_notes)
        #extend_notes_sub_menu.add_separator()
        extend_notes_sub_menu.add_command(label="Extend notes in all directions", command=self.extend_notes_all_directions)
        extend_notes_sub_menu.add_separator()
        extend_notes_sub_menu.add_command(label="Extend notes up", command=lambda: self.extend_notes(1, 0, 0, 0))
        extend_notes_sub_menu.add_command(label="Extend notes down", command=lambda: self.extend_notes(0, 1, 0, 0))
        extend_notes_sub_menu.add_separator()
        extend_notes_sub_menu.add_command(label="Extend notes left", command=lambda: self.extend_notes(0, 0, 1, 0))
        extend_notes_sub_menu.add_command(label="Extend notes right", command=lambda: self.extend_notes(0, 0, 0, 1))
        note_menu.add_cascade(label="Extend notes in direction by 1 pixel", menu=extend_notes_sub_menu)
        note_menu.add_separator()
        note_menu.add_command(label="Remove unautosnapped notes", command=self.remove_unautosnapped_notes)
        note_menu.add_separator()
        note_menu.add_command(label="Detect if notes are on line or on space", command=self.determine_if_notes_are_on_line)
        note_menu.add_separator()
        note_menu.add_command(label="Handle half/whole note vertical overlap with quarter note (F7)", command=self.handle_half_and_quarter_note_overlap)






        #Key menu
        key_menu = tk.Menu(self.menu, tearoff=0)
        self.menu.add_cascade(label="Key", menu=key_menu)
        key_menu.add_command(label="Set key for current page", command=self.set_key_for_current_page)
        key_menu.add_separator()
        self.key_type = tk.StringVar()
        self.key_values = ["None", "1 sharp", "2 sharps", "3 sharps", "4 sharps", "5 sharps", "6 sharps", "1 flat", "2 flats", "3 flats", "4 flats", "5 flats", "6 flats"]
        key_menu.add_radiobutton(label="None", variable=self.key_type, value=self.key_values[0])
        key_menu.add_radiobutton(label="1 Sharp", variable=self.key_type, value=self.key_values[1])
        key_menu.add_radiobutton(label="2 Sharps", variable=self.key_type, value=self.key_values[2])
        key_menu.add_radiobutton(label="3 Sharps", variable=self.key_type, value=self.key_values[3])
        key_menu.add_radiobutton(label="4 Sharps", variable=self.key_type, value=self.key_values[4])
        key_menu.add_radiobutton(label="5 Sharps", variable=self.key_type, value=self.key_values[5])
        key_menu.add_radiobutton(label="6 Sharps", variable=self.key_type, value=self.key_values[6])
        key_menu.add_radiobutton(label="1 flat", variable=self.key_type, value=self.key_values[7])
        key_menu.add_radiobutton(label="2 flats", variable=self.key_type, value=self.key_values[8])
        key_menu.add_radiobutton(label="3 flats", variable=self.key_type, value=self.key_values[9])
        key_menu.add_radiobutton(label="4 flats", variable=self.key_type, value=self.key_values[10])
        key_menu.add_radiobutton(label="5 flats", variable=self.key_type, value=self.key_values[11])
        key_menu.add_radiobutton(label="6 flats", variable=self.key_type, value=self.key_values[12])


        #Region menu
        self.overwrite_regions = tk.BooleanVar()
        self.overwrite_regions.set(False)
        region_menu = tk.Menu(self.menu, tearoff=0)
        self.menu.add_cascade(label="Region", menu=region_menu)
        region_menu.add_checkbutton(label="(Checkbox)Overwrite notes and accidentals that already are assigned letters", variable=self.overwrite_regions)
        #region_menu.add_command(label="Generate regions", command=lambda: self.generate_regions(overwrite=self.overwrite_regions.get()))
        region_menu.add_separator()
        region_menu.add_command(label="Calculate note letters(Give notes color)(F3)", command=lambda: self.calculate_notes_for_regions_using_staff_lines(overwrite=self.overwrite_regions.get()))
        region_menu.add_command(label="Calculate note letters for distorted image", command=lambda: self.calculate_notes_for_distorted_staff_lines(overwrite=self.overwrite_regions.get()))
        region_menu.add_command(label="Calculate note letters for distorted image using horizontal erode", command=lambda: self.calculate_notes_for_distorted_staff_lines_using_horizontal_erode(overwrite=self.overwrite_regions.get()))
        region_menu.add_command(label="Calculate note letters for distorted image by only keeping pixels that are removed on vertical erode", command=lambda: self.calculate_notes_for_distorted_staff_lines_by_only_keeping_pixels_that_are_removed_in_vertical_erode(overwrite=self.overwrite_regions.get()))
        region_menu.add_separator()
        region_menu.add_command(label="Calculate accidental letters by finding closest note to the right(Give accidentals color)(F4)", command=lambda: self.calculate_accidental_letter_by_finding_closest_note(overwrite=self.overwrite_regions.get()))
        region_menu.add_separator()
        region_menu.add_command(label="Calculate note accidentals(Shade notes)", command=lambda: self.calculate_note_accidentals_for_regions(overwrite=self.overwrite_regions.get()))


        #Reset menu
        reset_menu = tk.Menu(self.menu, tearoff=0)
        self.menu.add_cascade(label="Reset", menu=reset_menu)
        reset_menu.add_command(label="Staff lines", command=lambda: self.clear_feature("staff_line"))
        reset_menu.add_command(label="Treble clefs", command=lambda: self.clear_feature("treble_clef"))
        reset_menu.add_command(label="Bass Clefs", command=lambda: self.clear_feature("bass_clef"))
        reset_menu.add_command(label="Barlines", command=lambda: self.clear_feature("barline"))
        reset_menu.add_command(label="Notes", command=lambda: self.clear_feature("note"))
        reset_menu.add_command(label="Accidentals", command=lambda :self.clear_feature("natural"))#Natural will map to accidentals
        reset_menu.add_separator()
        reset_menu.add_command(label="Double Sharp", command=lambda: self.clear_accidental_type("double_sharp"))
        reset_menu.add_command(label="Sharp", command=lambda: self.clear_accidental_type("sharp"))
        reset_menu.add_command(label="Natural", command=lambda: self.clear_accidental_type("natural"))
        reset_menu.add_command(label="Flat", command=lambda: self.clear_accidental_type("flat"))
        reset_menu.add_command(label="Double Flat", command=lambda: self.clear_accidental_type("double_flat"))
        reset_menu.add_separator()
        reset_menu.add_command(label="Quarter Note", command=lambda: self.clear_note_type("quarter"))
        reset_menu.add_command(label="Half Note", command=lambda: self.clear_note_type("half"))
        reset_menu.add_command(label="Whole Note", command=lambda: self.clear_note_type("whole"))
        reset_menu.add_separator()
        reset_menu.add_command(label="Regions", command=lambda: self.clear_region())
        reset_menu.add_command(label="Reset note and accidental letters", command=self.reset_note_and_accidental_letters)
        reset_menu.add_command(label="Reset note is on line for quarter notes", command=self.reset_note_is_on_line)

        info_menu = tk.Menu(self.menu, tearoff=0)
        ##self.info_string = tk.StringVar()
        self.menu.add_cascade(label="Info", menu=info_menu)
        #TODO, display image dimensions, number of notes, number of autosnapped notes, number of half notes
        #info_menu.
        self.allow_small_template_matching = tk.BooleanVar()
        self.allow_small_template_matching.set(False)
        info_menu.add_checkbutton(label="(Checkbutton) Allow small or all white rectangles for template matching", variable=self.allow_small_template_matching)
        self.debugging = tk.BooleanVar()
        self.debugging.set(False)
        info_menu.add_checkbutton(label="(Checkbutton)Debugging", variable=self.debugging, command=self.on_toggle_debugging)


    def handle_half_and_quarter_note_overlap(self):
        loop = self.get_loop_array_based_on_feature_mode()
        if loop == "single":
            loop = [self.image_index]
        else:
            message = "Handle half and quarter note overlap\n"
            message += "Pages(inclusive): " + str(loop[0]) + ":" + str(loop[-1]) + "\n"
            if not messagebox.askokcancel("Handle half and quarter note overlap", message):
                print("canceled")
                return
        for i in loop:
            self.image_processor.handle_half_and_quarter_note_overlap(i)
        self.draw_image_with_filters()

    def determine_if_notes_are_on_line(self):
        loop = self.get_loop_array_based_on_feature_mode()
        if loop == "single":
            loop = [self.image_index]
        else:
            message = "Determine if quarter notes are on line\n"
            message += "Pages(inclusive): " + str(loop[0]) + ":" + str(loop[-1]) + "\n"
            message += "Erode strength scale: " + str(self.erode_strength_scale.get() / 100)
            if not messagebox.askokcancel("Extend Notes", message):
                print("canceled")
                return
        for i in loop:
            self.image_processor.determine_if_notes_are_on_line(i, self.erode_strength_scale.get() / 100)
        self.draw_image_with_filters()
    def on_closing(self):
        # Ask for confirmation before closing the window
        if messagebox.askokcancel("Quit", "Do you really want to quit?"):
            self.destroy()  # Close the window if confirmed

    def on_toggle_debugging(self):
        if self.debugging.get() == True:
            self.add_mode_combobox.set(self.add_mode_combobox_values[3])

    def remove_unautosnapped_notes(self):
        loop = self.get_loop_array_based_on_feature_mode()
        if loop == "single":
            loop = [self.image_index]
        else:
            message = "Remove unautosnapped notes\n"
            message += "Pages(inclusive): " + str(loop[0]) + ":" + str(loop[-1]) + "\n"
            if not messagebox.askokcancel("Remove Unautosnapped notes", message):
                print("canceled")
                return
        for i in loop:
            self.image_processor.remove_unautosnapped_notes(i)
        self.draw_image_with_filters()

    def detect_unautosnapped_half_notes(self):
        loop = self.get_loop_array_based_on_feature_mode()
        if loop == "single":
            loop = [self.image_index]
        for i in loop:
            self.image_processor.detect_unautosnapped_half_notes(i)

    def set_cursor(self):
        if self.add_mode_combobox.get() == self.add_mode_combobox_values[0]:
            self.canvas.config(cursor="arrow")
        elif self.add_mode_combobox.get() == self.add_mode_combobox_values[1]:
            self.canvas.config(cursor="dotbox")
        elif self.add_mode_combobox.get() == self.add_mode_combobox_values[2]:
            self.canvas.config(cursor="tcross")
        elif self.add_mode_combobox.get() == self.add_mode_combobox_values[3]:
            self.canvas.config(cursor="cross")
        else:
            print("something wrong with setting add mode combobox values")

    def open_paint(self):
        path = self.image_processor.images_filenames[self.image_index]
        print(path)
        paint_path = r'C:\Windows\System32\mspaint.exe'
        if os.path.exists(path):
            #subprocess.run([paint_path, path])
            os.startfile(path)
            #subprocess.run(['mspaint.exe'])


    def convert_is_half_note(self):
        for i in range(self.num_pages):
            bw = self.image_processor.bw_images[i]
            h, w = bw.shape[:2]
            notes = self.image_processor.notes[i]
            if notes is not None and len(notes) > 0:
                for note in notes:
                    x_center, y_center = note.center
                    for y in range(y_center - 2, y_center + 2, 1):
                        for x in range(x_center - 2, x_center + 2, 1):
                            if 0 < y < h and 0 < x < w and bw[y][x] == 255:
                                note.is_half_note = "half"
                                if bw[y_center][x_center] == 255:
                                    note.is_on_line = False
                                else:
                                    note.is_on_line = True

    def auto_detect_note_letter_irregularities(self):
        #TODO look for adjacent notes and compare letters
        pass

    def reduce_image_size(self):
        for i in range(self.num_pages):
            self.image_processor.reduce_image_size(i)
        self.draw_image_with_filters()

    def regenerate_images(self):
        loop = self.get_loop_array_based_on_feature_mode()
        if loop == "single":
            loop = [self.image_index]
        else:
            message = "Regenerate images\n"
            message += "Pages(inclusive): " + str(loop[0]) + ":" + str(loop[-1]) + "\n"
            message += "Blackness scale: " + str(self.blackness_scale.get())
            if not messagebox.askokcancel("Regenerate Images", message):
                print("canceled")
                return
        for i in loop:
            self.image_processor.regenerate_images(i, self.blackness_scale.get())
        #if self.fast_editing_mode.get() == True:
        #self.reload_image()
        self.draw_image_with_filters()
        #self.draw_image_canvas_mode()

    @staticmethod
    def fill_in_white_spots_parallel(task):
        page_index, image, bw_image, filename = task
        print("Fill in white spots on page ", page_index)
        min_size = 10
        # Step 1: Load the image in grayscale mode
       # img = cv.adaptiveThreshold(gray_image, 255, cv.ADAPTIVE_THRESH_MEAN_C, cv.THRESH_BINARY, 15, -2)
        # Step 2: Apply binary thresholding to get a binary image
        #_, binary_img = cv.threshold(img, 190, 255, cv.THRESH_BINARY)

        # Step 3: Find connected components (to detect individual white regions)
        # 'connectivity=4' ensures only direct neighbors are considered connected
        num_labels, labels, stats, centroids = cv.connectedComponentsWithStats(bw_image, connectivity=4)

        # Step 4: Loop through the detected components and fill small white regions
        for i in range(1, num_labels):  # Ignore label 0 (background)
            area = stats[i, cv.CC_STAT_AREA]

            # If the area of the component is less than the minimum size, fill it
            if area < min_size:
                # Fill the region with black
                #binary_img[labels == i] = 0  # Set pixels of this label to black
                image[labels == i] = [0, 0, 0]

        cv.imwrite(filename, image)

    def fill_in_white_spots(self):
        loop = self.get_loop_array_based_on_feature_mode()
        if loop == "single":
            loop = [self.image_index]

        # Prepare the arguments for each task
        tasks = [
            (i, self.image_processor.images[i], self.image_processor.bw_images[i], self.image_processor.images_filenames[i])
            for i in loop
        ]

        # Create a pool of worker processes
        with multiprocessing.Pool() as pool:
            results = pool.map(ImageEditor.fill_in_white_spots_parallel, tasks)
        self.regenerate_images()
        self.draw_image_with_filters()

    def auto_detect_quarter_notes(self):
        loop = self.get_loop_array_based_on_feature_mode()
        if loop == "single":
            loop = [self.image_index]
        for i in loop:
            self.image_processor.auto_detect_quarter_notes(i, self.note_width_ratio_scale.get())
        self.draw_image_with_filters()

    def are_notes_on_line(self):
        loop = self.get_loop_array_based_on_feature_mode()
        if loop == "single":
            loop = [self.image_index]
        for i in loop:
            self.image_processor.are_notes_on_line(i)
        #self.draw_image_with_filters()

    def auto_detect_half_or_quarter_note(self):
        loop = self.get_loop_array_based_on_feature_mode()
        if loop == "single":
            loop = [self.image_index]
        for i in loop:
            self.image_processor.auto_detect_half_or_quarter_note(i)
        self.draw_image_with_filters()

    def remove_small_notes(self):

        loop = self.get_loop_array_based_on_feature_mode()
        if loop == "single":
            loop = [self.image_index]
        for i in loop:
            self.image_processor.remove_small_notes(i)
        print("Removed small notes")
        self.draw_image_with_filters()

    def auto_extend_notes(self):
        loop = self.get_loop_array_based_on_feature_mode()
        if loop == "single":
            loop = [self.image_index]
        else:
            message = "Auto extend notes\n"
            message += "Pages(inclusive): " + str(loop[0]) + ":" + str(loop[-1]) + "\n"
            message += "Note height/width ratio: " + str(self.note_width_ratio_scale.get()) + "\n"
            message += "Erode strength scale: " + str(self.erode_strength_scale.get() / 100)
            if not messagebox.askokcancel("Auto extend notes", message):
                print("canceled")
                return
        for i in loop:
            self.image_processor.auto_extend_notes(i, self.note_width_ratio_scale.get(), self.debugging.get(), self.erode_strength_scale.get() / 100)
        self.draw_image_with_filters()

    def clear_combobox(self, event):
        self.selected_label.focus()
    '''
    def set_note_type(self):
        self.is_half_note = not self.is_half_note
    '''

    def make_all_notes_same_size(self):
        for i in range(len(self.num_pages)):
            self.image_processor.make_all_notes_same_size(i)
    def reset_note_and_accidental_letters(self):
        loop = self.get_loop_array_based_on_feature_mode()
        if loop == "single":
            loop = [self.image_index]
        for i in loop:
            if self.image_processor.notes[i] is not None:
                for note in self.image_processor.notes[i]:
                    note.letter = ""
                    note.accidental = ""
            if self.image_processor.accidentals[i] is not None:
                for acc in self.image_processor.accidentals[i]:
                    acc.letter = ""
        self.draw_image_with_filters()

    def reset_note_is_on_line(self):
        loop = self.get_loop_array_based_on_feature_mode()
        if loop == "single":
            loop = [self.image_index]
        for i in loop:
            print("reset quarter note is_on_line", i)
            if self.image_processor.notes[i] is not None:
                for note in self.image_processor.notes[i]:
                    if note.is_half_note == "quarter":
                        note.is_on_line = None
        self.draw_image_with_filters()
    def set_key_for_current_page(self):
        topleft = [0,0]
        bottomright = [self.image_processor.image_widths[self.image_index] - 1, self.image_processor.image_heights[self.image_index] - 1]

        key = self.key_type.get()
        if key == "None":
            print("key is none")
            # todo get rid of all accidentals for none key
            self.image_processor.reset_accidentals(self.image_index, topleft, bottomright)
        elif "sharp" in key:
            num_sharp = int(key[0])
            letters = self.sharp_order[0: num_sharp]
            print("Key: ", key, "letters: ", letters)
            self.image_processor.set_key(self.image_index, topleft, bottomright, "sharp", letters)
        elif "flat" in key:
            num_flat = int(key[0])
            letters = self.flat_order[0: num_flat]
            print("Key: ", key, "letters: ", letters)
            self.image_processor.set_key(self.image_index, topleft, bottomright, "flat", letters)
        else:
            print("someghing bad happened with key combobox values")

        self.draw_image_with_filters()

    def get_barlines(self):
        loop = self.get_loop_array_based_on_feature_mode()
        if loop == "single":
            loop = [self.image_index]
        for i in loop:
            self.image_processor.get_barlines(i)
        self.draw_image_with_filters()

    def find_page_with_missing_clefs(self):
        loop = range(self.num_pages)
        for i in loop:
            if self.image_processor.is_page_missing_clef(i):
                print("Page " + str(i) + " needs clef action")
                self.image_index = i
                self.draw_image_with_filters()
                return
            else:
                pass
        print("starting clefs good")

    def find_page_with_wrong_staff_lines(self):
        loop = range(self.num_pages)
        for i in loop:
            lines = self.image_processor.staff_lines[i]
            #If staff lines is note multiple of 5
            if lines is not None and len(lines) % 5 == 0:
                #todo compare angle of lines to spot outlier
                pass
            else:
                print("Page " + str(i) + " needs staff line action")
                self.image_index = i
                self.draw_image_with_filters()
                return
        #if clef doesnt have 5 staff lines
        for i in loop:
            if self.image_processor.does_page_have_staff_line_error(i):
                print("Page " + str(i) + " needs staff line action")
                self.image_index = i
                self.draw_image_with_filters()
                break
            else:
                pass
        print("staff lines good")

    def extend_notes(self, up, down, left, right):
        loop = self.get_loop_array_based_on_feature_mode()

        direction = "up"
        if up == 1:
            direction = "up"
        elif down == 1:
            direction = "down"
        elif left == 1:
            direction = "left"
        else:
            direction = "right"
        if loop == "single":
            loop = [self.image_index]
        else:
            message = "Extend notes " + direction + "\n"
            message += "Pages(inclusive): " + str(loop[0]) + ":" + str(loop[-1]) + "\n"
            if not messagebox.askokcancel("Extend Notes", message):
                print("canceled")
                return
        for i in loop:
            if up == 1:
                print("extend notes up", i)
            if down == 1:
                print("extend notes down", i)
            if left == 1:
                print("extend notes left", i)
            if right == 1:
                print("extend notes right", i)
            self.image_processor.extend_notes(i, up, down, left, right)
        self.draw_image_with_filters()

    def extend_notes_all_directions(self):
        loop = self.get_loop_array_based_on_feature_mode()
        if loop == "single":
            loop = [self.image_index]
        else:
            message = "Extend notes in all directions\n"
            message += "Pages(inclusive): " + str(loop[0]) + ":" + str(loop[-1]) + "\n"
            if not messagebox.askokcancel("Extend Notes", message):
                print("canceled")
                return
        for i in loop:
            print("extend notes in all directions", i)
            self.image_processor.extend_notes(i, 1, 0, 0, 0)
            self.image_processor.extend_notes(i, 0, 1, 0, 0)
            self.image_processor.extend_notes(i, 0, 0, 1, 0)
            self.image_processor.extend_notes(i, 0, 0, 0, 1)

        self.draw_image_with_filters()

    def autosnap_notes(self):
        loop_array = self.get_loop_array_based_on_feature_mode()
        if loop_array == "single":
            loop_array = [self.image_index]
        for i in loop_array:
            self.image_processor.autosnap_notes_to_implied_line(i)
        self.draw_image_with_filters()

    def rotate_cw(self):
        '''
        image = Image.open(self.image_processor.images_filenames[self.image_index])#self.dirname + "\\SheetsMusic\\page" + str(self.image_index) + ".jpg")
        image = image.rotate(1, fillcolor=(255, 255, 255), expand=True)
        image.save(self.image_processor.images_filenames[self.image_index])#self.dirname + '\\SheetsMusic/page' + str(self.image_index) + '.jpg')
        self.image_processor.staff_lines[self.image_index] = []
        self.generate_staff_lines(page_index=self.image_index)
        self.draw_image_with_filters()
        '''
        image = cv.imread(self.image_processor.images_filenames[self.image_index])
        height, width = image.shape[:2]
        center = (width // 2, height // 2)
        angle = -1
        scale = 1
        M = cv.getRotationMatrix2D(center, angle, scale)
        # Calculate the cosine and sine of the rotation angle
        cos = np.abs(M[0, 0])
        sin = np.abs(M[0, 1])

        # Compute the new bounding dimensions of the image
        new_w = int((height * sin) + (width * cos))
        new_h = int((height * cos) + (width * sin))

        # Adjust the rotation matrix to take into account the translation
        M[0, 2] += (new_w / 2) - center[0]
        M[1, 2] += (new_h / 2) - center[1]

        # Perform the actual rotation and return the image
        rotated_image = cv.warpAffine(image, M, (new_w, new_h))
        # Perform the actual rotation and return the rotated image
        #rotated_image = cv.warpAffine(image, M, (width, height))

        cv.imwrite(self.image_processor.images_filenames[self.image_index], rotated_image)
        self.draw_image_with_filters()


    def rotate_ccw(self):
        '''#TOdo rotate based of of user input
        image = Image.open(self.image_processor.images_filenames[self.image_index])#self.dirname + "\\SheetsMusic\\page" + str(self.image_index) + ".jpg")
        image = image.rotate(.1, fillcolor=(255, 255, 255), expand=True)
        image.save(self.image_processor.images_filenames[self.image_index])#self.dirname + '\\SheetsMusic/page' + str(self.image_index) + '.jpg')
        #cv.imwrite(self.dirname + '\\SheetsMusic/page' + str(self.image_index) + '.jpg', image)
        self.generate_staff_lines(page_index=self.image_index)
        self.draw_image_with_filters()
        '''
        image = cv.imread(self.image_processor.images_filenames[self.image_index])
        height, width = image.shape[:2]
        center = (width // 2, height // 2)
        angle = 1
        scale = 1
        M = cv.getRotationMatrix2D(center, angle, scale)
        # Calculate the cosine and sine of the rotation angle
        cos = np.abs(M[0, 0])
        sin = np.abs(M[0, 1])

        # Compute the new bounding dimensions of the image
        new_w = int((height * sin) + (width * cos))
        new_h = int((height * cos) + (width * sin))

        # Adjust the rotation matrix to take into account the translation
        M[0, 2] += (new_w / 2) - center[0]
        M[1, 2] += (new_h / 2) - center[1]

        # Perform the actual rotation and return the image
        rotated_image = cv.warpAffine(image, M, (new_w, new_h))
        # Perform the actual rotation and return the rotated image
        # rotated_image = cv.warpAffine(image, M, (width, height))

        cv.imwrite(self.image_processor.images_filenames[self.image_index], rotated_image)
        self.draw_image_with_filters()

    def rotate_based_off_staff_lines(self):
        loop = self.get_loop_array_based_on_feature_mode()
        if loop == "single":
            loop = [self.image_index]
        for i in loop:
            self.image_processor.rotate_based_off_staff_lines(i)
        self.draw_image_with_filters()

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
                        if feature in all_features:
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

    #def set_mode(self):
    #    print("current mode: ", self.editing_mode.get())


    def get_loop_array_based_on_feature_mode(self):
        if self.add_mode_combobox.get() == self.add_mode_combobox_values[0]:#current page and next
            return range(self.image_index, self.num_pages, 1)
        if self.add_mode_combobox.get() == self.add_mode_combobox_values[1]:#Current page
            return [self.image_index]
        if self.add_mode_combobox.get() == self.add_mode_combobox_values[2]:#all pages
            return range(self.num_pages)
        if self.add_mode_combobox.get() == self.add_mode_combobox_values[3]:#single feature, no match_template
            return "single"

    def generate_staff_lines_diagonal(self, use_union_image):
        error_value = self.staff_line_error_scale.get()
        #blackness_threshold_value = self.staff_line_blackness_threshold_scale.get()
        loop = self.get_loop_array_based_on_feature_mode()
        if loop == "single":
            loop = [self.image_index]
        for i in loop:
            self.image_processor.get_staff_lines_diagonal_recursive(i, error_value, use_union_image=use_union_image, vertical_size=20, horizontal_size=20)
        self.draw_image_with_filters()

    def generate_staff_lines_diagonal_by_traversing_vertical_line(self, override=False):
        loop = self.get_loop_array_based_on_feature_mode()
        if loop == "single":
            loop = [self.image_index]
        check_num_clefs_and_staff_lines = False
        for i in loop:
            if i == self.image_index:
                check_num_clefs_and_staff_lines = False
            else:
                check_num_clefs_and_staff_lines = True
            if override == True:
                check_num_clefs_and_staff_lines = False
            self.image_processor.get_staff_lines_diagonal_by_traversing_vertical_line(i, check_num_clefs_and_staff_lines)
        self.draw_image_with_filters()

    def generate_staff_lines_diagonal_by_traversing_vertical_line_using_horizontal_erode(self, override=False):
        loop = self.get_loop_array_based_on_feature_mode()
        if loop == "single":
            loop = [self.image_index]
        check_num_clefs_and_staff_lines = False
        for i in loop:
            if i == self.image_index:
                check_num_clefs_and_staff_lines = False
            else:
                check_num_clefs_and_staff_lines = True
            if override == True:
                check_num_clefs_and_staff_lines = False
            self.image_processor.get_staff_lines_diagonal_by_traversing_vertical_line_using_horizontal_erode(i, check_num_clefs_and_staff_lines)
        self.draw_image_with_filters()

    def generate_staff_lines(self):
        error_value = self.staff_line_error_scale.get()
        blackness_threshold_value = 250#self.staff_line_blackness_threshold_scale.get()
        loop = self.get_loop_array_based_on_feature_mode()
        if loop == "single":
            loop = [self.image_index]
        for i in loop:
            self.image_processor.get_staff_lines(page_index=i, error=error_value, blackness_threshold=blackness_threshold_value)
        self.draw_image_with_filters()

    def generate_regions(self, overwrite):
        print("Generating Regions")
        loop_array = self.get_loop_array_based_on_feature_mode()
        if loop_array == "single":
            loop_array = [self.image_index]
        for i in loop_array:

            if self.image_processor.all_clefs[i] is not None:
                self.image_processor.all_clefs[i].clear()
            if self.image_processor.regions[i] is not None:
                self.image_processor.regions[i].clear()
            self.image_processor.sort_clefs(i)
            self.image_processor.get_clef_regions(i)
            #self.image_processor.remove_adjacent_matches(self.image_processor.barlines[i], error=30)
            self.image_processor.sort_barlines(i, error=30)
            self.image_processor.split_regions_by_bar(i)
            #self.image_processor.are_notes_on_line(i)
            self.image_processor.find_notes_and_accidentals_in_region(i)

            if self.image_processor.regions[i] is not None:
                #print("num regions:", len(self.image_processor.regions[i]))
                for region in self.image_processor.regions[i]:
                    region.fill_implied_lines(self.image_processor.staff_lines[i], self.image_processor.image_widths[i], self.image_processor.image_heights[i])
                    region.autosnap_notes_and_accidentals(overwrite)
                    region.find_accidental_for_note(overwrite)
                    #print("region: ", region)
            #self.image_processor.draw_regions(i)
        self.draw_image_with_filters()

    def calculate_notes_for_regions_using_staff_lines(self, overwrite):

        loop = self.get_loop_array_based_on_feature_mode()
        if loop == "single":
            loop = [self.image_index]
        else:
            message = "Calculate Notes\n"
            message += "Pages(inclusive): " + str(loop[0]) + ":" + str(loop[-1]) + "\n"
            message += "Overwrite: " + str(overwrite)
            if not messagebox.askokcancel("Calculate Notes", message):
                print("canceled")
                return
        for i in loop:
            print("calculate notes using staff lines page", i)
            if self.image_processor.all_clefs[i] is not None:
                self.image_processor.all_clefs[i].clear()
            if self.image_processor.regions[i] is not None:
                self.image_processor.regions[i].clear()
            self.image_processor.sort_clefs(i)
            self.image_processor.get_clef_regions(i)
            # self.image_processor.remove_adjacent_matches(self.image_processor.barlines[i], error=30)
            self.image_processor.sort_barlines(i, error=30)
            self.image_processor.split_regions_by_bar(i)
            # self.image_processor.are_notes_on_line(i)
            self.image_processor.find_notes_and_accidentals_in_region(i)
            if self.image_processor.regions[i] is not None:
                for region in self.image_processor.regions[i]:
                    region.fill_implied_lines(self.image_processor.staff_lines[i], self.image_processor.image_widths[i], self.image_processor.image_heights[i])
                    #region.autosnap_notes_and_accidentals(overwrite)
                    self.image_processor.calculate_notes_using_staff_lines(i, region, overwrite)
        self.draw_image_with_filters()
    def calculate_notes_for_regions_using_staff_lines_single_page(self, overwrite, page_index):

        print("calculate notes using staff lines page", page_index)
        if self.image_processor.all_clefs[page_index] is not None:
            self.image_processor.all_clefs[page_index].clear()
        if self.image_processor.regions[page_index] is not None:
            self.image_processor.regions[page_index].clear()
        self.image_processor.sort_clefs(page_index)
        self.image_processor.get_clef_regions(page_index)
        # self.image_processor.remove_adjacent_matches(self.image_processor.barlines[i], error=30)
        self.image_processor.sort_barlines(page_index, error=30)
        self.image_processor.split_regions_by_bar(page_index)
        # self.image_processor.are_notes_on_line(i)
        self.image_processor.find_notes_and_accidentals_in_region(page_index)
        if self.image_processor.regions[page_index] is not None:
            for region in self.image_processor.regions[page_index]:
                region.fill_implied_lines(self.image_processor.staff_lines[page_index], self.image_processor.image_widths[page_index], self.image_processor.image_heights[page_index])
                #region.autosnap_notes_and_accidentals(overwrite)
                self.image_processor.calculate_notes_using_staff_lines(page_index, region, overwrite)
        self.draw_image_with_filters()


    def calculate_notes_for_distorted_staff_lines(self, overwrite):

        loop = self.get_loop_array_based_on_feature_mode()
        if loop == "single":
            loop = [self.image_index]
        else:
            message = "Calculate Notes for distorted staff lines\n"
            message += "Pages(inclusive): " + str(loop[0]) + ":" + str(loop[-1]) + "\n"
            message += "Overwrite: " + str(overwrite)
            if not messagebox.askokcancel("Calculate Notes", message):
                print("canceled")
                return
        for i in loop:
            if self.image_processor.all_clefs[i] is not None:
                self.image_processor.all_clefs[i].clear()
            if self.image_processor.regions[i] is not None:
                self.image_processor.regions[i].clear()
            self.image_processor.sort_clefs(i)
            self.image_processor.get_clef_regions(i)
            # self.image_processor.remove_adjacent_matches(self.image_processor.barlines[i], error=30)
            self.image_processor.sort_barlines(i, error=30)
            self.image_processor.split_regions_by_bar(i)
            # self.image_processor.are_notes_on_line(i)
            self.image_processor.find_notes_and_accidentals_in_region(i)
            if self.image_processor.regions[i] is not None:
                bw = self.image_processor.bw_images[i]
                print("calculating note letters for distorted staff lines on page", i, "staff line error:", self.staff_line_error_scale.get(), "pxls")
                for region in self.image_processor.regions[i]:
                    if len(region.notes) > 0 or len(region.accidentals) > 0:
                        self.image_processor.calculate_notes_for_distorted_staff_lines(i, region, bw, self.staff_line_error_scale.get(), overwrite)
                if self.debugging.get() == True:
                    cv.imwrite("anote_calculating.jpg", bw)
        self.draw_image_with_filters()

    def calculate_notes_for_distorted_staff_lines_using_horizontal_erode(self, overwrite):
        loop = self.get_loop_array_based_on_feature_mode()
        if loop == "single":
            loop = [self.image_index]
        else:
            message = "Calculate Notes for distorted staff lines using horizontal erode\n"
            message += "Pages(inclusive): " + str(loop[0]) + ":" + str(loop[-1]) + "\n"
            message += "Overwrite: " + str(overwrite) + "\n"
            message += "Staff line error scale: " + str(self.staff_line_error_scale.get()) + " pixels\n"
            message += "Erode strength scale: " + str(self.erode_strength_scale.get() / 100)
            if not messagebox.askokcancel("Calculate Notes", message):
                print("canceled")
                return
        for i in loop:
            if self.image_processor.all_clefs[i] is not None:
                self.image_processor.all_clefs[i].clear()
            if self.image_processor.regions[i] is not None:
                self.image_processor.regions[i].clear()
            self.image_processor.sort_clefs(i)
            self.image_processor.get_clef_regions(i)
            # self.image_processor.remove_adjacent_matches(self.image_processor.barlines[i], error=30)
            self.image_processor.sort_barlines(i, error=30)
            self.image_processor.split_regions_by_bar(i)
            # self.image_processor.are_notes_on_line(i)
            self.image_processor.find_notes_and_accidentals_in_region(i)
            if self.image_processor.regions[i] is not None:
                horizontal = self.image_processor.get_horizontal_image(i, self.erode_strength_scale.get() / 100)
                print("calculating notesletters for distorted staff lines using horizontal erode on page", i, "staff line error:", self.staff_line_error_scale.get(), "pxls")
                for region in self.image_processor.regions[i]:
                    self.image_processor.calculate_notes_for_distorted_staff_lines(i, region, horizontal, self.staff_line_error_scale.get(), overwrite)
                if self.debugging.get() == True:
                    cv.imwrite("anote_calculating_horizontal.jpg", horizontal)
        self.draw_image_with_filters()

    def calculate_notes_for_distorted_staff_lines_by_only_keeping_pixels_that_are_removed_in_vertical_erode(self, overwrite):
        loop = self.get_loop_array_based_on_feature_mode()
        if loop == "single":
            loop = [self.image_index]
        else:
            message = "Calculate Notes for distorted staff lines by only keeping pixels that are removed in vertical erode\n"
            message += "Pages(inclusive): " + str(loop[0]) + ":" + str(loop[-1]) + "\n"
            message += "Overwrite: " + str(overwrite) + "\n"
            message += "Staff line error scale: " + str(self.staff_line_error_scale.get()) + " pixels\n"
            if not messagebox.askokcancel("Calculate Notes", message):
                print("canceled")
                return
        for i in loop:
            if self.image_processor.all_clefs[i] is not None:
                self.image_processor.all_clefs[i].clear()
            if self.image_processor.regions[i] is not None:
                self.image_processor.regions[i].clear()
            self.image_processor.sort_clefs(i)
            self.image_processor.get_clef_regions(i)
            # self.image_processor.remove_adjacent_matches(self.image_processor.barlines[i], error=30)
            self.image_processor.sort_barlines(i, error=30)
            self.image_processor.split_regions_by_bar(i)
            # self.image_processor.are_notes_on_line(i)
            self.image_processor.find_notes_and_accidentals_in_region(i)
            if self.image_processor.regions[i] is not None:
                horizontal = self.image_processor.get_keep_only_vertical_erode_image(i, 5)
                print("calculating note letters for distorted staff lines using pixels that arent removed from vertical erode", i, "staff line error:", self.staff_line_error_scale.get(), "pxls")
                for region in self.image_processor.regions[i]:
                    self.image_processor.calculate_notes_for_distorted_staff_lines(i, region, horizontal, self.staff_line_error_scale.get(), overwrite)
                if self.debugging.get() == True:
                    cv.imwrite("anote_calculating_horizontal.jpg", horizontal)
        self.draw_image_with_filters()

    def calculate_accidental_letter_by_finding_closest_note(self, overwrite):
        loop = self.get_loop_array_based_on_feature_mode()
        if loop == "single":
            loop = [self.image_index]
        else:
            message = "Calculate accidental letter by finding closest note\n"
            message += "Pages(inclusive): " + str(loop[0]) + ":" + str(loop[-1]) + "\n"
            message += "Overwrite: " + str(overwrite) + "\n"
            if not messagebox.askokcancel("Calculate Accidentals", message):
                print("canceled")
                return
        for i in loop:
            self.image_processor.calculate_accidental_letter_by_finding_closest_note(i, overwrite)
        self.draw_image_with_filters()

    def calculate_note_accidentals_for_regions(self, overwrite):
        loop = self.get_loop_array_based_on_feature_mode()
        if loop == "single":
            loop = [self.image_index]
        else:
            message = "Calculate note accidentals\n"
            message += "Pages(inclusive): " + str(loop[0]) + ":" + str(loop[-1]) + "\n"
            message += "Overwrite: " + str(overwrite) + "\n"
            if not messagebox.askokcancel("Calculate Note Accidentals", message):
                print("canceled")
                return
        for i in loop:
            print("Calculate note accidentals page", i)
            note_height = self.image_processor.get_note_height(i)
            if self.image_processor.all_clefs[i] is not None:
                self.image_processor.all_clefs[i].clear()
            if self.image_processor.regions[i] is not None:
                self.image_processor.regions[i].clear()
            self.image_processor.sort_clefs(i)
            self.image_processor.get_clef_regions(i)
            # self.image_processor.remove_adjacent_matches(self.image_processor.barlines[i], error=30)
            self.image_processor.sort_barlines(i, error=30)
            self.image_processor.split_regions_by_bar(i)
            # self.image_processor.are_notes_on_line(i)
            self.image_processor.find_notes_and_accidentals_in_region(i)
            if self.image_processor.regions[i] is not None:
                for region in self.image_processor.regions[i]:
                    region.fill_implied_lines(self.image_processor.staff_lines[i], self.image_processor.image_widths[i], self.image_processor.image_heights[i])
                    region.find_accidental_for_note(overwrite, note_height)
        self.draw_image_with_filters()


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

    def clear_region(self):
        loop = self.get_loop_array_based_on_feature_mode()
        if loop == "single":
            loop = [self.image_index]
        for i in loop:
            self.image_processor.regions[i] = []
        self.draw_image_with_filters()

    def clear_note_type(self, type):
        loop = self.get_loop_array_based_on_feature_mode()
        if loop == "single":
            loop = [self.image_index]
        for i in loop:
            if self.image_processor.is_list_iterable(self.image_processor.notes[i]):
                for j in range(len(self.image_processor.notes[i]) - 1, - 1, -1):
                    note = self.image_processor.notes[i][j]
                    if note.is_half_note == type:
                        print(note.is_half_note)
                        self.image_processor.notes[i].remove(note)
        self.draw_image_with_filters()

    def clear_accidental_type(self, type):
        loop = self.get_loop_array_based_on_feature_mode()
        if loop == "single":
            loop = [self.image_index]
        for i in loop:
            if self.image_processor.is_list_iterable(self.image_processor.accidentals[i]):
                for j in range(len(self.image_processor.accidentals[i]) - 1, - 1, -1):
                    acc = self.image_processor.accidentals[i][j]
                    if acc.type == type:
                        self.image_processor.accidentals[i].remove(acc)
        self.draw_image_with_filters()

    def clear_feature(self, feature_type):
        loop = self.get_loop_array_based_on_feature_mode()
        if loop == "single":
            loop = [self.image_index]
        for i in loop:
            self.image_processor.array_types_dict[feature_type][i] = []
        self.draw_image_with_filters()



    def set_feature_type(self, feature_name, note_type=None):
        if "staff_line" in feature_name:
            self.staff_line_block_coordinates = []
            self.staff_line_diagonal_coordinates = []
        self.current_feature_type = feature_name
        if note_type is not None:
            self.set_note_type(note_type)
        if self.current_feature_type == "note":
            self.selected_label_text.set("Current Feature Selected: \n" + self.note_type.get() + " " + self.current_feature_type)
            print("note set")
        else:
            self.selected_label_text.set("Current Feature Selected: \n" + self.current_feature_type)
            print("other set")
    def set_note_type(self, note_type):
        self.note_type.set(note_type)
        print("note type: ", self.note_type.get())

    def set_key(self, topleft, bottomright):
        loop_array = self.get_loop_array_based_on_feature_mode()
        if loop_array == "single":
            loop_array = [self.image_index]
        for i in loop_array:
            key = self.key_type.get()
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
        if event.char != "":
            print("keypress: ", event.char)
        c = event.char
        #if self.editing_mode.get() == self.editing_modes[0]:#add mode
        if c == 'i' or c == 'I':
            self.zoom_in()
        if c == 'o' or c == "O":
            self.zoom_out()
        if c == 's' or c == "S":
            self.set_feature_type("staff_line")
        if c == 'r' or c == "R":
            self.set_feature_type("bass_clef")
        if c == 't' or c == "T":
            self.set_feature_type("treble_clef")
        if c == 'q' or c == 'Q':
            self.set_note_type("quarter")
            self.set_feature_type("note")
            self.allow_note_to_be_auto_extended.set(True)
            self.threshold_scale.set(80)
        if c == 'n' or c == "N":
            self.set_note_type("quarter")
            self.set_feature_type("note")
            self.allow_note_to_be_auto_extended.set(False)
            self.threshold_scale.set(90)
        if c == 'h' or c == 'H':
            self.set_note_type("half")
            self.set_feature_type("note")
            self.allow_note_to_be_auto_extended.set(True)
            self.threshold_scale.set(80)
        if c == 'w' or c == "W":
            self.set_note_type("whole")
            self.set_feature_type("note")
            self.allow_note_to_be_auto_extended.set(True)
            self.threshold_scale.set(80)
        if c == 'y' or c == "Y":
            self.set_feature_type("barline")
            #setting mode to Single
            self.add_mode_combobox.set(self.add_mode_combobox_values[3])
        if c == 'k' or c == "K":
            self.set_feature_type("key")
        if c == 'm' or c == 'M':
            self.show_borders.set(not self.show_borders.get())
            self.show_crosshairs.set(not self.show_crosshairs.get())
            self.draw_image_with_filters()
        if c == ',':
            self.allow_note_to_be_auto_extended.set(not self.allow_note_to_be_auto_extended.get())
        if c == "[":
            self.current_feature = None
            self.staff_line_diagonal_coordinates = []
            self.staff_line_block_coordinates = []
            self.image_index = (self.image_index - 5) % self.num_pages
            #self.draw_image_canvas_mode()
            self.draw_image_with_filters()
        if c == "]":
            self.current_feature = None
            self.staff_line_diagonal_coordinates = []
            self.staff_line_block_coordinates = []
            self.image_index = (self.image_index + 5) % self.num_pages
            #self.draw_image_canvas_mode()
            self.draw_image_with_filters()
        if c == "{":
            self.current_feature = None
            self.staff_line_diagonal_coordinates = []
            self.staff_line_block_coordinates = []
            self.image_index = (self.image_index - 10) % self.num_pages
            #self.draw_image_canvas_mode()
            self.draw_image_with_filters()
        if c == "}":
            self.current_feature = None
            self.staff_line_diagonal_coordinates = []
            self.staff_line_block_coordinates = []
            self.image_index = (self.image_index + 10) % self.num_pages
            #self.draw_image_canvas_mode()
            self.draw_image_with_filters()

        if self.current_feature is not None:
            if c == 'a' or c == "A":
                self.current_feature.set_letter('A')
                self.draw_image_with_filters()
            if c == 'b' or c == "B":
                self.current_feature.set_letter('B')
                self.draw_image_with_filters()
            if c == 'c' or c == "C":
                self.current_feature.set_letter('C')
                self.draw_image_with_filters()
            if c == 'd' or c == "D":
                self.current_feature.set_letter('D')
                self.draw_image_with_filters()
            if c == 'e' or c == "E":
                self.current_feature.set_letter('E')
                self.draw_image_with_filters()
            if c == 'f' or c == "F":
                self.current_feature.set_letter('F')
                self.draw_image_with_filters()
            if c == 'g' or c == "G":
                self.current_feature.set_letter('G')
                self.draw_image_with_filters()
            if c == 'h' or c == 'H':
                if isinstance(self.current_feature, Note):
                    self.current_feature.is_half_note = not self.current_feature.is_half_note
                    self.draw_image_with_filters()
            if c == '\\':
                if self.current_feature.topleft[0] > 0:
                    self.current_feature.topleft[0] = self.current_feature.topleft[0] - 1
                    if isinstance(self.current_feature, Note):
                        self.current_feature.auto_extended = True
                else:
                    print("out of bounds")
                image_width = self.image_processor.image_widths[self.image_index]
                if self.current_feature.bottomright[0] < image_width - 1:
                    self.current_feature.bottomright[0] = self.current_feature.bottomright[0] + 1
                    if isinstance(self.current_feature, Note):
                        self.current_feature.auto_extended = True
                else:
                    print("out of bounds")
                self.draw_image_with_filters()
            if c == '|':
                if self.current_feature.topleft[0] > 5:
                    self.current_feature.topleft[0] = self.current_feature.topleft[0] - 5
                    if isinstance(self.current_feature, Note):
                        self.current_feature.auto_extended = True
                else:
                    print("out of bounds")
                image_width = self.image_processor.image_widths[self.image_index]
                if self.current_feature.bottomright[0] < image_width - 6:
                    self.current_feature.bottomright[0] = self.current_feature.bottomright[0] + 5
                    if isinstance(self.current_feature, Note):
                        self.current_feature.auto_extended = True
                else:
                    print("out of bounds")
                self.draw_image_with_filters()

            if c == '1':
                self.current_feature.set_accidental("DOUBLE_SHARP")
                self.draw_image_with_filters()
            if c == '2':
                self.current_feature.set_accidental("SHARP")
                self.draw_image_with_filters()
            if c == '3':
                self.current_feature.set_accidental("NATURAL")
                self.draw_image_with_filters()
            if c == '4':
                self.current_feature.set_accidental("FLAT")
                self.draw_image_with_filters()
            if c == '5':
                self.current_feature.set_accidental("DOUBLE_FLAT")
                self.draw_image_with_filters()
            if c == '6':
                self.current_feature.set_accidental("")
                self.draw_image_with_filters()
            if c == 'x' or c == "X":#DELETE
                self.image_processor.remove_feature(self.current_feature, self.image_index)
                print("deleted feature")
                self.current_feature = None
                self.draw_image_with_filters()


        else:
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

    def ctrl_a_key_press(self, event):
        print("keypress: ctrl a")
        if self.only_show_this_note_type.get() == 'a':
            self.only_show_this_note_type.set("none")
        else:
            self.only_show_this_note_type.set('a')
        self.draw_image_with_filters()
    def ctrl_b_key_press(self, event):
        print("keypress: ctrl b")
        if self.only_show_this_note_type.get() == 'b':
            self.only_show_this_note_type.set("none")
        else:
            self.only_show_this_note_type.set('b')
        self.draw_image_with_filters()
    def ctrl_c_key_press(self, event):
        print("keypress: ctrl c")
        if self.only_show_this_note_type.get() == 'c':
            self.only_show_this_note_type.set("none")
        else:
            self.only_show_this_note_type.set('c')
        self.draw_image_with_filters()
    def ctrl_d_key_press(self, event):
        print("keypress: ctrl d")
        if self.only_show_this_note_type.get() == 'd':
            self.only_show_this_note_type.set("none")
        else:
            self.only_show_this_note_type.set('d')
        self.draw_image_with_filters()
    def ctrl_e_key_press(self, event):
        print("keypress: ctrl e")
        if self.only_show_this_note_type.get() == 'e':
            self.only_show_this_note_type.set("none")
        else:
            self.only_show_this_note_type.set('e')
        self.draw_image_with_filters()
    def ctrl_f_key_press(self, event):
        print("keypress: ctrl f")
        if self.only_show_this_note_type.get() == 'f':
            self.only_show_this_note_type.set("none")
        else:
            self.only_show_this_note_type.set('f')
        self.draw_image_with_filters()
    def ctrl_g_key_press(self, event):
        print("keypress: ctrl g")
        if self.only_show_this_note_type.get() == 'g':
            self.only_show_this_note_type.set("none")
        else:
            self.only_show_this_note_type.set('g')
        self.draw_image_with_filters()

    #staffline, implied line, bass, treble, barline, note, accidental, region border
    def ctrl_r_key_press(self, event):
        print("keypress: ctrl r toggle bass clefs")
        self.filter_list[2].set(not self.filter_list[2].get())
        self.draw_image_with_filters()
    def ctrl_t_key_press(self, event):
        print("keypress: ctrl t toggle treble clefs")
        self.filter_list[3].set(not self.filter_list[3].get())
        self.draw_image_with_filters()
    def ctrl_y_key_press(self, event):
        print("keypress: ctrl y toggle barlines")
        self.filter_list[4].set(not self.filter_list[4].get())
        self.draw_image_with_filters()
    def ctrl_s_key_press(self, event):
        print("keypress: ctrl s toggle staff lines")
        self.filter_list[0].set(not self.filter_list[0].get())
        self.draw_image_with_filters()
    def ctrl_n_key_press(self, event):
        print("keypress: ctrl n toggle notes")
        self.filter_list[5].set(not self.filter_list[5].get())
        self.draw_image_with_filters()
    def ctrl_1_key_press(self, event):
        print("keypress: ctrl 1 toggle accidentals")
        self.filter_list[6].set(not self.filter_list[6].get())
        self.draw_image_with_filters()
    def ctrl_2_key_press(self, event):
        print("keypress: ctrl 2 toggle accidentals")
        self.filter_list[6].set(not self.filter_list[6].get())
        self.draw_image_with_filters()

    def ctrl_3_key_press(self, event):
        print("keypress: ctrl 3 toggle accidentals")
        self.filter_list[6].set(not self.filter_list[6].get())
        self.draw_image_with_filters()
    def ctrl_4_key_press(self, event):
        print("keypress: ctrl 4 toggle accidentals")
        self.filter_list[6].set(not self.filter_list[6].get())
        self.draw_image_with_filters()
    def ctrl_5_key_press(self, event):
        print("keypress: ctrl 5 toggle accidentals")
        self.filter_list[6].set(not self.filter_list[6].get())
        self.draw_image_with_filters()

    def ctrl_h_key_press(self, event):
        #show color image
        print("keypress: ctrl h show color image")
        self.view_mode.set(self.view_mode_values[0])
        self.draw_image_with_filters()
    def ctrl_j_key_press(self, event):
        #show intersection iamge
        print("keypress: ctrl j show intersection image")
        self.view_mode.set(self.view_mode_values[1])
        self.draw_image_with_filters()
    def ctrl_k_key_press(self, event):
        #show bw image
        print("keypress: ctrl k show black and white image")
        self.view_mode.set(self.view_mode_values[2])
        self.draw_image_with_filters()
    def ctrl_l_key_press(self, event):
        #show horizontal image
        print("keypress: ctrl l show horizontal image")
        self.view_mode.set(self.view_mode_values[3])
        self.draw_image_with_filters()
    def ctrl_semi_colon_key_press(self, event):
        #show vertical image
        print("keypress: ctrl ; show vertical image")
        self.view_mode.set(self.view_mode_values[4])
        self.draw_image_with_filters()
    def ctrl_single_quote_key_press(self, event):
        print("keypress: ctrl ' show only keep pixels that are vertically eroded image")
        self.view_mode.set(self.view_mode_values[5])
        self.draw_image_with_filters()

    def ctrl_minus_key_press(self, event):
        print("keypress: ctrl - show notes that are on line")
        if self.only_show_this_note_type.get() == 'on_line':
            self.only_show_this_note_type.set("none")
        else:
            self.only_show_this_note_type.set('on_line')
        self.draw_image_with_filters()

    def ctrl_equals_key_press(self, event):
        print("keypress: ctrl = show notes that are not on line")

        if self.only_show_this_note_type.get() == 'not_on_line':
            self.only_show_this_note_type.set("none")
        else:
            self.only_show_this_note_type.set('not_on_line')
        self.draw_image_with_filters()

    def ctrl_zero_key_press(self, event):
        print("keypress: ctrl 0 show notes that are undetermined if they are on line")
        if self.only_show_this_note_type.get() == 'undetermined':
            self.only_show_this_note_type.set("none")
        else:
            self.only_show_this_note_type.set('undetermined')
        self.draw_image_with_filters()
    def ctrl_nine_key_press(self, event):
        print("keypress: ctrl 9 show chord errors")
        if self.only_show_this_note_type.get() == 'chord_errors':
            self.only_show_this_note_type.set("none")
        else:
            self.only_show_this_note_type.set('chord_errors')
        self.draw_image_with_filters()

    def on_f1_press(self, event):
        print("keypress: f1 generate staff lines using horizontal erode")
        #self.generate_staff_lines_diagonal_by_traversing_vertical_line()
        self.generate_staff_lines_diagonal_by_traversing_vertical_line_using_horizontal_erode(override=True)
    def on_f2_press(self, event):
        print("keypress: f2 extend notes")
        self.auto_extend_notes()
    def on_f3_press(self, event):
        print("keypress: f3 calculate note letters")
        self.calculate_notes_for_regions_using_staff_lines(overwrite=self.overwrite_regions.get())
    def on_f4_press(self, event):
        print("keypress: f4 calculate accidental letters")
        self.calculate_note_accidentals_for_regions(overwrite=self.overwrite_regions.get())
    def on_f5_press(self, event):
        print("keypress: f5 regenerate image")
        self.regenerate_images()
        #if self.fast_editing_mode.get() == True:
        #    self.regenerate_images()

    def on_f6_press(self, event):
        print("keypress: f6 open image in paint")
        self.open_paint()
    def on_f7_press(self, event):
        print("keypress: f7 handle halg and quarter note overlap")
        self.handle_half_and_quarter_note_overlap()
    def on_f9_press(self, event):
        print("keypress: f9 set add mode to \"Current page and next\"")
        self.add_mode_combobox.set(self.add_mode_combobox_values[0])
        self.set_cursor()
    def on_f10_press(self, event):
        print("keypress: f10 set add mode to \"Current page\"")
        self.add_mode_combobox.set(self.add_mode_combobox_values[1])
        self.set_cursor()
    def on_f11_press(self, event):
        print("keypress: f11 set add mode to \"All pages\"")
        self.add_mode_combobox.set(self.add_mode_combobox_values[2])
        self.set_cursor()
    def on_f12_press(self, event):
        print("keypress: f12 set add mode to \"Single\"")
        self.add_mode_combobox.set(self.add_mode_combobox_values[3])
        self.set_cursor()


    def todofunc(self, event):
        print("event", event)

    def scroll_vertical(self, event):
        self.current_feature = None
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def scroll_horizontal(self, event):
        self.current_feature = None
        self.canvas.xview_scroll(int(-1 * (event.delta / 120)), "units")


    def open_pdf(self):
        file_path = filedialog.askopenfilename(title="Open PDF File", initialdir=self.dirname, filetypes=[("PDF Files", "*.pdf")])  # TODO initialdir
        f = file_path.split('/')
        self.file_name = f[-1]  # extracting filename from full directory
        self.file_name = self.file_name[:-4]  # remove .pdf
        if file_path:
            print("Filename: ", self.file_name)
            self.num_pages = PDFtoImages.filename_to_images(file_path)
            self.image_processor = ImageProcessing(self.dirname, file_path, self.num_pages)
            self.draw_image_with_filters()
        else:
            print("no file selected")


    def save_pdf(self):
        pdf_path = filedialog.asksaveasfilename(filetypes=[("PDF", "*.pdf")], defaultextension=[("PDF", "*.pdf")], initialfile=self.file_name + "_cheatmusic.pdf")
        if pdf_path == "":
            print("no pdf selected")
            return
        images = []
        filter_list = []
        for i in range(8):
            filter_list.append(tk.IntVar())
            if i == 5 or i == 6:
                filter_list[i].set(1)
            else:
                filter_list[i].set(0)
        for i in range(self.num_pages):
            print("save pdf page", i)
            image = cv.cvtColor(self.image_processor.draw_image_without_writing(filter_list, i, False, False, None, 1), cv.COLOR_BGR2RGB)
            images.append(Image.fromarray(image))
        images[0].save(pdf_path, "PDF", resolution=100.0, save_all=True, append_images=images[1:])
        print("pdf saved", pdf_path)

    def save_pdf_for_double_sided_printing(self):
        pdf_path = filedialog.asksaveasfilename(filetypes=[("PDF", "*.pdf")], defaultextension=[("PDF", "*.pdf")],
                                                initialfile=self.file_name + "_cheatmusic.pdf")
        if pdf_path == "":
            print("no pdf selected")
            return
        images = []
        filter_list = []
        for i in range(8):
            filter_list.append(tk.IntVar())
            if i == 5 or i == 6:
                filter_list[i].set(1)
            else:
                filter_list[i].set(0)
        loop = range(self.num_pages // 2)
        #todo change loop to
        for i in loop:
            print("save pdf page", i)
            image = cv.cvtColor(self.image_processor.draw_image_without_writing(filter_list, i, False, False, None, 1),
                                cv.COLOR_BGR2RGB)
            images.append(Image.fromarray(image))
        images[0].save(pdf_path, "PDF", resolution=100.0, save_all=True, append_images=images[1:])
        print("pdf saved", pdf_path)
    def save_binary(self):
        path = filedialog.asksaveasfilename(filetypes=[("pkl", "*.pkl")], defaultextension=[("pkl", "*.pkl")], initialfile=self.file_name)
        if path == "":
            print("no filename")
            return
        with open(path, "wb") as file:
            for i in range(self.num_pages):
                self.image_processor.images[i] = cv.imread(self.image_processor.images_filenames[i])
            pickle.dump(self.image_processor, file)
            pickle.dump(self.file_name, file)
            print("saved", path)

    def load_binary(self):
        file_path = filedialog.askopenfilename(title="Open pkl File", initialdir=self.dirname, filetypes=[("pkl files", "*.pkl")])  # TODO initialdir
        if file_path == "":
            print("no file selected")
            return
        with open(file_path, "rb") as file:
            print("open", file_path)
            self.image_processor = pickle.load(file)
            self.file_name = pickle.load(file)
            self.num_pages = self.image_processor.num_pages
            self.image_index = 0
            self.dirname = os.path.dirname(__file__)
            self.image_processor.dirname = self.dirname
            self.image_processor.images_filenames = []
            self.image_processor.annotated_images_filenames = []
            # write the images
            for i in range(self.num_pages):
                self.image_processor.images_filenames.append(self.dirname + '\\SheetsMusic\\page' + str(i) + '.jpg')
                self.image_processor.annotated_images_filenames.append(self.dirname + '\\SheetsMusic\\Annotated\\annotated' + str(i) + '.png')
                cv.imwrite(self.image_processor.images_filenames[i], self.image_processor.images[i])
            #problem = self.image_processor.determine_if_half_notes_are_on_line()
            #if problem:
            #    messagebox.showinfo("Half note expected to be on line", "Used click and drage to detect half note, however only 1 rect was found.")
            #todo remove
            #todo add extending notes by 2 pixels
            #self.generate_staff_lines_diagonal_by_traversing_vertical_line_using_horizontal_erode(True)
            #self.erode_strength_scale.set(250)
            #self.calculate_notes_for_distorted_staff_lines_using_horizontal_erode(True)
            #self.convert_is_half_note()
            self.draw_image_with_filters()

    def modify_filepath(self, filepath):
        # Split the path into directory and filename
        dir_path, file_name = os.path.split(filepath)

        # Extract the file name without the extension
        file_stem, file_ext = os.path.splitext(file_name)

        # Create the new directory path by appending the file_stem
        new_dir_path = os.path.join(dir_path, file_stem)
        print("new dir path", new_dir_path.replace("\\", '/'))
        # Create the new full file path
        try:
            os.makedirs(new_dir_path.replace("\\", '/'), exist_ok=True)  # Creates all intermediate directories if needed
            print(f"Folder created: {path}")
        except Exception as e:
            print(f"Error: {e}")
        new_filepath = os.path.join(new_dir_path, file_name)
        new_filepath = new_filepath.replace("\\", "/")

        return new_filepath
    '''
    def save_binary_compressed(self):
        path = filedialog.asksaveasfilename(filetypes=[("pkl", "*.pkl")], defaultextension=[("pkl", "*.pkl")],
                                            initialfile=self.file_name)
        if path == "":
            print("no filename")
            return
        #todo save pdf of images and all other image processor info
        #print(path)
        path = self.modify_filepath(path)
        #print(path)
        print(path[:-4] + ".pdf")
        with open(path, "wb") as file:
            #todo create folder: inset /filename/filename.pkl, save pdf and annotations in folder
            images = []
            for i in range(self.num_pages):
                #print("save pdf page", i)
                image = cv.cvtColor(self.image_processor.draw_image_without_writing(filter_list, i, False, False, None, 1),cv.COLOR_BGR2RGB)
                images.append(Image.fromarray(self.image_processor))
            images[0].save(path[:-4] + ".pdf", "PDF", resolution=100.0, save_all=True, append_images=images[1:])
            pickle.dump(self.file_name, file)
            # pickle.dump(self.image_processor.images, file)
            pickle.dump(self.image_processor.staff_lines, file)
            pickle.dump(self.image_processor.treble_clefs, file)
            pickle.dump(self.image_processor.bass_clefs, file)
            pickle.dump(self.image_processor.barlines, file)
            pickle.dump(self.image_processor.barlines_2d, file)
            pickle.dump(self.image_processor.accidentals, file)
            pickle.dump(self.image_processor.notes, file)
            pickle.dump(self.image_processor.image_heights, file)
            pickle.dump(self.image_processor.image_widths, file)
            pickle.dump(self.image_processor.all_clefs, file)
    '''

    def save_binary_compressed(self):
        path = filedialog.asksaveasfilename(filetypes=[("pkl", "*.pkl")], defaultextension=[("pkl", "*.pkl")],
                                            initialfile=self.file_name)
        if path == "":
            print("no filename")
            return
        # todo save pdf of images and all other image processor info
        # print(path)
        path = self.modify_filepath(path)
        # print(path)
        print(path[:-4] + ".pdf")
        with open(path, "wb") as file:
            pickle.dump(self.num_pages)
            # todo create folder: inset /filename/filename.pkl, save pdf and annotations in folder
            for img in self.image_processor.images:
                compressed = blosc.compress(img)
                pickle.dump(compressed)
            pickle.dump(self.file_name, file)
            # pickle.dump(self.image_processor.images, file)
            pickle.dump(self.image_processor.staff_lines, file)
            pickle.dump(self.image_processor.treble_clefs, file)
            pickle.dump(self.image_processor.bass_clefs, file)
            pickle.dump(self.image_processor.barlines, file)
            pickle.dump(self.image_processor.barlines_2d, file)
            pickle.dump(self.image_processor.accidentals, file)
            pickle.dump(self.image_processor.notes, file)
            pickle.dump(self.image_processor.image_heights, file)
            pickle.dump(self.image_processor.image_widths, file)
            pickle.dump(self.image_processor.all_clefs, file)
    def load_binary_compressed(self):
        #todo open pdf, convert to image, get bw , grayscale. load rest of image processor
        file_path = filedialog.askopenfilename(title="Open pkl File", initialdir=self.dirname, filetypes=[("pkl files", "*.pkl")])  # TODO initialdir
        if file_path == "":
            print("no file selected")
            return
        with open(file_path, "rb") as file:
            print("open", file_path)
            self.num_pages = pickle.load(file)
            self.image_processor = ImageProcessing(self.num_pages)
            for i in range(self.num_pages):
                self.image_processor.images[i] = blosc.decompress(pickle.load(file))
            self.image_processor = pickle.load(file)
            self.file_name = pickle.load(file)
            self.image_index = 0
            self.dirname = os.path.dirname(__file__)
            self.image_processor.dirname = self.dirname
            self.image_processor.images_filenames = []
            self.image_processor.annotated_images_filenames = []
            # write the images
            for i in range(self.num_pages):
                self.image_processor.images_filenames.append(self.dirname + '\\SheetsMusic\\page' + str(i) + '.jpg')
                self.image_processor.annotated_images_filenames.append(self.dirname + '\\SheetsMusic\\Annotated\\annotated' + str(i) + '.png')
                cv.imwrite(self.image_processor.images_filenames[i], self.image_processor.images[i])
            problem = self.image_processor.determine_if_half_notes_are_on_line()
            if problem:
                messagebox.showinfo("Half note expected to be on line", "Used click and drage to detect half note, however only 1 rect was found.")
            # todo remove
            # todo add extending notes by 2 pixels
            # self.generate_staff_lines_diagonal_by_traversing_vertical_line_using_horizontal_erode(True)
            # self.erode_strength_scale.set(250)
            # self.calculate_notes_for_distorted_staff_lines_using_horizontal_erode(True)
            # self.convert_is_half_note()
            self.draw_image_with_filters()
        pass
    '''
    def save_annotations(self):
        path = filedialog.asksaveasfilename(filetypes=[("pkl", "*.pkl")], defaultextension=[("pkl", "*.pkl")],
                                            initialfile=self.file_name)
        if path == "":
            print("No file selected")
            return
        with open(path, "wb") as file:
            pickle.dump(self.image_processor.treble_clefs)
            pickle.dump(self.image_processor.bass_clefs)
            pickle.dump(self.image_processor.stafflines)
            pickle.dump(self.image_processor.barlines)
            pickle.dump(self.image_processor.notes)
            pickle.dump(self.image_processor.accidentals)



    def load_annotations(self):
        file_path = filedialog.askopenfilename(title="Open pkl File", initialdir=self.dirname, filetypes=[("pkl files", "*.pkl")])
        with open(file_path, "rb") as file:
            self.image_processor.treble_clefs = pickle.load(file)
            self.image_processor.bass_clefs = pickle.load(file)
            self.image_processor.staff_lines = pickle.load(file)
            self.image_processor.barlines = pickle.load(file)
            self.image_processor.notes = pickle.load(file)
            self.image_processor.accidentals = pickle.load(file)

            #for i in range(self.num_pages):
            #    cv.imwrite(self.image_processor.images_filenames[i], self.image_processor.images[i])
            self.draw_image_with_filters()
    '''
    def bgr_to_hex(self, bgr):
        """Convert a BGR color tuple to a hex color string."""
        return "#{:02x}{:02x}{:02x}".format(bgr[2], bgr[1], bgr[0])

    def draw_image_with_filters(self):
        self.page_indicator.set(str(self.image_index) + "/" + str(self.num_pages))
        self.reload_image()
        self.canvas.create_image(0, 0, image=self.photo, anchor="nw")
        self.canvas.config(scrollregion=self.canvas.bbox(tk.ALL))

    def reload_image(self):
        if self.view_mode.get() == self.view_mode_values[0]:#color:
            image = cv.cvtColor(self.image_processor.draw_image_without_writing(self.filter_list, self.image_index, self.show_borders.get(), self.show_crosshairs.get(), self.current_feature, self.scale, self.only_show_this_note_type.get()), cv.COLOR_BGR2RGB)
            self.image = Image.fromarray(image)
            self.photo = ImageTk.PhotoImage(self.image)
        elif self.view_mode.get() == self.view_mode_values[1]:#erode image
            image = self.image_processor.get_intersection_image(self.image_index, self.erode_strength_scale.get() / 100, draw_notes=True)
            h, w = image.shape[:2]
            image = cv.resize(image, (int(w * self.scale), int(h * self.scale)))
            self.image = Image.fromarray(image)
            self.photo = ImageTk.PhotoImage(self.image)
        elif self.view_mode.get() == self.view_mode_values[2]:#black and white image
            #todo get bw image and below images
            image = self.image_processor.bw_images[self.image_index]
            h, w = image.shape[:2]
            image = cv.resize(image, (int(w * self.scale), int(h * self.scale)))
            self.image = Image.fromarray(image)
            self.photo = ImageTk.PhotoImage(self.image)
        elif self.view_mode.get() == self.view_mode_values[3]:#horizontal image
            image = self.image_processor.get_horizontal_image(self.image_index, self.erode_strength_scale.get() / 100, draw_notes=True)
            h, w = image.shape[:2]
            image = cv.resize(image, (int(w * self.scale), int(h * self.scale)))
            self.image = Image.fromarray(image)
            self.photo = ImageTk.PhotoImage(self.image)
        elif self.view_mode.get() == self.view_mode_values[4]:#vertical image
            image = self.image_processor.get_vertical_image(self.image_index, self.erode_strength_scale.get() / 100, draw_notes=True)
            h, w = image.shape[:2]
            image = cv.resize(image, (int(w * self.scale), int(h * self.scale)))
            self.image = Image.fromarray(image)
            self.photo = ImageTk.PhotoImage(self.image)
        elif self.view_mode.get() == self.view_mode_values[5]:#only keep vertical eroded pixels
            image = self.image_processor.get_keep_only_vertical_erode_image(self.image_index, 5)
            h, w = image.shape[:2]
            image = cv.resize(image, (int(w * self.scale), int(h * self.scale)))
            self.image = Image.fromarray(image)
            self.photo = ImageTk.PhotoImage(self.image)

    def on_blackness_scale_change(self, value):
        #print("blackness scale change")
        #if self.view_mode.get() == self.view_mode_values[2]:#bw image
        #    self.draw_image_with_filters()
        pass

    def on_erode_scale_change(self, value):
        #print("erode scale change")
        if self.view_mode.get() in [self.view_mode_values[1], self.view_mode_values[3], self.view_mode_values[4]]:
            self.draw_image_with_filters()
        if self.view_mode.get() == self.view_mode_values[0] and self.image_processor is not None:
            image = self.image_processor.get_intersection_image(self.image_index, self.erode_strength_scale.get() / 100, draw_notes=True)
            h, w = image.shape[:2]
            image = cv.resize(image, (int(w * self.scale), int(h * self.scale)))
            self.image = Image.fromarray(image)
            self.photo = ImageTk.PhotoImage(self.image)
            self.canvas.create_image(0, 0, image=self.photo, anchor="nw")
            self.canvas.config(scrollregion=self.canvas.bbox(tk.ALL))

    def left_key_press(self, event):
        print("left key pressed")
        if self.current_feature is not None:
            if self.current_feature.topleft[0] > 0:
                self.current_feature.topleft[0] = self.current_feature.topleft[0] - 1
                if isinstance(self.current_feature, Note):
                    self.current_feature.auto_extended = True
            else:
                print("out of bounds")
            print("Updated feature: ", self.current_feature)
            self.draw_image_with_filters()
        else:
            self.previous_image()





    def right_key_press(self, event):
        print("right key pressed")
        if self.current_feature is not None:
            image_width = self.image_processor.image_widths[self.image_index]
            if self.current_feature.bottomright[0] < image_width - 1:
                self.current_feature.bottomright[0] = self.current_feature.bottomright[0] + 1
                if isinstance(self.current_feature, Note):
                    self.current_feature.auto_extended = True
            else:
                print("out of bounds")
            print("Updated feature: ", self.current_feature)
            self.draw_image_with_filters()
        else:
            self.next_image()

    def up_key_press(self, event):
        if self.current_feature is not None:
            if self.current_feature.topleft[1] > 0:
                self.current_feature.topleft[1] = self.current_feature.topleft[1] - 1
                if isinstance(self.current_feature, Note):
                    self.current_feature.auto_extended = True
            else:
                print("out of bounds")
            print("Updated feature: ", self.current_feature)
            self.draw_image_with_filters()
        else:
            print("no feature selected")

    def down_key_press(self, event):
        if self.current_feature is not None:
            image_height = self.image_processor.image_heights[self.image_index]
            if self.current_feature.bottomright[1] < image_height - 1:
                self.current_feature.bottomright[1] = self.current_feature.bottomright[1] + 1
                if isinstance(self.current_feature, Note):
                    self.current_feature.auto_extended = True
            else:
                print("out of bounds")
            print("Updated feature: ", self.current_feature)
            self.draw_image_with_filters()
        else:
            print("no feature selected")

    def shift_left_key_press(self, event):
        if self.current_feature is not None:
            if self.current_feature.bottomright[0] > 0 and self.current_feature.bottomright[0] > self.current_feature.topleft[0] + 1:
                self.current_feature.bottomright[0] = self.current_feature.bottomright[0] - 1
                if isinstance(self.current_feature, Note):
                    self.current_feature.auto_extended = True
            else:
                print("out of bounds")
            print("Updated feature: ", self.current_feature)
            self.draw_image_with_filters()

    def shift_right_key_press(self, event):
        if self.current_feature is not None:
            image_width = self.image_processor.image_widths[self.image_index]
            if self.current_feature.topleft[0] < image_width - 1 and self.current_feature.bottomright[0] > self.current_feature.topleft[0] + 1:
                self.current_feature.topleft[0] = self.current_feature.topleft[0] + 1
                if isinstance(self.current_feature, Note):
                    self.current_feature.auto_extended = True
            else:
                print("out of bounds")
            print("Updated feature: ", self.current_feature)
            self.draw_image_with_filters()

    def shift_up_key_press(self, event):
        if self.current_feature is not None:
            if self.current_feature.bottomright[1] > 0 and self.current_feature.bottomright[1] > self.current_feature.topleft[1] + 1:
                self.current_feature.bottomright[1] = self.current_feature.bottomright[1] - 1
                if isinstance(self.current_feature, Note):
                    self.current_feature.auto_extended = True
            else:
                print("out of bounds")
            print("Updated feature: ", self.current_feature)
            self.draw_image_with_filters()

    def shift_down_key_press(self, event):
        if self.current_feature is not None:
            image_height = self.image_processor.image_heights[self.image_index]
            if self.current_feature.topleft[1] < image_height - 1 and self.current_feature.bottomright[1] > self.current_feature.topleft[1] + 1:
                self.current_feature.topleft[1] = self.current_feature.topleft[1] + 1
                if isinstance(self.current_feature, Note):
                    self.current_feature.auto_extended = True
            else:
                print("out of bounds")
            print("Updated feature: ", self.current_feature)
            self.draw_image_with_filters()

    def ctrl_left_key_press(self, event):
        if self.current_feature is not None:
            self.current_feature.set_center([self.current_feature.center[0] - 1, self.current_feature.center[1]])
            self.draw_image_with_filters()

    def ctrl_right_key_press(self, event):
        if self.current_feature is not None:
            self.current_feature.set_center([self.current_feature.center[0] + 1, self.current_feature.center[1]])
            self.draw_image_with_filters()

    def ctrl_up_key_press(self, event):
        if self.current_feature is not None:
            self.current_feature.set_center([self.current_feature.center[0], self.current_feature.center[1] - 1])
            self.draw_image_with_filters()

    def ctrl_down_key_press(self, event):
        if self.current_feature is not None:
            self.current_feature.set_center([self.current_feature.center[0], self.current_feature.center[1] + 1])
            self.draw_image_with_filters()

    def alt_left_key_press(self, event):
        if self.current_feature is not None:
            if self.current_feature.topleft[0] > 5:
                self.current_feature.topleft[0] = self.current_feature.topleft[0] - 5
            else:
                print("out of bounds")
            print("Updated feature: ", self.current_feature)
            self.draw_image_with_filters()

    def alt_right_key_press(self, event):
        if self.current_feature is not None:
            image_width = self.image_processor.image_widths[self.image_index]
            if self.current_feature.bottomright[0] < image_width - 6:
                self.current_feature.bottomright[0] = self.current_feature.bottomright[0] + 5
            else:
                print("out of bounds")
            print("Updated feature: ", self.current_feature)
            self.draw_image_with_filters()

    def alt_up_key_press(self, event):
        if self.current_feature is not None:
            if self.current_feature.topleft[1] > 5:
                self.current_feature.topleft[1] = self.current_feature.topleft[1] - 5
            else:
                print("out of bounds")
            print("Updated feature: ", self.current_feature)
            self.draw_image_with_filters()

    def alt_down_key_press(self, event):
        if self.current_feature is not None:
            image_height = self.image_processor.image_heights[self.image_index]
            if self.current_feature.bottomright[1] < image_height - 6:
                self.current_feature.bottomright[1] = self.current_feature.bottomright[1] + 5
            else:
                print("out of bounds")
            print("Updated feature: ", self.current_feature)
            self.draw_image_with_filters()



    def next_image(self):
        #print("test")
        self.current_feature = None
        self.staff_line_diagonal_coordinates = []
        self.staff_line_block_coordinates = []
        self.image_index = (self.image_index + 1) % self.num_pages
        #self.draw_image_canvas_mode()
        self.draw_image_with_filters()

    def previous_image(self):
        self.current_feature = None
        self.staff_line_diagonal_coordinates = []
        self.staff_line_block_coordinates = []
        self.image_index = (self.image_index - 1) % self.num_pages
        #self.draw_image_canvas_mode()
        self.draw_image_with_filters()

    def zoom_in(self):
        self.scale *= 1.1
        self.draw_image_with_filters()

    def zoom_out(self):
        self.scale /= 1.1
        self.draw_image_with_filters()



    def on_right_click(self, event):
        self.current_feature = None
        y = self.canvas.canvasy(event.y)
        x = self.canvas.canvasx(event.x)
        y_img = int(y / self.scale)
        x_img = int(x / self.scale)
        # Has to have image loaded onto the canvas
        if self.image is not None:
            self.rect_start = (self.canvas.canvasx(event.x), self.canvas.canvasy(event.y))
            if self.rect:
                self.canvas.delete(self.rect)
            self.rect = None


        print("right click")

    def on_right_click_drag(self, event):
        curX, curY = (self.canvas.canvasx(event.x), self.canvas.canvasy(event.y))
        if self.rect:
            self.canvas.coords(self.rect, self.rect_start[0], self.rect_start[1], curX, curY)
        else:
            self.rect = self.canvas.create_rectangle(self.rect_start[0], self.rect_start[1], curX, curY, outline='red')

    def on_right_click_release(self, event):
        curX, curY = (self.canvas.canvasx(event.x), self.canvas.canvasy(event.y))
        x0, y0 = self.rect_start
        x1, y1 = curX, curY

        # Convert canvas coordinates to image coordinates
        x0_img = int(x0 / self.scale)
        y0_img = int(y0 / self.scale)
        x1_img = int(x1 / self.scale)
        y1_img = int(y1 / self.scale)
        if x1_img < x0_img:
            temp = x1_img
            x1_img = x0_img
            x0_img = temp
        if y1_img < y0_img:
            temp = y1_img
            y1_img = y0_img
            y0_img = temp

        #if dragged
        if self.rect:
            if "staff_line" in self.current_feature_type:
                # find closest staff line and delete it
                for i in range(len(self.image_processor.staff_lines[self.image_index]) - 1, -1, -1):
                    line = self.image_processor.staff_lines[self.image_index][i]
                    #if midpoint of line is in rect
                    if y0_img < line.calculate_y(int(abs(x0_img - x1_img) / 2)) < y1_img:
                        self.image_processor.staff_lines[self.image_index].remove(line)
            else:
                features = self.image_processor.array_types_dict[self.current_feature_type][self.image_index]
                for i in range(len(features) - 1, -1, -1):
                    f = features[i]
                    topleft = f.topleft
                    bottomright = f.bottomright
                    if x0_img < topleft[0] < x1_img and x0_img < bottomright[0] < x1_img and y0_img < topleft[1] < y1_img and y0_img < bottomright[1] < y1_img:
                        features.remove(f)
        #if not dragged
        else:
            if "staff_line" in self.current_feature_type:
                # find closest staff line and delete it
                closest_line = self.image_processor.find_closest_staff_line(self.image_index, [x1_img, y1_img])
                if closest_line is not None:
                    self.image_processor.staff_lines[self.image_index].remove(closest_line)
                    print("removed line at y: ", closest_line.calculate_y(x1_img))
                else:
                    print("No line found")
            else:
                feature = self.image_processor.find_closest_feature(self.current_feature_type, self.image_index, x1_img,
                                                                    y1_img)
                if feature is not None:
                    print("feature removed: ", feature)
                    self.image_processor.remove_feature(feature, self.image_index)
                else:
                    print("No feature in click area")
        self.draw_image_with_filters()

    def on_control_button_press(self, event):
        y = self.canvas.canvasy(event.y)
        x = self.canvas.canvasx(event.x)
        y_img = int(y / self.scale)
        x_img = int(x / self.scale)
        if self.current_feature is not None:
            self.current_feature.set_center([x_img, y_img])
        print("control click")
        self.draw_image_with_filters()

    def on_control_shift_button_press(self, event):
        print("control shift click")
        y = self.canvas.canvasy(event.y)
        x = self.canvas.canvasx(event.x)
        y_img = int(y / self.scale)
        x_img = int(x / self.scale)
        self.image_processor.images[self.image_index][y_img][x_img] = (255, 255, 255)
        cv.imwrite(self.image_processor.images_filenames[self.image_index] + ".jpg", self.image_processor.images[self.image_index])

    def on_button_press(self, event):
        self.clear_combobox(event)
        #Has to have image loaded onto the canvas
        y = self.canvas.canvasy(event.y)
        x = self.canvas.canvasx(event.x)
        y_img = int(y / self.scale)
        x_img = int(x / self.scale)
        if self.image is not None:
            self.rect_start = (self.canvas.canvasx(event.x), self.canvas.canvasy(event.y))
            if self.rect:
                self.canvas.delete(self.rect)
            self.rect = None

            #self.draw_image_with_filters()

                

    def on_mouse_drag(self, event):
        curX, curY = (self.canvas.canvasx(event.x), self.canvas.canvasy(event.y))
        if self.rect:
            self.canvas.coords(self.rect, self.rect_start[0], self.rect_start[1], curX, curY)
        else:
            self.rect = self.canvas.create_rectangle(self.rect_start[0], self.rect_start[1], curX, curY, outline='red')

    def on_button_release(self, event):
        #print("released")

        if self.rect:
            print("click and drag")
            curX, curY = (self.canvas.canvasx(event.x), self.canvas.canvasy(event.y))
            x0, y0 = self.rect_start
            x1, y1 = curX, curY

            # Convert canvas coordinates to image coordinates
            x0_img = int(x0 / self.scale)
            y0_img = int(y0 / self.scale)
            x1_img = int(x1 / self.scale)
            y1_img = int(y1 / self.scale)
            if x1_img < x0_img:
                temp = x1_img
                x1_img = x0_img
                x0_img = temp
            if y1_img < y0_img:
                temp = y1_img
                y1_img = y0_img
                y0_img = temp
            #print("heiggt", str(y1_img - y0_img))


            rectangle = Feature([x0_img, y0_img], [x1_img, y1_img], self.current_feature_type)

            if self.current_feature_type == "key":
                print("key")
                self.set_key(rectangle.topleft, rectangle.bottomright)
                return

            if "staff_line" in self.current_feature_type:
                staff_line_error = self.staff_line_error_scale.get()
                self.image_processor.get_staff_lines_region(self.image_index, [x0_img, y0_img], [x1_img, y1_img], staff_line_error)
                self.draw_image_with_filters()
                return
            if "staff_line" in self.current_feature_type:
                return
            template = self.image_processor.images[self.image_index][rectangle.topleft[1]:rectangle.bottomright[1],
                       rectangle.topleft[0]:rectangle.bottomright[0]]
            if self.allow_small_template_matching.get() == False and self.add_mode_combobox.get() != "Single":
                if rectangle.get_width() <= 4 and rectangle.get_height() <= 4:
                    print("rect to small. try disabling Allow small or all white rectangles for template matching in Info menu")
                    return
                h, w = template.shape[:2]
                white_count = 0
                gray_template = cv.cvtColor(template, cv.COLOR_BGR2GRAY)
                _, template_bw = cv.threshold(gray_template, 127, 255, cv.THRESH_BINARY)
                for y_traverse in range(h):
                    for x_traverse in range(w):
                        if template_bw[y_traverse][x_traverse] == 255:
                            white_count += 1
                #print(white_count / (h * w) > .90, " white percentage")
                if white_count / (h * w) > .90:
                    print("rect to white, try disabling Allow small or all white rectangles for template matching in Info menu")
                    return

            if self.get_loop_array_based_on_feature_mode() != "single":#if the add mode is in single, dont need to match template
                #todo add messageg box
                loop_list = self.get_loop_array_based_on_feature_mode()

                message = ""
                if "note" == rectangle.type:
                    message = "Template matching for " + self.note_type.get() + " " + rectangle.type + "\n"
                else:
                    message = "Template matching for " + rectangle.type + "\n"
                message += "Pages(inclusive): " + str(loop_list[0]) + ":" + str(loop_list[-1]) + "\n"
                if not messagebox.askokcancel("Template Matching", message):
                    print("canceled")
                    return
                match_template_params = (
                    template,
                    (0, 255, 0),
                    rectangle.type,
                    self.note_type.get(),
                    not self.allow_note_to_be_auto_extended.get(),
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
                total_features_found, total_features_removed = 0, 0
                print_features_removed = True
                if self.allow_overlapping.get() == 0:
                    print("removing overlapping squares")
                    for i in loop_list:
                        existing_features = self.image_processor.array_types_dict[rectangle.type][i]
                        if existing_features is None:
                            print_features_removed = False
                            break
                        total_features_found += len(results[i - index_adjustment])
                        filtered_results = [
                            new_feature for new_feature in results[i - index_adjustment]
                            if not any(
                                ImageEditor.do_features_overlap(new_feature, existing_feature) for existing_feature
                                in existing_features)
                        ]
                        total_features_removed += len(results[i - index_adjustment]) - len(filtered_results)
                        #print("Page", i, ":", count, "features found.", count - len(filtered_results), "features removed for overlap")
                        results[i - index_adjustment] = filtered_results
                        #if existing_features is not None and len(existing_features) > 0 and len(results[i - index_adjustment]) > 0:
                        #    for new_feature in results[i - index_adjustment][:]:
                        #        for existing_feature in existing_features:
                        #            if ImageEditor.do_features_overlap(new_feature, existing_feature) == True:
                        #                results[i - index_adjustment].remove(new_feature)
                    if print_features_removed == True:
                        print("total number of features found after removing overlapping features:", total_features_found - total_features_removed)
                for i in loop_list:
                    self.undo_features[i] = results[i - index_adjustment]
                    self.image_processor.append_features(i, rectangle.type, results[i - index_adjustment])
                    '''
                    if self.image_processor.array_types_dict[rectangle.type][i] is None:
                        self.image_processor.array_types_dict[rectangle.type][i] = results[i - index_adjustment]
                    else:
                        self.image_processor.array_types_dict[rectangle.type][i] = self.image_processor.array_types_dict[rectangle.type][i] + results[i - index_adjustment]
                    self.image_processor.sort_features(self.image_processor.array_types_dict[rectangle.type][i])
                    '''

                    #self.undo_features = self.undo_features + results[i - index_adjustment]



                #TODO if staffline

                # Draw the rectangle on the actual image
                draw = ImageDraw.Draw(self.image)
                draw.rectangle([x0_img, y0_img, x1_img, y1_img], outline='red')
                self.draw_image_with_filters()

            else:#only add single feature
                print("single feature")
                #append_rect = True
                #if rect is small:
                if rectangle.get_width() <=3 and rectangle.get_height() <= 3:
                    if self.current_feature_type in ["double_flat", "flat", "natural", "sharp", "double_sharp"]:
                        print("small rect interpreted as click")
                        self.image_processor.add_feature_on_click(self.image_index, rectangle.center[0], rectangle.center[1], self.current_feature_type)
                        self.image_processor.calculate_accidental_letter_by_finding_closest_note(self.image_index, overwrite=False)
                else:#if rect isnt small
                    if rectangle.type == "note": #if note
                        auto_extended = not self.allow_note_to_be_auto_extended.get()
                        #print(auto_extended, "auto_extended")
                        note_type = self.note_type.get()
                        #print("note_type", note_type)
                        rectangle = Note(rectangle.topleft, rectangle.bottomright, is_half_note=note_type, auto_extended=auto_extended)
                        if self.num_notes_combobox.get() != "1":
                            rectangle = self.convert_notes([rectangle])
                        else:
                            if self.allow_note_to_be_auto_extended.get() == True:
                                #print("auto extend note single")
                                if self.note_type.get() == "quarter":
                                    self.image_processor.auto_extend_notes(self.image_index, self.note_width_ratio_scale.get(), self.debugging.get(), self.erode_strength_scale.get() / 100, rectangle)
                                else:
                                    is_note_on_space = self.image_processor.extend_half_note_single_drag(self.image_index, rectangle)
                                    if is_note_on_space == True:
                                        messagebox.showinfo("Half note expected to be on line", "Used click and drage to detect half note, however only 1 rect was found.")
                            if note_type != "quarter" and rectangle.auto_extended == True or self.allow_note_to_be_auto_extended.get() == False:
                                self.image_processor.append_features(self.image_index, rectangle.type, [rectangle])
                            self.calculate_notes_for_regions_using_staff_lines_single_page(overwrite=False, page_index=self.image_index)
                            self.draw_image_with_filters()
                            return

                    #if append_rect is True:

                    if isinstance(rectangle, list):
                        self.image_processor.append_features(self.image_index, rectangle[0].type, rectangle)
                    else:
                        self.image_processor.append_features(self.image_index, rectangle.type, [rectangle])

                self.draw_image_with_filters()

        else:#if rect wasnt started
            print("click with no drag")
            curX, curY = (self.canvas.canvasx(event.x), self.canvas.canvasy(event.y))
            x, y = curX, curY

            # Convert canvas coordinates to image coordinates
            x_img = int(x / self.scale)
            y_img = int(y / self.scale)

            if self.current_feature_type == "staff_line_block":

                self.staff_line_block_coordinates.append([x_img, y_img])
                if len(self.staff_line_block_coordinates) >= 3:
                    self.image_processor.generate_diagonal_staff_lines_block(self.image_index, self.staff_line_block_coordinates[0], self.staff_line_block_coordinates[1], self.staff_line_block_coordinates[2])
                    self.staff_line_block_coordinates = []
                    self.draw_image_with_filters()
                else:
                    print("staff line click #", len(self.staff_line_block_coordinates))
            elif self.current_feature_type == "staff_line":
                staff_line = StaffLine([0, y_img], [self.image_processor.image_heights[self.image_index], y_img], self.image_processor.image_widths[self.image_index], self.image_processor.image_heights[self.image_index])
                self.image_processor.add_staff_line(self.image_index, staff_line)
                self.draw_image_with_filters()
            elif self.current_feature_type == "staff_line_diagonal":
                self.staff_line_diagonal_coordinates.append([x_img, y_img])
                if len(self.staff_line_diagonal_coordinates) >= 2:
                    #if vertical line
                    if self.staff_line_diagonal_coordinates[0][0] == self.staff_line_diagonal_coordinates[1][0]:
                        pass
                    else:
                        #If right most point is in index 0, switch.
                        if self.staff_line_diagonal_coordinates[0][0] > self.staff_line_diagonal_coordinates[1][0]:
                            temp = self.staff_line_diagonal_coordinates[0]
                            self.staff_line_diagonal_coordinates[0] = self.staff_line_diagonal_coordinates[1]
                            self.staff_line_diagonal_coordinates[1] = temp
                        staff_line = StaffLine(self.staff_line_diagonal_coordinates[0], self.staff_line_diagonal_coordinates[1], self.image_processor.image_widths[self.image_index], self.image_processor.image_heights[self.image_index])
                        self.image_processor.add_staff_line(self.image_index, staff_line)
                    self.staff_line_diagonal_coordinates = []
                    self.draw_image_with_filters()
                else:
                    print("staff line diagonal click #", len(self.staff_line_diagonal_coordinates))


            else:
                feature = self.image_processor.find_closest_feature(self.current_feature_type, self.image_index, x_img, y_img, error=1)
                if feature is not None:
                    print("feature found: ", feature.type)
                    self.current_feature = feature
                    topleft = [int(feature.topleft[0] * self.scale), int(feature.topleft[1] * self.scale)]
                    bottomright = [int(feature.bottomright[0] * self.scale), int(feature.bottomright[1] * self.scale)]
                    #self.rect = self.canvas.create_rectangle(topleft[0], topleft[1], bottomright[0], bottomright[1], outline='black')
                    self.draw_image_with_filters()
                else:
                    #if self.current_feature_type == "note":
                    #    self.image_processor.add_note_by_center_coordinate(self.image_index, x_img, y_img, self.is_half_note.get(), self.note_width_ratio_scale.get())
                    print("No feature in click area")
                    if self.current_feature_type in ["double_flat", "flat", "natural", "sharp", "double_sharp"]:
                        self.image_processor.add_feature_on_click(self.image_index, x_img, y_img, self.current_feature_type)
                        self.image_processor.calculate_accidental_letter_by_finding_closest_note(self.image_index, overwrite=False)
                    if self.current_feature_type == "barline":
                        self.image_processor.add_barline_on_click(self.image_index, x_img, y_img)
                    if self.current_feature_type == "note" and self.note_type.get() == "quarter" and self.allow_note_to_be_auto_extended.get() == True:
                        self.image_processor.extend_small_note(self.image_index, x_img, y_img, self.erode_strength_scale.get() / 100)
                        self.calculate_notes_for_regions_using_staff_lines_single_page(overwrite=False, page_index=self.image_index)

                    if self.current_feature_type == "note" and self.note_type.get() in ["half", "whole"] and self.allow_note_to_be_auto_extended.get() == True:
                        self.image_processor.extend_half_note_single_click(self.image_index, x_img, y_img, self.note_type.get())
                        self.calculate_notes_for_regions_using_staff_lines_single_page(overwrite=False, page_index=self.image_index)

                    self.draw_image_with_filters()


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
                    tl = [tl[0], tl[1] + 2]
                    br = [br[0], br[1] - 2]
                elif "-" in num_notes:
                    tl = [tl[0], tl[1] + 1]
                    br = [br[0], br[1] - 1]
                if "Pb" in num_notes:
                    new_notes.append(Note(tl, [x_mid, y_mid_lower], self.note_type.get(), auto_extended=True))
                    new_notes.append(Note([x_mid, y_mid_upper], br, self.note_type.get(), auto_extended=True))
                else:#bP
                    new_notes.append(Note([tl[0], y_mid_upper], [x_mid, br[1]], self.note_type.get(), auto_extended=True))
                    new_notes.append(Note([x_mid, tl[1]], [br[0], y_mid_lower], self.note_type.get(), auto_extended=True))
        else:
            num_notes = int(num_notes)
            for note in notes:
                for i in range(num_notes):
                    spacing = abs(note.topleft[1] - note.bottomright[1]) / num_notes
                    tl = note.topleft
                    br = note.bottomright
                    top = int(tl[1] + spacing * i)
                    bottom = int(tl[1] + spacing * (i + 1))
                    auto_extended = True
                    if num_notes == 1:
                        auto_extended = not self.allow_note_to_be_auto_extended.get()
                    new_notes.append(Note([tl[0], top], [br[0], bottom], self.note_type.get(), auto_extended=auto_extended))
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
    def match_template_parallel(image, gray_image, template, color, type, is_half_note, auto_extended, threshold,
                                error=10, draw=True):
        #todo REMOVE draw and within error
        gray_template = cv.cvtColor(template, cv.COLOR_BGR2GRAY)
        gray_template_width, gray_template_height = gray_template.shape[::-1]
        method = cv.TM_CCOEFF_NORMED
        #if is_half_note == False:
        #    method = cv.TM_CCORR
        #TM_CCOEFF_NORMED, TM_SQDIFF, TM_SQDIFF_NORMED, TM_CCOEFF, TM_CCORR_NORMED
        res = cv.matchTemplate(gray_image, gray_template, method)
        #cv.imwrite("gray_image.jpg", gray_image)
        #cv.imwrite("gray_template.jpg", gray_template)
        loc = np.where(res >= threshold)
        features = []
        # print("start")
        first_iteration = True
        point = 0
        for pt in zip(*loc[::-1]):
            if first_iteration == True:
                point = pt
                first_iteration = False
                f = Feature([pt[0], pt[1]], [pt[0] + gray_template_width, pt[1] + gray_template_height], type)
                if type == "note":
                    f = Note([pt[0], pt[1]], [pt[0] + gray_template_width, pt[1] + gray_template_height], is_half_note=is_half_note, auto_extended=auto_extended)
                features.append(f)
                #if draw == True:
                ##    cv.rectangle(image, pt,
                #                 (pt[0] + gray_template_width, pt[1] + gray_template_height), color, 2)

            # if points are too close, skip
            # print("distance", get_distance(point, pt))
            if ImageEditor.get_distance(point, pt) < error:
                # print("skip")
                continue
            else:
                point = pt

            # print("point", pt)
            f = Feature([pt[0], pt[1]], [pt[0] + gray_template_width, pt[1] + gray_template_height], type)
            if type == "note":
                f = Feature([pt[0], pt[1]], [pt[0] + gray_template_width, pt[1] + gray_template_height], is_half_note)
            features.append(f)
            #if draw == True:
            #    cv.rectangle(image, pt, (pt[0] + gray_template_width, pt[1] + gray_template_height),
            #                 color, 2)
        ImageEditor.remove_adjacent_matches(features)
        return features


    @staticmethod
    def process_feature(args):
        i, image, gray_image, match_template_params = args
        #print("Process ", i, "started")
        # Unpack the match_template parameters
        template, color, rect_type, is_half_note, auto_extended, threshold, error, draw = match_template_params
        features = ImageEditor.match_template_parallel(image, gray_image, template, color, rect_type, is_half_note, auto_extended, threshold, error=error,
                                                  draw=draw)
        if features is not None:
            #TODO remove adjacent matches based on feature size
            #print("num features: ", len(features), "on page: ", i)
            print("On page ", i, ": ", len(features), "features found.")

        #print("Process ", i, "ended")
        return features





if __name__ == "__main__":
    app = ImageEditor()
    app.mainloop()

