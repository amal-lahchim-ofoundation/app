import pycountry

personal_info_questions_phase_1 = [
    # PHASE 1
{"question":"What is your age?", "type":"number", "placeholder":""},
    {"question":"What is your gender?", "type":"select", "options":["Male", "Female", "Other"],"placeholder":""},
    {"question": "What is your nationality?", "type": "select", "options": [country.name for country in pycountry.countries], "placeholder": "Select your nationality"},
    {"question": "What is your current country of residence?", "type": "select", "options": [country.name for country in pycountry.countries], "placeholder": "Select your current country of residence"},
    {"question":"What is your marital status?", "type":"select","options":["Single","Married","Divorced","Other"],"placeholder":""},
    {"question":"What is your education level?", "type":"select", "options":["High School","Bachelor's, Master's","Other"], "placeholder":""},
    {"question":"What is your employment status?", "type":"select", "options":["Employed","Unemployed","Retired","Other"],"placeholder":""},
    {"question":"what is your living situation?","type":"select","options":["Alone","With Family","With Friends","Other"],"placeholder":""},
    
    {"question":"What cultural or ethnic background do you identify with? How does this influence your daily life?", "type":"text","placeholder":"If this is an important topic related to your mental issue, please write more (optional)."},
    
    {
        "question": "To what extent do you believe your early childhood experiences influence your current mental health?",
        "type": "group",
        "inputs": [
            {
                "type": "range",
                "min": 1,
                "max": 100,
                "step": 1,
                "name": "childhood_influence_score"
            },
            {
                "type": "text",
                "placeholder": "If this is an important topic related to your mental issue, please write more (optional).",
                "name": "childhood_influence_comments"
            }
        ]
    },
    {
        "question": "How often do you reflect on your childhood when thinking about your current mental health challenges?",
        "type": "group",
        "inputs": [
            {
                "type": "range",
                "min": 1,
                "max": 100,
                "step": 1,
                "name": "reflection_frequency_score"
            },
            {
                "type": "text",
                "placeholder": "If this is an important topic related to your mental issue, please write more (optional).",
                "name": "reflection_frequency_comments"
            }
        ]
    },
    {
        "question": "To what extent do you feel your developmental milestones were met in a typical or healthy way?",
        "type": "group",
        "inputs": [
            {
                "type": "range",
                "min": 1,
                "max": 100,
                "step": 1,
                "name": "milestones_score"
            },
            {
                "type": "text",
                "placeholder": "If this is an important topic related to your mental issue, please write more (optional).",
                "name": "milestones_comments"
            }
        ]
    },
    {
        "question": "To what extent do you believe unresolved issues from your childhood affect your relationships today?",
        "type": "group",
        "inputs": [
            {
                "type": "range",
                "min": 1,
                "max": 100,
                "step": 1,
                "name": "unresolved_issues_score"
            },
            {
                "type": "text",
                "placeholder": "If this is an important topic related to your mental issue, please write more (optional).",
                "name": "unresolved_issues_comments"
            }
        ]
    },
    {
        "question": "To what extent do memories of your childhood evoke strong emotions in you today?",
        "type": "group",
        "inputs": [
            {
                "type": "range",
                "min": 1,
                "max": 100,
                "step": 1,
                "name": "memories_score"
            },
            {
                "type": "text",
                "placeholder": "If this is an important topic related to your mental issue, please write more (optional).",
                "name": "memories_comments"
            }
        ]
    },
    {
        "question": "To what extent are you motivated to make changes in your life to improve your mental health?",
        "type": "group",
        "inputs": [
            {
                "type": "range",
                "min": 1,
                "max": 100,
                "step": 1,
                "name": "motivation_score"
            },
            {
                "type": "text",
                "placeholder": "If this is an important topic related to your mental issue, please write more (optional).",
                "name": "motivation_comments"
            }
        ]
    },
    {
        "question": "To what extent do you believe in your ability to make the changes necessary for your well-being?",
        "type": "group",
        "inputs": [
            {
                "type": "range",
                "min": 1,
                "max": 100,
                "step": 1,
                "name": "ability_score"
            },
            {
                "type": "text",
                "placeholder": "If this is an important topic related to your mental issue, please write more (optional).",
                "name": "ability_comments"
            }
        ]
    },
    {
        "question": "To what extent do you feel ready to engage fully in therapy and the work it requires?",
        "type": "group",
        "inputs": [
            {
                "type": "range",
                "min": 1,
                "max": 100,
                "step": 1,
                "name": "therapy_readiness_score"
            },
            {
                "type": "text",
                "placeholder": "If this is an important topic related to your mental issue, please write more (optional).",
                "name": "therapy_readiness_comments"
            }
        ]
    },
    {
        "question": "To what extent do you believe that change is possible for you at this time?",
        "type": "group",
        "inputs": [
            {
                "type": "range",
                "min": 1,
                "max": 100,
                "step": 1,
                "name": "change_possibility_score"
            },
            {
                "type": "text",
                "placeholder": "If this is an important topic related to your mental issue, please write more (optional).",
                "name": "change_possibility_comments"
            }
        ]
    },
    {
        "question": "To what degree do you feel supported by others in your efforts to make changes?",
        "type": "group",
        "inputs": [
            {
                "type": "range",
                "min": 1,
                "max": 100,
                "step": 1,
                "name": "support_degree_score"
            },
            {
                "type": "text",
                "placeholder": "If this is an important topic related to your mental issue, please write more (optional).",
                "name": "support_degree_comments"
            }
        ]
    },
    {
        "question": "How frequently do you use substances (e.g., drugs, alcohol) to cope with stress or emotions?",
        "type": "group",
        "inputs": [
            {
                "type": "range",
                "min": 1,
                "max": 100,
                "step": 1,
                "name": "substance_use_frequency_score"
            },
            {
                "type": "text",
                "placeholder": "If this is an important topic related to your mental issue, please write more (optional).",
                "name": "substance_use_frequency_comments"
            }
        ]
    },
    {
        "question": "To what extent do you feel your substance use affects your mental health?",
        "type": "group",
        "inputs": [
            {
                "type": "range",
                "min": 1,
                "max": 100,
                "step": 1,
                "name": "substance_effect_score"
            },
            {
                "type": "text",
                "placeholder": "If this is an important topic related to your mental issue, please write more (optional).",
                "name": "substance_effect_comments"
            }
        ]
    },
    {
        "question": "How much control do you feel you have over your substance use?",
        "type": "group",
        "inputs": [
            {
                "type": "range",
                "min": 1,
                "max": 100,
                "step": 1,
                "name": "substance_control_score"
            },
            {
                "type": "text",
                "placeholder": "If this is an important topic related to your mental issue, please write more (optional).",
                "name": "substance_control_comments"
            }
        ]
    }

]


