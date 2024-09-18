import pycountry

personal_info_questions_phase_1 = [
    # PHASE 1
{"question":"What is your age?", "type":"number", "placeholder":""},
    {"question":"What is your gender?", "type":"select", "options":["Male", "Female", "Other"],"placeholder":""},
    {"question": "What is your nationality?", "type": "select", "options": [country.name for country in pycountry.countries], "placeholder": "Select your nationality"},
    {"question": "What is your current country of residence?", "type": "select", "options": [country.name for country in pycountry.countries], "placeholder": "Select your current country of residence"},
    {"question":"What cultural or ethnic background do you identify with? How does this influence your daily life?", "type":"text","placeholder":""},
    {"question":"What is your marital status?", "type":"select","options":["Single","Married","Divorced","Other"],"placeholder":""},
    {"question":"What is your education level?", "type":"select", "options":["High School","Bachelor's, Master's","Other"], "placeholder":""},
    {"question":"What is your employment status?", "type":"select", "options":["Employed","Unemployed","Retired","Other"],"placeholder":""},
    {"question":"what is your living situation?","type":"select","options":["Alone","With Family","With Friends","Other"],"placeholder":""},
 {"question": "To what extent do you believe your early childhood experiences influence your current mental health?",
     "type": "text", 
     "placeholder":"If this is an important topic related to your mental issue, please write more (optional)."
},

    {
    "question": "How often do you reflect on your childhood when thinking about your current mental health challenges?",
    "type": "text", 
     "placeholder":"If this is an important topic related to your mental issue, please write more (optional)."
},


   {
    "question": "To what extent do you feel your developmental milestones were met in a typical or healthy way?",
    "type": "text", 
     "placeholder":"If this is an important topic related to your mental issue, please write more (optional)."
},

{
    "question": "To what extent do you believe unresolved issues from your childhood affect your relationships today?",
     "type": "text", 
     "placeholder":"If this is an important topic related to your mental issue, please write more (optional)."
},
{
    "question": "To what extent do memories of your childhood evoke strong emotions in you today?",
     "type": "text", 
     "placeholder":"If this is an important topic related to your mental issue, please write more (optional)."
},
{
    "question": "To what extent are you motivated to make changes in your life to improve your mental health?",
     "type": "text", 
     "placeholder":""
},
{
    "question": "To what extent do you believe in your ability to make the changes necessary for your well-being?",
     "type": "text", 
     "placeholder":"If this is an important topic related to your mental issue, please write more (optional)."
},
{
    "question": "To what extent do you feel ready to engage fully in therapy and the work it requires?",
     "type": "text", 
     "placeholder":"If this is an important topic related to your mental issue, please write more (optional)."
},
{
    "question": "To what extent do you believe that change is possible for you at this time?",
     "type": "text", 
     "placeholder":"If this is an important topic related to your mental issue, please write more (optional)."
},

   {
        "question": "To what degree do you feel supported by others in your efforts to make changes?",
         "type": "text", 
     "placeholder":"If this is an important topic related to your mental issue, please write more (optional)."
},
    {
        "question": "How frequently do you use substances (e.g., drugs, alcohol) to cope with stress or emotions?",
         "type": "text", 
     "placeholder":"If this is an important topic related to your mental issue, please write more (optional)."
},
    {
        "question": "To what extent do you feel your substance use affects your mental health?",
         "type": "text", 
     "placeholder":"If this is an important topic related to your mental issue, please write more (optional)."
},
{
    "question": "How much control do you feel you have over your substance use?",
    "type": "text", 
     "placeholder":"If this is an important topic related to your mental issue, please write more (optional)."
}

]


