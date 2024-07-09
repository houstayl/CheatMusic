import copy

class Feature:
    def __init__(self, topleft, bottomright, width, height, type, center_y_offset = .5):
        self.topleft = topleft
        self.bottomright = bottomright
        self.width = width
        self.height = height
        self.type = type
        self.center = (int(self.topleft[0] + abs(self.bottomright[0] - self.topleft[0]) * .5), int(self.topleft[1] + abs(self.bottomright[1] - self.topleft[1]) * center_y_offset))
        self.letter = ""#letter only used for notes and accidentals
        self.accidental = ""#only used for notes with accidental
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
    def __str__(self):
        topleft_string = "(" + str(self.topleft[0]) + ", " + str(self.topleft[1]) + ")"
        bottomright_string = "(" + str(self.bottomright[0]) + ", " + str(self.bottomright[1]) + ")"
        return "Top left: " + topleft_string + " Bottom right: " + bottomright_string + " Width: " + str(self.width) + " Height: " + str(self.height) + "Type: " + str(self.type)

