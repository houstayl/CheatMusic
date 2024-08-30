from FeatureObject import Feature
class Note(Feature):

    def __init__(self, topleft, bottomright, is_half_note):
        super().__init__(topleft, bottomright, "note")
        self.is_half_note = is_half_note



