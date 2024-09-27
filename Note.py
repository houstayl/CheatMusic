from FeatureObject import Feature
class Note(Feature):

    def __init__(self, topleft, bottomright, is_half_note, auto_extended=False, is_on_line=None):
        super().__init__(topleft, bottomright, "note")
        self.is_half_note = note_type
        self.auto_extended = auto_extended
        #is on line or is on bar
        self.is_on_line = is_on_line


    def is_auto_extended(self):
        return self.auto_extended