# personal_info_questions_phase_2 = [
#     # PHASE 2
#     {"question": "How would you describe your overall physical health at the moment?", "type": "text", "placeholder": ""},
# {"question": "Have you experienced any recent changes in your physical health, such as weight loss, changes in appetite, sleep patterns, or energy levels?", "type": "text", "placeholder": ""},
# {"question": "Do you have any chronic conditions or ongoing medical issues that you think might be affecting your mood or mental state?", "type": "text", "placeholder": ""},
# {"question": "How does your body feel on a typical day? Do you experience any pain, discomfort, or physical tension?", "type": "text", "placeholder": ""},
# {"question": "How often do you engage in physical activity or exercise, and how do you feel it affects your mood and mental clarity?", "type": "text", "placeholder": ""},
# {"question": "Have you noticed any connection between your physical health and your emotional well-being? For instance, do your mood and energy levels fluctuate with changes in your physical condition?", "type": "text", "placeholder": ""},
# {"question": "Are there any medications or treatments you are currently undergoing that you believe might be affecting your mental state?", "type": "text", "placeholder": ""},
# {"question": "How is your sleep? Do you wake up feeling rested, or do you experience fatigue throughout the day?", "type": "text", "placeholder": ""},
# {"question": "Have you ever experienced psychosomatic symptoms, where physical symptoms might be related to stress or emotional distress?", "type": "text", "placeholder": ""},
# {"question": "How do you take care of your physical health, and do you feel that you have the resources or support you need to maintain it?", "type": "text", "placeholder": ""},
# {"question": "Are you currently taking any prescribed medications? If so, can you tell me a bit about them and how you feel they are affecting you?", "type": "text", "placeholder": ""},
# {"question": "Do you use any over-the-counter medications, supplements, or herbal remedies? How do you think these affect your mood or energy levels?", "type": "text", "placeholder": ""},
# {"question": "Have you been prescribed any medications in the past for mental health or other conditions? If so, how did you respond to them?", "type": "text", "placeholder": ""},
# {"question": "Do you use any substances, such as alcohol, tobacco, recreational drugs, or other substances? How often, and how do you feel they affect your mental and physical well-being?", "type": "text", "placeholder": ""},
# {"question": "Have you noticed any changes in your mood, anxiety, or energy levels after using certain substances or medications?", "type": "text", "placeholder": ""},
# {"question": "Are there any substances you use to help manage stress, anxiety, or other emotions? If so, how effective do you find them?", "type": "text", "placeholder": ""},
# {"question": "Have you ever experienced any negative side effects or withdrawal symptoms from medications or substances? How did you manage them?", "type": "text", "placeholder": ""},
# {"question": "Do you feel that your use of any medications or substances is helping or hindering your overall health and well-being?", "type": "text", "placeholder": ""},
# {"question": "Are you currently receiving guidance from a healthcare provider regarding your use of these substances or medications?", "type": "text", "placeholder": ""},
# {"question": "Is there anything about your use of medications or substances that you’re concerned about or that you think might be important for us to discuss?", "type": "text", "placeholder": ""},
    
