from FeatureObject import Feature
class StaffLine(Feature):

    def __init__(self, left, right, image_width, image_height, is_on_line=False):
        super().__init__(left, right, "staff_line")
        if self.topleft[0] == self.bottomright[0]:
            self.slope = 0
            self.bottomright[1] = self.topleft[1]
        else:
            self.slope = (self.bottomright[1] - self.topleft[1]) / (self.bottomright[0] - self.topleft[0])
        self.y_intercept = round(self.topleft[1] - self.slope * (self.topleft[0] - 0))
        self.extend_line(image_width, image_height)
        #used for implied line
        self.is_on_line=is_on_line

    def calculate_y(self, x):
        return round(self.y_intercept + self.slope * x)

    def extend_line(self, width, height):
        #TODO find which edge in intersects
        new_topleft = [0, self.y_intercept]
        new_y = round((width - self.bottomright[0]) * self.slope +self.bottomright[1])
        new_bottomright = [width - 1, new_y]
        if 0 <= new_topleft[0] < width and 0 <= new_topleft[1] < height:
            self.topleft = new_topleft
        else:
            #print("extending staff line out of bounds top left", self.topleft, self.bottomright, width, height)
            self.topleft = [0, self.topleft[1]]
            #TODO find closest point inbounds
        if 0 <= new_bottomright[0] < width and 0 <= new_bottomright[1] < height:
            self.bottomright = new_bottomright
        else:
            #print("extending staff line out of bounds bottom right", self.topleft, self.bottomright, width, height)
            self.bottomright = [width - 1, self.bottomright[1]]
            #TODO

    def __eq__(self, other):
        #TODO maybe use other method like y_int and slope
        if self.topleft == other.topleft and self.bottomright == other.bottomright:
            return True
        return False

