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
from StaffLine import StaffLine
from Note import Note
import concurrent.futures

'''
Steps: Find clefs
find staff lines
find notes
find accidentals
find barlines
generate regions
expand notes horizontally
autosnap
expand notes vertically
correct notes in wrong region

steps: find clefs and staff lines
find barlines
find notes
generate regions
auto extend notes
corrections
find accidentals
correct 

'
'''
"""
TODO
Big TODO
    chord letter checking: if notes are vertically stacked then notes should be 2 apart. if horizontally stacked, then 1 apart
    
    show self.dirname in info tab
    calculate note not using staff lines. draw line from top to bottom of region
    mxl parser: get all notes in measure, and there alteration, compare with
    for accidental, check 3 closest lines
    is vertical line in square, is horizontal line in square
    jump to page
    regenerate bw and gray images after changes in paint
    extract notes and compare with mxml
    half line detection
    dotted white line down center for quarter note accidetnal, black line for half note accidental
    auto extend note only applies to half/whole notes
    detect if note is on line or space for letter detection
    if note goes past region border: flood fill to find which clef. find vertical line closest to note. flood fill.
    add way to draw black to close half/whole notes
    image rotation based on slope of staff lines found
    when extending half notes, make height = note_height
    auto detect half/quarter note
    save pdf for printing order
    sort clefs
    parrallelize staff line detection
    converts all notes into sharps or all notes into flats, display double flats as fully filled
    draw notes over the accidentals
    remove overlaping squares loop "single"
    find name.pkl and name.pdf
    watermark



"""