# personal_info_questions_phase_1 = [
#     # PHASE 1
# {"question":"What is your age?", "type":"number", "placeholder":""},
#     {"question":"What is your gender?", "type":"select", "options":["Male", "Female", "Other"],"placeholder":""},
#     {"question": "What is your nationality?", "type": "select", "options": [country.name for country in pycountry.countries], "placeholder": "Select your nationality"},
#     {"question": "What is your current country of residence?", "type": "select", "options": [country.name for country in pycountry.countries], "placeholder": "Select your current country of residence"},
#     {"question":"What cultural or ethnic background do you identify with? How does this influence your daily life?", "type":"text","placeholder":""},
#     {"question":"What is your marital status?", "type":"select","options":["Single","Married","Divorced","Other"],"placeholder":""},
#     {"question":"What is your education level?", "type":"select", "options":["High School","Bachelor's, Master's","Other"], "placeholder":""},
#     {"question":"What is your employment status?", "type":"select", "options":["Employed","Unemployed","Retired","Other"],"placeholder":""},
#     {"question":"what is your living situation?","type":"select","options":["Alone","With Family","With Friends","Other"],"placeholder":""},
#  {"question": "To what extent do you believe your early childhood experiences influence your current mental health?",
#      "type": "text", 
#      "placeholder": "More thoughts"},

#     {
#     "question": "How often do you reflect on your childhood when thinking about your current mental health challenges?",
#     "type": "select",
#     "options": [
#         "0: Never - I never think about my childhood when dealing with my current mental health challenges.",
#         "20: Rarely - I rarely reflect on my childhood in relation to my current mental health issues.",
#         "40: Sometimes - I sometimes consider my childhood experiences when addressing my mental health challenges.",
#         "60: Often - I often think about my childhood when dealing with my current mental health challenges.",
#         "80: Very often - I frequently reflect on my childhood experiences in relation to my mental health issues.",
#         "100: Always - I always think about my childhood experiences when addressing my current mental health challenges."
#     ],
#     "placeholder": "Select a number between 0 and 100",
#     "additional_info": {
#         "type": "textarea",
#         "placeholder": "Please provide any additional comments or insights about how your childhood reflections impact your current mental health challenges."
#     }
# },


#    {
#     "question": "To what extent do you feel your developmental milestones were met in a typical or healthy way?",
#     "type": "select",
#     "options": [
#         "0: Not at all - I feel that my developmental milestones were not met in a typical or healthy way.",
#         "20: A little - I feel that my developmental milestones were met only to a small extent in a typical or healthy way.",
#         "40: Moderately - I feel that my developmental milestones were met in a moderate way in terms of typical or healthy development.",
#         "60: Quite a bit - I feel that my developmental milestones were met to a significant extent in a typical or healthy manner.",
#         "80: Very much - I feel that my developmental milestones were largely met in a typical or healthy way.",
#         "100: Extremely - I feel that my developmental milestones were fully met in a typical and healthy manner."
#     ],
#     "placeholder": "Select a number between 0 and 100"
# },