#     {"question":"Do you have a stable support system?","type":"text","placeholder":"Yes/No; If yes, please specify"},
#     {"question":"Who are the most significant people in your life, and what kind of relationships do you have with them?", "type":"text","placeholder":""},
#     {"question":"Are you actively involved in any community or social groups? How does this impact your social interactions?","type":"text","placeholder":""},
#     {"question":"Do you have any chronic physical illnesses?","type":"text","placeholder":"Yes/No; If yes, please specify"},
#     {"question":"Are you currently taking any medications?", "type":"text", "placeholder":"Yes/No; If yes, please specify"},
#     {"question":"Do you use substances like tobacco, alcohol, or recreational drugs?","type":"select", "options":["Yes","No"],"placeholder":""},
#     {"question":"How often do you exercise?", "type":"select", "options":["Daily","Weekly","Rarely","Never"],"placeholder":""},
#     {"question":"Can you describe your typical daily diet? Do you follow any specific dietary restrictions?", "type":"text","placeholder":""},
#     {"question":"How would you describe your typical sleep patterns and quality?", "type":"text","placeholder":""},
#     {"question":"Have you been diagnosed with any mental health disorders?", "type":"text","placeholder":"Yes/No; If yes, please specify"},
#     {"question":"Have you experienced significant life changes or stressors recently?","type":"text","placeholder":"Yes/No; If yes, please specify"},
#     {"question":"Rate your overall stress level on a scale from 1 to 10:","type":"select", "options":["1","2","3","4","5","6","7","8","9","10"], "placeholder":""},
#     {"question":"What are your primary ways of coping with stress or emotional distress?","type":"text","placeholder":""},
#     {"question":"Can you share an instance where you successfully managed a challenging life event?","type":"text","placeholder":""},
#     {"question":"Do you feel content with your personal life?", "type":"text","placeholder":"Yes/No; If no, what areas would you like to improve?"},
#     {"question":"How often do you engage in activities that you enjoy?","type":"select", "options":["Daily","Weekly","Rarely","Never"],"placeholder":""},
#     {"question":"Do you feel you have adequate social interactions?","type":"text","placeholder":"Yes/No; If no, what barriers do you face?"},
#     {"question":"How would you rate your overall happiness on a scale from 1 to 10?", "type":"select", "options":["1","2","3","4","5","6","7","8","9","10"], "placeholder":""},
#     {"question":"What aspects of your life are you most satisfied or dissatisfied with? Why?","type":"text","placeholder":""},
#     {"question":"What are your hopes and aspirations for the future? How do you plan to achieve them?","type":"text","placeholder":""},
#     {"question":"How would you describe your overall level of physical activity?","type":"select","options":["Very active","Moderately active","Lightly active","Sedentary"],"placeholder":""},
#     {"question":"What do you typically do in your leisure time? How do you balance relaxation with activity?","type":"text","placeholder":""},
# ]

