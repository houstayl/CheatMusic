from StaffLine import StaffLine

class ImpliedLine(StaffLine):

    def __init__(self, left, right, letter, is_on_line=False):
        StaffLine.__init__(left, right)
        self.letter = letter
        #if implied line is on line or is on space
        self.is_on_line = is_on_line