# {
#     "question": "To what extent do you believe unresolved issues from your childhood affect your relationships today?",
#     "type": "select",
#     "options": [
#         "0: Not at all - I don't believe that unresolved issues from my childhood have any effect on my relationships today.",
#         "20: A little - I believe that unresolved issues from my childhood have a minor effect on my current relationships.",
#         "40: Moderately - I feel that unresolved issues from my childhood have a moderate impact on my relationships today.",
#         "60: Quite a bit - I think that unresolved childhood issues have a significant effect on my relationships.",
#         "80: Very much - I believe that unresolved childhood issues greatly impact my current relationships.",
#         "100: Extremely - I think that unresolved childhood issues have a profound and overwhelming effect on my relationships today."
#     ],
#     "placeholder": "Select a number between 0 and 100"
# },
# {
#     "question": "To what extent do memories of your childhood evoke strong emotions in you today?",
#     "type": "select",
#     "options": [
#         "0: Not at all - Memories of my childhood never evoke strong emotions in me today.",
#         "20: A little - Childhood memories rarely trigger strong emotions for me today.",
#         "40: Moderately - I sometimes experience strong emotions triggered by childhood memories.",
#         "60: Quite a bit - Childhood memories often evoke strong emotions in me.",
#         "80: Very much - I frequently feel strong emotions when I recall my childhood memories.",
#         "100: Extremely - My childhood memories always evoke intense emotions in me."
#     ],
#     "placeholder": "Select a number between 0 and 100"
# },
# {
#     "question": "To what extent are you motivated to make changes in your life to improve your mental health?",
#     "type": "select",
#     "options": [
#         "0: Not at all - I have no motivation to make changes in my life to improve my mental health.",
#         "20: A little - I have a small amount of motivation to make changes for better mental health.",
#         "40: Moderately - I feel moderately motivated to make changes in my life to improve my mental health.",
#         "60: Quite a bit - I am quite motivated to make changes to enhance my mental health.",
#         "80: Very much - I am very motivated to make significant changes for improving my mental health.",
#         "100: Extremely - I am extremely motivated and committed to making changes to improve my mental health."
#     ],
#     "placeholder": "Select a number between 0 and 100"
# },
# {
#     "question": "To what extent do you believe in your ability to make the changes necessary for your well-being?",
#     "type": "select",
#     "options": [
#         "0: Not at all - I don't believe I have any ability to make the changes necessary for my well-being.",
#         "20: A little - I have a slight belief in my ability to make necessary changes for my well-being.",
#         "40: Moderately - I have a moderate belief in my ability to effect the changes needed for my well-being.",
#         "60: Quite a bit - I have a strong belief in my ability to make the changes necessary for my well-being.",
#         "80: Very much - I am very confident in my ability to make significant changes for my well-being.",
#         "100: Extremely - I am extremely confident in my ability to make all the changes needed for my well-being."
#     ],
#     "placeholder": "Select a number between 0 and 100"
# },
# {
#     "question": "To what extent do you feel ready to engage fully in therapy and the work it requires?",
#     "type": "select",
#     "options": [
#         "0: Not at all - I am not ready to engage in therapy or the work it requires.",
#         "20: A little - I am slightly ready to start therapy and engage in the required work.",
#         "40: Moderately - I am moderately ready to engage fully in therapy and its demands.",
#         "60: Quite a bit - I am quite ready to commit to therapy and the work it involves.",
#         "80: Very much - I am very ready to engage fully in therapy and the associated efforts.",
#         "100: Extremely - I am extremely ready and committed to fully engage in therapy and all its requirements."
#     ],
#     "placeholder": "Select a number between 0 and 100"
# },
# {
#     "question": "To what extent do you believe that change is possible for you at this time?",
#     "type": "select",
#     "options": [
#         "0: Not at all - I don't believe change is possible for me right now.",
#         "20: A little - I have a small belief that change is possible for me at this time.",
#         "40: Moderately - I moderately believe that change is achievable for me right now.",
#         "60: Quite a bit - I have a strong belief that change is possible for me at this time.",
#         "80: Very much - I believe that significant change is very likely for me right now.",
#         "100: Extremely - I am fully convinced that change is not only possible but likely for me at this time."
#     ],
#     "placeholder": "Select a number between 0 and 100"
# },

#    {
#         "question": "To what degree do you feel supported by others in your efforts to make changes?",
#         "type": "select",
#         "options": [
#             "0: Not at all - I feel completely unsupported in my efforts to make changes.",
#             "20: A little - I feel only a little support from others in my efforts to make changes.",
#             "40: Moderately - I receive a moderate level of support from others in my change efforts.",
#             "60: Quite a bit - I feel quite supported by others as I work to make changes.",
#             "80: Very much - I feel very supported by others in my efforts to bring about change.",
#             "100: Extremely - I feel extremely supported by others in all my efforts to make changes."
#         ],
#         "placeholder": "Select a number between 0 and 100"
#     },
#     {
#         "question": "How frequently do you use substances (e.g., drugs, alcohol) to cope with stress or emotions?",
#         "type": "select",
#         "options": [
#             "0: Never - I never use substances to cope with stress or emotions.",
#             "20: Rarely - I rarely turn to substances to manage stress or emotions.",
#             "40: Sometimes - I sometimes use substances as a way to cope with stress or emotions.",
#             "60: Often - I often use substances to deal with stress or emotional challenges.",
#             "80: Very often - I frequently rely on substances to manage stress or emotions.",
#             "100: Always - I always use substances as a primary way to cope with stress or emotions."
#         ],
#         "placeholder": "Select a number between 0 and 100"
#     },
#     {
#         "question": "To what extent do you feel your substance use affects your mental health?",
#         "type": "select",
#         "options": [
#             "0: Not at all - I don't believe my substance use has any impact on my mental health.",
#             "20: A little - My substance use has a minor effect on my mental health.",
#             "40: Moderately - My substance use affects my mental health to a moderate extent.",
#             "60: Quite a bit - I feel that my substance use significantly impacts my mental health.",
#             "80: Very much - My substance use has a strong effect on my mental health.",
#             "100: Extremely - My substance use has an overwhelming impact on my mental health."
#         ],
#         "placeholder": "Select a number between 0 and 100"
#     },