# personal_info_questions_phase_3 = [
#     #Phase 3
#     {"question":"Would you describe yourself more as an introvert or an extrovert?","type":"text","placeholder":""},
#     {"question":"How comfortable do you feel in social gatherings and public speaking scenarios?","type":"select","options":["Very comfortable","Somewhat comfortable","Neutral","Somewhat uncomfortable","Very uncomfortable"],"placeholder":""},
#     {"question":"How do you typically react to meeting new people or being in unfamiliar social situations?","type":"text","placeholder":"Examples:Seek interaction,Observe first then join,Remain mostly on the sidelines,Avoid if possible"},
#     {"question":"What skills or talents do you believe you possess?","type":"text","placeholder":""},
#     {"question":"How have you developed these skills over time?","type":"text","placeholder":"Examples:Formal education,Self-taught,Mentorship,On-the-job experience"},
#     {"question":"Can you provide examples of how you apply these skills in your personal or professional life?", "type":"text","placeholder":""},
#     {"question":"What skills do you find most useful in social interactions?","type":"text","placeholder":"Examples: Active listening, Empathy, Clear communication, Persuasiveness, Conflict resolution"},
# ]

personal_info_questions_phase_3 = [
    {
        "question": "How satisfied are you with your overall quality of life right now?",
        "type": "group",
        "inputs": [
            {
                "type": "range",
                "min": 1,
                "max": 100,
                "step": 1,
                "name": "quality_of_life_score"
            },
            {
                "type": "text",
                "placeholder": "If this is an important topic related to your mental issue, please write more (optional).",
                "name": "quality_of_life_comments"
            }
        ]
    },
    {
        "question": "To what extent do you feel your life is meaningful and fulfilling?",
        "type": "group",
        "inputs": [
            {
                "type": "range",
                "min": 1,
                "max": 100,
                "step": 1,
                "name": "life_meaning_score"
            },
            {
                "type": "text",
                "placeholder": "If this is an important topic related to your mental issue, please write more (optional).",
                "name": "life_meaning_comments"
            }
        ]
    },
    {
        "question": "How satisfied are you with your current level of physical health and well-being?",
        "type": "group",
        "inputs": [
            {
                "type": "range",
                "min": 1,
                "max": 100,
                "step": 1,
                "name": "physical_health_score"
            },
            {
                "type": "text",
                "placeholder": "If this is an important topic related to your mental issue, please write more (optional).",
                "name": "physical_health_comments"
            }
        ]
    },
    {
        "question": "To what extent do you feel your mental health impacts your overall life satisfaction?",
        "type": "group",
        "inputs": [
            {
                "type": "range",
                "min": 1,
                "max": 100,
                "step": 1,
                "name": "mental_health_impact_score"
            },
            {
                "type": "text",
                "placeholder": "If this is an important topic related to your mental issue, please write more (optional).",
                "name": "mental_health_impact_comments"
            }
        ]
    },
    {
        "question": "How much enjoyment do you get from the activities and hobbies you engage in?",
        "type": "group",
        "inputs": [
            {
                "type": "range",
                "min": 1,
                "max": 100,
                "step": 1,
                "name": "activities_enjoyment_score"
            },
            {
                "type": "text",
                "placeholder": "If this is an important topic related to your mental issue, please write more (optional).",
                "name": "activities_enjoyment_comments"
            }
        ]
    }
]


