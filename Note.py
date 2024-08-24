from FeatureObject import Feature
class StaffLine(Feature):

    def __init__(self, topleft, bottomright, fill_in_whitespace):
        super().__init__(topleft, bottomright, "note")
        self.fill_in_whitespace = fill_in_whitespace

    def calculate_y(self, x):
        return int(self.y_intercept + self.slope * x)


