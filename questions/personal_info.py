import pycountry

personal_info_questions_phase_1 = [
    {
      "topic": "Background",
      "questions": [
        {
          "question":"What is your age?",
          "info_type": "age",
          "type":"number",
          "placeholder":""
        },
        {
          "question":"What is your gender?",
          "info_type": "gender",
          "type":"select",
          "options":["Male", "Female", "Other"],
          "placeholder":""
        },
        {
          "question": "What is your nationality?",
          "info_type": "nationality",
          "type": "select",
          "options": [country.name for country in pycountry.countries],
          "placeholder": "Select your nationality"
        },
        {
          "question": "What is your current country of residence?",
          "info_type": "country of residence",
          "type": "select",
          "options": [country.name for country in pycountry.countries],
          "placeholder": "Select your current country of residence"
        },
        {
          "question":"What is your marital/relationship status?",
          "info_type": "marital status",
          "type":"select",
          "options":["Single","Married","Divorced","Other"],
          "placeholder":""
        },
			  {
          "question":"What is your education level?",
          "info_type": "education level",
          "type":"select",
          "options":["High School","Bachelor's, Master's","Other"],
          "placeholder":""
			  },
		    {
		      "question":"What is your employment status?",
		      "info_type": "employment status",
		      "type":"select",
		      "options":["Employed","Unemployed","Retired","Other"],
		      "placeholder":""
	      },
      ]
    },
    {
      "topic": "Developmental History",
      "questions": [
        {
          "question": "To what extent do you believe your early childhood experiences influence your current mental health?",
          "info_type": "extent of belief in the influence of early childhood experiences on current mental health",
          "type": "group",
        },
        {
          "question": "How often do you reflect on your childhood when thinking about your current mental health challenges?",
          "info_type": "frequency of reflecting childhood when thinking about current mental health challenges",
          "type": "group",
        },
        {
          "question": "To what degree do you feel your developmental milestones were met in a typical or healthy way?",
          "info_type": "extent of belief that developmental milestones were met in a typical or healthy way",
          "type": "group",
        },
        {
          "question": "To what extent do you believe unresolved issues from your childhood affect your relationships today?",
          "info_type": "extent of belief that unresolved issues from childhood affect relationships today",
          "type": "group",
        },
        {
          "question": "How often do memories of your childhood evoke strong emotions in you today?",
          "info_type": "frequency of memories of childhood evoking strong emotions today",
          "type": "group",
        },
      ]
    },
    {
      "topic": "Motivation and Readiness for Change",
      "questions": [
        {
          "question": "How motivated are you to make changes in your life to improve your mental health?",
          "info_type": "extent of feeling motivated to make changes in life to improve mental health",
          "type": "group",
        },
        {
          "question": "To what extent do you believe you have the ability to make the changes necessary for your well-being?",
          "info_type": "extent of belief in having the ability to make the changes necessary for well-being",
          "type": "group",
        },
        {
          "question": "How ready do you feel to engage fully in therapy and the work it requires?",
          "info_type": "extent of readiness to engage fully in therapy and the work it requires",
          "type": "group",
        },
        {
          "question": "How much do you believe that change is possible for you at this time?",
          "info_type": "extent of belief that change is possible at this time",
          "type": "group",
        },
        {
          "question": "To what degree do you feel supported by others in your efforts to make changes?",
          "info_type": "extent of feeling supported by others in efforts to make changes",
          "type": "group",
        },
      ]
    },
    {
      "topic": "Substance Use (Drugs and Alcohol)",
      "questions": [
        {
          "question": "How frequently do you use substances (e.g., drugs, alcohol) to cope with stress or emotions?",
          "info_type": "frequency of using substances (e.g., drugs, alcohol) to cope with stress or emotions",
          "type": "group",
        },
        {
          "question": "To what extent do you feel your substance use affects your mental health?",
          "info_type": "extent of belief in affection of substance use on mental health",
          "type": "group",
        },
        {
          "question": "How much control do you feel you have over your substance use?",
          "info_type": "extent of control over substance use",
          "type": "group",
        },
        {
          "question": "How often do you worry about the impact of your substance use on your overall health?",
          "info_type": "frequency of worrying about the impact of substance use on overall health",
          "type": "group",
        },
        {
          "question": "To what degree do you believe you could reduce or stop your substance use if you wanted to?",
          "info_type": "extent of belief in ability to reduce or stop substance use if wanted to ",
          "type": "group",
        },
      ]
    },
    {
      "topic": "Current Life Stressors",
      "questions": [
        {
          "question": "How much are current financial difficulties impacting your mental health?",
          "info_type": "extent of impact of current financial difficulties on mental health",
          "type": "group",
        },
        {
          "question": "To what extent do work pressures or responsibilities contribute to your stress levels?",
          "info_type": "extent of contribution of work pressures or responsibilities to stress levels",
          "type": "group",
        },
        {
          "question": "How much do family responsibilities (e.g., caregiving, parenting) contribute to your current stress?",
          "info_type": "extent of contribution of family responsibilities to  current stress",
          "type": "group",
        },
        {
          "question": "To what extent are major life changes (e.g., moving, divorce, job loss) affecting your mental well-being?",
          "info_type": "extent of affection of major life changes (e.g., moving, divorce, job loss) on mental well-being",
          "type": "group",
        },
        {
          "question": "How often do you feel overwhelmed by the stressors in your life?",
          "info_type": "frequency of feeling overwhelmed by the stressors in life",
          "type": "group",
        },
      ]
    },
    {
      "topic": "Trauma and Past Experiences",
      "questions": [
        {
          "question": "How much do past traumatic experiences influence your current mental health?",
          "info_type": "extent of influence of past traumatic experiences on current mental health",
          "type": "group",
        },
        {
          "question": "To what extent do you feel you have processed and healed from past traumas?",
          "info_type": "extent of feeling that being healed from past traumas",
          "type": "group",
        },
        {
          "question": "How often do memories of past traumatic events disrupt your daily life?",
          "info_type": "frequency that memories of past traumatic events disrupt daily life",
          "type": "group",
        },
        {
          "question": "To what degree do you avoid situations or people that remind you of past traumas?",
          "info_type": "degree of avoiding situations or people that remind past traumas",
          "type": "group",
        },
        {
          "question": "How much support have you received in addressing your past experiences?",
          "info_type": "degree of support received in addressing past experiences",
          "type": "group",
        },
      ]
    },
    {
      "topic": "Cognitive and Emotional Patterns",
      "questions": [
        {
          "question": "How frequently do you experience negative or self-critical thoughts?",
          "info_type": "frequency of experiencing negative or self-critical thoughts",
          "type": "group",
        },
        {
          "question": "To what extent do you struggle with perfectionism in your daily life?",
          "info_type": "extent of struggling with perfectionism in daily life",
          "type": "group",
        },
        {
          "question": "How often do you find yourself ruminating on past events or worries?",
          "info_type": "frequency of ruminating on past events or worries",
          "type": "group",
        },
        {
          "question": "How well do you feel you manage intense emotions when they arise?",
          "info_type": "degree of ability to manage intense emotions when they arise",
          "type": "group",
        },
        {
          "question": "To what extent do your emotions feel stable and manageable throughout the day?",
          "info_type": "degree of feeling stable and manageable throughout the day",
          "type": "group",
	      },
      ]
    },
    {
      "topic": "Cultural Background and Influences",
      "questions": [
        {
          "question": "How much does your cultural background influence your view on mental health?",
          "info_type": "degree of influence of cultural background on view on mental health",
          "type": "group",
        },
        {
          "question": "To what extent do you feel your cultural background impacts your willingness to seek help for mental health issues?",
          "info_type": "degree of impact of cultural background on willingness to seek help for mental health issues",
          "type": "group",
        },
        {
          "question": "How aligned do you feel your cultural values are with the mental health treatment you are receiving or considering?",
          "info_type": "degree of alignment of cultural values with the mental health treatment receiving or considering",
          "type": "group",
        },
        {
          "question": "To what degree do you feel understood and respected by mental health professionals regarding your cultural background?",
          "info_type": "degree of feeling understood and respected by mental health professionals regarding cultural background",
          "type": "group",
        },
			  {
          "question": "How much do you feel your cultural background has equipped you with effective coping strategies for dealing with stress?",
          "info_type": "degree of effective coping strategies for dealing with stress being equipped by cultural background",
          "type": "group",
        },
      ]
    },
    {
      "topic": "Sleep and Rest Patterns",
      "questions": [
			{
        "question": "How satisfied are you with the quality of your sleep on a regular basis?",
        "info_type": "degree of satisfaction with the quality of sleep on a regular basis",
        "type": "group",
      },
			{
        "question": "To what extent do you struggle with falling asleep or staying asleep?",
        "info_type": "degree of struggling with with falling asleep or staying asleep",
        "type": "group",
      },
			{
        "question": "How often do you wake up feeling rested and refreshed?",
        "info_type": "frequency of waking up feeling rested and refreshed",
        "type": "group",
      },
			{
        "question": "How much do sleep disturbances affect your mood and ability to function during the day?",
        "info_type": "degree of affection of sleep disturbances on mood and ability to function during the day",
         "type": "group",
      },
			{
        "question": "To what degree do you use sleep aids or other methods to help you sleep?",
        "info_type": "degree of using sleep aids or other methods to help sleep",
        "type": "group",
      },
    ]
  }
]

