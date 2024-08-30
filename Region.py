import copy
import numpy as np
import cv2 as cv
from StaffLine import StaffLine
from Note import Note

class Region:
    def __init__(self, topleft, bottomright, clef, key):
        self.topleft = topleft
        self.bottomright = bottomright
        self.clef = clef
        self.implied_lines = []
        self.notes = []
        self.accidentals = []
        self.key = key

    def is_point_in_region(self, point):
        if self.topleft[0] < point[0] < self.bottomright[0] and self.topleft[1] < point[1] < self.bottomright[1]:
            return True
        return False

    def copy(self):
        return copy.copy(self)

    def calculate_notes(self):
        pass

    def find_closest_line(self, point):
        min = 10000
        closest_line = 0
        for line in self.implied_lines:
            if abs(point[1] - line.calculate_y(point[0])) < min:
                min = abs(point[1] - line.calculate_y(point[0]))
                closest_line = line
        return closest_line

    '''
    Given the center lien of a note, it finds the two adjacent implied lines and returns them in an array
    If no adjacent lines are found, it returns an empty list
    '''
    def find_adjacent_lines(self, line):
        #print("start find_adj")
        #for l in self.implied_lines:
        #    print("line", l.topleft)
        for i in range(1, len(self.implied_lines) - 1, 1):
            if line.y_intercept == self.implied_lines[i].y_intercept:
                #print("yint", line.y_intercept, self.implied_lines[i].y_intercept)
                #print("adjacent lines", self.implied_lines[i - 1].topleft, self.implied_lines[i + 1].topleft)
                return [self.implied_lines[i - 1], self.implied_lines[i + 1]]
        print("cant autosnap")
        return []

    def autosnap_notes_to_implied_line(self):
        if self.notes is not None and len(self.notes) > 0:
            for note in self.notes:
                center = self.find_closest_line(note.center)
                adjacent_implied_lines = self.find_adjacent_lines(center)
                if len(adjacent_implied_lines) > 0:
                    note.topleft[1] = adjacent_implied_lines[0].calculate_y(note.topleft[0])
                    note.bottomright[1] = adjacent_implied_lines[1].calculate_y(note.bottomright[0])
                    note.auto_extended = True
                    #note.topleft = (note.topleft[0], adjacent_implied_lines.calculate_y(note.topleft[0]))
                    #note.bottomright = (note.bottomright[0], adjacent_implied_lines[1])

    def find_accidental_for_note(self, override=0):
        #todO KEY
        for note in self.notes:
            closest = 0
            for acc in self.accidentals:
                print("accidental autosnapping", acc, "note: ", note.accidental)
                # if note and accidental are on same line, and accidental is to left of note
                #if acc.type == "flat":
                    #print("flat:", acc, "center: ", acc.get_center())
                closest_line_note = self.find_closest_line(note.center)
                closest_line_acc = self.find_closest_line(acc.center)
                #if note and accidental are on the same line and the accidental is to the left of the note and the note doesnt have an accidental
                if override == 0:
                    if closest_line_note == closest_line_acc and acc.center[0] < note.center[0] and note.accidental == "":
                        print("not overriding accidental")
                        print("asdffd")
                        #if first accidental encountered
                        if type(closest) == int:
                            closest = acc
                        #if there is another accidental on the same line
                        else:
                            #if current accidental is closer to note than the closest
                            if acc.center[0] > closest.center[0]:
                                closest = acc
                else:
                    print("overriding accidental")
                    if closest_line_note == closest_line_acc and acc.center[0] < note.center[0]:
                        print("asdffd")
                        #if first accidental encountered
                        if type(closest) == int:
                            closest = acc
                        #if there is another accidental on the same line
                        else:
                            #if current accidental is closer to note than the closest
                            if acc.center[0] > closest.center[0]:
                                closest = acc
            #If accidental was found
            if type(closest) != int:
                note.accidental = closest.type#[letter, accidental]
                print("closest accidental: ", closest)



    '''
    Changing center coordinate of feature to be on an implied line
    '''

    def autosnap_notes_and_accidentals(self):
        for i in range(len(self.notes)):
            self.autosnap(self.notes[i])
            print("note", self.notes[i])
        for i in range(len(self.accidentals)):
            self.autosnap(self.accidentals[i])
            print("accidental", self.accidentals[i])


    def autosnap(self, feature):
        closest_line = self.find_closest_line(feature.center)
        #y_dif = closest_line.y - feature.center[1]
        #if feature.type in ["double_flat", "flat", "natural", "sharp", "double_sharp"]:
        print("accidental autosnaped", closest_line.calculate_y(feature.center[0]))
        #feature.center[1] = closest_line
        if not isinstance(feature, Note):
            feature.center[1] = closest_line.calculate_y(feature.center[0])
        #feature.topleft = (feature.topleft[0], feature.topleft[1] + y_dif)
        #feature.bottomright = (feature.bottomright[0], feature.bottomright[1] + y_dif)
        feature.letter = closest_line.letter



    """
    Takes the stafflines. Finds the first staff line that is in the region. Then fills implied lines bases off that
    """
    def fill_implied_lines(self, all_staff_lines, image_width, image_height):
        self.implied_lines = []
        letters = ['a', 'b', 'c', 'd', 'e', 'f', 'g']
        start_treble_index = 5
        start_bass_index = 0
        letter_index = start_bass_index
        if self.clef == "treble_clef":
            #print("treble clef ....")
            letter_index = start_treble_index

        lines_in_region = []
        for line in all_staff_lines:
            if self.topleft[1] < line.calculate_y(image_width / 2) < self.bottomright[1]:#if line is in region
                lines_in_region.append(line)
        if len(lines_in_region) > 1:
            line_spacing = abs(lines_in_region[-1].calculate_y(image_width / 2) - lines_in_region[0].calculate_y(image_width / 2)) / 8
        else:
            print("missing staff line")
            return

        for i in range(0, len(all_staff_lines) - 4, 5):
            #print("loop start")
            #if line is in region
            if self.topleft[1] < all_staff_lines[i].calculate_y(image_width / 2) < self.bottomright[1]:
                #print("staffy", self.topleft, all_staff_lines[i].calculate_y(image_width / 2), self.bottomright)
                #line_spacing = (all_staff_lines[i + 4] - all_staff_lines[i]) / 8
                start_line = all_staff_lines[i].y_intercept
                slope = all_staff_lines[i].slope
                top_line = 0
                #finding top implid line in the region
                for k in np.arange(start_line - line_spacing, self.topleft[1], -1 * line_spacing):
                    #self.implied_lines.append(ImpliedLine(int(k), letters[letter_index]))
                    letter_index = (letter_index + 1) % len(letters)
                    top_line = k
                #finding implied lines starting from top of region going down to bottom
                for k in np.arange(top_line, self.bottomright[1], line_spacing):
                    #print("k index", int(k))
                    #all_staff_lines[i].letter = letters[letter_index]
                    left = [0, int(k)]
                    right =[image_width - 1, int(k + image_width * slope)]
                    implied_line = StaffLine(left, right, image_width, image_height)
                    implied_line.letter = letters[letter_index]
                    self.implied_lines.append(implied_line)
                    #print("implied lines length", len(self.implied_lines))
                    #print("added line", implied_line.topleft)
                    letter_index = (letter_index - 1) % len(letters)
                break
        #print("Implied lines: ", self.implied_lines)


    def fill_in_feature(self, img, gray_img, topleft, bottomright, color):
        for i in range(topleft[1], bottomright[1], 1):
            for j in range(topleft[0], bottomright[0], 1):
                if gray_img[i][j] < 255 / 2:
                    img[i][j] = color

    def draw_region_fill_in_feature(self, img, gray_img, letter_colors):
        for note in self.notes:
            #print(note)
            #If note has accidental
            if(note.accidental != ""):
                print("note: ", note)
                accidental = note.accidental
                if accidental == "flat":
                    self.fill_in_feature(img, gray_img, (note.topleft[0], note.center[1]),note.bottomright, letter_colors[note.letter])
                if accidental == "sharp":
                    self.fill_in_feature(img, gray_img, note.topleft, (note.bottomright[0], note.center[1]), letter_colors[note.letter])

                if accidental == "double_flat":
                    self.fill_in_feature(img, gray_img, note.topleft, (note.center[0], note.bottomright[1]), letter_colors[note.letter])
                if accidental == "double_sharp":
                    self.fill_in_feature(img, gray_img, (note.center[0], note.topleft[1]), note.bottomright, letter_colors[note.letter])
                if accidental == "natural":
                    self.fill_in_feature(img, gray_img, note.topleft, note.bottomright, letter_colors[note.letter])

            else:
                self.fill_in_feature(img, gray_img, note.topleft, note.bottomright, letter_colors[note.letter])


        for acc in self.accidentals:
            #print(acc)
            self.fill_in_feature(img, gray_img, acc.topleft, acc.bottomright, letter_colors[acc.letter])

    '''
    def draw_region(self, img, letter_colors, lines=True, borders=True, notes=True, accidentals=True, clefs=True):
        if lines:
            for i in range(len(self.implied_lines)):
                left = (self.topleft[0], self.implied_lines[i].y)
                right = (self.bottomright[0], self.implied_lines[i].y)
                cv.line(img, left, right, letter_colors[self.implied_lines[i].letter], 1)

        if borders:
            color = (255, 0, 0)
            if self.clef == "bass_clef":
                color = (0, 255, 0)
            cv.rectangle(img, self.topleft, self.bottomright, color, 2)

        if notes:
            for note in self.notes:
                #print(note)
                #If note has accidental
                if note.accidental != "":
                    #print("note: ", note)
                    accidental = note.accidental
                    if accidental == "flat":
                        cv.rectangle(img, (note.topleft[0], note.center[1]), note.bottomright, letter_colors[note.letter], 2)
                    if accidental == "sharp":
                        cv.rectangle(img, note.topleft, (note.bottomright[0], note.center[1]), letter_colors[note.letter], 2)
                    if accidental == "double_flat":
                        #TODO impliment what to do for doulbe sharps/flats
                        pass
                    if accidental == "double_sharp":
                        pass
                else:
                    cv.rectangle(img, note.topleft, note.bottomright, letter_colors[note.letter], 2)

        if accidentals:
            for acc in self.accidentals:
                #print(acc)
                cv.rectangle(img, acc.topleft, acc.bottomright, letter_colors[acc.letter], 2)
    '''


    def __str__(self):
        topleft_string = "(" + str(self.topleft[0]) + ", " + str(self.topleft[1]) + ")"
        bottomright_string = "(" + str(self.bottomright[0]) + ", " + str(self.bottomright[1]) + ")"
        return "Top left: " + topleft_string + " Bottom right: " + bottomright_string + " Clef: " + str(
            self.clef) + " Num notes: " + str(len(self.notes)) + " Num accidentals: " + str(len(self.accidentals))
