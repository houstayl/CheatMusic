import math
import sys
import cv2 as cv
import tkinter as tk
import numpy as np
from tkinter import Scrollbar, Canvas
from PIL import Image, ImageTk
from FeatureObject import Feature
from Region import Region
from StaffLine import StaffLine
from Note import Note

class ImageProcessing:

    def __init__(self, dirname, filename, num_pages):
        # TODO add stack for states
        self.dirname = dirname
        self.filename = filename
        self.num_pages = num_pages
        self.regions = [None] * self.num_pages
        self.images_filenames = []
        self.annotated_images_filenames = []
        self.images = []
        self.gray_images = []
        self.bw_images = []
        #self.lines_removed_images = []

        #BGR
        self.letter_colors = {
            'a': (182, 58, 103),
            'b': (160, 66, 216),
            'c': (62, 47, 246),
            'd': (41, 152, 254),
            'e': (1, 224, 255),
            'f': (52, 202, 119),
            'g': (136, 151, 1)
        }

        self.type_colors = {
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

        }

        # features objects:
        # each index represents a page
        self.staff_lines = [None] * self.num_pages
        self.treble_clefs = [None] * self.num_pages
        self.bass_clefs = [None] * self.num_pages
        self.barlines = [None] * self.num_pages
        self.barlines_2d = [None] * self.num_pages

        self.accidentals = [None] * self.num_pages

        self.notes = [None] * self.num_pages
        self.image_heights = []
        self.image_widths = []
        self.all_clefs = [None] * self.num_pages

        # Used to instantly convert from type to array for that type

        for i in range(num_pages):
            self.images_filenames.append(dirname + '\\SheetsMusic\\page' + str(i) + '.jpg')
            self.annotated_images_filenames.append(dirname + '\\SheetsMusic\\Annotated\\annotated' + str(i) + '.png')
            self.images.append(cv.imread(self.images_filenames[i]))
            self.image_heights.append(self.images[i].shape[0])
            self.image_widths.append(self.images[i].shape[1])
            self.gray_images.append(cv.cvtColor(self.images[i], cv.COLOR_BGR2GRAY))
            self.bw_images.append(cv.threshold(self.gray_images[i], 127, 255, cv.THRESH_BINARY)[1])
            #self.lines_removed_images.append(cv.adaptiveThreshold(self.graw_images[i], 255, cv.ADAPTIVE_THRESH_MEAN_C, cv.THRESH_BINARY, 15, -2))
            #self.get_staff_lines(page_index=i)
            #self.draw_staff_lines(page_index=i)
            cv.imwrite(self.annotated_images_filenames[i], self.images[i])

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
    def __reduce__(self):
        pass
    '''

    def __eq__(self, other):
        for i in range(self.num_pages):
            if len(other.treble_clefs[i]) == len(self.treble_clefs[i]) and len(self.bass_clefs[i]) == len(self.bass_clefs[i]) and len(other.barlines[i]) == len(self.barlines[i]):
                if self.notes == other.notes and self.accidentals == other.acidentals:
                    return


    def remove_lines_from_image(self):
        pass
        #for img in self.lines_removed_images:
        #    img =

    '''
    Takes a sub image and finds all occurances of that sub image in the image.
    Returns a set of Feature objects 
    Not used. parallelized version in Window.py
    '''
    def match_template(self, image, template, color, type,
                       error=10, draw=True):
        gray_template = cv.cvtColor(template, cv.COLOR_BGR2GRAY)
        gray_template_width, gray_template_height = gray_template.shape[::-1]
        gray_image = cv.cvtColor(image, cv.COLOR_BGR2GRAY)
        #res = cv.matchTemplate(gray_image, gray_template, cv.TM_CCOEFF_NORMED)
        res = cv.matchTemplate(gray_image, gray_template, cv.TM_SQDIFF)
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
                f = Feature(pt, (pt[0] + gray_template_width, pt[1] + gray_template_height), type)
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
            f = Feature(pt, (pt[0] + gray_template_width, pt[1] + gray_template_height), type)
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

        #print("feature_lsit:",feature_list)
        if self.is_list_iterable(feature_list) == False:
            print("no features of type", feature_type)
            return
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

    def draw_staff_lines(self, page_index):
        if self.staff_lines[page_index] is not None:
            for line in self.staff_lines[page_index]:
                cv.line(self.images[page_index], line.topleft, line.bottomright, self.type_colors["staff_line"], 1)
        #cv.imwrite(self.annotated_images_filenames[page_index], self.images[page_index])
    '''
    def draw_regions(self, page_index):
        if self.regions[page_index] != None:
            for region in self.regions[page_index]:
                region.draw_region_fill_in_feature(self.images[page_index], self.gray_images[page_index], self.letter_colors, lines=False, borders=True, notes=True, accidentals=True)
        cv.imwrite(self.annotated_images_filenames[page_index], self.images[page_index])
    '''
    '''
    def draw_barlines(self, image, barlines):
        for i in range(len(barlines)):
            for j in range(len(barlines[i])):
                # topleft = (barlines[i][0], barlines[i][1])
                # bottomright = (barlines[i][0] + width, barlines[i][1] + height)
                cv.rectangle(image, barlines[i][j].topleft, barlines[i][j].bottomright, (255, 255, 0), 2)
    '''

    def is_list_iterable(self, list):
        if list is not None and len(list) > 0:
            return True
        return False

    def add_feature_on_click(self, page_index, x, y, type):
        note_height = self.get_note_height(page_index)

        topleft = [x - note_height // 2, y - note_height]
        bottomright = [x + note_height // 2, y + note_height]
        if "flat" == type:
            topleft = [x - note_height // 2, y - (note_height * 3) // 2]
            bottomright = [x + note_height // 2, y + note_height // 2]
        elif "double_flat" == type:
            topleft = [x - note_height, y - (note_height * 3) // 2]
            bottomright = [x + note_height, y + note_height // 2]
        elif "double_sharp" == type:
            topleft = [x - note_height // 2, y - note_height // 2]
            bottomright = [x + note_height // 2, y + note_height // 2]
        feature = Feature(topleft, bottomright, type)
        self.append_features(page_index, type, [feature])

    def add_small_note_on_click(self, page_index, x, y):
        note_height = self.get_note_height(page_index) // 2
        topleft = [x - note_height, y - note_height]
        bottomright = [x + note_height, y + note_height]
        note = Note(topleft, bottomright, is_half_note="quarter", auto_extended=True)
        self.append_features(page_index, "note", [note])

    def add_barline_on_click(self, page_index, x, y):
        if self.is_list_iterable(self.staff_lines[page_index]):
            for i in range(0, len(self.staff_lines[page_index]), 10):
                if i + 9 < len(self.staff_lines[page_index]):
                    top = self.staff_lines[page_index][i].calculate_y(x)
                    bottom = self.staff_lines[page_index][i + 9].calculate_y(x)
                    if top < y < bottom:
                        barline = Feature([x, top],[x + 4, bottom], "barline")
                        self.append_features(page_index, "barline", [barline])
                        return
            print("staff line error when adding barline")
    '''
    If staff lines are note a multiple of 5, then error
    '''
    def does_page_have_staff_line_error(self, page_index):
        self.sort_clefs(page_index)
        if self.is_list_iterable(self.all_clefs[page_index]):
            for row in self.all_clefs[page_index]:
                clef = row[0]
                tl = clef.topleft
                br = clef.bottomright
                if self.is_list_iterable(self.staff_lines[page_index]):
                    staff_line_count = 0
                    for line in self.staff_lines[page_index]:
                        if tl[0] <= line.calculate_y(br[0]) <= br[1]:
                            staff_line_count += 1
                    if staff_line_count != 5:
                        return True
        return False




    # TODO let user input error size
    '''
    Detects horizontal staff lines brute force
    '''
    '''
    Finds horizontal lines in image, then returns set of y-values of staff lines

    First starts off by drawing a vertical line down the center of the page, and selecting black y-values
    Then checks only these y values for staff lines
    If you check every y-value for a staff line it is inefficient
    If page index = -1,  constructor
    '''
    def get_staff_lines(self, page_index, error=5, blackness_threshold=250):
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
        current_staff_lines = []
        for y in histogram:
            current_staff_lines.append(StaffLine([0, y], [self.image_widths[page_index], y], self.image_widths[page_index], self.image_heights[page_index]))
        #if self.staff_lines[page_index] is None:
        #    self.staff_lines[page_index] = current_staff_lines
        #else:
        #    self.staff_lines[page_index] = self.staff_lines[page_index] + current_staff_lines
        self.staff_lines[page_index] = current_staff_lines


    #TODO maybe give more params
    '''
    Used for staff lien detection. Finds first clef in set of staff lines. Then finds white points(inverted image) along vertical line
    '''
    def get_staff_line_candidates(self, page_index, img):
        staff_line_areas = []
        # findind first clef in line
        for row in self.all_clefs[page_index]:
            clef = row[0]
            top = [clef.bottomright[0], clef.topleft[1]]
            bottom = [clef.bottomright[0], clef.bottomright[1]]
            staff_line_areas.append([top, bottom])
        candidates = []
        #finding points just to the right of first clefs
        for area in staff_line_areas:
            top = area[0]
            bottom = area[1]
            for y in range(top[1], bottom[1], 1):
                if img[y][top[0]] > 0:
                    candidates.append([top[0], y])
        return candidates

    def in_bounds(self, x, y, width, height):
        if x < 0 or x >= width or y < 0 or y >= height:
            return False
        return True



    def recursive_vertical(self, vertical_bw_img, x, y, width, height):
        # Base case: if out of bounds or the current pixel is not white, return current coordinates
        best_x, max_y = x, y

        # Explore down
        if self.in_bounds(x, y + 1, width, height) and vertical_bw_img[y + 1][x] > 0:
            temp_x, temp_y = self.recursive_vertical(vertical_bw_img, x, y + 1, width, height)
            if temp_y > max_y:  # Compare y-coordinates to find the furthest downward movement
                best_x, max_y = temp_x, temp_y

        # Explore left-down diagonal
        if self.in_bounds(x - 1, y + 1, width, height) and vertical_bw_img[y + 1][x - 1] > 0:
            temp_x, temp_y = self.recursive_vertical(vertical_bw_img, x - 1, y + 1, width, height)
            if temp_y > max_y:  # Compare y-coordinates to find the furthest downward movement
                best_x, max_y = temp_x, temp_y

        # Explore right-down diagonal
        if self.in_bounds(x + 1, y + 1, width, height) and vertical_bw_img[y + 1][x + 1] > 0:
            temp_x, temp_y = self.recursive_vertical(vertical_bw_img, x + 1, y + 1, width, height)
            if temp_y > max_y:  # Compare y-coordinates to find the furthest downward movement
                best_x, max_y = temp_x, temp_y

        return [best_x, max_y]

    '''
    Gets barlines by finding vertical lines that start at upper top staff line and end at lower bottom staff line
    '''
    def get_barlines(self, page_index):
        start_and_end_staff_lines = []
        #0 and 9th staff lines
        for i in range(0 ,len(self.staff_lines[page_index]), 10):
            if i + 9 < len(self.staff_lines[page_index]):
                start_and_end_staff_lines.append([self.staff_lines[page_index][i], self.staff_lines[page_index][i + 9]])
        img = cv.imread(self.images_filenames[page_index], cv.IMREAD_COLOR)
        # Check if image is loaded fine
        if img is None:
            print('Error opening image: ')
            return -1

        # Transform source image to gray if it is not already
        if len(img.shape) != 2:
            gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
        else:
            gray = img

        # Apply adaptiveThreshold at the bitwise_not of gray, notice the ~ symbol
        gray = cv.bitwise_not(gray)
        #cv.imwrite("gray.jpg", gray)
        vertical = cv.adaptiveThreshold(gray, 255, cv.ADAPTIVE_THRESH_MEAN_C, cv.THRESH_BINARY, 15, -2)
        #cv.imwrite("gray2.jpg", vertical)

        sub_line_length = 10
        verticalStructure = cv.getStructuringElement(cv.MORPH_RECT, (1, sub_line_length))

        # Apply morphology operations
        vertical = cv.erode(vertical, verticalStructure)
        vertical = cv.dilate(vertical, verticalStructure)
        height, width = vertical.shape[:2]
        #edges = cv.adaptiveThreshold(vertical, 255, cv.ADAPTIVE_THRESH_MEAN_C, cv.THRESH_BINARY, 3, -2)
        #edges = cv.Canny(vertical, 50, 150, apertureSize=3)
        #cv.imwrite("vertical.jpg", vertical)

        barlines = []
        error = 10
        mask = np.zeros((height + 2, width + 2), np.uint8)
        for start_and_end in start_and_end_staff_lines:
            start, end = start_and_end
            for x in range(0, self.image_widths[page_index], 2):
                y = start.calculate_y(x) + 10
                #print(x, y)
                if vertical[y][x] > 0:
                    #print("white point")
                    #max_y, best_x = self.recursive_vertical(edges, x, y, width, height)
                    #print(max_y, best_x)
                    _, _, _, rect = cv.floodFill(vertical, mask, (x, y), 0)
                    if (0, 0, 0, 0) == rect:
                        continue
                    x, y, width, height = rect
                    #print(rect)

                    if abs(end.calculate_y(x + width) - (y + height)) < error and width < 10:
                        topleft = [x, y]
                        bottomright = [x + 4, y + height]
                        barlines.append(Feature(topleft, bottomright, "barline"))
                        x += 10

        self.sort_features(barlines)

        if self.barlines[page_index] is None:
            self.barlines[page_index] = barlines
        else:
            self.barlines[page_index] = self.barlines[page_index] + barlines
        #self.remove_adjacent_matches() TODO remove overlapping
        self.remove_adjacent_matches(self.barlines[page_index], 10)

        self.sort_barlines(page_index, error=30)



    '''
    User draws rectangle on screen. Tries to brute force detect staff lines in area
    '''
    def get_staff_lines_region(self, page_index, topleft, bottomright, staff_line_error):
        #Removing any lines in area:
        for i in range(len(self.staff_lines[page_index]) - 1, -1, -1):
            line = self.staff_lines[page_index][i]
            y = line.calculate_y(int(abs(bottomright[0] - topleft[0]) / 2))
            if topleft[1] < y < bottomright[1]:
                #print("existing staff line removed in area")
                self.staff_lines[page_index].remove(line)

        img = cv.imread(self.images_filenames[page_index], cv.IMREAD_COLOR)
        # Check if image is loaded fine
        if img is None:
            print('Error opening image: ')
            return -1

        # Transform source image to gray if it is not already
        if len(img.shape) != 2:
            gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
        else:
            gray = img

        # Apply adaptiveThreshold at the bitwise_not of gray, notice the ~ symbol
        gray = cv.bitwise_not(gray)
        horizontal = cv.adaptiveThreshold(gray, 255, cv.ADAPTIVE_THRESH_MEAN_C, cv.THRESH_BINARY, 15, -2)
        height, width = horizontal.shape[:2]
        x_end = bottomright[0]
        x_start = topleft[0]
        staff_line_offset = 10
        correctness_threshold = .7
        results = []
        for y_start in range(topleft[1], bottomright[1], 1):  # For every white pixel found

            for y_end in range(y_start - staff_line_offset, y_start + staff_line_offset, 1):  # for every pixel on right side within +- staff_line_offset of start_Y
                if y_end >= 0 and y_end < height:  # If in bounds
                    Ay = y_end - y_start
                    Ax = x_end - x_start
                    slope = Ay / Ax
                    count = 0
                    # num_consecutive = 0
                    for x_traverse in range(x_start, x_end - 1, 1):  # Traverse the line between y_start and y_end
                        y_traverse = int(slope * (x_traverse - x_start) + y_start)
                        if horizontal[y_traverse][x_traverse] > 0:
                            count = count + 1
                        if (x_traverse - x_start) > 100 and count / (x_traverse - x_start) < correctness_threshold:
                            break
                    if count > (x_end - x_start) / 2:
                        results.append([y_start, y_end, count])

        print("unfiltered", results)
        results.sort(key=lambda x: (x[0], x[2]))#Sort by y_value, then count
        results_filtered = []
        i = 0
        while i < len(results) - 1:
            if results[i][0] == results[i + 1][0]:  # Same y-coordinate
                results_filtered.append(results[i])
                while i < len(results) - 1 and results[i][0] == results[i + 1][0]:
                    i += 1
            i += 1  # Move to the next element

        # Append the last element if needed
        if i == len(results) - 1:
            results_filtered.append(results[i])

        i = 0
        while i < len(results_filtered):
            current = i
            i = i + 1
            while i < len(results_filtered) and abs(results_filtered[i][0] - results_filtered[current][0]) < staff_line_error:
                # print(histogram[current], "current")
                # print(histogram[i], "removed")
                results_filtered.remove(results_filtered[i])
                # i = i + 1


        print("results", results_filtered)
        current_staff_lines = []
        for result in results_filtered:
            current_staff_lines.append(StaffLine([x_start, result[0]], [x_end, result[1]], self.image_widths[page_index], self.image_heights[page_index]))
        if self.staff_lines[page_index] is None:
            self.staff_lines[page_index] = current_staff_lines
        else:
            self.staff_lines[page_index] = self.staff_lines[page_index] + current_staff_lines
        self.sort_staff_lines(page_index)



    def recursive(self, img, x, y, width, height, was_previous_iteration_diagonal):
        # Base case: if out of bounds or no further movement possible, return current x and y values
        max_x, best_y = x, y

        # Explore right
        if self.in_bounds(x + 1, y, width, height) and img[y][x + 1] > 0:
            temp_x, temp_y = self.recursive(img, x + 1, y, width, height, False)
            if temp_x > max_x:
                max_x, best_y = temp_x, temp_y

        # Explore right-down diagonal
        elif was_previous_iteration_diagonal != True:
            if self.in_bounds(x + 1, y + 1, width, height) and img[y + 1][x + 1] > 0:
                temp_x, temp_y = self.recursive(img, x + 1, y + 1, width, height, True)
                if temp_x > max_x:
                    max_x, best_y = temp_x, temp_y

            # Explore right-up diagonal
            elif self.in_bounds(x + 1, y - 1, width, height) and img[y - 1][x + 1] > 0:
                temp_x, temp_y = self.recursive(img, x + 1, y - 1, width, height, True)
                if temp_x > max_x:
                    max_x, best_y = temp_x, temp_y

        #to the right two pixels
        elif self.in_bounds(x + 3, y, width, height) and img[y][x + 2] > 0:
            temp_x, temp_y = self.recursive(img, x + 2, y, width, height, False)
            if temp_x > max_x:
                max_x, best_y = temp_x, temp_y

        #to right 10 pixels
        elif self.in_bounds(x + 10, y, width, height) and img[y][x + 10] > 0:
            temp_x, temp_y = self.recursive(img, x + 10, y, width, height, False)
            if temp_x > max_x:
                max_x, best_y = temp_x, temp_y

        elif self.in_bounds(x + 50, y, width, height) and img[y][x + 50] > 0:
            temp_x, temp_y = self.recursive(img, x + 50, y, width, height, False)
            if temp_x > max_x:
                max_x, best_y = temp_x, temp_y

        return [max_x, best_y]


    '''
    Tries to draw a line from left to right side
    '''
    def get_staff_lines_diagonal_recursive(self, page_index, error=5, use_union_image=False, vertical_size=20, horizontal_size=20):
        self.sort_clefs(page_index)
        self.staff_lines[page_index] = []
        img = cv.imread(self.images_filenames[page_index], cv.IMREAD_COLOR)
        # Check if image is loaded fine
        if img is None:
            print('Error opening image: ')
            return -1

        # Transform source image to gray if it is not already
        if len(img.shape) != 2:
            gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
        else:
            gray = img

        # Apply adaptiveThreshold at the bitwise_not of gray, notice the ~ symbol
        gray = cv.bitwise_not(gray)
        #horizontal = cv.bitwise_not(gray)
        bw = cv.adaptiveThreshold(gray, 255, cv.ADAPTIVE_THRESH_MEAN_C, cv.THRESH_BINARY, 15, -2)

        # [init]
        # Create the images that will use to extract the horizontal and vertical lines
        horizontal = np.copy(bw)

        # Create structure element for extracting horizontal lines through morphology operations
        horizontalStructure = cv.getStructuringElement(cv.MORPH_RECT, (horizontal_size, 1))

        # Apply morphology operations
        horizontal = cv.erode(horizontal, horizontalStructure)
        horizontal = cv.dilate(horizontal, horizontalStructure)
        #cv.imwrite("horizontal" + str(page_index) +".jpg", horizontal)
        height, width = horizontal.shape[:2]
        img = None
        if use_union_image == True:
            vertical = np.copy(bw)
            verticalStructure = cv.getStructuringElement(cv.MORPH_RECT, (1, vertical_size))

            # Apply morphology operations
            vertical = cv.erode(vertical, verticalStructure)
            vertical = cv.dilate(vertical, verticalStructure)
            img = cv.bitwise_or(vertical, horizontal)
            #cv.imwrite("aunionstaffline.jpg", img)
        else:
            img = horizontal


        candidates = self.get_staff_line_candidates(page_index, img)#(x, y)
        results = []
        sys.setrecursionlimit(width * 2)
        for candidate in candidates:  # For every white pixel found
            x_start = candidate[0]
            y_start = candidate[1]
            result = self.recursive(img, x_start, y_start, width, height, False)
            if result[0] > width * 3 / 4:
                results.append([x_start, y_start, result[0], result[1]])

        results.sort(key=lambda x: (x[1]))
        #print(results)

        #Removing adjacent lines
        results_filtered = []
        i = 0
        while i < len(results):
            current = i
            i = i + 1
            results_filtered.append(results[current])

            while i < len(results) and abs(results[current][1] - results[i][1]) < error:
                #print(error, "removed")
                #results.remove(results[i])
                i = i + 1


        current_staff_lines = []
        for result in results_filtered:
            current_staff_lines.append(StaffLine([result[0], result[1]], [result[2], result[3]], self.image_widths[page_index], self.image_heights[page_index]))
        if self.staff_lines[page_index] is None:
            self.staff_lines[page_index] = current_staff_lines
        else:
            self.staff_lines[page_index] = self.staff_lines[page_index] + current_staff_lines



    def detect_staff_line_group(self, img, x, top_y, bottom_y, staff_line_thickness=5):
        points = []

        # Iterate through the y-axis in the column (x)
        y = top_y
        while y < bottom_y:
            if img[y][x] == 255:
                y_start = y

                # Continue until the end of the white pixel region
                while y < bottom_y and img[y][x] == 255:
                    y += 1

                # Check if the detected white region is too thick
                if (y - y_start) > staff_line_thickness:
                    return False

                # Store the midpoint of the white region
                midpoint = y_start + (y - y_start) // 2
                points.append(midpoint)

            y += 1

        # Ensure exactly 5 points were detected
        if len(points) != 5:
            return False

        # Calculate the expected spacing between points
        spacing = points[1] - points[0]

        # Check that the spacing between points is consistent
        for i in range(1, len(points) - 1):
            if abs((points[i + 1] - points[i]) - spacing) > 2:
                return False

        # Return the detected points if all conditions are met
        #print(points)
        return points

    '''
    Todo: draws vertical lines, finds if vertical line intersects staff line exactly 5 times
    '''
    def get_staff_lines_diagonal_by_traversing_vertical_line(self, page_index):
        self.sort_clefs(page_index)
        self.staff_lines[page_index] = []
        img = cv.imread(self.images_filenames[page_index], cv.IMREAD_COLOR)
        # Check if image is loaded fine
        if img is None:
            print('Error opening image: ')
            return -1

        # Transform source image to gray if it is not already
        if len(img.shape) != 2:
            gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
        else:
            gray = img

        # Apply adaptiveThreshold at the bitwise_not of gray, notice the ~ symbol
        gray = cv.bitwise_not(gray)
        # horizontal = cv.bitwise_not(gray)
        bw = cv.adaptiveThreshold(gray, 255, cv.ADAPTIVE_THRESH_MEAN_C, cv.THRESH_BINARY, 15, -2)

        height, width = bw.shape[:2]
        img = bw
        #cv.imwrite("aimg.jpg", img)
        #TODO calculate all groups, then find closest group for note
        staff_line_areas = []
        # findind first clef in line
        if not self.is_list_iterable(self.all_clefs[page_index]):
            print("Need to add clefs")
            return
        for row in self.all_clefs[page_index]:
            clef = row[0]
            adjustment = 20
            if clef.type == "treble_clef":
                adjustment = 0
            top = [clef.topleft[0], clef.topleft[1] - adjustment]
            bottom = [clef.topleft[0], clef.bottomright[1] + adjustment]
            staff_line_areas.append([top, bottom])
        current_staff_lines = []
        for area in staff_line_areas:
            top, bottom = area
            current_group = []
            left_x = 0
            left_group = []
            right_x = 0
            right_group = []
            count = 0
            for x in range(top[0], width, 1):
                group = self.detect_staff_line_group(img, x, top[1], bottom[1])
                if group:
                    left_x = x
                    left_group = group
                    count += 1
                    break
            for x in range(self.image_widths[page_index] - 1, top[0], -1):
                group = self.detect_staff_line_group(img, x, top[1], bottom[1])
                if group:
                    right_x = x
                    right_group = group
                    count += 1
                    break
            if count == 2:
                for i in range(5):
                    current_staff_lines.append(StaffLine([left_x,left_group[i]],[right_x, right_group[i]],width, height))
            else:
                print("Unable to generate staff lines on page " + str(page_index))


        if self.staff_lines[page_index] is None:
            self.staff_lines[page_index] = current_staff_lines
        else:
            self.staff_lines[page_index] = self.staff_lines[page_index] + current_staff_lines

    def calculate_note_or_accidental(self, note, group, clef):
        spacing = abs(group[4][1] - group[0][1]) / 8
        distance = note.center[1] - group[0][1]
        letters = ['a', 'b', 'c', 'd', 'e', 'f', 'g']
        letter_index = 0
        if clef == "treble_clef":
            letter_index = 5
        note_shift = round(distance / spacing)
        letter_index = (letter_index - note_shift) % len(letters)
        if note.letter.islower():
            note.letter = letters[letter_index]


    def calculate_notes_and_accidentals_for_distorted_staff_lines(self, page_index, region, img, staff_line_error):
        #TODO
        print("calculating notes and accidentals for distorted staff lines on page", page_index)
        notes = region.notes
        accidentals = region.accidentals
        height, width = img.shape[:2]
        lines_in_region = []
        if self.is_list_iterable(self.staff_lines[page_index]) == False:
            return
        for line in self.staff_lines[page_index]:
            if region.topleft[1] < line.calculate_y(width / 2) < region.bottomright[1]:  # if line is in region
                lines_in_region.append(line)
        if len(lines_in_region) == 5:
            line_spacing = abs(lines_in_region[-1].calculate_y(width / 2) - lines_in_region[0].calculate_y(width / 2)) / 8
        else:
            print("missing staff line")
            return

        topleft = lines_in_region[0].calculate_y(region.topleft[0])
        topright = lines_in_region[0].calculate_y(region.bottomright[0])
        bottomleft = lines_in_region[4].calculate_y(region.topleft[0])
        bottomright = lines_in_region[4].calculate_y(region.bottomright[0])
        top_y = min(topleft, topright) - staff_line_error
        bottom_y = max(bottomleft, bottomright) + staff_line_error
        current_group = []
        x = region.topleft[0]
        consecutive_times_without_finding_group = 0
        while x < region.bottomright[0]:
        #for x in range(region.topleft[0], region.bottomright[0], 1):
            group = self.detect_staff_line_group(img, x, top_y, bottom_y)
            if group:
                coordinates_2d = [[x, y] for y in group]
                current_group.append(coordinates_2d)
                #current_group.append([x, group])
                #for y in group:
                #self.notes[page_index].append(Note([x-1, group[0]],[x+1, group[4]], False, False, False))
                cv.line(img, [x, coordinates_2d[0][1]], [x, coordinates_2d[4][1]], 255, 1)
                x += 20
                consecutive_times_without_finding_group = 0
            else:
                consecutive_times_without_finding_group += 1
                x += 1
            if consecutive_times_without_finding_group > 20:
                print("went 20 pixels without detecting staff lines", region.topleft, region.bottomright)
        for note in notes:
            closest_group = None
            min_distance = 100000
            for group in current_group:
                if abs(group[0][0] - note.center[0]) < min_distance:
                    closest_group = group
                    min_distance = abs(x - note.center[0])
            if closest_group is not None:
                self.calculate_note_or_accidental(note, closest_group, region.clef)
            else:
                print("couldnt find any groups for region", region.topleft, region.bottomright)
        for acc in accidentals:
            closest_group = None
            min_distance = 100000
            for group in region.staff_line_groups:
                if abs(group[0][0] - acc.center[0]) < min_distance:
                    closest_group = group
                    min_distance = abs(x - acc.center[0])
            if group is not None:
                self.calculate_note_or_accidental(acc, group, region.clef)

    def generate_diagonal_staff_lines_block(self, page_index, topleft, topright, bottomright):
        line_spacing = int(abs(topright[1] - bottomright[1]) / 4)
        for i in range(5):
            self.staff_lines[page_index].append(StaffLine([topleft[0], topleft[1] + line_spacing * i], [topright[0], topright[1] + line_spacing * i], self.image_widths[page_index], self.image_heights[page_index]))
        self.sort_staff_lines(page_index)

    def add_staff_line(self, page_index, staff_line):
        if self.staff_lines[page_index] is None:
            self.staff_lines[page_index] = [staff_line]
        else:
            self.staff_lines[page_index].append(staff_line)
        self.sort_staff_lines(page_index)

    def sort_staff_lines(self, page_index):
        self.staff_lines[page_index].sort(key=lambda x: x.topleft[1])

    '''
    Sorts array of features from top to bottom, left to right in 1d array
    '''

    def sort_features(self, features):
        if features is not None:
            features.sort(key=lambda x: (x.topleft[1], x.topleft[0]))


    def is_feature_in_rectange(self, feature, topleft, bottomright):
        if topleft[0] < feature.center[0] < bottomright[0] and topleft[1] < feature.center[1] < bottomright[1]:
            return True
        else:
            return False
    '''
    Resets every accidental
    '''
    def reset_accidentals(self, page_index, topleft, bottomright):
        if self.notes[page_index] is not None and len(self.notes[page_index]) > 0:
            for note in self.notes[page_index]:
                if self.is_feature_in_rectange(note, topleft, bottomright) == True:
                    note.accidental = ""
    '''
    Finds notes in the rectangle drawn on the screen and sets the accidental as long as the current note doesnt have an accidental
    '''
    def set_key(self, page_index, topleft, bottomright, accidental_type, key):
        if self.notes[page_index] is not None and len(self.notes[page_index]) > 0:
            for note in self.notes[page_index]:
                if self.is_feature_in_rectange(note, topleft, bottomright) == True and note.accidental == "":
                    if note.letter.lower() in key:
                        note.accidental = accidental_type

    def get_note_height(self, page_index):
        note_height = 5
        if len(self.staff_lines[page_index]) > 4:
            mid = int(self.image_widths[page_index] / 2)
            note_height = int(abs(self.staff_lines[page_index][4].calculate_y(mid) - self.staff_lines[page_index][0].calculate_y(mid)) / 4)
            #print(note_size)
        else:
            print("need more staff lines to auto resize notes")
        return note_height + 2

    def detect_note_type(self, page_index, note):
        white_count = 0
        for y in range(note.topleft[1], note.bottomright[1]):
            for x in range(note.topleft[0], note.bottomright[0]):
                if self.bw_images[page_index][y][x] == 1:
                    white_count += 1
        if white_count / self.get_area_of_feature(note) < 50:
            return "quarter"
        else:
            return "half"

    def auto_detect_half_or_quarter_note(self, page_index):
        for note in self.notes[page_index]:
            if self.detect_note_type(page_index, note) == "half":
                note.is_half_note = "half"
            else:
                note.is_half_note = "quarter"

    def remove_small_notes(self, page_index):
        note_height = self.get_note_height(page_index)
        for i in range(len(self.notes[page_index]) - 1, -1, -1):
            note = self.notes[page_index][i]
            if note.get_height() / note_height < .8 and note.auto_extended == False:
                self.notes[page_index].pop(i)
            if note.get_width() / note_height > 2:
                self.notes[page_index].pop(i)

    def remove_unautosnapped_notes(self, page_index):
        for i in range(len(self.notes[page_index]) - 1, -1, -1):
             if self.notes[page_index][i].auto_extended == False:
                self.notes[page_index].pop(i)


    def detect_unautosnapped_half_notes(self, page_index):
        for i in range(len(self.notes[page_index]) - 1, -1, -1):
            note = self.notes[page_index][i]
            if note.auto_extended == False and note.is_half_note == "half" or note.is_half_note == "whole":
                print("Half note not auto extended on page ", page_index, ": ", note.center)
    def do_features_overlap(self, one, two):
        #if one feature is to the left
        if one.bottomright[0] <= two.topleft[0] or two.bottomright[0] <= one.topleft[0]:
            return False
        #if one feature is above
        if one.bottomright[1] <= two.topleft[1] or two.bottomright[1] <= one.topleft[1]:
            return False
        return True

    def is_feature_to_left(self, one, two):
        (x1_tl, y1_tl) = one.topleft
        (x1_br, y1_br) = one.bottomright
        (x2_tl, y2_tl) = two.topleft
        (x2_br, y2_br) = two.bottomright

        # Check if the left side of rect1 intersects with rect2
        left_x1 = x1_tl
        if x2_tl <= left_x1 <= x2_br:
            # Check if the y ranges overlap
            if not (y1_br < y2_tl or y1_tl > y2_br):
                return True
        return False


    def is_feature_to_right(self, one, two):
        (x1_tl, y1_tl) = one.topleft
        (x1_br, y1_br) = one.bottomright
        (x2_tl, y2_tl) = two.topleft
        (x2_br, y2_br) = two.bottomright

        # Check if the right side of rect1 intersects with rect2
        right_x1 = x1_br
        if x2_tl <= right_x1 <= x2_br:
            # Check if the y ranges overlap
            if not (y1_br < y2_tl or y1_tl > y2_br):
                return True
        return False

    def is_feature_below(self, one, two):
        (x1_tl, y1_tl) = one.topleft
        (x1_br, y1_br) = one.bottomright
        (x2_tl, y2_tl) = two.topleft
        (x2_br, y2_br) = two.bottomright

        # Check if the top side of rect1 intersects with rect2
        top_y1 = y1_tl
        if y2_br <= top_y1 <= y2_tl:
            # Check if the x ranges overlap
            if not (x1_br < x2_tl or x1_tl > x2_br):
                return True
        return False

    def is_feature_above(self, one, two):
        (x1_tl, y1_tl) = one.topleft
        (x1_br, y1_br) = one.bottomright
        (x2_tl, y2_tl) = two.topleft
        (x2_br, y2_br) = two.bottomright

        # Check if the bottom side of rect1 intersects with rect2
        bottom_y1 = y1_br
        if y2_br <= bottom_y1 <= y2_tl:
            # Check if the x ranges overlap
            if not (x1_br < x2_tl or x1_tl > x2_br):
                return True

        #check if top side of rect2 intersects with rect1
        return False

    def does_vertical_line_intersect_feature(self, line_top, line_bottom, feature):
        # Unpack coordinates for readability
        line_x, line_y_top = line_top
        _, line_y_bottom = line_bottom

        rect_x_left, rect_y_top = feature.topleft
        rect_x_right, rect_y_bottom = feature.bottomright

        # Condition 1: The vertical line's x-coordinate must be strictly inside the rectangle's horizontal boundaries
        if line_x <= rect_x_left or line_x >= rect_x_right:
            return False

        # Condition 2: The line must overlap the rectangle vertically, excluding cases where it only touches the edges
        if line_y_bottom <= rect_y_top or line_y_top >= rect_y_bottom:
            return False

        # If both conditions are satisfied, the line intersects the rectangle
        return True

    def does_horizontal_line_intersect_feature(self, line_left, line_right, feature):
        # Unpack coordinates for readability
        line_x_left, line_y = line_left
        line_x_right, _ = line_right

        rect_x_left, rect_y_top = feature.topleft
        rect_x_right, rect_y_bottom = feature.bottomright

        # Condition 1: The horizontal line's y-coordinate must be strictly inside the rectangle's vertical boundaries
        if line_y <= rect_y_top or line_y >= rect_y_bottom:
            return False

        # Condition 2: The line must overlap the rectangle horizontally, excluding cases where it only touches the edges
        if line_x_right <= rect_x_left or line_x_left >= rect_x_right:
            return False

        # If both conditions are satisfied, the line intersects the rectangle
        return True

    '''
    Manually extending notes in a direction. If notes overlap, wont extend
    '''
    def extend_notes(self, page_index, up, down, left, right, note_type, include_auto_extended_notes):
        if self.notes[page_index] is not None and len(self.notes[page_index]) > 0:
            for i in range(len(self.notes[page_index])):

                note = self.notes[page_index][i]
                if note.is_half_note != note_type or note.is_auto_extended() != include_auto_extended_notes:
                    continue
                note.topleft = [note.topleft[0] - left, note.topleft[1] - up]
                note.bottomright = [note.bottomright[0] + right, note.bottomright[1] + down]
                for j in range(len(self.notes[page_index])):
                    if i != j:
                        if left != 0:#extending horizontally
                            if self.does_vertical_line_intersect_feature(note.topleft, note.get_bottomleft(), self.notes[page_index][j]) == True:
                                note.topleft[0] += left
                                break
                        if right != 0:
                            if self.does_vertical_line_intersect_feature(note.get_topright(), note.bottomright, self.notes[page_index][j]) == True:
                                note.bottomright[0] -= right
                                break
                        if up != 0:#Extending vertically
                            if self.does_horizontal_line_intersect_feature(note.topleft, note.get_topright(), self.notes[page_index][j]) == True:
                                note.topleft[1] += up
                                break
                        if down != 0:
                            if self.does_horizontal_line_intersect_feature(note.get_bottomleft(), note.bottomright, self.notes[page_index][j]) == True:
                                note.bottomright[1] -= down
                                break


    def add_note_by_center_coordinate(self, page_index, x, y, note_type, note_height_width_ratio):
        note_height = self.get_note_height(page_index)
        note_width = int(note_height * note_height_width_ratio / 100)
        topleft = [int(x - note_width / 2), int(y - note_height / 2)]
        bottomright = [int(x + note_width / 2), int(y + note_height / 2)]
        note = Note(topleft, bottomright, is_half_note=note_type, auto_extended=False)
        #TODO
    '''
    Tries to autosnap notes by assuming that implied lines will pass through center of note, and adjacent implied lines travel through top and bottom of note
    '''
    def autosnap_notes_to_implied_line(self, page_index):
        if self.regions[page_index] is not None and len(self.regions[page_index]) > 0:
            for region in self.regions[page_index]:
                region.autosnap_notes_to_implied_line()

    '''
    Extends half notes using flood fill. Cases for when staff line runs through the note or not
    '''
    def auto_extend_half_note(self, page_index, note, img, mask, note_height, note_width):
        rects = []
        #adjustment = 2
        vertical_adjustment = 2
        horizontal_adjustment = 2
        if note.is_half_note == "whole":
            horizontal_adjustment = 7
        #cv.imwrite("ahalfnote.jpg", img)

        #traversing around the center and outward
        center_x, center_y = note.center

        # Calculate the maximum radius from the center to the rectangle's edges
        x_radius = note.get_width() // 2
        y_radius = note.get_height() // 2
        max_radius = max(x_radius, y_radius)
        # Traverse outward from the center
        for radius in range(max_radius + 1):
            for y_offset in range(-radius, radius + 1):
                for x_offset in range(-radius, radius + 1):
                    # Calculate the current position
                    x_traverse = center_x + x_offset
                    y_traverse = center_y + y_offset

                    # Ensure the position is within the bounds of the rectangle
                    if (note.topleft[0] <= x_traverse <= note.bottomright[0] and note.topleft[1] <= y_traverse <= note.bottomright[1]):
                        # Do your processing here with x_traverse and y_traverse
                        #if pixel is white, flood fill
                        if img[y_traverse][x_traverse] == 0:
                            start_point = (x_traverse, y_traverse)
                            _, _, _, rect = cv.floodFill(img, mask, start_point, 0)
                            #print(rect)
                            x, y, width, height = rect
                            if height > note_height * 1.5 or width > note_height * 2:
                                print("Half note is open", note.center)
                            else:
                                if rect != (0,0,0,0):
                                    if height / note_height < 1.3 and width / note_width < 1.3:
                                        rects.append(rect)
                                        #self.notes[page_index].append(Note([rect[0], rect[1]], [rect[0] + rect[2], rect[1] + rect[3]], "quarter", True))

                                if .5 < height / note_height < 1.3 and .3 < width / note_width < 1.3:
                                    #adjustment = int((note_height - height) / 2)
                                    if x <= center_x <= x + width and y <= center_y <= y + height:
                                        note.topleft = [x - horizontal_adjustment, y - vertical_adjustment]
                                        note.bottomright = [x + width + horizontal_adjustment, y + height + vertical_adjustment]
                                        note.reset_center()
                                        note.auto_extended = True
                                        note.is_on_line = False
                                    else:
                                        print("center not in resultant half note", center_x, center_y)
                                    return
                                if len(rects) == 2:
                                    top_rect = rects[0]
                                    bottom_rect = rects[1]
                                    # if second rect is above first rect
                                    if rects[1][1] < rects[0][1]:
                                        top_rect = rects[1]
                                        bottom_rect = rects[0]
                                    x_top, y_top, width_top, height_top = top_rect
                                    x_bottom, y_bottom, width_bottom, height_bottom = bottom_rect
                                    x_topleft = x_top
                                    x_bottomright = x_bottom
                                    if x_bottomright < x_topleft:
                                        x_topleft = x_bottom
                                        x_bottomright = x_top
                                        temp = width_bottom
                                        width_bottom = width_top
                                        width_top = temp
                                    if x_topleft <= center_x <= x_bottomright + width_bottom and y_top <= center_y <= y_bottom + height_bottom:

                                        # adjustment = int((note_height - height) / 2)
                                        note.topleft = [x_topleft - horizontal_adjustment, y_top - vertical_adjustment]
                                        note.bottomright = [x_bottomright + width_bottom + horizontal_adjustment,
                                                            y_bottom + height_bottom + vertical_adjustment]
                                        note.reset_center()
                                        note.center[1] = y_top + height_top + int((y_bottom - (y_top + height_top)) / 2)
                                        note.auto_extended = True
                                        note.is_on_line = True
                                    else:
                                        print("center not in resultant half note", center_x, center_y)
                                    return

        if len(rects) == 1:
            print("half note is probably open", note.center)
            '''
            x, y, width, height = rects[0]
            note.topleft = [x - horizontal_adjustment, y - vertical_adjustment]
            note.bottomright = [x + width + horizontal_adjustment, y + height + vertical_adjustment]
            note.reset_center()
            note.auto_extended = True
            '''

        else:
            print("couldnt autosnap half note ", len(rects), "rects")




    def get_area_of_feature(self, feature):
        return int(abs(feature.bottomright[0] - feature.topleft[0]) * abs(feature.bottomright[1] - feature.topleft[1]))

    def remove_overlapping_notes(self, page_index, topleft, bottomright):
        if self.is_list_iterable(self.notes[page_index]):
            for i in range(len(self.notes[page_index]) - 1, -1, -1):
                current_note = self.notes[page_index][i]
                if self.do_features_overlap(Feature(topleft, bottomright, "temp"), current_note) and current_note.auto_extended == False:
                    #TODO condition for removal
                    if current_note.auto_extended == False or self.current_note.topleft == topleft and self.current_note.bottomright == bottomright:
                        self.notes[page_index].pop(i)


    def extend_quarter_note_single(self, note, x, y, width, height):
        note.topleft[0] = x - 1
        note.topleft[1] = y - 1
        note.bottomright[0] = x + width + 1
        note.bottomright[1] = y + height + 1

        note.reset_center()
        note.auto_extended = True

    def extend_quarter_note_multiple(self, page_index, x, y, width, height, note_height, note_count):
        spacing = height / note_count
        for i in range(note_count):
            top = y + round(i * spacing)
            bottom = y + round((i + 1) * spacing)
            note = Note([x, top], [x + width, bottom], is_half_note="quarter", auto_extended=True)
            #self.remove_overlapping_notes(page_index, note, note_height)
            self.append_features(page_index, "note", [note])


    def using_rect_dimensions_get_combination_note_type(self, page_index, rect, note_height, note_width):
        x, y, width, height = rect
        #print(x, y, width, height, "rect dimensions")
        #if .7 < width / note_width < 1.3:
        height_ratio = round(height / note_height)
        if .5 < height_ratio < 1.5:
            note = Note([x, y], [x + width, y + height], is_half_note="quarter", auto_extended=True)
            #self.notes[page_index].append(note)
            self.append_features(page_index, "note", [note])
            self.extend_quarter_note_single(note, x, y, width, height)
        elif 1.5 < height_ratio < 5.5:
            self.extend_quarter_note_multiple(page_index, x, y, width, height, note_height, height_ratio)
    '''
    Using flood fill on center of note, if rect dimensions make match an expected note's dimensions, then extend.
    Also senses clusters of notes like pb, bp and 2,3,4,5, notes vertically aligned
    '''
    def auto_extend_quarter_note(self, page_index, note, img, mask, note_height, note_width, debugging):
        #TODO no mutliple extending, just draw black line on image
        #recursively expand inside note border. Then reduce

        start_point = (note.center[0], note.center[1])
        # Flood fill starting from the start_point
        # The function will replace the connected white region with a new value (e.g., 127)
        #print("image",img[start_point[1]][start_point[0]])
        if img[start_point[1]][start_point[0]] == 255:
            _, _, _, rect = cv.floodFill(img, mask, start_point, 255)
            if rect == (0, 0, 0, 0):
                pass
            else:
                #print(rect)
                x, y, width, height = rect
                #note = Note([x, y], [x + width, y + height], False, auto_extended=True)
                #self.notes[page_index].append(note)
                #return
                if .7 < width / note_width < 1.3:
                    self.remove_overlapping_notes(page_index, [x, y], [x + width, y + height])
                    self.using_rect_dimensions_get_combination_note_type(page_index, rect, note_height, note_width)

                elif .7 < width / note_width / 2 < 1.3:# and .7 < height > note_height  * 2:
                    #TODO we are editing the notes list while iterating through it. need to same img. try making blank line thicker
                    #Reseting the mask to 0
                    #todo reset mask to 0 only in portion using rect dimensions
                    mask_copy = mask[y:y+height+1, x:x+width+1].copy()
                    np.set_printoptions(threshold=np.inf)
                    #print(mask_copy)
                    mask[y:y+height, x:x+width] = np.zeros((height, width), np.uint8)
                    #Making a border on the center line
                    for y_traverse in range(y, y + height, 1):
                        img[y_traverse][x + int(width / 2)] = 0
                    #removing small groups of pixels in case splitting not exactly in the center
                    horizontalStructure = cv.getStructuringElement(cv.MORPH_RECT, (3, 1))
                    sub_image = img[y:y+height, x:x+width]
                    sub_image = cv.erode(sub_image, horizontalStructure)
                    sub_image = cv.dilate(sub_image, horizontalStructure)
                    img[y:y+height, x:x+width] = sub_image
                    if debugging:
                        cv.imwrite("avertremoved.jpg", img)
                    #traversing left side vertically
                    for y_traverse in range(y, y + height + 1, 1):
                        start_point = (x + int(width / 4), y_traverse)
                        #print("y_start", y, "yend", y + height, "traverse", y_traverse, "reset mask val", mask[start_point[1]][start_point[0]], "old mask val", mask_copy[start_point[1] - y][start_point[0] - x])
                        if img[start_point[1]][start_point[0]] == 255 and mask_copy[start_point[1] - y][start_point[0] - x] == 1:
                            _, _, _, rect2 = cv.floodFill(img, mask, start_point, 255)
                            #self.barlines[page_index].append(Feature(start_point, [start_point[0] + 2, start_point[1] + 2], type="barline"))
                            #self.images[page_index][start_point[1]][start_point[0]] = (255, 0, 0)
                            if rect2 == (0, 0, 0, 0):
                                pass
                            else:
                                x2, y2, width2, height2 = rect2
                                #self.treble_clefs[page_index].append(Feature([x,y], [x + width, y + height], "treble_clef"))
                                self.remove_overlapping_notes(page_index, [x2, y2], [x2 + width2, y2 + height2])
                                self.using_rect_dimensions_get_combination_note_type(page_index, rect2, note_height, note_width)
                                #break

                    for y_traverse in range(y, y + height, 1):
                        start_point = (x + int(width * 3 / 4), y_traverse)
                        #print("y_start", y, "yend", y + height, "traverse", y_traverse, "reset mask val", mask[start_point[1]][start_point[0]], "old mask val", mask_copy[start_point[1] - y][start_point[0] - x])
                        if img[start_point[1]][start_point[0]] == 255 and mask_copy[start_point[1] - y][start_point[0] - x] == 1:
                            _, _, _, rect2 = cv.floodFill(img, mask, start_point, 255)
                            #self.barlines[page_index].append(Feature(start_point, [start_point[0] + 2, start_point[1] + 2], type="barline"))
                            #self.images[page_index][start_point[1]][start_point[0]] = (255, 0, 0)
                            if rect2 == (0, 0, 0, 0):
                                pass
                            else:
                                x2, y2, width2, height2 = rect2
                                #self.bass_clefs[page_index].append(Feature([x, y], [x + width, y + height], "bass_clef"))
                                self.remove_overlapping_notes(page_index, [x2, y2], [x2 + width2, y2 + height2])
                                self.using_rect_dimensions_get_combination_note_type(page_index, rect2, note_height, note_width)
                                #break
                else:
                    pass
                    #note = Note([x, y], [x + width, y + height], False, auto_extended=True)
                    #self.notes[page_index].append(note)
        else:
            #print("center not black")
            return "remove"
            #TODO remove note


    def extend_small_note(self, page_index, x, y, blackness):
        note_height = self.get_note_height(page_index)
        # print(note_height, note_width)
        # gray = cv.bitwise_not(self.gray_images[page_index])
        # bw = cv.adaptiveThreshold(gray, 255, cv.ADAPTIVE_THRESH_MEAN_C, cv.THRESH_BINARY, 15, -2)
        _, bw = cv.threshold(self.gray_images[page_index], blackness, 255, cv.THRESH_BINARY)
        bw = cv.bitwise_not(bw)
        vertical = np.copy(bw)
        horizontal = np.copy(bw)
        horizontal_size = int(note_height / 2)
        horizontalStructure = cv.getStructuringElement(cv.MORPH_RECT, (horizontal_size, 1))

        # Apply morphology operations
        horizontal = cv.erode(horizontal, horizontalStructure)
        horizontal = cv.dilate(horizontal, horizontalStructure)
        verticalsize = int(note_height / 2)
        # Create structure element for extracting vertical lines through morphology operations
        verticalStructure = cv.getStructuringElement(cv.MORPH_RECT, (1, verticalsize))

        # Apply morphology operations
        vertical = cv.erode(vertical, verticalStructure)
        vertical = cv.dilate(vertical, verticalStructure)
        intersection = cv.bitwise_and(horizontal, vertical)
        h, w = intersection.shape[:2]
        mask = np.zeros((h + 2, w + 2), np.uint8)
        intersection_image = cv.bitwise_and(horizontal, vertical)
        if intersection_image[y][x] == 255:
            _, _, _, rect = cv.floodFill(intersection_image, mask, (x, y), 255)
            if rect == (0, 0, 0, 0):
                print("small note note not found")
                pass
            else:
                #print(rect)
                print("small note found")
                x, y, width, height = rect
                adjustment = 1

                topleft = [x - adjustment, y - adjustment]
                bottomright = [x + width + adjustment, y + height + adjustment]
                note = Note(topleft, bottomright, is_half_note="quarter", auto_extended=True)
                self.append_features(page_index, "note", [note])
        else:
            print("center note black")

    '''
    usign an image that removes staff lines, extends notes
    '''
    def auto_extend_notes(self, page_index, note_height_width_ratio, debugging, blackness, note=None):
        print("auto extend page", page_index)
        note_height = self.get_note_height(page_index)
        note_width = int(note_height * note_height_width_ratio / 100)
        #print(note_height, note_width)
        #gray = cv.bitwise_not(self.gray_images[page_index])
        #bw = cv.adaptiveThreshold(gray, 255, cv.ADAPTIVE_THRESH_MEAN_C, cv.THRESH_BINARY, 15, -2)
        _, bw = cv.threshold(self.gray_images[page_index], blackness, 255, cv.THRESH_BINARY)
        bw = cv.bitwise_not(bw)
        vertical = np.copy(bw)
        horizontal = np.copy(bw)
        horizontal_size = int(note_height / 2)
        horizontalStructure = cv.getStructuringElement(cv.MORPH_RECT, (horizontal_size, 1))

        # Apply morphology operations
        horizontal = cv.erode(horizontal, horizontalStructure)
        horizontal = cv.dilate(horizontal, horizontalStructure)
        verticalsize = int(note_height / 2)
        # Create structure element for extracting vertical lines through morphology operations
        verticalStructure = cv.getStructuringElement(cv.MORPH_RECT, (1, verticalsize))

        # Apply morphology operations
        vertical = cv.erode(vertical, verticalStructure)
        vertical = cv.dilate(vertical, verticalStructure)
        intersection = cv.bitwise_and(horizontal, vertical)
        h, w = intersection.shape[:2]
        mask = np.zeros((h + 2, w + 2), np.uint8)
        half_note_mask = np.zeros((h + 2, w + 2), np.uint8)

        intersection_image = cv.bitwise_and(horizontal, vertical)
        if note is not None:
            if note.is_half_note == "quarter":
                remove = self.auto_extend_quarter_note(page_index, note, intersection_image, mask, note_height, note_width, debugging)
            else:
                self.auto_extend_half_note(page_index, note, bw, half_note_mask, note_height, note_width)
        else:
            if self.is_list_iterable(self.notes[page_index]):
                for i in range(len(self.notes[page_index]) - 1, -1, -1):
                    current_note = self.notes[page_index][i]
                    if current_note.is_auto_extended() == True:
                        continue
                    if current_note.is_half_note == "quarter":
                        remove = self.auto_extend_quarter_note(page_index, current_note, intersection_image, mask, note_height, note_width, debugging)
                        if remove == "remove":
                            self.notes[page_index].pop(i)
                    else:
                        self.auto_extend_half_note(page_index, current_note, bw, half_note_mask, note_height, note_width)

        #TODO reload image and do it again
        if debugging:
            cv.imwrite("agray.jpg", self.gray_images[page_index])
            cv.imwrite("abw.jpg", bw)
            cv.imwrite("ahorizontal.jpg", horizontal)
            cv.imwrite("avertical.jpg", vertical)
            cv.imwrite("aintersection.jpg", intersection_image)

    def split_up_notes_immage(self, page_index, note_height, note_width):
        # print(note_height, note_width)
        gray = cv.bitwise_not(self.gray_images[page_index])
        bw = cv.adaptiveThreshold(gray, 255, cv.ADAPTIVE_THRESH_MEAN_C, cv.THRESH_BINARY, 15, -2)
        vertical = np.copy(bw)
        horizontal = np.copy(bw)
        horizontal_size = int(note_height / 2)
        horizontalStructure = cv.getStructuringElement(cv.MORPH_RECT, (horizontal_size, 1))

        # Apply morphology operations
        horizontal = cv.erode(horizontal, horizontalStructure)
        horizontal = cv.dilate(horizontal, horizontalStructure)
        verticalsize = int(note_height / 2)
        # Create structure element for extracting vertical lines through morphology operations
        verticalStructure = cv.getStructuringElement(cv.MORPH_RECT, (1, verticalsize))

        # Apply morphology operations
        vertical = cv.erode(vertical, verticalStructure)
        vertical = cv.dilate(vertical, verticalStructure)
        intersection = cv.bitwise_and(horizontal, vertical)
        intersection_lines_removed = np.copy(intersection)
        intersection_height, intersection_width = intersection.shape[:2]
        mask = np.zeros((intersection_height + 2, intersection_width + 2), np.uint8)
        #print(intersection_height, intersection_width)
        candidates = []
        #TODO find rects bigger than note and split symetrically. add candidates array
        for y_traverse in range(0, intersection_height, 1):
            for x_traverse in range(0, intersection_width, 1):
                #print(intersection[y_traverse][x_traverse])
                if intersection[y_traverse][x_traverse] > 0 and mask[y_traverse + 1][x_traverse + 1] == 0:
                    _, _, _, rect = cv.floodFill(intersection, mask, (x_traverse, y_traverse), 0)
                    if rect == (0, 0, 0, 0):
                        pass
                    else:
                        #print(rect)
                        x, y, width, height = rect
                        if .7 < width / note_width < 1.3:
                            height_ratio = round(height / note_height)

                            if 1.5 < height_ratio < 5.5:
                                spacing = height / height_ratio
                                for i in range(height_ratio - 1):
                                    bottom = y + round((i + 1) * spacing)
                                    for x_traverse_2 in range(x, x + width + 1, 1):
                                        intersection_lines_removed[bottom][x_traverse_2] = 0

                        elif .7 < width / note_width / 2 < 1.3:
                            # Making a border on the center line
                            for y_traverse_2 in range(y, y + height + 1, 1):
                                intersection_lines_removed[y_traverse_2][x + int(width / 2)] = 0

                        else:
                            #Rect found that isnt a note
                            pass
        #cv.imwrite("aperfect.jpg", intersection_lines_removed)
        return intersection_lines_removed

    def auto_detect_quarter_notes(self, page_index, note_height_width_ratio):
        print("auto detect quarter note")
        note_height = self.get_note_height(page_index)
        note_width = int(note_height * note_height_width_ratio / 100)
        intersection = self.split_up_notes_image(page_index, note_height, note_width)
        h, w = intersection.shape[:2]
        mask = np.zeros((h + 2, w + 2), np.uint8)
        #TODO get candidate rects to loop through
        for y_traverse in range(0, h, 1):
            for x_traverse in range(0, w, 1):
                if intersection[y_traverse][x_traverse] == 255 and mask[y_traverse + 1][x_traverse + 1] == 0:
                    _, _, _, rect = cv.floodFill(intersection, mask, (x_traverse, y_traverse), 255)
                    if rect == (0, 0, 0, 0):
                        pass
                    else:
                        # print(rect)

                        x, y, width, height = rect
                        if .7 < width / note_width < 1.3:
                            height_ratio = round(height / note_height)
                            if .5 < height_ratio < 1.5:
                                topleft = [x - 1, y - 1]
                                bottomright = [x + width + 1, y + height + 1]
                                note = Note(topleft, bottomright, is_half_note="quarter", auto_extended=True)
                                self.append_features(page_index, "note", [note])

    def fill_in_white_spots(self, page_index, image, gray_image, filename):
        '''
        img = cv.adaptiveThreshold(self.gray_images[page_index], 255, cv.ADAPTIVE_THRESH_MEAN_C, cv.THRESH_BINARY, 15, -2)
        h, w = img.shape[:2]
        mask = np.zeros((h + 2, w + 2), np.uint8)
        cv.imwrite("before.jpg", self.images[page_index])

        for y in range(h):
            for x in range(w):
                if img[y][x] > 0:# and mask[y - 1][x - 1] == 0:#if white
                    _, _, _, rect = cv.floodFill(img, mask, (x, y), 0)
                    if rect == (0, 0, 0, 0):
                        pass
                    else:
                        x, y, width, height = rect
                        if width <= 3 and height <= 3:
                            for y_traverse in range(y, y + height + 1, 1):
                                for x_traverse in range(x, x + width + 1, 1):
                                    if mask[y_traverse + 1][x_traverse + 1] != 0:#if floodFill accessed this pixel
                                        #print("changing pixel to black")
                                        self.images[page_index][y_traverse][x_traverse] = [0, 0, 0]
                                        #print(self.images[page_index][y_traverse][x_traverse])
        cv.imwrite("aimg.jpg", img)
        cv.imwrite("aafter.jpg", self.images[page_index])
        cv.imwrite(self.images_filenames[page_index] + ".jpg", self.images[page_index])
        #TODO resave bw and gray images
        #self.bw_images[page_index] = cv.COLOR_BGR2GRAY()
        '''
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
                image[page_index][labels == i] = [0, 0, 0]

        #cv.imwrite("aimg.jpg", img)
        #cv.imwrite("aafter.jpg", self.images[page_index])
        #TODO reload bw and gray images
        #cv.imwrite(filename, image)
        #self.gray_images[page_index] = cv.cvtColor(self.images[page_index], cv.COLOR_BGR2GRAY)
        #self.bw_images[page_index] = cv.threshold(self.gray_images[page_index], 200, 255, cv.THRESH_BINARY)[1]
        return image

    def reduce_image_size(self, page_index):
        if self.is_list_iterable(self.staff_lines[page_index]):
            self.staff_lines[page_index] = []
        if self.is_list_iterable(self.treble_clefs[page_index]):
            self.treble_clefs[page_index] = []
        if self.is_list_iterable(self.bass_clefs[page_index]):
            self.bass_clefs[page_index] = []
        if self.is_list_iterable(self.barlines[page_index]):
            self.barlines[page_index] = []
        if self.is_list_iterable(self.barlines_2d[page_index]):
            self.barlines_2d[page_index] = []
        if self.is_list_iterable(self.accidentals[page_index]):
            self.accidentals[page_index] = []
        if self.is_list_iterable(self.notes[page_index]):
            self.notes[page_index] = []
        if self.is_list_iterable(self.all_clefs[page_index]):
            self.all_clefs[page_index] = []
        if self.is_list_iterable(self.regions[page_index]):
            self.regions[page_index] = []

        self.image_widths[page_index] = self.image_widths[page_index] // 2
        self.image_heights[page_index] = self.image_heights[page_index] // 2
        self.images[page_index] = cv.resize(self.images[page_index], (self.image_widths[page_index], self.image_heights[page_index]), interpolation=cv.INTER_AREA)
        cv.imwrite(self.images_filenames[page_index], self.images[page_index])
        self.regenerate_images(page_index)

    def regenerate_images(self, page_index, blackness):
        self.images[page_index] = cv.imread(self.images_filenames[page_index])
        self.gray_images[page_index] = cv.cvtColor(self.images[page_index], cv.COLOR_BGR2GRAY)
        self.bw_images[page_index] = cv.threshold(self.gray_images[page_index], blackness, 255, cv.THRESH_BINARY)[1]

    def rotate_based_off_staff_lines(self, page_index):
        angle = 0
        if self.is_list_iterable(self.staff_lines[page_index]):
            length = len(self.staff_lines[page_index])
            for line in self.staff_lines[page_index]:
                x_dif = line.bottomright[0] - line.topleft[0]
                y_dif = line.bottomright[1] - line.topleft[1]
                #if y_dif is negative
                angle = angle + math.atan(y_dif / x_dif) / length
                print("angle in loop", angle)
        angle = angle * 180 / math.pi
        print("angle",angle)
        image = self.images[page_index]
        height, width = image.shape[:2]
        center = (width // 2, height // 2)
        #angle = 1
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
        mask = np.zeros((height + 2, width + 2), np.uint8)

        # Perform the actual rotation and return the image
        rotated_image = cv.warpAffine(image, M, (new_w, new_h))
        #start_points = [[0, height / 2], [width / 2, 0], [width - 1, height / 2], [width / 2, height - 1]]
        #for start_point in start_points:
        #    _, _, mask, rect = cv.floodFill(rotated_image, mask, start_point, (255, 255, 255))
        # Perform the actual rotation and return the rotated image
        # rotated_image = cv.warpAffine(image, M, (width, height))
        self.images[page_index] = rotated_image
        cv.imwrite(self.images_filenames[page_index], rotated_image)
        self.regenerate_images(page_index)
        self.treble_clefs[page_index] = []
        self.bass_clefs[page_index] = []
        self.staff_lines[page_index] = []


    '''
    Takes set of bass_clef and treble_clef
    Sorts them from top to bottom then left to right in 2d array
    '''
    def is_page_missing_clef(self, page_index):
        #Get number of clefs on start page
        target_treble_count = 0
        target_bass_count = 0
        if self.treble_clefs[0] is not None:
            target_treble_count = len(self.treble_clefs[0])
        if self.bass_clefs[0] is not None:
            target_bass_count = len(self.bass_clefs[0])
        target_count = target_treble_count + target_bass_count
        treble_count = 0
        bass_count = 0
        #get number of clefs on page_index
        if self.treble_clefs[page_index] is not None:
            treble_count = len(self.treble_clefs[page_index])
        if self.bass_clefs[page_index] is not None:
            bass_count = len(self.bass_clefs[page_index])
        #If current page has same count as first page
        if target_count == treble_count + bass_count:
            return False
        if (treble_count + bass_count) % 2 == 1:
            return False
        return True

    """
    Puts clefs into 2d list for region generating
    """
    def sort_clefs(self, page_index):
        clef_error = 100
        if self.treble_clefs[page_index] is not None and len(self.treble_clefs[page_index]) > 0:
            clef_error = abs(self.treble_clefs[page_index][0].topleft[1] -
                        self.treble_clefs[page_index][0].bottomright[1]) / 2
        elif self.bass_clefs[page_index] is not None and len(self.bass_clefs[page_index]) > 0:
            clef_error = abs(self.bass_clefs[page_index][0].topleft[1] -
                        self.bass_clefs[page_index][0].bottomright[1]) * 3 / 4

        if self.all_clefs[page_index] is None:
            self.all_clefs[page_index] = []
        if self.is_list_iterable(self.bass_clefs[page_index]) or self.is_list_iterable(self.treble_clefs):
            pass
        else:
            print("no clefs on page")
            return


        multiple_in_row = False
        # Combine treble and bass clefs
        if self.is_list_iterable(self.bass_clefs[page_index]) and self.is_list_iterable(self.treble_clefs):
            self.all_clefs[page_index] = self.treble_clefs[page_index] + self.bass_clefs[page_index]
        elif self.is_list_iterable(self.bass_clefs[page_index]):
            self.all_clefs[page_index] =self.bass_clefs[page_index]
        elif self.is_list_iterable(self.treble_clefs):
            self.all_clefs[page_index] = self.treble_clefs[page_index]
        self.sort_features(self.all_clefs[page_index])

        temp = []
        i = 0
        while i < len(self.all_clefs[page_index]) - 1:
            current_row = [self.all_clefs[page_index][i]]

            # Check if the next clefs are in the same row
            while (i + 1 < len(self.all_clefs[page_index]) and
                   abs(self.all_clefs[page_index][i].topleft[1] - self.all_clefs[page_index][i + 1].topleft[1]) < clef_error):
                i += 1
                current_row.append(self.all_clefs[page_index][i])

            # Sort current row from left to right
            current_row.sort(key=lambda x: x.topleft[0])
            temp.append(current_row)

            # Move to the next clef
            i += 1

        # Handle the last clef if it wasn't processed
        if i == len(self.all_clefs[page_index]) - 1:
            temp.append([self.all_clefs[page_index][i]])

        self.all_clefs[page_index] = temp


        #print("All clefs ")#, self.all_clefs[page_index])
        #for clef in self.all_clefs[page_index]:
        #    for c in clef:
        #        #print("clef: ", c.topleft, c.bottomright, c.type, end=" ")
        #        print(c.type, end=" ")
        #    print()


    def split_notes_by_measure(self, page_index):
        region_lines = [0]  # Start of first region will always be from top of page
        if self.is_list_iterable(self.staff_lines[page_index]):
            for i in range(4, len(self.staff_lines[page_index]), 5):
                # find midpoint between staff lines
                if i + 1 < len(self.staff_lines[page_index]):
                    midpoint = self.image_widths[page_index] / 2
                    region_lines.append(int((self.staff_lines[page_index][i].calculate_y(midpoint) + self.staff_lines[page_index][i + 1].calculate_y(midpoint)) / 2))
        else:
            print("staff line error on ", page_index)
            return
        region_lines.append(self.image_heights[page_index])
        self.sort_clefs(page_index)
        self.sort_barlines(page_index, error=30)
        if self.is_list_iterable(self.all_clefs[page_index]) and self.is_list_iterable(self.barlines_2d[page_index]):
            for row in self.all_clefs[page_index]:
                first = row[0]
                for j in range(len(self.barlines_2d[page_index])):
                    for k in range(len(self.barlines_2d[page_index][j])):
                        #TODO
                        if self.is_bar_in_region(self.regions[page_index][i], self.barlines_2d[page_index][j][k]):
                            pass
        else:
            print("clef error or barline error on", page_index)
            return
    #TODO start at first clef in line. then go to barlines, then end of page. then find noets in those regions
    '''
    Using sorted clefs, gets regions
    '''

    def get_clef_regions(self, page_index):
        # finding top and bottom of regions
        region_lines = [0]  # Start of first region will always be from top of page
        for i in range(4, len(self.staff_lines[page_index]), 5):
            # find midpoint between staff lines
            if i + 1 < len(self.staff_lines[page_index]):
                midpoint = self.image_widths[page_index] / 2
                region_lines.append(int((self.staff_lines[page_index][i].calculate_y(midpoint) + self.staff_lines[page_index][i + 1].calculate_y(midpoint)) / 2))
        region_lines.append(self.image_heights[page_index])
        #print("Image height: ", self.image_heights[page_index])

        if self.all_clefs[page_index] != None:
            #print("Clefs not empty")
            for i in range(len(self.all_clefs[page_index])):
                for j in range(len(self.all_clefs[page_index][i])):
                    for k in range(len(region_lines)):
                        # find vertical region that clef lands in
                        if self.all_clefs[page_index][i][j].topleft[1] < region_lines[k]:
                            # top left corner and bottom right corner
                            top_left = (self.all_clefs[page_index][i][j].topleft[0], region_lines[k - 1])
                            bottom_right = (self.image_widths[page_index], region_lines[k])
                            # if there are multiple clefs on this staff line, bottom right of region stops at next staff line
                            if len(self.all_clefs[page_index][i]) > 1:
                                # if this staff isnt the right most staff that already goes to the end of the page
                                #print("multiple clefs on same line")
                                if j != len(self.all_clefs[page_index][i]) - 1:
                                    bottom_right = (self.all_clefs[page_index][i][j + 1].topleft[0], region_lines[k])
                                    #print("Multiple clefs on same line: bottom right: ", bottom_right)

                            r = Region(top_left, bottom_right, self.all_clefs[page_index][i][j].type)
                            if self.regions[page_index] is None:
                                self.regions[page_index] = [r]
                            else:
                                self.regions[page_index].append(r)

                            break
        else:
            print("clefs are empty")

        #print("Printing regions")
        #for r in self.regions[page_index]:
        #    print(r)

    '''
    Sorts the barlines into 2d array
    '''

    def sort_barlines(self, page_index, error=30):
        # Sort first by top to bottom, then left to right
        current_row = []
        sorted_bars = []
        if self.barlines[page_index] is not None:
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
        self.barlines_2d[page_index] = sorted_bars
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
    breaking up get_regions by barlines
    '''
    def split_regions_by_bar(self, page_index):
        i = 0
        # TODO only call when regions are already split up by clef and barlines are sorted
        if self.regions[page_index] != None:
            #print("Region not none")
            while i < len(self.regions[page_index]):
                # print(regions_with_lines[i])
                if self.barlines_2d[page_index] is not None:
                    for j in range(len(self.barlines_2d[page_index])):
                        #print("Barline: row", self.barlines_2d[page_index][j])
                        for k in range(len(self.barlines_2d[page_index][j])):
                            if self.is_bar_in_region(self.regions[page_index][i], self.barlines_2d[page_index][j][k]):
                                new_region = self.regions[page_index][i].copy()
                                new_region.type = "new region \n\n"
                                new_topleft = (
                                self.barlines_2d[page_index][j][k].topleft[0], self.regions[page_index][i].topleft[1])
                                new_region.topleft = new_topleft
                                prev_bottomright = (
                                self.barlines_2d[page_index][j][k].topleft[0], self.regions[page_index][i].bottomright[1])
                                self.regions[page_index][i].bottomright = prev_bottomright
                                self.regions[page_index].insert(i + 1, new_region)
                                # break
                i = i + 1

    def are_notes_on_line(self, page_index):
        #todo detect if note is on line or on space. if there are notes adjacent, only check one side
        #todo use intersection image to flood fill notes. if width is greater, only take one side
        img = cv.imread(self.images_filenames[page_index], cv.IMREAD_COLOR)
        # Check if image is loaded fine
        if img is None:
            print('Error opening image: ')
            return -1

        # Transform source image to gray if it is not already
        if len(img.shape) != 2:
            gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
        else:
            gray = img

        # Apply adaptiveThreshold at the bitwise_not of gray, notice the ~ symbol
        gray = cv.bitwise_not(gray)
        '''
        horizontal = cv.adaptiveThreshold(gray, 255, cv.ADAPTIVE_THRESH_MEAN_C, cv.THRESH_BINARY, 15, -2)
        #horizontal = np.copy(bw)
        note_height = self.get_note_height(page_index)
        horizontal_size = note_height + 2
        # Create structure element for extracting horizontal lines through morphology operations
        horizontalStructure = cv.getStructuringElement(cv.MORPH_RECT, (horizontal_size, 1))

        # Apply morphology operations
        horizontal = cv.erode(horizontal, horizontalStructure)
        horizontal = cv.dilate(horizontal, horizontalStructure)
        cv.imwrite("ahorizontalonline.jpg", horizontal)
        '''
        for note in self.notes[page_index]:
            if note.is_half_note == "quarter":
                histogram = []
                for y in range(note.topleft[1], note.bottomright[1], 1):
                    if gray[y][note.center[0]] == 255:
                        pass
                        #width = get_width()
                        #TODO get horizontal histograms and see if one line is bigger than others. Make sure no notes beside current note


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
                    pass
                    #print("Accidentals empty on page", page_index)
        else:
            print("regions empty on page", page_index)




    def find_closest_staff_line(self, page_index, point):
        min_distance = 10000000
        closest_line = None
        for staff_line in self.staff_lines[page_index]:
            distance = abs(staff_line.calculate_y(point[0]) - point[1])
            if distance < min_distance:
                min_distance = distance
                closest_line = staff_line
        if min_distance < 20:
            return closest_line
        return None

    def append_features(self, page_index, type, new_features):
        #TODO use this method in window.py
        #current_features = self.array_types_dict[type][page_index]
        if self.array_types_dict[type][page_index] is not None:
            self.array_types_dict[type][page_index] = self.array_types_dict[type][page_index] + new_features
        else:
            self.array_types_dict[type][page_index] = new_features
        self.sort_features(self.array_types_dict[type][page_index])

    '''
    def find_closest_line(self, implied_lines, point):
        min = 10000
        closest_line = 0
        for line in implied_lines:
            if abs(point[1] - line.y) < min:
                min = abs(point[1] - line[0])
                closest_line = line
        return closest_line
    '''

    '''
    def fill_implied_lines(self):
        for i in range(self.num_pages):
            for region in self.regions[i]:
                region.fill_implied_lines()
    '''
    '''

    def is_half_note(self, page_index, note):
        c = note.center
        distance_from_center = 3
        percent_white = .5
        topleft = [c[0] - distance_from_center, c[1] - distance_from_center]
        bottomright = [c[0] + distance_from_center, c[1] + distance_from_center]
        white_count = 0
        for y in range(topleft[1], bottomright[1] + 1, 1):
            for x in range(topleft[0], bottomright[0] + 1, 1):
                if self.gray_images[page_index][y][x] > 255 / 2:
                    white_count += 1
        if white_count / distance_from_center /distance_from_center > percent_white:
            return True
        return False
    '''

    def fill_in_half_note(self, page_index, note, color):
        #travel from center to top until you hit black. if you dont hit black, dont fill.
        # draw cross hair. if sharp add upper cross hair if flat add lower cross hair
        note_height = self.get_note_height(page_index)
        topleft = [note.topleft[0], note.topleft[1]]
        bottomright = [note.bottomright[0], note.bottomright[1]]
        center = note.center
        accidental = note.accidental
        #cv.imwrite("abw.jpg", self.bw_images[page_index])
        #draw line down center then recursively expand
        if accidental == "" or accidental == "natural":
            #for x in range(topleft[0], bottomright[0], 1):
            #    self.images[page_index][center[1]][x] = color
            pass
            #return
        else:
            #TODO move mask out of method

            img = cv.bitwise_not(self.bw_images[page_index])
            h, w = img.shape[:2]
            mask = np.zeros((h + 2, w + 2), np.uint8)
            #img = np.copy(self.images[page_index])
            #print(self.images[page_index].shape[:2], bw.shape[:2])

            rects = []
            center_x, center_y = note.center
            # Calculate the maximum radius from the center to the rectangle's edges
            x_radius = note.get_width() // 2
            y_radius = note.get_height() // 2
            max_radius = max(x_radius, y_radius)
            # Traverse outward from the center
            break_loop = False
            for radius in range(max_radius + 1):
                for y_offset in range(-radius, radius + 1):
                    for x_offset in range(-radius, radius + 1):
                        # Calculate the current position
                        x_traverse = center_x + x_offset
                        y_traverse = center_y + y_offset

                        # Ensure the position is within the bounds of the rectangle
                        if (note.topleft[0] <= x_traverse <= note.bottomright[0] and note.topleft[1] <= y_traverse <= note.bottomright[1]):
                            # Do your processing here with x_traverse and y_traverse
                            # if pixel is white, flood fill
                            if img[y_traverse][x_traverse] == 0:
                                start_point = (x_traverse, y_traverse)
                                _, _, _, rect = cv.floodFill(img, mask, start_point, color)
                                # print(rect)
                                x, y, width, height = rect
                                if height > note_height * 1.5 or width > note_height * 2:
                                    print("Half note is open")
                                else:

                                    if rect != (0, 0, 0, 0):
                                        if height / note_height < 1.3 and width / note_height < 1.3:
                                            rects.append(rect)
                                    if .5 < height / note_height < 1.3 and .3 < width / note_height < 1.3:
                                        break_loop = True
                                    if len(rects) == 2:
                                        break_loop = True
                        if break_loop:
                            break
                    if break_loop:
                        break
                if break_loop:
                    break

            '''     
            for y in range(topleft[1], bottomright[1], 1):
                #todo copy extend half note loop herre
                # if pixel is white, flood fill
                if img[y][center[0]] == 0:
                    start_point = (center[0], y)
                    floodflags = 8
                    _, _, mask, rect = cv.floodFill(img, mask, start_point, 1, floodflags)
                    print(rect)
                    x, y, width, height = rect
            '''
            vertical_line = False
            horizontal_line = False
            if accidental == "flat":
                topleft[1] = center[1]
                horizontal_line = True
            elif accidental == "sharp":
                bottomright[1] = center[1]
                horizontal_line = True
            elif accidental == "double_flat":
                bottomright[0] = center[0]
                vertical_line = True
            elif accidental == "double_sharp":
                topleft[0] = center[0]
                vertical_line = True
            for y in range(topleft[1], bottomright[1], 1):
                for x in range(topleft[0], bottomright[0], 1):
                    if mask[y][x] == 1:
                        self.images[page_index][y - 1][x - 1] = color
            if vertical_line:
                for y in range(topleft[1], bottomright[1], 2):
                    self.images[page_index][y][center[0]] = [0, 0, 0]
            if horizontal_line:
                for x in range(topleft[0], bottomright[0], 2):
                    self.images[page_index][center[1]][x] = [0, 0, 0]



    def fill_in_feature(self, page_index, topleft, bottomright, color):
        for i in range(topleft[1], bottomright[1], 1):
            for j in range(topleft[0], bottomright[0], 1):
                if self.gray_images[page_index][i][j] < 255 / 2:
                    self.images[page_index][i][j] = color

    def draw_features(self, features, page_index, draw_rectangle=True):
        #print("Drawing the features loop")
        if features[page_index] is not None:
            for feature in features[page_index]:
                if feature is not None:
                    # if it is a note or accidental that has a letter labeled
                    if feature.letter != "":
                        color = self.letter_colors[feature.letter.lower()]
                        #print("note: ", feature)
                        if feature.accidental != "":
                            #print("note: ", feature)
                            accidental = feature.accidental.lower()
                            if accidental == "flat":
                                self.fill_in_feature(page_index, (feature.topleft[0], feature.center[1]), feature.bottomright, color)
                            if accidental == "sharp":
                                self.fill_in_feature(page_index, feature.topleft,(feature.bottomright[0], feature.center[1]), color)

                            if accidental == "double_flat":
                                self.fill_in_feature(page_index, feature.topleft,(feature.center[0], feature.bottomright[1]), color)
                            if accidental == "double_sharp":
                                self.fill_in_feature(page_index,(feature.center[0], feature.topleft[1]), feature.bottomright, color)
                            if accidental == "natural":
                                self.fill_in_feature(page_index, feature.topleft, feature.bottomright, color)
                        else:  # note with no accidental
                            self.fill_in_feature(page_index, feature.topleft, feature.bottomright,
                                                 color)
                        if isinstance(feature, Note) and (feature.is_half_note == "half" or feature.is_half_note == "whole"):
                            #self.fill_in_feature(page_index, feature.topleft, feature.bottomright, color)
                            self.fill_in_half_note(page_index, feature, color)
                        # self.fill_in_feature(page_index, f.topleft, f.bottomright, self.letter_colors[f.letter])
                    else:
                        if draw_rectangle == True:
                            cv.rectangle(self.images[page_index], feature.topleft, feature.bottomright, self.type_colors[feature.type], 2)


    """
    Anytime match_template is called or filter is changed
    """
    def draw_image(self, filter_list, page_index):
        #print("Filter list", filter_list)
        if filter_list[0].get() == 1:#staffline
            self.draw_staff_lines(page_index)
        if filter_list[1].get() == 1:#implied line
            if self.regions[page_index] is not None:
                for region in self.regions[page_index]:
                    if region.implied_lines is not None:
                        for line in region.implied_lines:
                            #print("implied line", line.topleft, line.bottomright)
                            topleft_in_region = [region.topleft[0], line.calculate_y(region.topleft[0])]
                            bottomright_in_region = [region.bottomright[0], line.calculate_y(region.bottomright[0])]
                            cv.line(self.images[page_index], topleft_in_region, bottomright_in_region, self.letter_colors[line.letter.lower()], 1)
        if filter_list[2].get() == 1:#bass clef
            self.draw_features(self.bass_clefs, page_index)
        if filter_list[3].get() == 1:#treble clef
            #print("Drawing treble clefs")
            self.draw_features(self.treble_clefs, page_index)
        if filter_list[4].get() == 1:#barline
            self.draw_features(self.barlines, page_index)
        if filter_list[6].get() == 1: #accidental
            self.draw_features(self.accidentals, page_index)
        if filter_list[5].get() == 1:#note
            self.draw_features(self.notes, page_index)
        if filter_list[7].get() == 1:#region border
            if self.regions[page_index] is not None:
                for region in self.regions[page_index]:
                    if region.clef == "bass_clef" or region.clef == "treble_clef":
                        cv.rectangle(self.images[page_index], region.topleft, region.bottomright, self.type_colors[region.clef], 1)
                        #print("Region: ", region.topleft, region.bottomright)
        #print("drawing image")
        cv.imwrite(self.annotated_images_filenames[page_index], self.images[page_index])
        #clearing the image of drawings
        self.images[page_index] = cv.imread(self.images_filenames[page_index])

    def fill_in_feature_without_reloading(self, page_index, topleft, bottomright, color, image):
        for i in range(topleft[1], bottomright[1], 1):
            for j in range(topleft[0], bottomright[0], 1):
                if self.gray_images[page_index][i][j] < 255 / 2:
                    image[i][j] = color

    def draw_features_without_reloading(self, features, page_index, image, draw_rectangle=True):
        #print("Drawing the features loop")
        if features[page_index] is not None:
            for feature in features[page_index]:
                if feature is not None:
                    # if it is a note or accidental that has a letter labeled
                    if feature.letter != "":
                        color = self.letter_colors[feature.letter.lower()]
                        #print("note: ", feature)
                        if feature.accidental != "":
                            #print("note: ", feature)
                            accidental = feature.accidental.lower()
                            if accidental == "flat":
                                self.fill_in_feature(page_index, (feature.topleft[0], feature.center[1]), feature.bottomright, color)
                            if accidental == "sharp":
                                self.fill_in_feature(page_index, feature.topleft,(feature.bottomright[0], feature.center[1]), color)

                            if accidental == "double_flat":
                                self.fill_in_feature(page_index, feature.topleft,(feature.center[0], feature.bottomright[1]), color)
                            if accidental == "double_sharp":
                                self.fill_in_feature(page_index,(feature.center[0], feature.topleft[1]), feature.bottomright, color)
                            if accidental == "natural":
                                self.fill_in_feature(page_index, feature.topleft, feature.bottomright, color)
                        else:  # note with no accidental
                            self.fill_in_feature(page_index, feature.topleft, feature.bottomright,
                                                 color)
                        if isinstance(feature, Note) and (feature.is_half_note == "half" or feature.is_half_note == "whole"):
                            #self.fill_in_feature(page_index, feature.topleft, feature.bottomright, color)
                            self.fill_in_half_note(page_index, feature, color)
                        # self.fill_in_feature(page_index, f.topleft, f.bottomright, self.letter_colors[f.letter])
                    else:
                        if draw_rectangle == True:
                            cv.rectangle(image, feature.topleft, feature.bottomright, self.type_colors[feature.type], 2)

    def draw_staff_lines_without_reloading(self, page_index):
        if self.staff_lines[page_index] is not None:
            for line in self.staff_lines[page_index]:
                cv.line(self.images[page_index], line.topleft, line.bottomright, self.type_colors["staff_line"], 1)

    def draw_image_without_reloading(self, filter_list, page_index, image):
        # print("Filter list", filter_list)
        if filter_list[0].get() == 1:  # staffline
            self.draw_staff_lines(page_index)
        if filter_list[1].get() == 1:  # implied line
            if self.regions[page_index] is not None:
                for region in self.regions[page_index]:
                    if region.implied_lines is not None:
                        for line in region.implied_lines:
                            # print("implied line", line.topleft, line.bottomright)
                            topleft_in_region = [region.topleft[0], line.calculate_y(region.topleft[0])]
                            bottomright_in_region = [region.bottomright[0], line.calculate_y(region.bottomright[0])]
                            cv.line(image, topleft_in_region, bottomright_in_region, self.letter_colors[line.letter.lower()], 1)
        if filter_list[2].get() == 1:  # bass clef
            self.draw_features(self.bass_clefs, page_index)
        if filter_list[3].get() == 1:  # treble clef
            # print("Drawing treble clefs")
            self.draw_features(self.treble_clefs, page_index)
        if filter_list[4].get() == 1:  # barline
            self.draw_features(self.barlines, page_index)
        if filter_list[6].get() == 1:  # accidental
            self.draw_features(self.accidentals, page_index)
        if filter_list[5].get() == 1:  # note
            self.draw_features(self.notes, page_index)
        if filter_list[7].get() == 1:  # region border
            if self.regions[page_index] is not None:
                for region in self.regions[page_index]:
                    if region.clef == "bass_clef" or region.clef == "treble_clef":
                        cv.rectangle(image, region.topleft, region.bottomright, self.type_colors[region.clef], 1)
                        # print("Region: ", region.topleft, region.bottomright)
        # print("drawing image")
        #cv.imwrite(self.annotated_images_filenames[page_index], self.images[page_index])
        # clearing the image of drawings
        #self.images[page_index] = cv.imread(self.images_filenames[page_index])



