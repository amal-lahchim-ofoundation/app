from enum import Enum

class Disorders(Enum):
    ANXIETY = "Anxiety"
    SOCIAL_ANXIETY = "Social Anxiety"
    BEHAVIORAL_EMOTIONAL_CHILDREN = "Behavioural and emotional disorders in children"
    BIPOLAR_AFFECTIVE = "Bipolar affective disorder"
    DEPRESSION = "Depression"
    DISSOCIATION = "Dissociation"
    OCD = "OCD"
    EATING_DISORDERS = "Eating disorders"
    PARANOIA = "Paranoia"
    PSYCHOSIS = "Psychosis"
    SCHIZOPHRENIA = "Schizophrenia"
    PTSD = "Post-traumatic stress disorder"


    def __init__(self, disorder_name):
        self.disorder_name = disorder_name