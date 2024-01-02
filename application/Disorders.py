from Disorder import Disorder
from Anxiety import Anxiety
from Social_Anxiety import Social_Anxiety
from Behavioral_Emotional_Children import Behavioral_Emotional_Children
from Bipolar_affective_disorder import Bipolar_affective_disorder
from Depression import Depression
from Dissociation import Dissociation
from OCD import OCD
from Eating_disorders import Eating_disorders
from Paranoia import Paranoia
from Psychosis import Psychosis
from Schizophrenia import Schizophrenia
from PTSD import PTSD

class Disorders:
    def __init__(self):
        self.ANXIETY = Anxiety("Anxiety", "application/content/Anxiety")
        self.SOCIAL_ANXIETY = Social_Anxiety("Social Anxiety", "application/content/Social_anxiety")
        self.BEHAVIORAL_EMOTIONAL_CHILDREN = Behavioral_Emotional_Children("Behavioural and emotional disorders in children", None)
        self.BIPOLAR_AFFECTIVE = Bipolar_affective_disorder("Bipolar affective disorder", None)
        self.DEPRESSION = Depression("Depression", None)
        self.DISSOCIATION = Dissociation("Dissociation", None)
        self.OCD = OCD("OCD", None)
        self.EATING_DISORDERS = Eating_disorders("Eating disorders", None)
        self.PARANOIA = Paranoia("Paranoia", None)
        self.PSYCHOSIS = Psychosis("Psychosis", None)
        self.SCHIZOPHRENIA = Schizophrenia("Schizophrenia", None)
        self.PTSD = PTSD("Post-traumatic stress disorder", None)

        # Store disorders in a list
        self.disorder_list = [
            self.ANXIETY, self.SOCIAL_ANXIETY, self.BEHAVIORAL_EMOTIONAL_CHILDREN,
            self.BIPOLAR_AFFECTIVE, self.DEPRESSION, self.DISSOCIATION,
            self.OCD, self.EATING_DISORDERS, self.PARANOIA,
            self.PSYCHOSIS, self.SCHIZOPHRENIA, self.PTSD
        ]

    def __getattr__(self, name):
        if name.isupper():
            raise AttributeError(f"Disorders object has no attribute {name}")
        return Disorder(name, None)
