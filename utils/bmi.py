"""
utils/bmi.py
BMI calculation logic + yoga class suggestions + Asana Library data.
No external API is used — everything is pure Python.
"""


# ── BMI Calculation ──────────────────────────────────────────────────────────

def calculate_bmi(weight_kg: float, height_cm: float) -> tuple:
    """
    Returns (bmi_value: float, category: str).
    Categories: Underweight | Normal | Overweight | Obese
    """
    height_m = height_cm / 100.0
    bmi = round(weight_kg / (height_m ** 2), 1)

    if bmi < 18.5:
        category = 'Underweight'
    elif bmi < 25.0:
        category = 'Normal'
    elif bmi < 30.0:
        category = 'Overweight'
    else:
        category = 'Obese'

    return bmi, category


def get_bmi_advice(category: str) -> dict:
    """Return display advice dict for a BMI category."""
    advice_map = {
        'Underweight': {
            'color':     'info',
            'icon':      'bi-arrow-up-circle-fill',
            'headline':  'You are Underweight',
            'message':   'Focus on strength-building yoga styles to increase muscle mass and bone density.',
            'yoga_tip':  'Ashtanga Fundamentals and structured flows will help you build a stronger physique.',
        },
        'Normal': {
            'color':     'success',
            'icon':      'bi-check-circle-fill',
            'headline':  'Healthy Weight — Great!',
            'message':   'Your BMI is in the healthy range. Maintain it with a balanced yoga routine.',
            'yoga_tip':  'Morning Hatha Flow and Meditation & Pranayama are perfect for you.',
        },
        'Overweight': {
            'color':     'warning',
            'icon':      'bi-exclamation-circle-fill',
            'headline':  'Slightly Overweight',
            'message':   'Dynamic yoga styles can aid weight management and boost your metabolism.',
            'yoga_tip':  'Power Vinyasa sessions are highly effective for burning calories and toning.',
        },
        'Obese': {
            'color':     'danger',
            'icon':      'bi-heart-fill',
            'headline':  'Obese — Start Gently',
            'message':   'Begin your journey with low-impact, supportive yoga under instructor guidance.',
            'yoga_tip':  'Restorative Yoga and Pranayama are the safest and most beneficial starting point.',
        },
    }
    return advice_map.get(category, advice_map['Normal'])


# ── Asana Library ─────────────────────────────────────────────────────────────