personal_info_questions_phase_3 = [
  {
    "topic": "Life Satisfaction and Quality of Life",
    "questions": [
      {
        "question": "How satisfied are you with your overall quality of life right now?",
				"info_type": "satisfaction with overall quality of life",
        "type": "group",
    	},
    	{
        "question": "To what extent do you feel your life is meaningful and fulfilling?",
        "info_type": "extent of feeling life is meaningful and fulfilling",
        "type": "group",
    	},
    	{
        "question": "How satisfied are you with your current level of physical health and well-being?",
        "info_type": "satisfaction with current level of physical health and well-being",
        "type": "group",
    	},
    	{
        "question": "To what extent do you feel your mental health impacts your overall life satisfaction?",
        "info_type": "extent of feeling mental health impacts overall life satisfaction",
        "type": "group",
    	},
    	{
      	"question": "How much enjoyment do you get from the activities and hobbies you engage in?",
      	"info_type": "enjoyment from activities and hobbies",
      	"type": "group",
    	},
		],
	},
]

personal_info_questions_phase_2 = [
	{
    "topic": "Social and Interpersonal Relationships",
    "questions": [
      {
      	"question":"How satisfied are you with the quality of your relationships with family and friends?",
    		"info_type": "quality of your relationships with family and friends",
        "type": "group",
			},
      {
        "question": "To what extent do you feel supported by those close to you?",
        "info_type": "extent of feeling supported by those close to you",
        "type": "group",
			},
      {
        "question": "How much conflict or tension do you experience in your close relationships?",
        "info_type": "conflict or tension experiencing in your close relationships",
        "type": "group",
			},
      {
        "question": "How well do you feel you can communicate your needs and feelings to those around you?",
        "info_type": "Extent of feeling you can communicate your needs and feelings to those around you",
        "type": "group",
			},
  	  {
    		"question": "To what degree do your relationships provide you with a sense of belonging and connection?",
        "info_type": "degree of relationships providing you with a sense of belonging and connection",
    	  "type": "group",
      },
    ]
  },
  {
    "topic": "Legal or Financial Issues",
    "questions": [
      {
      	"question": "How much are legal or financial issues causing you stress right now?",
      	"info_type": "extent of legal or financial issues causing stress",
      	"type": "group",
			},
      {
        "question": "To what extent do financial concerns affect your ability to focus on other areas of your life?",
        "info_type": "extent of financial concerns affecting ability to focus on other areas of life",
    		"type": "group",
			},
      {
    		"question": "How well do you feel you are managing your current legal or financial issues?",
				"info_type": "extent of feeling managing current legal or financial issues",
    		"type": "group",

			},
      {
    		"question": "To what degree do you feel supported by others in dealing with your legal or financial problems?",
				"info_type": "degree of feeling supported by others in dealing with legal or financial problems",
    		"type": "group",
			},
      {
    		"question": "How often do you worry about your financial or legal future?",
				"info_type": "frequency of worrying about financial or legal future",
    		"type": "group",
			},
    ],
	},
  {
    "topic": "Diet and Nutrition",
    "questions": [
      {
				"question": "How satisfied are you with your current eating habits?",
				"info_type": "satisfaction with current eating habits",
				"type": "group",
			},
      {
        "question": "To what extent do you believe your diet affects your mental health?",
        "info_type": "extent of belief that diet affects mental health",
        "type": "group",
			},
      {
        "question": "How often do you engage in disordered eating behaviors (e.g., overeating, restricting food)?",
        "info_type": "frequency of disordered eating behaviors",
        "type": "group",
			},
      {
        "question": "To what degree do you feel knowledgeable about nutrition and its impact on your health?",
        "info_type": "degree of knowledge about nutrition and its impact on health",
        "type": "group",
			},
      {
        "question": "How much control do you feel you have over your eating habits?",
        "info_type": "extent of control over eating habits",
        "type": "group",
			},
		],
	},
  {
    "topic": "Physical Health and Well-being",
    "questions": [
			{
				"question": "How satisfied are you with your overall physical health at the moment?",
				"info_type": "satisfaction with overall physical health",
				"type": "group",
			},
      {
        "question": "How much do physical health issues (e.g., chronic illness, pain) impact your daily mental well-being?",
        "info_type": "impact of physical health issues on daily mental well-being",
        "type": "group",
			},
      {
        "question": "To what extent do sleep disturbances (e.g., insomnia, poor sleep quality) affect your mood and energy levels?",
        "info_type": "extent of sleep disturbances affecting mood and energy levels",
        "type": "group",
			},
      {
        "question": "How well do you feel you manage the side effects of any medications you are currently taking?",
        "info_type": "ability to manage side effects of medications",
        "type": "group",
			},
      {
        "question": "How well do you feel you manage the side effects of any medications you are currently taking?",
        "info_type": "ability to manage side effects of medications",
        "type": "group",
			},
      {
        "question": "To what extent do you believe your physical health and mental health are interconnected?",
        "info_type": "belief in the interconnectedness of physical and mental health",
        "type": "group",
			},
      {
        "question": "How often do you engage in activities that promote your physical health (e.g., exercise, healthy eating)?",
        "info_type": "frequency of engaging in activities promoting physical health",
        "type": "group",
			},
		],
	},
  {
    "topic": "Academic or Occupational Functioning",
    "questions": [
      {
        "question": "How well do you feel you are performing in your academic or occupational role?",
        "info_type": "performance in academic or occupational role",
        "type": "group",
			},
      {
        "question": "To what extent do stress or mental health issues interfere with your academic or occupational functioning?",
        "info_type": "interference of stress or mental health issues with academic or occupational functioning",
        "type": "group",
			},
			{
				"question": "How satisfied are you with your current academic or occupational achievements?",
				"info_type": "satisfaction with academic or occupational achievements",
        "type": "group",
			},
      {
        "question": "How much support do you feel you have in your academic or occupational environment?",
        "info_type": "support in academic or occupational environment",
        "type": "group",
			},
      {
        "question": "To what degree do you feel your mental health affects your ability to progress in your academic or occupational goals?",
        "info_type": "impact of mental health on academic or occupational goals",
        "type": "group",
			},
		],
	},
]