# {
#     "question": "How much control do you feel you have over your substance use?",
#     "type": "select",
#     "options": [
#         "0: No control - I feel I have no control over my substance use.",
#         "20: A little control - I feel I have very limited control over my substance use.",
#         "40: Moderate control - I have a moderate level of control over my substance use.",
#         "60: Quite a bit of control - I feel I have a significant amount of control over my substance use.",
#         "80: Very much control - I believe I have a strong control over my substance use.",
#         "100: Complete control - I feel I have full control over my substance use."
#     ],
#     "placeholder": "Select a number between 0 and 100"
# }


# ]







personal_info_questions_phase_2 = [
    # PHASE 2
    {"question": "How would you describe your overall physical health at the moment?", "type": "text", "placeholder": ""},
{"question": "Have you experienced any recent changes in your physical health, such as weight loss, changes in appetite, sleep patterns, or energy levels?", "type": "text", "placeholder": ""},
{"question": "Do you have any chronic conditions or ongoing medical issues that you think might be affecting your mood or mental state?", "type": "text", "placeholder": ""},
{"question": "How does your body feel on a typical day? Do you experience any pain, discomfort, or physical tension?", "type": "text", "placeholder": ""},
{"question": "How often do you engage in physical activity or exercise, and how do you feel it affects your mood and mental clarity?", "type": "text", "placeholder": ""},
{"question": "Have you noticed any connection between your physical health and your emotional well-being? For instance, do your mood and energy levels fluctuate with changes in your physical condition?", "type": "text", "placeholder": ""},
{"question": "Are there any medications or treatments you are currently undergoing that you believe might be affecting your mental state?", "type": "text", "placeholder": ""},
{"question": "How is your sleep? Do you wake up feeling rested, or do you experience fatigue throughout the day?", "type": "text", "placeholder": ""},
{"question": "Have you ever experienced psychosomatic symptoms, where physical symptoms might be related to stress or emotional distress?", "type": "text", "placeholder": ""},
{"question": "How do you take care of your physical health, and do you feel that you have the resources or support you need to maintain it?", "type": "text", "placeholder": ""},
{"question": "Are you currently taking any prescribed medications? If so, can you tell me a bit about them and how you feel they are affecting you?", "type": "text", "placeholder": ""},
{"question": "Do you use any over-the-counter medications, supplements, or herbal remedies? How do you think these affect your mood or energy levels?", "type": "text", "placeholder": ""},
{"question": "Have you been prescribed any medications in the past for mental health or other conditions? If so, how did you respond to them?", "type": "text", "placeholder": ""},
{"question": "Do you use any substances, such as alcohol, tobacco, recreational drugs, or other substances? How often, and how do you feel they affect your mental and physical well-being?", "type": "text", "placeholder": ""},
{"question": "Have you noticed any changes in your mood, anxiety, or energy levels after using certain substances or medications?", "type": "text", "placeholder": ""},
{"question": "Are there any substances you use to help manage stress, anxiety, or other emotions? If so, how effective do you find them?", "type": "text", "placeholder": ""},
{"question": "Have you ever experienced any negative side effects or withdrawal symptoms from medications or substances? How did you manage them?", "type": "text", "placeholder": ""},
{"question": "Do you feel that your use of any medications or substances is helping or hindering your overall health and well-being?", "type": "text", "placeholder": ""},
{"question": "Are you currently receiving guidance from a healthcare provider regarding your use of these substances or medications?", "type": "text", "placeholder": ""},
{"question": "Is there anything about your use of medications or substances that you’re concerned about or that you think might be important for us to discuss?", "type": "text", "placeholder": ""},
    
    {"question":"Do you have a stable support system?","type":"text","placeholder":"Yes/No; If yes, please specify"},
    {"question":"Who are the most significant people in your life, and what kind of relationships do you have with them?", "type":"text","placeholder":""},
    {"question":"Are you actively involved in any community or social groups? How does this impact your social interactions?","type":"text","placeholder":""},
    {"question":"Do you have any chronic physical illnesses?","type":"text","placeholder":"Yes/No; If yes, please specify"},
    {"question":"Are you currently taking any medications?", "type":"text", "placeholder":"Yes/No; If yes, please specify"},
    {"question":"Do you use substances like tobacco, alcohol, or recreational drugs?","type":"select", "options":["Yes","No"],"placeholder":""},
    {"question":"How often do you exercise?", "type":"select", "options":["Daily","Weekly","Rarely","Never"],"placeholder":""},
    {"question":"Can you describe your typical daily diet? Do you follow any specific dietary restrictions?", "type":"text","placeholder":""},
    {"question":"How would you describe your typical sleep patterns and quality?", "type":"text","placeholder":""},
    {"question":"Have you been diagnosed with any mental health disorders?", "type":"text","placeholder":"Yes/No; If yes, please specify"},
    {"question":"Have you experienced significant life changes or stressors recently?","type":"text","placeholder":"Yes/No; If yes, please specify"},
    {"question":"Rate your overall stress level on a scale from 1 to 10:","type":"select", "options":["1","2","3","4","5","6","7","8","9","10"], "placeholder":""},
    {"question":"What are your primary ways of coping with stress or emotional distress?","type":"text","placeholder":""},
    {"question":"Can you share an instance where you successfully managed a challenging life event?","type":"text","placeholder":""},
    {"question":"Do you feel content with your personal life?", "type":"text","placeholder":"Yes/No; If no, what areas would you like to improve?"},
    {"question":"How often do you engage in activities that you enjoy?","type":"select", "options":["Daily","Weekly","Rarely","Never"],"placeholder":""},
    {"question":"Do you feel you have adequate social interactions?","type":"text","placeholder":"Yes/No; If no, what barriers do you face?"},
    {"question":"How would you rate your overall happiness on a scale from 1 to 10?", "type":"select", "options":["1","2","3","4","5","6","7","8","9","10"], "placeholder":""},
    {"question":"What aspects of your life are you most satisfied or dissatisfied with? Why?","type":"text","placeholder":""},
    {"question":"What are your hopes and aspirations for the future? How do you plan to achieve them?","type":"text","placeholder":""},
    {"question":"How would you describe your overall level of physical activity?","type":"select","options":["Very active","Moderately active","Lightly active","Sedentary"],"placeholder":""},
    {"question":"What do you typically do in your leisure time? How do you balance relaxation with activity?","type":"text","placeholder":""},
]

personal_info_questions_phase_3 = [
    #Phase 3
    {"question":"Would you describe yourself more as an introvert or an extrovert?","type":"text","placeholder":""},
    {"question":"How comfortable do you feel in social gatherings and public speaking scenarios?","type":"select","options":["Very comfortable","Somewhat comfortable","Neutral","Somewhat uncomfortable","Very uncomfortable"],"placeholder":""},
    {"question":"How do you typically react to meeting new people or being in unfamiliar social situations?","type":"text","placeholder":"Examples:Seek interaction,Observe first then join,Remain mostly on the sidelines,Avoid if possible"},
    {"question":"What skills or talents do you believe you possess?","type":"text","placeholder":""},
    {"question":"How have you developed these skills over time?","type":"text","placeholder":"Examples:Formal education,Self-taught,Mentorship,On-the-job experience"},
    {"question":"Can you provide examples of how you apply these skills in your personal or professional life?", "type":"text","placeholder":""},
    {"question":"What skills do you find most useful in social interactions?","type":"text","placeholder":"Examples: Active listening, Empathy, Clear communication, Persuasiveness, Conflict resolution"},
]

