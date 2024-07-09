import copy
import numpy as np
import cv2 as cv
from ImpliedLine import ImpliedLine

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
            if abs(point[1] - line.y) < min:
                min = abs(point[1] - line.y)
                closest_line = line
        return closest_line

    def find_accidental_for_note(self):
        #todO KEY
        for note in self.notes:
            closest = 0
            for acc in self.accidentals:
                # if note and accidental are on same line, and accidental is to left of note
                #if acc.type == "flat":
                    #print("flat:", acc, "center: ", acc.get_center())
                if note.center[1] == acc.center[1] and acc.center[0] < note.center[0]:
                    #if fist accidental encountered
                    if closest == 0:
                        closest = acc
                    #if there is another accidental on the same line
                    else:
                        #if current accidental is closer to note than the closest
                        if acc.center[0] > closest.center[0]:
                            closest = acc
            #If accidental was found
            if closest != 0:
                note.accidental = closest.type#[letter, accidental]
                #print("closest accidental: ", closest)



    '''
    Changing center coordinate of feature to be on an implied line
    '''

    def autosnap_notes_and_accidentals(self):
        for i in range(len(self.notes)):
            self.autosnap(self.notes[i])


        for i in range(len(self.accidentals)):
            self.autosnap(self.accidentals[i])
            #print("accidetnal: ", self.accidentals[i], "center: ", self.accidentals[i].center)
            #closest_line = self.find_closest_line(self.accidentals[i].center)
            #y_dif = closest_line[0] - self.accidentals[i].center[1]
            #self.accidentals[i].topleft = (self.accidentals[i].topleft[0], self.accidentals[i].topleft[1] + y_dif)
            #self.accidentals[i].bottomright = (self.accidentals[i].bottomright[0], self.accidentals[i].bottomright[1] + y_dif)
            #self.accidentals[i].type = [self.accidentals[i].type, closest_line[1]]
            #print("closest_line accidental", closest_line[0], self.accidentals[i].center[1], self.accidentals[i].type[0])

    def autosnap(self, feature):
        closest_line = self.find_closest_line(feature.center)
        y_dif = closest_line.y - feature.center[1]
        feature.topleft = (feature.topleft[0], feature.topleft[1] + y_dif)
        feature.bottomright = (feature.bottomright[0], feature.bottomright[1] + y_dif)
        feature.letter = closest_line.letter



    """
    Takes the stafflines. Finds the first staff line that is in the region. Then fills implied lines bases off that
    """
    def fill_implied_lines(self, all_staff_lines):
        letters = ['a', 'b', 'c', 'd', 'e', 'f', 'g']
        letter_index = 0
        if self.clef == "t":
            letter_index = 5
        if len(all_staff_lines) % 5 != 0:
            print("Staff line error. Not multiple of five")
        #Find first staff line in the region, then base all other lines off of that one.
        for i in range(len(all_staff_lines) - 4):
            #if line is in region
            if self.topleft[1] < all_staff_lines[i] < self.bottomright[1]:
                line_spacing = (all_staff_lines[i + 4] - all_staff_lines[i]) / 10
                start_line = all_staff_lines[i]
                #draw lines starting from top of staff line and moving to bottom of region
                for k in np.arange(start_line + line_spacing, self.bottomright[1], line_spacing):
                    self.implied_lines.append(ImpliedLine(int(k), letters[letter_index]))
                    letter_index = (letter_index + 1) % len(letters)
                if self.clef == "t":
                    letter_index = 4
                else:
                    letter_index = 6
                # drawing lines starting from top staff line and drawing to top of region
                for k in np.arange(start_line, self.topleft[1], -1 * line_spacing):
                    self.implied_lines.append(ImpliedLine(int(k), letters[letter_index]))
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
                    self.fill_in_feature(img, gray_img, (note.center[0], note.topleft[1], note.bottomright), letter_colors[note.letter])
                if accidental == "natural":
                    self.fill_in_feature(img, gray_img, note.topleft, note.bottomright, letter_colors[note.letter])

            else:
                self.fill_in_feature(img, gray_img, note.topleft, note.bottomright, letter_colors[note.letter])


        for acc in self.accidentals:
            #print(acc)
            self.fill_in_feature(img, gray_img, acc.topleft, acc.bottomright, letter_colors[acc.letter])


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



    def __str__(self):
        topleft_string = "(" + str(self.topleft[0]) + ", " + str(self.topleft[1]) + ")"
        bottomright_string = "(" + str(self.bottomright[0]) + ", " + str(self.bottomright[1]) + ")"
        return "Top left: " + topleft_string + " Bottom right: " + bottomright_string + " Clef: " + str(
            self.clef) + " Num notes: " + str(len(self.notes)) + " Num accidentals: " + str(len(self.accidentals))
