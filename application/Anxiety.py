from Disorder import Disorder

class Anxiety(Disorder):
    def __init__(self):
        super().__init__("Anxiety","Anxiety")
        self.add_session(1, [""])