personal_info_questions_phase_2 = [
{
    "question": "How satisfied are you with the quality of your relationships with family and friends?",
    "type": "group",
    "inputs": [
        {
            "type": "range",
            "min": 1,
            "max": 100,
            "step": 1,
            "name": "relationship_quality_score"
        },
        {
            "type": "text",
            "placeholder": "If this is an important topic related to your mental issue, please write more (optional).",
            "name": "relationship_quality_comments"
        }
    ]
},
{
    "question": "To what extent do you feel supported by those close to you?",
    "type": "group",
    "inputs": [
        {
            "type": "range",
            "min": 1,
            "max": 100,
            "step": 1,
            "name": "support_level_score"
        },
        {
            "type": "text",
            "placeholder": "If this is an important topic related to your mental issue, please write more (optional).",
            "name": "support_level_comments"
        }
    ]
},
{
    "question": "How much conflict or tension do you experience in your close relationships?",
    "type": "group",
    "inputs": [
        {
            "type": "range",
            "min": 1,
            "max": 100,
            "step": 1,
            "name": "relationship_conflict_score"
        },
        {
            "type": "text",
            "placeholder": "If this is an important topic related to your mental issue, please write more (optional).",
            "name": "relationship_conflict_comments"
        }
    ]
},
{
    "question": "How well do you feel you can communicate your needs and feelings to those around you?",
    "type": "group",
    "inputs": [
        {
            "type": "range",
            "min": 1,
            "max": 100,
            "step": 1,
            "name": "communication_score"
        },
        {
            "type": "text",
            "placeholder": "If this is an important topic related to your mental issue, please write more (optional).",
            "name": "communication_comments"
        }
    ]
},
{
    "question": "To what degree do your relationships provide you with a sense of belonging and connection?",
    "type": "group",
    "inputs": [
        {
            "type": "range",
            "min": 1,
            "max": 100,
            "step": 1,
            "name": "belonging_score"
        },
        {
            "type": "text",
            "placeholder": "If this is an important topic related to your mental issue, please write more (optional).",
            "name": "belonging_comments"
        }
    ]
},
{
    "question": "How much are legal or financial issues causing you stress right now?",
    "type": "group",
    "inputs": [
        {
            "type": "range",
            "min": 1,
            "max": 100,
            "step": 1,
            "name": "legal_financial_stress_score"
        },
        {
            "type": "text",
            "placeholder": "If this is an important topic related to your mental issue, please write more (optional).",
            "name": "legal_financial_stress_comments"
        }
    ]
},
{
    "question": "To what extent do financial concerns affect your ability to focus on other areas of your life?",
    "type": "group",
    "inputs": [
        {
            "type": "range",
            "min": 1,
            "max": 100,
            "step": 1,
            "name": "financial_concerns_score"
        },
        {
            "type": "text",
            "placeholder": "If this is an important topic related to your mental issue, please write more (optional).",
            "name": "financial_concerns_comments"
        }
    ]
},
{
    "question": "How well do you feel you are managing your current legal or financial issues?",
    "type": "group",
    "inputs": [
        {
            "type": "range",
            "min": 1,
            "max": 100,
            "step": 1,
            "name": "management_score"
        },
        {
            "type": "text",
            "placeholder": "If this is an important topic related to your mental issue, please write more (optional).",
            "name": "management_comments"
        }
    ]
},
{
    "question": "To what degree do you feel supported by others in dealing with your legal or financial problems?",
    "type": "group",
    "inputs": [
        {
            "type": "range",
            "min": 1,
            "max": 100,
            "step": 1,
            "name": "support_score"
        },
        {
            "type": "text",
            "placeholder": "If this is an important topic related to your mental issue, please write more (optional).",
            "name": "support_comments"
        }
    ]
},
{
    "question": "How often do you worry about your financial or legal future?",
    "type": "group",
    "inputs": [
        {
            "type": "range",
            "min": 1,
            "max": 100,
            "step": 1,
            "name": "worry_frequency_score"
        },
        {
            "type": "text",
            "placeholder": "If this is an important topic related to your mental issue, please write more (optional).",
            "name": "worry_frequency_comments"
        }
    ]
},
{
    "question": "How satisfied are you with your current eating habits?",
    "type": "group",
    "inputs": [
        {
            "type": "range",
            "min": 1,
            "max": 100,
            "step": 1,
            "name": "eating_habits_score"
        },
        {
            "type": "text",
            "placeholder": "If this is an important topic related to your mental issue, please write more (optional).",
            "name": "eating_habits_comments"
        }
    ]
},
{
    "question": "To what extent do you believe your diet affects your mental health?",
    "type": "group",
    "inputs": [
        {
            "type": "range",
            "min": 1,
            "max": 100,
            "step": 1,
            "name": "diet_effect_score"
        },
        {
            "type": "text",
            "placeholder": "If this is an important topic related to your mental issue, please write more (optional).",
            "name": "diet_effect_comments"
        }
    ]
},
{
    "question": "How often do you engage in disordered eating behaviors (e.g., overeating, restricting food)?",
    "type": "group",
    "inputs": [
        {
            "type": "range",
            "min": 1,
            "max": 100,
            "step": 1,
            "name": "disordered_eating_score"
        },
        {
            "type": "text",
            "placeholder": "If this is an important topic related to your mental issue, please write more (optional).",
            "name": "disordered_eating_comments"
        }
    ]
},
{
    "question": "To what degree do you feel knowledgeable about nutrition and its impact on your health?",
    "type": "group",
    "inputs": [
        {
            "type": "range",
            "min": 1,
            "max": 100,
            "step": 1,
            "name": "nutrition_knowledge_score"
        },
        {
            "type": "text",
            "placeholder": "If this is an important topic related to your mental issue, please write more (optional).",
            "name": "nutrition_knowledge_comments"
        }
    ]
},
{
    "question": "How much control do you feel you have over your eating habits?",
    "type": "group",
    "inputs": [
        {
            "type": "range",
            "min": 1,
            "max": 100,
            "step": 1,
            "name": "eating_control_score"
        },
        {
            "type": "text",
            "placeholder": "If this is an important topic related to your mental issue, please write more (optional).",
            "name": "eating_control_comments"
        }
    ]
},
{
    "question": "How much do physical health issues (e.g., chronic illness, pain) impact your daily mental well-being?",
    "type": "group",
    "inputs": [
        {
            "type": "range",
            "min": 1,
            "max": 100,
            "step": 1,
            "name": "physical_health_impact_score"
        },
        {
            "type": "text",
            "placeholder": "If this is an important topic related to your mental issue, please write more (optional).",
            "name": "physical_health_impact_comments"
        }
    ]
},
{
    "question": "To what extent do sleep disturbances (e.g., insomnia, poor sleep quality) affect your mood and energy levels?",
    "type": "group",
    "inputs": [
        {
            "type": "range",
            "min": 1,
            "max": 100,
            "step": 1,
            "name": "sleep_impact_score"
        },
        {
            "type": "text",
            "placeholder": "If this is an important topic related to your mental issue, please write more (optional).",
            "name": "sleep_impact_comments"
        }
    ]
},
{
    "question": "How well do you feel you manage the side effects of any medications you are currently taking?",
    "type": "group",
    "inputs": [
        {
            "type": "range",
            "min": 1,
            "max": 100,
            "step": 1,
            "name": "medication_management_score"
        },
        {
            "type": "text",
            "placeholder": "If this is an important topic related to your mental issue, please write more (optional).",
            "name": "medication_management_comments"
        }
    ]
},
{
    "question": "To what extent do you believe your physical health and mental health are interconnected?",
    "type": "group",
    "inputs": [
        {
            "type": "range",
            "min": 1,
            "max": 100,
            "step": 1,
            "name": "health_interconnection_score"
        },
        {
            "type": "text",
            "placeholder": "If this is an important topic related to your mental issue, please write more (optional).",
            "name": "health_interconnection_comments"
        }
    ]
},
{
    "question": "How often do you engage in activities that promote your physical health (e.g., exercise, healthy eating)?",
    "type": "group",
    "inputs": [
        {
            "type": "range",
            "min": 1,
            "max": 100,
            "step": 1,
            "name": "physical_health_activity_score"
        },
        {
            "type": "text",
            "placeholder": "If this is an important topic related to your mental issue, please write more (optional).",
            "name": "physical_health_activity_comments"
        }
    ]
},
{
    "question": "How well do you feel you are performing in your academic or occupational role?",
    "type": "group",
    "inputs": [
        {
            "type": "range",
            "min": 1,
            "max": 100,
            "step": 1,
            "name": "performance_score"
        },
        {
            "type": "text",
            "placeholder": "If this is an important topic related to your mental issue, please write more (optional).",
            "name": "performance_comments"
        }
    ]
},
{
    "question": "To what extent do stress or mental health issues interfere with your academic or occupational functioning?",
    "type": "group",
    "inputs": [
        {
            "type": "range",
            "min": 1,
            "max": 100,
            "step": 1,
            "name": "interference_score"
        },
        {
            "type": "text",
            "placeholder": "If this is an important topic related to your mental issue, please write more (optional).",
            "name": "interference_comments"
        }
    ]
},
{
    "question": "How satisfied are you with your current academic or occupational achievements?",
    "type": "group",
    "inputs": [
        {
            "type": "range",
            "min": 1,
            "max": 100,
            "step": 1,
            "name": "achievement_satisfaction_score"
        },
        {
            "type": "text",
            "placeholder": "If this is an important topic related to your mental issue, please write more (optional).",
            "name": "achievement_satisfaction_comments"
        }
    ]
},
{
    "question": "How much support do you feel you have in your academic or occupational environment?",
    "type": "group",
    "inputs": [
        {
            "type": "range",
            "min": 1,
            "max": 100,
            "step": 1,
            "name": "support_environment_score"
        },
        {
            "type": "text",
            "placeholder": "If this is an important topic related to your mental issue, please write more (optional).",
            "name": "support_environment_comments"
        }
    ]
},
{
    "question": "To what degree do you feel your mental health affects your ability to progress in your academic or occupational goals?",
    "type": "group",
    "inputs": [
        {
            "type": "range",
            "min": 1,
            "max": 100,
            "step": 1,
            "name": "progress_impact_score"
        },
        {
            "type": "text",
            "placeholder": "If this is an important topic related to your mental issue, please write more (optional).",
            "name": "progress_impact_comments"
        }
    ]
}







]