class ImageEditor(tk.Tk):
    def __init__(self):
        super().__init__()
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

        self.page_indicator = tk.StringVar()
        # self.page_indicator.set(str(self.image_index) + "/" + self.num_pages)
        self.page_indicator_label = tk.Label(self.left_frame, textvariable=self.page_indicator)
        self.page_indicator_label.pack()

        # Show selected feature label
        self.selected_label_text = tk.StringVar()
        self.current_feature_type = "treble_clef"
        self.current_feature = None
        self.selected_label_text.set("Current Feature Selected: \n " + self.current_feature_type)
        self.feature_mode_add = True  # fasle for remove
        self.selected_label = tk.Label(self.left_frame,
                                       textvariable=self.selected_label_text)  # "Current Feature Selected: \n " + self.current_feature_type)
        self.selected_label.pack(pady=5)


        # Setting how the features will be added to just the current page, all pages, or the current and next pages
        self.add_mode_label = tk.Label(self.left_frame, text="Feature add mode:")
        self.add_mode_label.pack()
        self.add_mode_combobox_values = ["Current page and next pages", "Current Page", "All pages", "Single"]
        self.add_mode_combobox = ttk.Combobox(self.left_frame, state="readonly", values=self.add_mode_combobox_values, takefocus=0)
        self.add_mode_combobox.current(0)
        #self.add_mode_combobox.bind("<FocusOut>", self.clear_combobox)
        self.add_mode_combobox.pack()

        # CHeck button for whether to draw the image on the canvas or the jpg
        #self.draw_jpg_label = tk.Label(self.left_frame, text="Draw jpg:")
        #self.draw_jpg_label.pack()
        self.draw_jpg = tk.IntVar()
        self.draw_jpg.set(0)
        self.draw_image_on_jpg_check_button = tk.Checkbutton(self.left_frame, text="Fast editing mode", onvalue=1, offvalue=0, variable=self.draw_jpg, command=self.draw_image_canvas_mode)
        self.draw_image_on_jpg_check_button.pack()

        # Allow overlapping featues checkbox
        self.allow_overlapping = tk.IntVar()
        self.allow_overlapping.set(0)
        self.allow_overlapping_check_button = tk.Checkbutton(self.left_frame, text="Allow overlapping squares on add", onvalue=1, offvalue=0, variable=self.allow_overlapping)
        self.allow_overlapping_check_button.pack()

        self.is_half_note = tk.BooleanVar()
        self.is_half_note.set(False)
        self.allow_overlapping_check_button = tk.Checkbutton(self.left_frame, text="Half note", onvalue=True, offvalue=False, variable=self.is_half_note)
        self.allow_overlapping_check_button.pack()

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
        self.staff_line_error_scale = tk.Scale(self.left_frame, from_=0, to=42, orient="horizontal", label="Staff line error")
        self.staff_line_error_scale.set(5)
        self.staff_line_error_scale.pack()

        self.note_width_ratio_scale = tk.Scale(self.left_frame, from_=50, to=200, orient="horizontal", label="Note height/width ratio (Percentage)")
        self.note_width_ratio_scale.set(100)
        self.note_width_ratio_scale.pack()


        #threshold scale
        self.threshold_scale = tk.Scale(self.left_frame, from_=0, to=99, orient="horizontal", label="Threshold")
        self.threshold_scale.set(80)
        self.threshold_scale.pack()

        #Used for three click staff line addition
        self.staff_line_block_coordinates = []

        #Used for two click diagonal staff line
        self.staff_line_diagonal_coordinates = []


        #Setting the key
        self.sharp_order = ['f', 'c', 'g', 'd', 'a', 'e', 'b']
        self.flat_order = ['b', 'e', 'a', 'd', 'g', 'c', 'f',]

        self.key_label = tk.Label(self.left_frame, text="Key:")
        self.key_label.pack()
        self.key_combobox_values = ["None","1 sharp", "2 sharps", "3 sharps", "4 sharps", "5 sharps", "6 sharps", "1 flat", "2 flats", "3 flats", "4 flats", "5 flats", "6 flats"]
        self.key_combobox = ttk.Combobox(self.left_frame, state="readonly", values=self.key_combobox_values, takefocus=0)
        self.key_combobox.current(0)
        self.key_combobox.pack()



        #Filtering what is displayted
        '''
        self.filter_label = tk.Label(self.left_frame, text="Filter: ")
        self.filter_label.pack()
        '''
        self.filter_list = []#staff line, implied line, bass, treble, barline, note, accidental, region border, colored notes
        for i in range(8):
            self.filter_list.append(tk.IntVar())
            self.filter_list[i].set(1)
        self.filter_list[1].set(0)
        '''
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
        '''



        #Mutltiple notes
        self.num_notes_label = tk.Label(self.left_frame, text="Number of notes: ")
        self.num_notes_label.pack()
        self.num_notes_values = [1, 2, 3, 4, 5, "Pb", "bP", "Pb-", "bP-", "Pb--", "bP--"]
        self.num_notes_combobox = ttk.Combobox(self.left_frame, state="readonly", values=self.num_notes_values, takefocus=0)
        self.num_notes_combobox.current(0)
        self.num_notes_combobox.pack()

        #Current image file_name
        '''
        self.current_image_file_name = tk.StringVar()
        self.current_image_file_name.set("")
        self.current_image_file_name_label = tk.Label(self.left_frame, textvariable = self.current_image_file_name)
        self.current_image_file_name_label.pack()
        '''











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


        self.bind("<Key>", self.keypress)
        #self.bind("<Key>", self.keypress)


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
        file_menu.add_command(label="Open annotations with pdf", command=self.load_binary)
        file_menu.add_command(label="Save annotations with pdf", command=self.save_binary)
        file_menu.add_separator()
        #file_menu.add_command(label="Open annotations without pdf", command=self.load_annotations)
        #file_menu.add_command(label="Save annotations without pdf", command=self.save_annotations)
        #file_menu.add_separator()
        file_menu.add_command(label="Undo", command=self.undo)
        file_menu.add_command(label="Redo", command=self.redo)
        file_menu.add_separator()
        # file_menu.add_separator()
        file_menu.add_command(label="Regenerate images", command=self.regenerate_images)
        file_menu.add_separator()
        file_menu.add_command(label="Reduce pixels by half", command=self.reduce_image_size)
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
        view_menu.add_command(label="Auto rotate based off of staff lines", command=self.rotate_based_off_staff_lines)
        view_menu.add_separator()
        view_menu.add_command(label="Fast editing mode", command=self.switch_fast_editing_mode)
        view_menu.add_separator()
        view_menu.add_command(label="Fill in white spots", command=self.fill_in_white_spots)
        view_menu.add_separator()
        view_menu.add_checkbutton(label="Staff Lines", onvalue=1, offvalue=0, variable=self.filter_list[0], command=self.set_filter)
        view_menu.add_checkbutton(label="Implied Lines", onvalue=1, offvalue=0, variable=self.filter_list[1], command=self.set_filter)
        view_menu.add_checkbutton(label="Treble Clefs", onvalue=1, offvalue=0, variable=self.filter_list[2], command=self.set_filter)
        view_menu.add_checkbutton(label="Bass Clefs", onvalue=1, offvalue=0, variable=self.filter_list[3], command=self.set_filter)
        view_menu.add_checkbutton(label="Barlines", onvalue=1, offvalue=0, variable=self.filter_list[4], command=self.set_filter)
        view_menu.add_checkbutton(label="Notes", onvalue=1, offvalue=0, variable=self.filter_list[5], command=self.set_filter)
        view_menu.add_checkbutton(label="Accidentals", onvalue=1, offvalue=0, variable=self.filter_list[6], command=self.set_filter)
        view_menu.add_checkbutton(label="Region Borders", onvalue=1, offvalue=0, variable=self.filter_list[7], command=self.set_filter)


        #filter_menu = tk.Menu(self.menu, tearoff=0)
        #self.menu.add_cascade(label="Filter", menu=filter_menu)




        #Set Feature Menu
        set_feature_menu = tk.Menu(self.menu, tearoff=0)
        self.menu.add_cascade(label="Set Feature Type", menu=set_feature_menu)
        set_feature_menu.add_command(label="Staff line(1 click)", command=lambda: self.set_feature_type("staff_line"))
        set_feature_menu.add_command(label="Diagonal Staff Line(2 clicks)", command=lambda: self.set_feature_type("staff_line_diagonal"))
        set_feature_menu.add_command(label="Staff line region(3 clicks)", command=lambda: self.set_feature_type("staff_line_block"))
        set_feature_menu.add_separator()
        set_feature_menu.add_command(label="Bass Clef (r)", command=lambda :self.set_feature_type("bass_clef"))
        set_feature_menu.add_command(label="Treble Clef (t)", command=lambda :self.set_feature_type("treble_clef"))
        set_feature_menu.add_separator()
        set_feature_menu.add_command(label="Barline (y)", command=lambda :self.set_feature_type("barline"))
        set_feature_menu.add_separator()
        set_feature_menu.add_command(label="Note (n)", command=lambda :self.set_feature_type("note"))
        set_feature_menu.add_command(label="Half Note (h)", command=lambda :self.set_feature_type("note", is_half_note=True))
        set_feature_menu.add_separator()
        set_feature_menu.add_command(label="Double Sharp (1)", command=lambda: self.set_feature_type("double_sharp"))
        set_feature_menu.add_command(label="Sharp (2)", command=lambda: self.set_feature_type("sharp"))
        set_feature_menu.add_command(label="Natural (3)", command=lambda: self.set_feature_type("natural"))
        set_feature_menu.add_command(label="Flat (4)", command=lambda: self.set_feature_type("flat"))
        set_feature_menu.add_command(label="Double Flat (5)", command=lambda: self.set_feature_type("double_flat"))
        set_feature_menu.add_separator()
        set_feature_menu.add_command(label="Key (k)", command=lambda :self.set_feature_type("key"))



        #Clef menu
        clef_menu = tk.Menu(self.menu, tearoff=0)
        self.menu.add_cascade(label="Clef", menu=clef_menu)
        clef_menu.add_command(label="Find page missing start clefs", command=self.find_page_with_missing_clefs)


        # Staff line menu
        staff_line_menu = tk.Menu(self.menu, tearoff=0)
        self.menu.add_cascade(label="Staff Lines", menu=staff_line_menu)
        staff_line_menu.add_command(label="Generate staff lines horizontal", command=self.generate_staff_lines)
        staff_line_menu.add_command(label="Generate staff lines diagonal, Primary method (Prerequisite: Clefs)", command=self.generate_staff_lines_diagonal_by_traversing_vertical_line)
        staff_line_menu.add_command(label="Generate staff lines diagonal, Alternate method (Prerequisite: Clefs)", command=lambda :self.generate_staff_lines_diagonal(use_union_image=False))
        staff_line_menu.add_separator()
        staff_line_menu.add_command(label="Find action needed page", command=self.find_page_with_wrong_staff_lines)

        # Barline menu
        barline_menu = tk.Menu(self.menu, tearoff=0)
        self.menu.add_cascade(label="Barline", menu=barline_menu)
        barline_menu.add_command(label="Generate barlines  (Prerequisite: Staff lines)", command=self.get_barlines)
        # barline_menu.add_command(label="Barline", command=lambda :self.set_feature_type("barline"))


        # Note menu
        self.include_auto_extended_notes = tk.BooleanVar()
        self.include_auto_extended_notes.set(False)
        note_menu = tk.Menu(self.menu, tearoff=0)
        self.menu.add_cascade(label="Notes", menu=note_menu)
        # note_menu.add_command(label="Note", command=lambda :self.set_feature_type("note"))
        note_menu.add_checkbutton(label="(Checkbox)Half note", variable=self.is_half_note)
        note_menu.add_command(label="Auto extend and center notes (Prerequisite: Staff lines)", command=self.auto_extend_notes)
        note_menu.add_separator()
        note_menu.add_command(label="Auto detect quarter notes (Prerequisite: Staff lines)",command=self.auto_detect_quarter_notes)
        note_menu.add_separator()
        note_menu.add_command(label="Autosnap notes using implied lines  (Prerequisite: Staff lines)", command=self.autosnap_notes)
        note_menu.add_separator()
        note_menu.add_checkbutton(label="(Checkbox)Include auto extended notes", variable=self.include_auto_extended_notes)
        note_menu.add_command(label="Extend notes horizontally", command=lambda: self.extend_notes(0, 0, 1, 1))
        note_menu.add_command(label="Extend notes vertically", command=lambda: self.extend_notes(1, 1, 0, 0))
        note_menu.add_separator()
        note_menu.add_command(label="Extend notes down", command=lambda: self.extend_notes(0, 1, 0, 0))
        note_menu.add_command(label="Extend notes up", command=lambda: self.extend_notes(1, 0, 0, 0))
        note_menu.add_separator()
        note_menu.add_command(label="Extend notes left", command=lambda: self.extend_notes(0, 0, 1, 0))
        note_menu.add_command(label="Extend notes right", command=lambda: self.extend_notes(0, 0, 0, 1))
        note_menu.add_separator()
        note_menu.add_command(label="Auto remove small erroneous notes", command=self.remove_small_notes)
        note_menu.add_separator()
        note_menu.add_command(label="Auto detect half and quarter note", command=self.auto_detect_half_or_quarter_note)
        #note_menu.add_separator()
        #note_menu.add_command(label="Are notes on line", command=self.are_notes_on_line)

        #note_menu.add_separator()
        #note_menu.add_command(label="Make all notes same size", command=self.make_all_notes_same_size)






        #Key menu
        key_menu = tk.Menu(self.menu, tearoff=0)
        self.menu.add_cascade(label="Key", menu=key_menu)
        key_menu.add_command(label="Set key for current page", command=self.set_key_for_current_page)

        #Region menu
        self.overwrite_regions = tk.BooleanVar()
        self.overwrite_regions.set(True)
        region_menu = tk.Menu(self.menu, tearoff=0)
        self.menu.add_cascade(label="Region", menu=region_menu)
        region_menu.add_checkbutton(label="(Checkbox)Overwrite manual note and accidental changes", variable=self.overwrite_regions)
        #region_menu.add_command(label="Generate regions", command=lambda: self.generate_regions(overwrite=self.overwrite_regions.get()))
        region_menu.add_separator()
        region_menu.add_command(label="Calculate note and accidental letters", command=lambda: self.calculate_notes_and_accidentals_for_regions_using_staff_lines(overwrite=self.overwrite_regions.get()))
        region_menu.add_command(label="Calculate note and accidental letters for distorted image", command=lambda: self.calculate_notes_and_accidentals_for_distorted_staff_lines(overwrite=self.overwrite_regions.get()))

        region_menu.add_separator()
        region_menu.add_command(label="Calculate note accidentals", command=lambda: self.calculate_note_accidentals_for_regions(overwrite=self.overwrite_regions.get()))


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
        reset_menu.add_command(label="Half/Whole Note", command=lambda: self.clear_note_type("half"))
        reset_menu.add_separator()
        reset_menu.add_command(label="Regions", command=lambda: self.clear_region())
        reset_menu.add_command(label="Reset note and accidental letters", command=self.reset_note_and_accidental_letters)

        #info_menu = tk.Menu(self.menu, tearoff=0)
        ##self.info_string = tk.StringVar()
        #self.menu.add_cascade(label="Info", menu=info_menu)
        #TODO, display image dimensions, number of notes, number of autosnapped notes, number of half notes
        #info_menu.

    def reduce_image_size(self):
        for i in range(self.num_pages):
            self.image_processor.reduce_image_size(i)
        self.draw_image_with_filters()

    def regenerate_images(self):
        loop = self.get_loop_array_based_on_feature_mode()
        if loop == "single":
            loop = [self.image_index]
        for i in loop:
            self.image_processor.regenerate_images(i)
        self.draw_image_with_filters()

    @staticmethod
    def fill_in_white_spots_parallel(task):
        page_index, image, gray_image, filename = task
        print("Fill in white spots on page ", page_index)
        min_size = 10
        # Step 1: Load the image in grayscale mode
        img = cv.adaptiveThreshold(gray_image, 255, cv.ADAPTIVE_THRESH_MEAN_C, cv.THRESH_BINARY, 15, -2)
        # Step 2: Apply binary thresholding to get a binary image
        _, binary_img = cv.threshold(img, 190, 255, cv.THRESH_BINARY)

        # Step 3: Find connected components (to detect individual white regions)
        # 'connectivity=4' ensures only direct neighbors are considered connected
        num_labels, labels, stats, centroids = cv.connectedComponentsWithStats(binary_img, connectivity=4)

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
            (i, self.image_processor.images[i], self.image_processor.gray_images[i], self.image_processor.images_filenames[i])
            for i in loop
        ]

        # Create a pool of worker processes
        with multiprocessing.Pool() as pool:
            results = pool.map(ImageEditor.fill_in_white_spots_parallel, tasks)
        for i in loop:
            self.image_processor.images[i] = cv.imread(self.image_processor.images_filenames[i])
            self.image_processor.gray_images[i] = cv.cvtColor(self.image_processor.images[i], cv.COLOR_BGR2GRAY)
            self.image_processor.bw_images[i] = cv.threshold(self.image_processor.gray_images[i], 200, 255, cv.THRESH_BINARY)[1]
        #for i in loop:
            #self.image_processor.fill_in_white_spots(i)
        #self.image_processor.fill_in_white_spots(self.image_index)
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
        for i in loop:
            self.image_processor.auto_extend_notes(i, self.note_width_ratio_scale.get())
        self.draw_image_with_filters()

    def clear_combobox(self, event):
        self.selected_label.focus()

    def set_note_type(self):
        self.is_half_note = not self.is_half_note

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

    def set_key_for_current_page(self):
        topleft = [0,0]
        bottomright = [self.image_processor.image_widths[self.image_index] - 1, self.image_processor.image_heights[self.image_index] - 1]

        key = self.key_combobox.get()
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
        loop_list = self.get_loop_array_based_on_feature_mode()
        if loop_list == "single":
            loop_list = [self.image_index]
        for i in loop_list:
            self.image_processor.extend_notes(i, up, down, left, right, self.is_half_note.get(), self.include_auto_extended_notes.get())
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

    def generate_staff_lines_diagonal_by_traversing_vertical_line(self):
        loop = self.get_loop_array_based_on_feature_mode()
        if loop == "single":
            loop = [self.image_index]
        for i in loop:
            self.image_processor.get_staff_lines_diagonal_by_traversing_vertical_line(i,)
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

    def calculate_notes_and_accidentals_for_regions_using_staff_lines(self, overwrite):
        loop = self.get_loop_array_based_on_feature_mode()
        if loop == "single":
            loop = [self.image_index]
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
                for region in self.image_processor.regions[i]:
                    region.fill_implied_lines(self.image_processor.staff_lines[i], self.image_processor.image_widths[i], self.image_processor.image_heights[i])
                    region.autosnap_notes_and_accidentals(overwrite)
        self.draw_image_with_filters()

    def calculate_notes_and_accidentals_for_distorted_staff_lines(self, overwrite):

        loop = self.get_loop_array_based_on_feature_mode()
        if loop == "single":
            loop = [self.image_index]
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
                img = cv.imread(self.image_processor.images_filenames[i], cv.IMREAD_COLOR)
                if img is None:
                    print('Error opening image: ')
                    return -1
                if len(img.shape) != 2:
                    gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
                else:
                    gray = img
                gray = cv.bitwise_not(gray)
                bw = cv.adaptiveThreshold(gray, 255, cv.ADAPTIVE_THRESH_MEAN_C, cv.THRESH_BINARY, 15, -2)
                for region in self.image_processor.regions[i]:
                    self.image_processor.calculate_notes_and_accidentals_for_distorted_staff_lines(i, region, bw)
        self.draw_image_with_filters()


    def calculate_note_accidentals_for_regions(self, overwrite):
        loop = self.get_loop_array_based_on_feature_mode()
        if loop == "single":
            loop = [self.image_index]
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
                for region in self.image_processor.regions[i]:
                    region.fill_implied_lines(self.image_processor.staff_lines[i], self.image_processor.image_widths[i], self.image_processor.image_heights[i])
                    region.find_accidental_for_note(overwrite)
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
        is_half = False
        if type == "half":
            is_half = True
        loop = self.get_loop_array_based_on_feature_mode()
        if loop == "single":
            loop = [self.image_index]
        for i in loop:
            if self.image_processor.is_list_iterable(self.image_processor.notes[i]):
                for j in range(len(self.image_processor.notes[i]) - 1, - 1, -1):
                    note = self.image_processor.notes[i][j]
                    if note.is_half_note == is_half:
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



    def set_feature_type(self, feature_name, is_half_note=False):
        if "staff_line" in feature_name:
            self.staff_line_block_coordinates = []
            self.staff_line_diagonal_coordinates = []
        self.current_feature_type = feature_name
        self.is_half_note.set(is_half_note)

        self.selected_label_text.set("Current Feature Selected: \n" + self.current_feature_type)
        print("Current feature type: ", self.current_feature_type, "Is half note: ", str(self.is_half_note.get()))

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
        if c == 's' or c == "S":
            self.set_feature_type("staff_line")
        if c == 'r' or c == "R":
            self.set_feature_type("bass_clef")
        if c == 't' or c == "T":
            self.set_feature_type("treble_clef")
        if c == 'n' or c == "N":
            self.set_feature_type("note")
        if c == 'h' or c == 'H':
            self.set_feature_type("note", is_half_note=True)
        if c == 'y' or c == "Y":
            self.set_feature_type("barline")
        if c == 'k' or c == "K":
            self.set_feature_type("key")
        if c == 'm' or c == 'M':
            if self.draw_jpg.get() == 0:
                self.draw_jpg.set(1)
            else:
                self.draw_jpg.set(0)
            self.draw_image_with_filters()
        #if c == ',':
        #    if self.editing_mode.get() == self.editing_modes[0]:#currently add
        #        self.editing_mode.set(self.editing_modes[1])
        #    else:#currently edit
        #        self.editing_mode.set(self.editing_modes[0])
        if c == "[":
            self.current_feature = None
            self.staff_line_diagonal_coordinates = []
            self.staff_line_block_coordinates = []
            self.image_index = (self.image_index - 5) % self.num_pages
            self.draw_image_canvas_mode()
            self.draw_image_with_filters()
        if c == "]":
            self.current_feature = None
            self.staff_line_diagonal_coordinates = []
            self.staff_line_block_coordinates = []
            self.image_index = (self.image_index + 5) % self.num_pages
            self.draw_image_canvas_mode()
            self.draw_image_with_filters()
        if c == "{":
            self.current_feature = None
            self.staff_line_diagonal_coordinates = []
            self.staff_line_block_coordinates = []
            self.image_index = (self.image_index - 10) % self.num_pages
            self.draw_image_canvas_mode()
            self.draw_image_with_filters()
        if c == "}":
            self.current_feature = None
            self.staff_line_diagonal_coordinates = []
            self.staff_line_block_coordinates = []
            self.image_index = (self.image_index + 10) % self.num_pages
            self.draw_image_canvas_mode()
            self.draw_image_with_filters()

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
            self.display_image()
        else:
            print("no file selected")


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
                cv.imwrite(self.image_processor.annotated_images_filenames[i], self.image_processor.images[i])

                print("test", folder + "\\annotated" + str(i) + ".png")
                images.append(Image.open(folder + "\\annotated" + str(i) + ".png"))
            # go through all the images in the folder
            print("test", folder + "\\annotated" + str(0) + ".png")
            pdf_path = filedialog.asksaveasfilename(filetypes=[("PDF", "*.pdf")], defaultextension=[("PDF", "*.pdf")], initialfile=self.file_name+"_cheatmusic.pdf")
            if pdf_path == "":
                print("no pdf selected")
                return
            images[0].save(pdf_path, "PDF", resolution=100.0, save_all=True, append_images=images[1:])
        else:
            print("cant save")

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

    def load_binary(self):
        file_path = filedialog.askopenfilename(title="Open pkl File", initialdir=self.dirname, filetypes=[("pkl files", "*.pkl")])  # TODO initialdir
        if file_path == "":
            print("no file selected")
            return
        with open(file_path, "rb") as file:
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
            self.draw_image_with_filters()

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

    def display_image(self):
        #clearing the canvas so there arent shapes drawn on top of each other making things slow
        self.canvas.delete("all")

        if self.draw_jpg.get() == 0:
            print("drawing image on jpg")
            self.image = Image.open(self.image_processor.annotated_images_filenames[self.image_index])#self.dirname + "\\SheetsMusic\\Annotated\\annotated" + str(self.image_index) + ".png")
            self.photo = ImageTk.PhotoImage(
                self.image.resize((int(self.image.width * self.scale), int(self.image.height * self.scale))))
            self.canvas.create_image(0, 0, image=self.photo, anchor="nw")
            self.canvas.config(scrollregion=self.canvas.bbox(tk.ALL))
            if self.current_feature is not None:
                f = self.current_feature
                topleft = [int(f.topleft[0] * self.scale), int(f.topleft[1] * self.scale)]
                bottomright = [int(f.bottomright[0] * self.scale), int(f.bottomright[1] * self.scale)]
                self.canvas.create_rectangle(topleft[0], topleft[1], bottomright[0], bottomright[1], outline='black')
        else:
            print("Drawing image on canvas")
            #self.image = Image.open(self.dirname + "\\SheetsMusic\\page" + str(self.image_index) + ".jpg")
            self.image = Image.open(self.image_processor.annotated_images_filenames[self.image_index])#self.dirname + "\\SheetsMusic\\Annotated\\annotated" + str(self.image_index) + ".png")

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
                #line = int(line * self.scale)
                x0 = int(line.topleft[0] * self.scale)
                y0 = int(line.topleft[1] * self.scale)
                x1 = int(line.bottomright[0] * self.scale)
                y1 = int(line.bottomright[1] * self.scale)
                self.canvas.create_line(x0, y0, x1, y1, fill="green")

        if self.current_feature is not None:
            f = self.current_feature
            topleft = [int(f.topleft[0] * self.scale), int(f.topleft[1] * self.scale)]
            bottomright = [int(f.bottomright[0] * self.scale), int(f.bottomright[1] * self.scale)]
            self.canvas.create_rectangle(topleft[0], topleft[1], bottomright[0], bottomright[1], outline='black')

    def draw_cross_hairs(self, feature, color):

        x_mid = int(feature.center[0] * self.scale)
        y_mid = int(feature.center[1] * self.scale)
        x0 = int(feature.topleft[0] * self.scale)
        y0 = int(feature.topleft[1] * self.scale)
        x1 = int(feature.bottomright[0] * self.scale)
        y1 = int(feature.bottomright[1] * self.scale)

        self.canvas.create_rectangle(x0, y0, x1, y1, outline=color)
        self.canvas.create_line(x0, y_mid, x1, y_mid, fill=color)
        self.canvas.create_line(x_mid, y0, x_mid, y1, fill=color)

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
        self.draw_image_canvas_mode()
        self.draw_image_with_filters()
        #self.display_image()

    def previous_image(self):
        self.current_feature = None
        self.staff_line_diagonal_coordinates = []
        self.staff_line_block_coordinates = []
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
        self.page_indicator.set(str(self.image_index) + "/" + str(self.num_pages))
        #self.current_image_file_name.set(self.image_processor.images_filenames[self.image_index])
        #if self.current_feature is not None:
        #    f = self.current_feature
        #    topleft = [int(f.topleft[0] * self.scale), int(f.topleft[1] * self.scale)]
        #    bottomright = [int(f.bottomright[0] * self.scale), int(f.bottomright[1] * self.scale)]
        #    self.canvas.create_rectangle(topleft[0], topleft[1], bottomright[0], bottomright[1], outline='black')
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
        print("released")

        if self.rect:
            print("rect started")
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
            if self.get_loop_array_based_on_feature_mode() != "single":#if the add mode is in single, dont need to match template
                match_template_params = (
                    template,
                    (0, 255, 0),
                    rectangle.type,
                    self.is_half_note.get(),
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
                if rectangle.type == "note":
                    rectangle = Note(rectangle.topleft, rectangle.bottomright, self.is_half_note)
                    if self.num_notes_combobox.get() != 1:
                        rectangle = self.convert_notes([rectangle])
                if isinstance(rectangle, list):
                    self.image_processor.append_features(self.image_index, rectangle[0].type, rectangle)
                else:
                    self.image_processor.append_features(self.image_index, rectangle.type, [rectangle])
                self.draw_image_with_filters()

        else:#if rect wasnt started
            print("rect wasnt started")
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
                feature = self.image_processor.find_closest_feature(self.current_feature_type, self.image_index, x_img, y_img)
                if feature is not None:
                    print("feature found: ", feature)
                    self.current_feature = feature
                    topleft = [int(feature.topleft[0] * self.scale), int(feature.topleft[1] * self.scale)]
                    bottomright = [int(feature.bottomright[0] * self.scale), int(feature.bottomright[1] * self.scale)]
                    #self.rect = self.canvas.create_rectangle(topleft[0], topleft[1], bottomright[0], bottomright[1], outline='black')
                    self.draw_image_with_filters()
                else:
                    #if self.current_feature_type == "note":
                    #    self.image_processor.add_note_by_center_coordinate(self.image_index, x_img, y_img, self.is_half_note.get(), self.note_width_ratio_scale.get())
                    print("No feature in click area")

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
                    new_notes.append(Note(tl, [x_mid, y_mid_lower], self.is_half_note.get(), auto_extended=True))
                    new_notes.append(Note([x_mid, y_mid_upper], br, self.is_half_note.get(), auto_extended=True))
                else:#bP
                    new_notes.append(Note([tl[0], y_mid_upper], [x_mid, br[1]], self.is_half_note.get(), auto_extended=True))
                    new_notes.append(Note([x_mid, tl[1]], [br[0], y_mid_lower], self.is_half_note.get(), auto_extended=True))
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
                        auto_extended = False
                    new_notes.append(Note([tl[0], top], [br[0], bottom], self.is_half_note.get(), auto_extended=auto_extended))
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
    def match_template_parallel(image, gray_image, template, color, type, is_half_note, threshold,
                                error=10, draw=True):
        #todo REMOVE draw and within error
        gray_template = cv.cvtColor(template, cv.COLOR_BGR2GRAY)
        gray_template_width, gray_template_height = gray_template.shape[::-1]
        res = cv.matchTemplate(gray_image, gray_template, cv.TM_CCOEFF_NORMED)
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
                    f = Note([pt[0], pt[1]], [pt[0] + gray_template_width, pt[1] + gray_template_height], is_half_note)
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
        print("Process ", i, "started")
        # Unpack the match_template parameters
        template, color, rect_type, is_half_note, threshold, error, draw = match_template_params
        features = ImageEditor.match_template_parallel(image, gray_image, template, color, rect_type, is_half_note, threshold, error=error,
                                                  draw=draw)
        if features is not None:
            #TODO remove adjacent matches based on feature size
            print("num features: ", len(features), "on page: ", i)

        print("Process ", i, "ended")
        return features





if __name__ == "__main__":
    app = ImageEditor()
    app.mainloop()

