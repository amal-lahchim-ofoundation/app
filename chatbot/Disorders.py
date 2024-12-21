from Disorder import Disorder
from Anxiety import Anxiety
from Social_Anxiety import Social_Anxiety
from Low_self_confident import Low_self_confident
from Work_Study_Problems import Work_Study_Problems
from Depression import Depression
from Dissociation import Dissociation
from OCD import OCD
from Stress import Stress
from Fear_of_illness_or_death import Fear_of_illness_or_death
from Unresolved_past_issues import Unresolved_past_issues
from Assertiveness import Assertiveness
from PTSD import PTSD
from Compulsivity import Compulsivity
from Processing_issues import Processing_issues
from Identity_questions import Identity_questions
from Sleep_problems import Sleep_problems
from Grief_problems import Grief_problems
from Friendships_Relationships import Friendships_Relationships
from Adaptation import Adaptation
import os
from dotenv import load_dotenv


load_dotenv() 
class Disorders:
    def __init__(self):
        self.ANXIETY = Anxiety("Anxiety", os.getenv('CONTENT_FOLDER')+"Anxiety")
        self.SOCIAL_ANXIETY = Social_Anxiety("Social Anxiety", os.getenv('CONTENT_FOLDER')+"Social_anxiety")
        self.LOW_SELF_CONFIDENT = Low_self_confident("Low self confident", None)
        self.WORK_STUDY_PROBLEMS = Work_Study_Problems("Work and study problems", None)
        self.DEPRESSION = Depression("Depression", os.getenv('CONTENT_FOLDER')+"Depression")
        self.DISSOCIATION = Dissociation("Dissociation", None)
        self.OCD = OCD("OCD", None)
        self.STRESS = Stress("Stress", None)
        self.FEAR_OF_ILLNESS_OR_DEATH = Fear_of_illness_or_death("Fear of illness or death", None)
        self.UNRESOLVED_PAST_ISSUES = Unresolved_past_issues("Unresolved past issues", None)
        self.ASSERTIVENESS = Assertiveness("Assertiveness", None)
        self.PTSD = PTSD("Post-traumatic stress disorder", None)
        self.COMPULSIVITY = Compulsivity("Compulsivity", None)
        self.PROCESSING_ISSUES = Processing_issues("Processing issues with illness or loss", None)
        self.IDENTITY_QUESTIONS = Identity_questions("Identity questions", None)
        self.SLEEP_PROBLEMS = Sleep_problems("Sleep problems", None)
        self.GRIEF_PROBLEMS = Grief_problems("Grief problems", None)
        self.FRIENDSHIPS_RELATIONSHIPS =Friendships_Relationships("Issues with Friendships and Relationships", None)
        self.ADAPTATION = Adaptation("Adaptation", None)


        # Store disorders in a list
        self.disorder_list = [
            self.ANXIETY, self.SOCIAL_ANXIETY, self.LOW_SELF_CONFIDENT,
            self.WORK_STUDY_PROBLEMS, self.DEPRESSION, self.DISSOCIATION,
            self.OCD, self.STRESS, self.FEAR_OF_ILLNESS_OR_DEATH,
            self.UNRESOLVED_PAST_ISSUES, self.ASSERTIVENESS, self.PTSD, 
            self.COMPULSIVITY, self.PROCESSING_ISSUES, self.PROCESSING_ISSUES,
            self.SLEEP_PROBLEMS, self.GRIEF_PROBLEMS, self.FRIENDSHIPS_RELATIONSHIPS,
            self.ADAPTATION

        ]

    def __getattr__(self, name):
        if name.isupper():
            raise AttributeError(f"Disorders object has no attribute {name}")
        return Disorder(name, None)

    def get_disorder_by_name(self, disorder_name):
        for disorder in self.disorder_list:
            if disorder.name.lower() == disorder_name.lower():
                return disorder
        # If the disorder with the given name is not found, you can return None or raise an exception.
        return None 