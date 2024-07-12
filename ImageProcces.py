import cv2 as cv
import tkinter as tk
import numpy as np
from tkinter import Scrollbar, Canvas
from PIL import Image, ImageTk
from FeatureObject import Feature
from Region import Region


class ImageProcessing:

    def __init__(self, dirname, filename, num_pages):
        # TODO add stack for states
        # TODO remove [none]
        self.dirname = dirname
        self.filename = filename
        self.num_pages = num_pages
        self.regions = [None] * self.num_pages
        self.images_filenames = []
        self.images = []
        self.gray_images = []
        self.bw_images = []
        self.staff_lines = []

        self.letter_colors = {
            'a': (103, 183, 58),
            'b': (216, 161, 67),
            'c': (247, 63, 45),
            'd': (255, 41, 153),
            'e': (255, 0, 225),
            'f': (119, 52, 202),
            'g': (0, 136, 150)
        }
        self.type_colors = {
            "bass_clef": (255, 0, 0),
            "treble_clef": (0, 255, 0),
            "note": (0, 0, 255),
            "barline": (0, 255, 255),
            "double_flat": (255, 0, 255),
            "flat": (255, 0, 255),
            "natural": (255, 0, 255),
            "sharp": (255, 0, 255),
            "double_sharp": (255, 0, 255),

        }

        # features objects:
        # each index represents a page
        self.treble_clefs = [None] * self.num_pages
        self.bass_clefs = [None] * self.num_pages
        self.barlines = [None] * self.num_pages

        self.accidentals = [None] * self.num_pages

        self.notes = [None] * self.num_pages
        self.image_heights = []
        self.image_widths = []
        self.all_clefs = [None] * self.num_pages

        # Used to instantly convert from type to array for that type

        for i in range(num_pages):
            self.images_filenames.append(dirname + '\\SheetsMusic\\page' + str(i) + '.jpg')
            self.images.append(cv.imread(self.images_filenames[i]))
            self.image_heights.append(self.images[i].shape[1])  # TODO swap
            self.image_widths.append(self.images[i].shape[0])
            self.gray_images.append(cv.cvtColor(self.images[i], cv.COLOR_BGR2GRAY))
            self.bw_images.append(cv.threshold(self.gray_images[i], 200, 255, cv.THRESH_BINARY)[1])
            self.get_stafflines(page_index=-1)
            self.draw_stafflines(page_index=i)
            cv.imwrite(self.dirname + "\\SheetsMusic\\Annotated\\annotated" + str(i) + ".png", self.images[i])

        self.array_types_dict = {
            "treble_clef": self.treble_clefs,
            "bass_clef": self.bass_clefs,
            "barline": self.barlines,
            "double_flat": self.accidentals,
            "flat": self.accidentals,
            "natural": self.accidentals,
            "sharp": self.accidentals,
            "double_sharp": self.accidentals,
            "note": self.notes,
            "staff_line": self.staff_lines
        }




    '''
    Takes a sub image and finds all occurances of that sub image in the image.
    Returns a set of Feature objects 
    '''
    def match_template(self, image, template, color, type,
                       error=10, draw=True):
        gray_template = cv.cvtColor(template, cv.COLOR_BGR2GRAY)
        gray_template_width, gray_template_height = gray_template.shape[::-1]
        gray_image = cv.cvtColor(image, cv.COLOR_BGR2GRAY)
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
            if self.get_distance(point, pt) < error:
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
        #TODO remove adjacents. error is based on dimensions of template


    '''
    WHen user clicks mouse, removes feature associated with mouse click
    '''

    def remove_feature(self, feature, page_index):
        if self.array_types_dict[feature.type][page_index] is not None:
            self.array_types_dict[feature.type][page_index].remove(feature)
        if self.regions[page_index] is not None:
            pass#todo regenerate region

    def is_list_2d(self, lst):
        if lst is None:
            return False
        if isinstance(lst[0], list):#TODO make sure this works
            return True
        else:
            return False

    def flatten_2d_list(self, lst):
        if lst is None:
            return None
        return [element for sublist in lst for element in sublist]

    def is_point_within_feature(self, point, feature):
        if feature.topleft[0] < point[0] < feature.bottomright[0] and feature.topleft[1] < point[1] < feature.bottomright[1]:
            return True
        else:
            return False

    def find_closest_feature(self, feature_type, page_index, x, y, error=10):
        feature_list = self.array_types_dict[feature_type][page_index]
        min_distance = 1000000
        closest_feature = None
        #TODO barlines can be stored in 2d list, so convert to 1d to match how other features are stored
        #print("feature_lsit before flatten:", feature_list)

        if self.is_list_2d(feature_list):
            print("2d list")
            feature_list = self.flatten_2d_list(feature_list)
        #print("feature_lsit:",feature_list)
        for feature in feature_list:
            if self.is_point_within_feature((x, y), feature):
                return feature
            corners = [feature.topleft, feature.bottomright, (feature.topleft[0], feature.bottomright[1]), (feature.bottomright[0], feature.topleft[1])]
            for corner in corners:
                distance = self.get_distance(corner, (x, y))
                if distance < min_distance:
                    min_distance = distance
                    closest_feature = feature
        if min_distance < error:
            return closest_feature
        else:
            return None

    '''
    Calculates distance between coordinates
    '''

    def get_distance(self, p1, p2):
        x2 = (p1[0] - p2[0]) * (p1[0] - p2[0])
        y2 = (p1[1] - p2[1]) * (p1[1] - p2[1])
        return (x2 + y2) ** .5

    '''
    Removes featues that have been double counted
    '''

    def remove_adjacent_matches(self, points, error):
        i = 0
        #todo handle 2d list?
        while points is not None and i < len(points):
            j = i + 1
            while j < len(points):
                if self.get_distance(points[i].topleft, points[j].topleft) < error:
                    points.pop(j)
                else:
                    j += 1
            i += 1

    '''
    Takes a 2d set of features(barlines) and draws them on the image
    '''

    def draw_stafflines(self, page_index):
        if self.staff_lines[page_index] is not None:
            for line in self.staff_lines[page_index]:
                cv.line(self.images[page_index], (0, line), (self.image_widths[page_index], line), (0, 255, 0), 1)
        cv.imwrite(self.dirname + "\\SheetsMusic\\Annotated\\annotated" + str(page_index) + ".png",
                   self.images[page_index])

    def draw_regions(self, page_index):
        if self.regions[page_index] != None:
            for region in self.regions[page_index]:
                region.draw_region_fill_in_feature(self.images[page_index], self.gray_images[page_index], self.letter_colors, lines=False, borders=True, notes=True, accidentals=True)
        cv.imwrite(self.dirname + "\\SheetsMusic\\Annotated\\annotated" + str(page_index) + ".png",
                   self.images[page_index])
    '''
    def draw_barlines(self, image, barlines):
        for i in range(len(barlines)):
            for j in range(len(barlines[i])):
                # topleft = (barlines[i][0], barlines[i][1])
                # bottomright = (barlines[i][0] + width, barlines[i][1] + height)
                cv.rectangle(image, barlines[i][j].topleft, barlines[i][j].bottomright, (255, 255, 0), 2)
    '''
    '''
    Finds horizontal lines in image, then returns set of y-values of staff lines
    
    First starts off by drawing a vertical line down the center of the page, and selecting black y-values
    Then checks only these y values for staff lines
    If you check every y-value for a staff line it is inefficient
    If page index = -1,  constructor
    '''

    # TODO let user input error size
    def get_stafflines(self, page_index, error=5, blackness_threshold=250):
        # holds the row that a staff line exists in
        histogram = []

        # draw a line straight down center of page, only check black indexes
        # TODO draw 3 lines down the page, and take the intersection of the set
        check_for_staff_line_indexes = []
        for i in range(self.bw_images[page_index].shape[0]):
            midpoint = int(self.bw_images[page_index].shape[1] / 2)
            if self.bw_images[page_index][i][midpoint] < 250:
                check_for_staff_line_indexes.append(i)
                # print(i)

        # checking marked rows for staff lines
        for i in check_for_staff_line_indexes:
            count = 0
            for j in range(self.bw_images[page_index].shape[1]):
                if self.bw_images[page_index][i][j] < blackness_threshold:
                    count = count + 1
                    if count > self.bw_images[page_index].shape[1] / 2:
                        break

            if count > self.bw_images[page_index].shape[1] / 2:
                histogram.append(i)
                continue

        # histogram.sort()
        # removing adjacent lines
        i = 0
        while i < len(histogram):
            current = i
            i = i + 1
            while i < len(histogram) and abs(histogram[i] - histogram[current]) < error:
                # print(histogram[current], "current")
                # print(histogram[i], "removed")
                histogram.remove(histogram[i])
                # i = i + 1
        # page index = -1 from constructor
        if page_index == -1:
            self.staff_lines.append(histogram)
        else:
            self.staff_lines[page_index] = histogram

    """
    automatically finds barlines in similar fashion to barlines
    """
    def get_barlines(self):
        pass
    '''
    Sorts array of features from top to bottom, left to right in 1d array
    '''

    def sort_features(self, features):
        if features is not None:
            features.sort(key=lambda x: (x.topleft[1], x.topleft[0]))

    '''
    Takes set of bass_clef and treble_clef
    Sorts them from top to bottom then left to right in 2d array
    '''

    def sort_clefs(self, page_index, error=100):
        #TODO multiple clefs in row
        # Initialize all_clefs[page_index] as an empty list if not already initialized
        if self.all_clefs[page_index] is None:
            self.all_clefs[page_index] = []

        length = len(self.bass_clefs[page_index]) + len(self.treble_clefs[page_index])
        i = 0
        bass_index = 0
        trebles_index = 0
        current_row = []
        multiple_in_row = False

        while i < length and trebles_index < len(self.treble_clefs[page_index]) and bass_index < len(
                self.bass_clefs[page_index]):
            # if clefs are in line with each other
            if abs(self.bass_clefs[page_index][bass_index].topleft[1] -
                   self.treble_clefs[page_index][trebles_index].topleft[1]) < error:
                multiple_in_row = True
                # left most clef
                if self.bass_clefs[page_index][bass_index].topleft[0] < \
                        self.treble_clefs[page_index][trebles_index].topleft[0]:
                    current_row.append(self.bass_clefs[page_index][bass_index])
                    bass_index += 1
                else:
                    current_row.append(self.treble_clefs[page_index][trebles_index])
                    trebles_index += 1
            else:
                if multiple_in_row:
                    self.all_clefs[page_index].append(current_row)
                    current_row = []
                multiple_in_row = False
                # top most clef
                if self.bass_clefs[page_index][bass_index].topleft[1] < \
                        self.treble_clefs[page_index][trebles_index].topleft[1]:
                    current_row.append(self.bass_clefs[page_index][bass_index])
                    bass_index += 1
                else:
                    current_row.append(self.treble_clefs[page_index][trebles_index])
                    trebles_index += 1

                self.all_clefs[page_index].append(current_row)
                current_row = []

        while bass_index < len(self.bass_clefs[page_index]):
            current_row = [self.bass_clefs[page_index][bass_index]]
            self.all_clefs[page_index].append(current_row)
            bass_index += 1

        while trebles_index < len(self.treble_clefs[page_index]):
            current_row = [self.treble_clefs[page_index][trebles_index]]
            self.all_clefs[page_index].append(current_row)
            trebles_index += 1

        print("All clefs ", self.all_clefs[page_index])

    '''
    Using sorted clefs, gets regions
    '''

    def get_clef_regions(self, page_index):
        # finding top and bottom of regions
        region_lines = [0]  # Start of first region will always be from top of page
        for i in range(4, len(self.staff_lines[page_index]), 5):
            # find midpoint between staff lines
            if i + 1 < len(self.staff_lines[page_index]):
                region_lines.append(int((self.staff_lines[page_index][i] + self.staff_lines[page_index][i + 1]) / 2))
        region_lines.append(self.image_heights[page_index])

        if self.all_clefs[page_index] != None:
            #print("Clefs not empty")
            for i in range(len(self.all_clefs[page_index])):
                for j in range(len(self.all_clefs[page_index][i])):
                    for k in range(len(region_lines)):
                        # find vertical region that clef lands in
                        # print(all_clefs[i][j][0])
                        if self.all_clefs[page_index][i][j].topleft[1] < region_lines[k]:
                            # top left corner and bottom right corner
                            top_left = (self.all_clefs[page_index][i][j].topleft[0], region_lines[k - 1])
                            bottom_right = (self.image_widths[page_index], region_lines[k])
                            # if there are multiple clefs on this staff line, bottom right of region stops at next staff line
                            if len(self.all_clefs[page_index][i]) > 1:
                                # if this staff isnt the right most staff that already goes to the end of the page
                                if j != len(self.all_clefs[page_index][i]) - 1:
                                    bottom_right = (
                                    self.all_clefs[page_index][i][j + 1].topleft[0], region_lines[k - 1])
                            r = Region(top_left, bottom_right, self.all_clefs[page_index][i][j].type, 0)
                            if self.regions[page_index] is None:
                                self.regions[page_index] = [r]
                            else:
                                self.regions[page_index].append(r)

                            break
        else:
            print("clefs are empty")

    '''
    Sorts the barlines into 2d array
    '''

    def sort_barlines(self, page_index, error=30):
        # Sort first by top to bottom, then left to right
        current_row = []
        sorted_bars = []

        for i in range(len(self.barlines[page_index])):
            if i < len(self.barlines[page_index]) - 1:
                # Check if barlines are on the same line
                if abs(self.barlines[page_index][i].topleft[1] - self.barlines[page_index][i + 1].topleft[1]) < error:
                    current_row.append(self.barlines[page_index][i])
                else:
                    current_row.append(self.barlines[page_index][i])
                    sorted_bars.append(sorted(current_row, key=lambda tup: tup.topleft[0]))
                    current_row = []
            else:
                # Handle the last element
                current_row.append(self.barlines[page_index][i])
                sorted_bars.append(sorted(current_row, key=lambda tup: tup.topleft[0]))
        self.barlines[page_index] = sorted_bars
        #print("Sorted barlines: ", self.barlines[page_index])

    def is_bar_in_region(self, region, bar):
        bottomleft_rect = (bar.topleft[0], bar.bottomright[1])
        # see if any of the 4 points are in bounds
        if region.is_point_in_region(bar.topleft):
            return True
        if region.is_point_in_region(bottomleft_rect):
            return True
        return False

    '''
    breaking up get_regions by barlines: #TODO make get regions into one
    '''

    def split_regions_by_bar(self, page_index):
        i = 0
        # TODO only call when regions are already split up by clef and barlines are sorted
        if self.regions[page_index] != None:
            #print("Region not none")
            while i < len(self.regions[page_index]):
                # print(regions_with_lines[i])
                for j in range(len(self.barlines[page_index])):
                    #print("Barline: row", self.barlines[page_index][j])
                    for k in range(len(self.barlines[page_index][j])):
                        if self.is_bar_in_region(self.regions[page_index][i], self.barlines[page_index][j][k]):
                            new_region = self.regions[page_index][i].copy()
                            new_region.type = "new region \n\n"
                            new_topleft = (
                            self.barlines[page_index][j][k].topleft[0], self.regions[page_index][i].topleft[1])
                            new_region.topleft = new_topleft
                            prev_bottomright = (
                            self.barlines[page_index][j][k].topleft[0], self.regions[page_index][i].bottomright[1])
                            self.regions[page_index][i].bottomright = prev_bottomright
                            self.regions[page_index].insert(i + 1, new_region)
                            # break
                i = i + 1

    def find_notes_and_accidentals_in_region(self, page_index):
        if self.regions[page_index] is not None:#TODO is not None for all loops
            for region in self.regions[page_index]:
                notes_in_region = []
                if self.notes[page_index] is not None:
                    for note in self.notes[page_index]:
                        if region.is_point_in_region(note.center):
                            #notes_in_region.append(note.copy())
                            notes_in_region.append(note)
                    region.notes = (notes_in_region)
                else:
                    print("notes empty on page", page_index)

                accidentals_in_region = []
                if self.accidentals[page_index] is not None:
                    for accidental in self.accidentals[page_index]:
                        if region.is_point_in_region(accidental.center):
                            # print("inregion topleft: ", region.topleft, "bottomright: ", region.bottomright, "Center: ", accidental.get_center())
                            #accidentals_in_region.append(accidental.copy())
                            accidentals_in_region.append(accidental)

                    region.accidentals = (accidentals_in_region)
                else:
                    print("Accidentals empty on page", page_index)
        else:
            print("regions empty on page", page_index)






    def find_closest_line(self, implied_lines, point):
        min = 10000
        closest_line = 0
        for line in implied_lines:
            if abs(point[1] - line.y) < min:
                min = abs(point[1] - line[0])
                closest_line = line
        return closest_line

    def fill_implied_lines(self):
        for i in range(self.num_pages):
            for region in self.regions[i]:
                region.fill_implied_lines()

    def fill_in_feature(self, page_index, topleft, bottomright, color):
        for i in range(topleft[1], bottomright[1], 1):
            for j in range(topleft[0], bottomright[0], 1):
                if self.gray_images[page_index][i][j] < 255 / 2:
                    self.images[page_index][i][j] = color

    def draw_features(self, features, page_index, color):
        print("Drawing the features loop")
        feature_list = features[page_index]
        if self.is_list_2d(features[page_index]):
            print("2d list")
            feature_list = self.flatten_2d_list(features[page_index])
        # print("feature_lsit:",feature_list)
        if feature_list is not None:
            for feature in feature_list:
                if feature is not None:
                #if features[page_index] is not None:
                #    for feature in features[page_index]:
                #        if type(feature) is not Feature:#if 2d list: barlines
                #            for f in feature:
                #                cv.rectangle(self.images[page_index], f.topleft, f.bottomright, color, 1)

                    #print("Drawing: ", feature)
                    # if it is a note or accidental that has a letter labeled
                    if feature.letter != "":
                        print("note: ", feature)
                        if feature.accidental != "":
                            print("note: ", feature)
                            accidental = feature.accidental
                            if accidental == "flat":
                                self.fill_in_feature(page_index, (feature.topleft[0], feature.center[1]),
                                                     feature.bottomright, self.letter_colors[feature.letter])
                            if accidental == "sharp":
                                self.fill_in_feature(page_index, feature.topleft,
                                                     (feature.bottomright[0], feature.center[1]),
                                                     self.letter_colors[feature.letter])

                            if accidental == "double_flat":
                                self.fill_in_feature(page_index, feature.topleft,
                                                     (feature.center[0], feature.bottomright[1]),
                                                     self.letter_colors[feature.letter])
                            if accidental == "double_sharp":
                                self.fill_in_feature(page_index,
                                                     (feature.center[0], feature.topleft[1]), feature.bottomright,
                                                     self.letter_colors[feature.letter])
                            if accidental == "natural":
                                self.fill_in_feature(page_index, feature.topleft, feature.bottomright,
                                                     self.letter_colors[feature.letter])

                        else:  # note with no accidental
                            self.fill_in_feature(page_index, feature.topleft, feature.bottomright,
                                                 self.letter_colors[feature.letter])
                        # self.fill_in_feature(page_index, f.topleft, f.bottomright, self.letter_colors[f.letter])
                   # else:  # if not a note or accidental
                    cv.rectangle(self.images[page_index], feature.topleft, feature.bottomright, color, 1)


    """
    Anytime match_template is called or filter is changed
    """
    def draw_image(self, filter_list, page_index):
        print("Filter list", filter_list)
        if filter_list[0].get() == 1:#staffline
            self.draw_stafflines(page_index)
        if filter_list[1].get() == 1:#implied line
            if self.regions[page_index] is not None:
                for region in self.regions[page_index]:
                    if region.implied_lines is not None:
                        for line in region.implied_lines:
                            cv.line(self.images[page_index], (0, line.y), (self.image_widths[page_index], line.y), self.letter_colors[line.letter], 1)
        if filter_list[2].get() == 1:#bass clef
            self.draw_features(self.bass_clefs, page_index, self.type_colors["bass_clef"])
        if filter_list[3].get() == 1:#treble clef
            print("Drawing treble clefs")
            self.draw_features(self.treble_clefs, page_index, self.type_colors["treble_clef"])
        if filter_list[4].get() == 1:#barline
            self.draw_features(self.barlines, page_index, self.type_colors["barline"])
        if filter_list[5].get() == 1:#note
            self.draw_features(self.notes, page_index, self.type_colors["note"])
        if filter_list[6].get() == 1: #accidental
            self.draw_features(self.accidentals, page_index, self.type_colors["flat"])
        if filter_list[7].get() == 1:#region border
            if self.regions[page_index] is not None:
                for region in self.regions[page_index]:
                    if region.clef == "bass_clef" or region.clef == "treble_clef":
                        cv.rectangle(self.images[page_index], region.topleft, region.bottomright, self.type_colors[region.clef], 1)
        if filter_list[8].get() == 1:#Colored notes and accidentals
            if self.regions[page_index] is not None:
                for region in self.regions[page_index]:
                    region.draw_region_fill_in_feature(self.images[page_index], self.gray_images[page_index], self.letter_colors)
        print("drawing image")
        cv.imwrite(self.dirname + "\\SheetsMusic\\Annotated\\annotated" + str(page_index) + ".png", self.images[page_index])
        #clearing the image of drawings
        self.images[page_index] = cv.imread(self.images_filenames[page_index])


    '''
            # getting note images
            # TODO make num_notes equal to number of files in Features/notes
            num_notes = 6
            note_images = []
            all_notes = []
            for j in range(num_notes):
                filename = "Features/notes/note" + str(j + 1) + ".jpg"
                note = cv.imread(filename)
                gray_note = cv.cvtColor(note, cv.COLOR_BGR2GRAY)
                notes = self.matchTemplate(self.images[i], self.gray_images[i], gray_note, (255, 0, 0), "note" + str(j), draw=False)
                all_notes.append(notes)

            # TODO remove adjacent notes

            # getting bass clefs
            filename = "Features/clefs/bass_clef.jpg"
            bass_clef = cv.imread(filename)
            gray_bass_clef = cv.cvtColor(bass_clef, cv.COLOR_BGR2GRAY)
            bass_clef = self.matchTemplate(self.images[i], self.gray_images[i], gray_bass_clef, (0, 255, 0), "b")
            # print("bass clefs\n", bass_clef)

            # getting treble clefs
            filename = "Features/clefs/treble_clef.jpg"
            treble_clef = cv.imread(filename)
            gray_treble_clef = cv.cvtColor(treble_clef, cv.COLOR_BGR2GRAY)
            trebles_clef = self.matchTemplate(self.images[i], self.gray_images[i], gray_treble_clef, (0, 255, 0), "t")
            # print("treble clefs\n", trebles_clef)

            '''
    '''
            # sorting the clefs
            # self.all_clefs = self.sort_clefs(bass_clef, trebles_clef)
            # print("all clefs\n", all_clefs)

            # getting clef regions
            # self.regions.append(self.get_clef_regions(all_clefs, self.staff_lines[i], self.images[i].shape[0], self.images[i].shape[1]))
            # print("regions\n", regions)
    '''


    '''
            # getting bar lines
            filename = "Features/barline/barline.jpg"
            barline = cv.imread(filename)
            gray_barline = cv.cvtColor(barline, cv.COLOR_BGR2GRAY)
            barlines = self.matchTemplate(self.images[i], self.gray_images[i], gray_barline, (255, 255, 0), "barline", 100, draw=False)
            self.remove_adjacent_matches(barlines, 300)
            sorted_barlines = self.sort_barlines(barlines)
            self.draw_barlines(self.images[i], sorted_barlines)
            print("sorted bar lines\n")
            for row in sorted_barlines:
                for bar in row:
                    print(str(bar))

            self.regions[i] = self.split_regions_by_bar(self.regions[i], sorted_barlines)
            # draw_regions(regions_with_lines_split_by_bars)

            # Getting implied lines:
            for region in self.regions[i]:
                region.fill_implied_lines(self.staff_lines[i])

            # getting accidentals
            num_accidentals = 3
            accidentals = []
            accidental_files = ["flat", "natural", "sharp"]
            for j in range(num_accidentals):
                filename = "Features/accidentals/" + accidental_files[j] + ".jpg"
                accidental = cv.imread(filename)
                gray_accidental = cv.cvtColor(accidental, cv.COLOR_BGR2GRAY)
                accidentals.append(self.matchTemplate(self.images[i], self.gray_images[i], gray_accidental, (0, 0, 255), accidental_files[j], draw=False))

            # Auto snap features(notes, accidentals) to implied lines:
            # Add each note/accidental to a reggion, then autosnap those notes
            print("\n\nStart regions\n\n")
            for region in self.regions[i]:
                notes_in_region = []
                # print("region: ", region)
                for row in all_notes:
                    for note in row:
                        if region.is_point_in_region(note.get_center()):
                            notes_in_region.append(note.copy())
                region.notes = (notes_in_region)

                accidentals_in_region = []
                for row_acc in accidentals:
                    for accidental in row_acc:
                        if region.is_point_in_region(accidental.get_center()):
                            # print("inregion topleft: ", region.topleft, "bottomright: ", region.bottomright, "Center: ", accidental.get_center())
                            accidentals_in_region.append(accidental.copy())
                region.accidentals = (accidentals_in_region)

                region.autosnap_notes_and_accidentals()
                region.find_accidental_for_note()

                # region.draw_region(img, letter_colors)
                region.draw_region_fill_in_feature(self.images[i], self.gray_images[i], self.letter_colors)

            # Getting note accidentals

            # regions_split_by_bars[4].draw_region(img, letter_colors)
            cv.imwrite(self.dirname + "\\SheetsMusic\\Annotated\\annotated" + str(i) + ".png", self.images[i])
    '''
    '''
    #dictionary that maps letters to colors:
    letter_colors = {
        'a': (103, 183, 58),
        'b': (216, 161, 67),
        'c': (247, 63, 45),
        'd': (255, 41, 153),
        'e': (255, 0, 225),
        'f': (119, 52, 202),
        'g': (0, 136, 150)
    }
    '''
    '''
    letter_colors = {
        'a': (103, 58, 183),
        'b': (216, 67, 161),
        'c': (247, 45, 63),
        'd': (255, 153, 41),
        'e': (255, 225, 0),
        'f': (119, 202, 52),
        'g': (0, 150, 136)
    }'''
    '''
    #TODO consolidate these 2 for loops into one
    #Loading in the pages of the sheet music
    images = []
    num_pages = 7
    for i in range(num_pages):
        images.append('SheetsMusic/page' + str(i) + '.jpg')


    #TODO open all images
    #loading in the note images and scanning for the note in the page
    img = cv.imread(images[0])
    gray_img = cv.cvtColor(img, cv.COLOR_BGR2GRAY)

    #getting staff lines
    bw_img = cv.threshold(gray_img, 200, 255, cv.THRESH_BINARY)[1]
    cv.imwrite('annotatedexample.png', bw_img)
    staff_lines = getStaffLines(bw_img)
    #draw_stafflines(img, staff_lines)


    #features objects:
    trebles_clef = []
    bass_clef = []
    barlines = []
    accidentals = []
    notes = []
    all_clefs = []

    #getting note images
    #TODO make num_notes equal to number of files in Features/notes
    num_notes = 6
    note_images = []
    all_notes = []
    for i in range(num_notes):
        filename = "Features/notes/note" + str(i + 1) + ".jpg"
        note = cv.imread(filename)
        gray_note = cv.cvtColor(note, cv.COLOR_BGR2GRAY)
        notes = matchTemplate(gray_img, gray_note, (255,0,0), "note" + str(i), draw=False)
        all_notes.append(notes)

    #TODO remove adjacent notes

    #getting bass clefs
    filename = "Features/clefs/bass_clef.jpg"
    bass_clef = cv.imread(filename)
    gray_bass_clef = cv.cvtColor(bass_clef, cv.COLOR_BGR2GRAY)
    bass_clef = matchTemplate(gray_img, gray_bass_clef, (0,255,0), "b")
    #print("bass clefs\n", bass_clef)

    #getting treble clefs
    filename = "Features/clefs/treble_clef.jpg"
    treble_clef = cv.imread(filename)
    gray_treble_clef = cv.cvtColor(treble_clef, cv.COLOR_BGR2GRAY)
    trebles_clef = matchTemplate(gray_img, gray_treble_clef, (0,255,0), "t")
    #print("treble clefs\n", trebles_clef)

    #TODO test multiple clefs on same line
    #sorting the clefs
    all_clefs = sort_clefs(bass_clef, trebles_clef)
    #print("all clefs\n", all_clefs)


    #getting clef regions
    regions = get_clef_regions(all_clefs, staff_lines, img.shape[0], img.shape[1])
    #print("regions\n", regions)


    #TODO break regions by bars, add key to regions, add sharps, naturals, flats, double flats and double sharps: shade bottom half/ top half different color
    #TODO region object: topleft, bottomright, notes, sharps, flats, double sharp, double flats, clef


    #getting bar lines
    filename = "Features/barline/barline.jpg"
    barline = cv.imread(filename)
    gray_barline = cv.cvtColor(barline, cv.COLOR_BGR2GRAY)
    barlines = matchTemplate(gray_img, gray_barline, (255,255,0), "barline", 100, draw=False)
    remove_adjacent_matches(barlines, 300)
    sorted_barlines = sort_barlines(barlines)
    draw_barlines(sorted_barlines)
    print("sorted bar lines\n")
    for row in sorted_barlines:
        for bar in row:
            print(str(bar))


    regions_split_by_bars = split_regions_by_bar(regions, sorted_barlines)
    #draw_regions(regions_with_lines_split_by_bars)

    #Getting implied lines:
    for region in regions_split_by_bars:
        region.fill_implied_lines(staff_lines)


    #getting accidentals
    num_accidentals = 3
    accidentals = []
    accidental_files = ["flat", "natural", "sharp"]
    for i in range(num_accidentals):
        filename = "Features/accidentals/" + accidental_files[i] + ".jpg"
        accidental = cv.imread(filename)
        gray_accidental = cv.cvtColor(accidental, cv.COLOR_BGR2GRAY)
        accidentals.append(matchTemplate(gray_img, gray_accidental, (0,0,255), accidental_files[i], draw=False))

    #Auto snap features(notes, accidentals) to implied lines:
    #Add each note/accidental to a reggion, then autosnap those notes
    print("\n\nStart regions\n\n")
    for region in regions_split_by_bars:
        notes_in_region = []
        #print("region: ", region)
        for row in all_notes:
            for note in row:
                if region.is_point_in_region(note.get_center()):
                    notes_in_region.append(note.copy())
        region.notes = (notes_in_region)

        accidentals_in_region = []
        for row_acc in accidentals:
            for accidental in row_acc:
                if region.is_point_in_region(accidental.get_center()):
                    #print("inregion topleft: ", region.topleft, "bottomright: ", region.bottomright, "Center: ", accidental.get_center())
                    accidentals_in_region.append(accidental.copy())
        region.accidentals = (accidentals_in_region)

        region.autosnap_notes_and_accidentals()
        region.find_accidental_for_note()

        #region.draw_region(img, letter_colors)
        region.draw_region_fill_in_feature(img, gray_img, letter_colors)

    #Getting note accidentals

    #regions_split_by_bars[4].draw_region(img, letter_colors)
    '''

    # TODO for gui
    """
    Color Picker
    Color match game
    Step 1: User selects a pdf
    Step 2: Pdf broken into images
    Step 3: Maybe have user rotate images to be perfectly horizontal. Maybe have user do this before hand
    Step 4: Identify Staff lines, give user the oppurtinity to add/ delete
    Step 5: User identifies Treble, Bass, barlines.
        If any are missing user, can fill in or delete
    Step 6: Break into regions and user identifies keys of regions
    Step 6: User identifies all accidentals, plus center of flats. Accidentals include, sharp, flat, double flat, doulbe sharp, natural, and small versions of these
        If any are missing, user can add or delete
    Step 7: User identifies notes big and small:
        If any are missing user can add or delete
    Step 8: Given all features have been inputed correctly, the note's color is changed appropriatly
    Step 9: Store file as (image, features), to allow for later editing
    """

    # TODO editor:
    """
    move feature with arrow keys
    delete with delete key
    CLick and drag to select multiple
    
    Add new feature: rectangle then say whay type.
    
    """

    '''
    cv.imwrite('annotatedexample.png', img)
    show_image_with_scrollbar(img)
    '''

