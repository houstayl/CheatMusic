from FeatureObject import Feature
class Note(Feature):

    def __init__(self, topleft, bottomright, is_half_note, auto_extended=False):
        super().__init__(topleft, bottomright, "note")
        self.is_half_note = is_half_note
        self.auto_extended = auto_extended


    def is_auto_extended(self):
        return self.auto_extended



