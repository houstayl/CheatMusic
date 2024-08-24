from StaffLine import StaffLine

class ImpliedLine(StaffLine):

    def __init__(self, left, right, letter):
        StaffLine.__init__(left, right)
        self.letter = letter
