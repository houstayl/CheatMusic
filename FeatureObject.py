import copy

class Feature:
    def __init__(self, topleft, bottomright, type):
        self.topleft = topleft
        self.bottomright = bottomright
        self.type = type
        if self.type == "flat" or self.type == "double_flat":
            self.center = [int(self.topleft[0] + abs(self.bottomright[0] - self.topleft[0]) * .5), int(self.topleft[1] + abs(self.bottomright[1] - self.topleft[1]) * .75)]
        else:
            self.center = [int(self.topleft[0] + abs(self.bottomright[0] - self.topleft[0]) * .5), int(self.topleft[1] + abs(self.bottomright[1] - self.topleft[1]) * .5)]
        self.letter = ""#letter only used for notes and accidentals
        self.accidental = ""#only used for notes with accidental
    def __eq__(self, f):
        return self.topleft == f.topleft and self.bottomright == f.bottomright and self.type == f.type#TODO maybe compare letter and accidental

    def get_width(self):
        return abs(self.bottomright[0] - self.topleft[0])

    def get_height(self):
        return abs(self.bottomright[1] - self.topleft[1])

    def get_topright(self):
        return (self.bottomright[0], self.topleft[1])

    def get_bottomleft(self):
        return (self.topleft[0], self.bottomright[1])

    def is_accidental(self):
        if self.type == "flat" or self.type == "natural" or self.type == "double_flat" or self.type == "double_sharp" or self.type == "sharp":
            return True
        return False

    def copy(self):
        return copy.copy(self)
    def set_letter(self, letter):
        if self.type == "note" or self.type == "double_sharp" or self.type == "sharp" or self.type == "natural" or self.type == "flat" or self.type == "double_flat":
            self.letter = letter
            print("Feature letter changed to ", letter)
        else:
            print("Current feature is not a note or accidental, so cant set letter")

    def set_accidental(self, accidental):
        if self.type == "note":
            self.accidental = accidental
        else:
            print("Current feature is not a note, so cant set accidental")

    def set_center(self, new_center):
        if self.topleft[0] < new_center[0] < self.bottomright[0] and self.topleft[1] < new_center[1] < self.bottomright[1]:

            self.center = new_center
    def reset_center(self):
        #print("old center", self.center)
        self.center = [int(self.topleft[0] + abs(self.bottomright[0] - self.topleft[0]) * .5), int(self.topleft[1] + abs(self.bottomright[1] - self.topleft[1]) * .5)]
        #print("new center", self.center)
    def __eq__(self, other):
        return self.topleft == other.topleft and self.bottomright == other.bottomright and self.width == other.width and self.height == other.height and self.type == other.type and self.letter == other.letter and self.accidental == other.accidental
    def __str__(self):
        topleft_string = "(" + str(self.topleft[0]) + ", " + str(self.topleft[1]) + ")"
        bottomright_string = "(" + str(self.bottomright[0]) + ", " + str(self.bottomright[1]) + ")"
        return "Top left: " + topleft_string + " Bottom right: " + bottomright_string + "Type: " + str(self.type)