ASANA_LIBRARY = [
    {
        'id': 1,
        'name': 'Tadasana',
        'english': 'Mountain Pose',
        'difficulty': 'Beginner',
        'duration': '30 – 60 sec',
        'icon': '🏔️',
        'benefits': [
            'Improves posture and body alignment',
            'Strengthens thighs, knees, and ankles',
            'Increases body awareness and focus',
            'Relieves mild sciatica pain',
        ],
        'precautions': [
            'Avoid with low blood pressure',
            'Modify if you have headaches or insomnia',
        ],
        'description': (
            'The foundational standing pose of yoga. Stand tall with feet together, '
            'arms at your sides, and weight distributed evenly. It is the starting '
            'point for all standing sequences.'
        ),
    },
    {
        'id': 2,
        'name': 'Balasana',
        'english': "Child's Pose",
        'difficulty': 'Beginner',
        'duration': '1 – 3 min',
        'icon': '🧘',
        'benefits': [
            'Gently stretches hips, thighs, and ankles',
            'Calms the nervous system and relieves stress',
            'Relieves back and neck tension',
            'Excellent resting pose between challenging asanas',
        ],
        'precautions': [
            'Avoid with knee injuries',
            'Not recommended during later stages of pregnancy',
            'Skip if you have diarrhea',
        ],
        'description': (
            'A restorative resting pose that gently opens the hips and lower back '
            'while calming the mind. An essential "reset" pose used throughout practice.'
        ),
    },
    {
        'id': 3,
        'name': 'Adho Mukha Svanasana',
        'english': 'Downward-Facing Dog',
        'difficulty': 'Beginner',
        'duration': '1 – 3 min',
        'icon': '🐕',
        'benefits': [
            'Builds strength in arms, shoulders, and core',
            'Lengthens hamstrings, calves, and spine',
            'Energises the body and mind',
            'Helps relieve mild depression and back pain',
        ],
        'precautions': [
            'Avoid with carpal tunnel syndrome',
            'High blood pressure — keep head lower than heart',
            'Late-term pregnancy — avoid',
        ],
        'description': (
            'The iconic inverted-V pose that simultaneously stretches and strengthens '
            'the whole body. A cornerstone of Sun Salutations and most vinyasa flows.'
        ),
    },
    {
        'id': 4,
        'name': 'Virabhadrasana I',
        'english': 'Warrior I',
        'difficulty': 'Intermediate',
        'duration': '30 – 60 sec / side',
        'icon': '⚔️',
        'benefits': [
            'Strengthens shoulders, arms, legs, and ankles',
            'Stretches chest, lungs, shoulders, and hip flexors',
            'Improves focus, balance, and stability',
            'Builds confidence and inner power',
        ],
        'precautions': [
            'High blood pressure — avoid raising arms overhead',
            'Shoulder or neck problems — look forward, not up',
            'Heart conditions — consult a doctor first',
        ],
        'description': (
            'A powerful standing pose named after the fierce warrior Virabhadra. '
            'Builds lower-body strength and opens the chest for better breathing.'
        ),
    },
    {
        'id': 5,
        'name': 'Trikonasana',
        'english': 'Triangle Pose',
        'difficulty': 'Intermediate',
        'duration': '30 sec / side',
        'icon': '📐',
        'benefits': [
            'Stretches legs, hips, groins, and hamstrings',
            'Strengthens thighs, knees, and ankles',
            'Stimulates digestion and abdominal organs',
            'Relieves stress, anxiety, and mild back pain',
        ],
        'precautions': [
            'Diarrhea or headache — avoid',
            'Heart condition — practice against a wall',
            'Low blood pressure — exit the pose slowly',
        ],
        'description': (
            'A standing lateral stretch that simultaneously opens the hips, chest, '
            'and shoulders while building strength in the legs and core.'
        ),
    },
    {
        'id': 6,
        'name': 'Setu Bandhasana',
        'english': 'Bridge Pose',
        'difficulty': 'Intermediate',
        'duration': '30 – 60 sec',
        'icon': '🌉',
        'benefits': [
            'Strengthens back muscles and spine',
            'Stretches chest, neck, and spine',
            'Calms the brain and reduces anxiety',
            'Improves digestion and relieves menstrual pain',
        ],
        'precautions': [
            'Avoid with neck injuries — never turn head',
            'Back injury — practice with caution and support',
            'Knee problems — keep feet parallel',
        ],
        'description': (
            'A backbend that lifts the hips and opens the chest. Excellent for '
            'strengthening the posterior chain and countering the effects of sitting.'
        ),
    },
    {
        'id': 7,
        'name': 'Sirsasana',
        'english': 'Headstand',
        'difficulty': 'Advanced',
        'duration': '1 – 5 min',
        'icon': '🤸',
        'benefits': [
            'Strengthens arms, shoulders, and spine',
            'Improves blood circulation to the brain',
            'Stimulates pituitary and pineal glands',
            'Builds exceptional mental focus and calmness',
        ],
        'precautions': [
            'Never practice without wall support as a beginner',
            'Avoid with back, neck, or head injuries',
            'High blood pressure or heart conditions — avoid',
            'During menstruation — avoid',
        ],
        'description': (
            'The "King of Asanas." A full inversion that develops upper-body strength '
            'and mental fortitude. Should only be learned under experienced guidance.'
        ),
    },
    {
        'id': 8,
        'name': 'Kapalbhati Pranayama',
        'english': 'Skull-Shining Breath',
        'difficulty': 'Beginner',
        'duration': '5 – 10 min',
        'icon': '💨',
        'benefits': [
            'Clears respiratory system and sinuses',
            'Improves metabolism and aids weight management',
            'Energises the mind and improves concentration',
            'Detoxifies the body with each forceful exhalation',
        ],
        'precautions': [
            'Avoid during pregnancy',
            'High blood pressure — practise very gently',
            'Heart problems — consult a doctor',
            'Avoid on a full stomach',
        ],
        'description': (
            'A powerful breathing technique involving rapid, forceful exhalations. '
            'One of the most effective pranayamas for energising and detoxifying the body.'
        ),
    },
    {
        'id': 9,
        'name': 'Shavasana',
        'english': 'Corpse Pose',
        'difficulty': 'Beginner',
        'duration': '5 – 15 min',
        'icon': '😴',
        'benefits': [
            'Deeply relaxes the entire body and nervous system',
            'Lowers blood pressure and heart rate',
            'Helps with insomnia, fatigue, and anxiety',
            'Integrates all benefits of the practice session',
        ],
        'precautions': [
            'Pregnancy — elevate head and chest slightly',
            'Back pain — place a bolster under the knees',
            'Use a blanket to stay warm',
        ],
        'description': (
            'The final relaxation pose. Deceptively simple yet considered one of the most '
            'challenging poses to truly master — the art of conscious stillness.'
        ),
    },
    {
        'id': 10,
        'name': 'Ustrasana',
        'english': 'Camel Pose',
        'difficulty': 'Advanced',
        'duration': '30 – 60 sec',
        'icon': '🐪',
        'benefits': [
            'Opens the chest and stretches the entire front body',
            'Strengthens back muscles and improves spinal flexibility',
            'Stimulates abdominal and thyroid organs',
            'Counteracts the effects of prolonged sitting',
        ],
        'precautions': [
            'Low blood pressure or migraines — avoid',
            'Neck or back injury — use a modified version',
            'Do not compress the lower back — engage the core',
        ],
        'description': (
            'A deep backbend that dramatically opens the chest and hip flexors. '
            'Requires a thorough warm-up and should be practiced with care.'
        ),
    },
    {
        'id': 11,
        'name': 'Natarajasana',
        'english': "Dancer's Pose",
        'difficulty': 'Advanced',
        'duration': '20 – 30 sec / side',
        'icon': '💃',
        'benefits': [
            'Develops exceptional balance and concentration',
            'Stretches shoulders, chest, thighs, and groin',
            'Strengthens legs, ankles, and core',
            'Builds grace, poise, and proprioception',
        ],
        'precautions': [
            'Low blood pressure or vertigo — avoid',
            'Ankle or back injuries — avoid',
            'Use a wall for balance support initially',
        ],
        'description': (
            'An elegant balancing pose named after the cosmic dancer Shiva. '
            'A beautiful blend of strength, flexibility, and balance in one posture.'
        ),
    },
    {
        'id': 12,
        'name': 'Anjaneyasana',
        'english': 'Low Lunge',
        'difficulty': 'Beginner',
        'duration': '30 – 60 sec / side',
        'icon': '🦵',
        'benefits': [
            'Deeply stretches hip flexors and groin',
            'Strengthens thighs, glutes, and core',
            'Opens the chest and improves shoulder mobility',
            'Excellent counter-pose for desk workers',
        ],
        'precautions': [
            'Knee injury — place a folded blanket under the knee',
            'High blood pressure — keep arms at sides',
            'Shoulder injury — keep hands on the hips',
        ],
        'description': (
            'A deep lunge that targets the hip flexors, often chronically tight from '
            'prolonged sitting. A staple in warm-up sequences and sun salutations.'
        ),
    },
]
