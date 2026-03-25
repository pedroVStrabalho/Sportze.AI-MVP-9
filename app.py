import streamlit as st
import random
import re
import difflib
import requests
from bs4 import BeautifulSoup
from datetime import date, datetime, timedelta

# =========================
# PAGE SETUP
# =========================
st.set_page_config(page_title="Sportze.AI", layout="wide")

st.title("Sportze.AI")
st.write("Generate smarter, more professional sport-specific training sessions.")

TODAY = datetime.today().date()

# =========================
# SESSION STATE
# =========================
if "active_section" not in st.session_state:
    st.session_state.active_section = "Training Generator"

# =========================
# CONSTANTS / OPTIONS
# =========================
SPORTS = [
    "Gym",
    "Running",
    "Tennis",
    "Baseball",
    "Rowing",
    "Weightlifting",
    "Water Polo",
    "Soccer",
    "Boxing",
    "Volleyball",
]

ROLES = ["Player", "Coach"]

COMMON_GOALS = [
    "Improve performance",
    "Build fitness",
    "Return after a break",
    "Learn how to play",
    "Have fun / stay active",
]

SKILL_LEVELS = ["Beginner", "Intermediate", "Advanced"]
INJURY_OPTIONS = ["No", "Yes - minor limitation", "Yes - recent injury"]

RUNNING_FOCUS_OPTIONS = [
    "Short distance",
    "Medium distance",
    "Long distance",
    "Ultra long distance",
    "Mixed event conditioning",
]

RUNNING_DISTANCE_MAP = {
    "Short distance": ["100m", "200m", "400m", "800m"],
    "Medium distance": ["1.2k", "1.5k", "3k", "5k", "10k"],
    "Long distance": ["15k", "Half marathon", "32k", "Marathon"],
    "Ultra long distance": ["50k", "160k"],
}

TIME_OPTIONS_GENERAL = [
    "30 minutes",
    "45 minutes",
    "60 minutes",
    "75 minutes",
    "90 minutes",
    "120 minutes",
]

TIME_OPTIONS_ENDURANCE = [
    "30 minutes",
    "45 minutes",
    "60 minutes",
    "75 minutes",
    "90 minutes",
    "120 minutes",
    "150 minutes",
    "180 minutes",
    "210 minutes",
    "240 minutes",
]

PHYSIO_BODY_AREAS = [
    "Knee",
    "Ankle / foot",
    "Hamstring",
    "Quad",
    "Hip / groin",
    "Lower back",
    "Shoulder",
    "Elbow / forearm",
    "Wrist / hand",
    "Neck",
    "Other",
]

SECTION_OPTIONS = [
    "Training Generator",
    "Video Review",
    "Counselling",
    "Physio",
]

SOCCER_POSITIONS = [
    "Goalkeeper",
    "Centre back",
    "Full back / wing back",
    "Defensive midfielder",
    "Central midfielder",
    "Attacking midfielder",
    "Winger",
    "Striker",
    "Mixed / multiple positions",
]

SOCCER_FOCUS_OPTIONS = [
    "General development",
    "Technical development",
    "Finishing",
    "First touch & passing",
    "1v1 attacking / defending",
    "Possession",
    "Build-up play",
    "Pressing & defending",
    "Transition",
    "Small-sided games",
    "Conditioning with the ball",
    "Set pieces",
]

SOCCER_AGE_BANDS = [
    "U8-U10",
    "U11-U13",
    "U14-U16",
    "U17-U19",
    "Senior",
]

SOCCER_COUNTRIES_BY_CONTINENT = {
    "Europe": [
        "England", "Spain", "Germany", "Italy", "France",
        "Portugal", "Netherlands", "Belgium", "Scotland",
        "Ireland", "Turkey", "Greece", "Croatia", "Poland",
    ],
    "South America": [
        "Brazil", "Argentina", "Uruguay", "Colombia", "Chile",
        "Paraguay", "Peru", "Ecuador", "Bolivia", "Venezuela",
    ],
    "North America": [
        "USA", "Canada", "Mexico", "Costa Rica",
    ],
    "Asia": [
        "Japan", "South Korea", "Saudi Arabia", "UAE", "Qatar",
    ],
    "Africa": [
        "Morocco", "Egypt", "South Africa", "Tunisia",
    ],
    "Oceania": [
        "Australia", "New Zealand",
    ],
}

# Conservative reference pools for soccer counselling
# Purpose: do not make unrealistic jumps; keep suggestions tier-aware
SOCCER_CLUB_POOLS = {
    "England": {
        "academy": ["Sunderland Academy", "Blackburn Rovers Academy", "Middlesbrough Academy"],
        "semi-pro": ["York City", "Oldham Athletic", "Southend United"],
        "second-tier": ["Preston North End", "Bristol City", "Millwall"],
        "top-tier": ["Brentford", "Bournemouth", "Brighton"],
    },
    "Spain": {
        "academy": ["Sporting Gijon B", "Zaragoza Academy", "Malaga Academy"],
        "semi-pro": ["Castellon", "Cordoba", "Cultural Leonesa"],
        "second-tier": ["Eibar", "Oviedo", "Tenerife"],
        "top-tier": ["Getafe", "Rayo Vallecano", "Osasuna"],
    },
    "Germany": {
        "academy": ["Nurnberg Academy", "Karlsruher SC Academy", "Hannover Academy"],
        "semi-pro": ["1860 Munich", "Saarbrucken", "Dynamo Dresden"],
        "second-tier": ["Paderborn", "Fortuna Dusseldorf", "Greuther Furth"],
        "top-tier": ["Augsburg", "Mainz", "Freiburg"],
    },
    "Italy": {
        "academy": ["Parma Primavera", "Brescia Academy", "Modena Academy"],
        "semi-pro": ["Cesena", "Padova", "Pescara"],
        "second-tier": ["Palermo", "Bari", "Modena"],
        "top-tier": ["Torino", "Udinese", "Bologna"],
    },
    "France": {
        "academy": ["Toulouse Academy", "Auxerre Academy", "Le Havre Academy"],
        "semi-pro": ["Red Star", "Nancy", "Versailles"],
        "second-tier": ["Caen", "Guingamp", "Amiens"],
        "top-tier": ["Nantes", "Reims", "Strasbourg"],
    },
    "Portugal": {
        "academy": ["Braga B", "Vitoria Guimaraes B", "Famalicao U23"],
        "semi-pro": ["Leiria", "Academico Viseu", "Oliveirense"],
        "second-tier": ["Tondela", "Maritimo", "Penafiel"],
        "top-tier": ["Casa Pia", "Rio Ave", "Estoril"],
    },
    "Netherlands": {
        "academy": ["Heerenveen Academy", "Groningen Academy", "Utrecht Academy"],
        "semi-pro": ["ADO Den Haag", "FC Eindhoven", "MVV Maastricht"],
        "second-tier": ["Cambuur", "De Graafschap", "Roda JC"],
        "top-tier": ["NEC Nijmegen", "Go Ahead Eagles", "Sparta Rotterdam"],
    },
    "Belgium": {
        "academy": ["Genk Academy", "Standard Liege Academy", "Gent Academy"],
        "semi-pro": ["Lierse", "RFC Liege", "Patro Eisden"],
        "second-tier": ["Zulte Waregem", "Beerschot", "Lommel"],
        "top-tier": ["Mechelen", "Charleroi", "Cercle Brugge"],
    },
    "Scotland": {
        "academy": ["Hibernian Academy", "Dundee United Academy", "Aberdeen Academy"],
        "semi-pro": ["Falkirk", "Partick Thistle", "Raith Rovers"],
        "second-tier": ["Inverness", "Dunfermline", "Greenock Morton"],
        "top-tier": ["Motherwell", "St Mirren", "Kilmarnock"],
    },
    "Ireland": {
        "academy": ["Shamrock Rovers Academy", "St Patrick's Athletic Academy", "Bohemians Academy"],
        "semi-pro": ["Galway United", "Finn Harps", "Treaty United"],
        "second-tier": ["Cork City", "Athlone Town", "Bray Wanderers"],
        "top-tier": ["Derry City", "Sligo Rovers", "Shelbourne"],
    },
    "Brazil": {
        "academy": ["Athletico Paranaense U20", "Coritiba Academy", "America Mineiro Academy"],
        "semi-pro": ["Brusque", "Ypiranga", "Figueirense"],
        "second-tier": ["CRB", "Operario", "Avai"],
        "top-tier": ["Fortaleza", "Bragantino", "Athletico Paranaense"],
    },
    "Argentina": {
        "academy": ["Talleres Academy", "Belgrano Academy", "Lanus Academy"],
        "semi-pro": ["Chacarita Juniors", "Temperley", "Almagro"],
        "second-tier": ["Quilmes", "San Martin Tucuman", "Defensores de Belgrano"],
        "top-tier": ["Banfield", "Huracan", "Talleres"],
    },
    "Uruguay": {
        "academy": ["Defensor Sporting Academy", "Danubio Academy", "Liverpool Montevideo Academy"],
        "semi-pro": ["Atenas", "Albion", "Sud America"],
        "second-tier": ["Racing Montevideo", "Oriental", "Cerrito"],
        "top-tier": ["Defensor Sporting", "Liverpool Montevideo", "Wanderers"],
    },
    "USA": {
        "academy": ["FC Dallas Academy", "Philadelphia Union II", "NY Red Bulls II"],
        "semi-pro": ["Richmond Kickers", "Greenville Triumph", "Northern Colorado"],
        "second-tier": ["Charleston Battery", "Louisville City", "Tampa Bay Rowdies"],
        "top-tier": ["Real Salt Lake", "FC Dallas", "Philadelphia Union"],
    },
    "Mexico": {
        "academy": ["Pachuca Academy", "Santos Laguna Academy", "Toluca Academy"],
        "semi-pro": ["Atlante", "Celaya", "Alebrijes Oaxaca"],
        "second-tier": ["Leones Negros", "Mineros", "Venados"],
        "top-tier": ["Pachuca", "Toluca", "Santos Laguna"],
    },
    "Japan": {
        "academy": ["Gamba Osaka Academy", "Cerezo Osaka Academy", "Kashiwa Reysol Academy"],
        "semi-pro": ["Kataller Toyama", "FC Imabari", "Vanraure Hachinohe"],
        "second-tier": ["JEF United", "Montedio Yamagata", "Omiya Ardija"],
        "top-tier": ["Sagan Tosu", "Avispa Fukuoka", "Kashiwa Reysol"],
    },
    "Australia": {
        "academy": ["Sydney FC Academy", "Melbourne City Academy", "Western Sydney Academy"],
        "semi-pro": ["South Melbourne", "Marconi Stallions", "APIA Leichhardt"],
        "second-tier": ["Brisbane Roar NPL pathway", "Adelaide United NPL pathway", "Perth Glory pathway"],
        "top-tier": ["Central Coast Mariners", "Wellington Phoenix", "Western Sydney Wanderers"],
    },
}

# =========================
# TENNIS COUNSELLING DATA
# =========================
UPCOMING_TOURNAMENTS = [
    {
        "name": "Fayez Sarofim & Co. U.S. Men's Clay Court Championship",
        "tour": "ATP Tour",
        "level": "ATP 250",
        "city": "Houston",
        "country": "USA",
        "region": "North America",
        "surface": "Clay",
        "start_date": date(2026, 3, 29),
        "estimated_direct_acceptance_best_fit": (1, 120),
        "estimated_qualifying_fit": (100, 220),
        "notes": "High-level option; better for established ATP players who already travel on ATP schedule.",
    },
    {
        "name": "Tiriac Open",
        "tour": "ATP Tour",
        "level": "ATP 250",
        "city": "Bucharest",
        "country": "Romania",
        "region": "Europe",
        "surface": "Clay",
        "start_date": date(2026, 3, 29),
        "estimated_direct_acceptance_best_fit": (1, 120),
        "estimated_qualifying_fit": (100, 220),
        "notes": "Clay ATP 250. Good if player level is already close to ATP Tour / upper Challenger level.",
    },
    {
        "name": "Grand Prix Hassan II",
        "tour": "ATP Tour",
        "level": "ATP 250",
        "city": "Marrakech",
        "country": "Morocco",
        "region": "Africa / Europe travel corridor",
        "surface": "Clay",
        "start_date": date(2026, 3, 29),
        "estimated_direct_acceptance_best_fit": (1, 120),
        "estimated_qualifying_fit": (100, 220),
        "notes": "Clay ATP 250. Usually better for stronger clay-court profiles.",
    },
    {
        "name": "Sao Paulo Challenger",
        "tour": "ATP Challenger Tour",
        "level": "Challenger",
        "city": "Sao Paulo",
        "country": "Brazil",
        "region": "South America",
        "surface": "Clay",
        "start_date": date(2026, 3, 23),
        "estimated_direct_acceptance_best_fit": (80, 260),
        "estimated_qualifying_fit": (220, 420),
        "notes": "Very logical option for Brazilian or South American clay-court players.",
    },
    {
        "name": "Morelia Open",
        "tour": "ATP Challenger Tour",
        "level": "Challenger",
        "city": "Morelia",
        "country": "Mexico",
        "region": "North America",
        "surface": "Hard",
        "start_date": date(2026, 3, 23),
        "estimated_direct_acceptance_best_fit": (90, 260),
        "estimated_qualifying_fit": (220, 420),
        "notes": "Better for hard-court players already above typical ITF range.",
    },
    {
        "name": "Split Open",
        "tour": "ATP Challenger Tour",
        "level": "Challenger",
        "city": "Split",
        "country": "Croatia",
        "region": "Europe",
        "surface": "Clay",
        "start_date": date(2026, 3, 23),
        "estimated_direct_acceptance_best_fit": (90, 260),
        "estimated_qualifying_fit": (220, 420),
        "notes": "European clay option, best for players already at strong Challenger standard.",
    },
    {
        "name": "III Challenger Montemar ENE Construccion",
        "tour": "ATP Challenger Tour",
        "level": "Challenger",
        "city": "Alicante",
        "country": "Spain",
        "region": "Europe",
        "surface": "Clay",
        "start_date": date(2026, 3, 23),
        "estimated_direct_acceptance_best_fit": (90, 260),
        "estimated_qualifying_fit": (220, 420),
        "notes": "Spanish clay option, good for clay specialists with Challenger level.",
    },
    {
        "name": "Bucaramanga Challenger",
        "tour": "ATP Challenger Tour",
        "level": "Challenger",
        "city": "Bucaramanga",
        "country": "Colombia",
        "region": "South America",
        "surface": "Clay",
        "start_date": date(2026, 3, 23),
        "estimated_direct_acceptance_best_fit": (90, 260),
        "estimated_qualifying_fit": (220, 420),
        "notes": "South American clay route. Strong fit for players already established above ITF level.",
    },
    {
        "name": "Yokkaichi Challenger",
        "tour": "ATP Challenger Tour",
        "level": "Challenger",
        "city": "Yokkaichi",
        "country": "Japan",
        "region": "Asia",
        "surface": "Hard",
        "start_date": date(2026, 3, 23),
        "estimated_direct_acceptance_best_fit": (90, 260),
        "estimated_qualifying_fit": (220, 420),
        "notes": "Hard-court Challenger option. Better only if the player is strong enough and travel makes sense.",
    },
    {
        "name": "M15 Punta del Este",
        "tour": "ITF Men's World Tennis Tour",
        "level": "M15",
        "city": "Punta del Este",
        "country": "Uruguay",
        "region": "South America",
        "surface": "Clay",
        "start_date": date(2026, 3, 23),
        "estimated_direct_acceptance_best_fit": (250, 900),
        "estimated_qualifying_fit": (700, 1800),
        "notes": "Entry-level pro event. Good for lower-ranked players building points on clay.",
        "entry_deadline": "Thu 5 Mar 2026, 14:00 GMT",
        "withdrawal_deadline": "Tue 10 Mar 2026, 14:00 GMT",
    },
    {
        "name": "M15 Altamura",
        "tour": "ITF Men's World Tennis Tour",
        "level": "M15",
        "city": "Altamura",
        "country": "Italy",
        "region": "Europe",
        "surface": "Hard",
        "start_date": date(2026, 3, 23),
        "estimated_direct_acceptance_best_fit": (250, 900),
        "estimated_qualifying_fit": (700, 1800),
        "notes": "Entry-level pro event on indoor hard. Better for developing hard-court players.",
        "entry_deadline": "Thu 5 Mar 2026, 14:00 GMT",
        "withdrawal_deadline": "Tue 10 Mar 2026, 14:00 GMT",
    },
    {
        "name": "M15 Antalya",
        "tour": "ITF Men's World Tennis Tour",
        "level": "M15",
        "city": "Antalya",
        "country": "Turkiye",
        "region": "Europe / Asia",
        "surface": "Clay",
        "start_date": date(2026, 3, 23),
        "estimated_direct_acceptance_best_fit": (250, 900),
        "estimated_qualifying_fit": (700, 1800),
        "notes": "Common entry-level route on clay. Good for players trying to manage costs and get matches.",
        "entry_deadline": "Thu 5 Mar 2026, 14:00 GMT",
        "withdrawal_deadline": "Tue 10 Mar 2026, 14:00 GMT",
    },
    {
        "name": "M15 Opatija",
        "tour": "ITF Men's World Tennis Tour",
        "level": "M15",
        "city": "Opatija",
        "country": "Croatia",
        "region": "Europe",
        "surface": "Clay",
        "start_date": date(2026, 3, 23),
        "estimated_direct_acceptance_best_fit": (250, 900),
        "estimated_qualifying_fit": (700, 1800),
        "notes": "Solid European clay ITF route for players still building ranking.",
        "entry_deadline": "Thu 5 Mar 2026, 14:00 GMT",
        "withdrawal_deadline": "Tue 10 Mar 2026, 14:00 GMT",
    },
]

# =========================
# HELPER FUNCTIONS
# =========================
def choose(*options):
    return random.choice(options)

def bullet_list(items):
    return "\n".join([f"- {item}" for item in items])

def format_plan(title, focus, warmup, main_work, strength=None, cooldown=None, notes=None, coach_block=None):
    text = f"## {title}\n"
    text += f"**Focus:** {focus}\n\n"
    text += f"### Warm-up\n{bullet_list(warmup)}\n\n"
    text += f"### Main part\n{bullet_list(main_work)}\n\n"

    if strength:
        text += f"### Secondary block\n{bullet_list(strength)}\n\n"
    if cooldown:
        text += f"### Cooldown\n{bullet_list(cooldown)}\n\n"
    if coach_block:
        text += f"### Coach organization notes\n{bullet_list(coach_block)}\n\n"
    if notes:
        text += f"### Coaching notes\n{bullet_list(notes)}\n\n"

    return text

def beginner_modifier(level):
    return level == "Beginner"

def injury_caution(injury_status):
    return injury_status != "No"

def goal_is_learning(goal):
    return goal == "Learn how to play"

def time_to_minutes(time_str):
    digits = "".join([c for c in time_str if c.isdigit()])
    return int(digits) if digits else 60

def minutes_to_readable(minutes):
    if minutes < 60:
        return f"{minutes} minutes"
    hours = minutes // 60
    mins = minutes % 60
    if mins == 0:
        return f"{hours}h"
    return f"{hours}h {mins}min"

def running_distance_category(distance):
    sprint = ["100m", "200m", "400m", "800m"]
    medium = ["1.2k", "1.5k", "3k", "5k", "10k"]
    long = ["15k", "Half marathon", "32k", "Marathon"]
    ultra = ["50k", "160k"]

    if distance in sprint:
        return "short"
    if distance in medium:
        return "medium"
    if distance in long:
        return "long"
    if distance in ultra:
        return "ultra"
    return "medium"

def pain_requires_physio(pain_score):
    return pain_score >= 6

def parse_date(d):
    if isinstance(d, date):
        return d
    return datetime.strptime(d, "%Y-%m-%d").date()

def format_date(d):
    return parse_date(d).strftime("%d %b %Y")

def region_match_score(player_region, tournament_region):
    player_region = player_region.lower()
    tournament_region = tournament_region.lower()

    if player_region in tournament_region:
        return 20
    if player_region == "south america" and "north america" in tournament_region:
        return 8
    if player_region == "north america" and "south america" in tournament_region:
        return 8
    if player_region == "europe" and ("africa" in tournament_region or "europe" in tournament_region):
        return 12
    return 0

def surface_match_score(preferred_surface, tournament_surface):
    if preferred_surface == "No preference":
        return 8
    if preferred_surface == tournament_surface:
        return 20
    return 0

def ranking_fit_score(player_ranking, event):
    direct_low, direct_high = event["estimated_direct_acceptance_best_fit"]
    qual_low, qual_high = event["estimated_qualifying_fit"]

    if player_ranking <= 0:
        return 0, "No ranking entered"
    if direct_low <= player_ranking <= direct_high:
        return 35, "Strong direct-acceptance fit"
    if qual_low <= player_ranking <= qual_high:
        return 24, "More realistic qualifying/alternate fit"
    if player_ranking < direct_low:
        return 18, "Strong enough level-wise, but event may be below best schedule level"
    return 6, "Probably too low for comfortable entry"

def level_preference_score(target_level, event_level):
    if target_level == "Best fit":
        return 0
    if target_level == event_level:
        return 18
    if target_level == "ITF" and event_level in ["M15", "M25"]:
        return 18
    if target_level == "Challenger" and event_level == "Challenger":
        return 18
    if target_level == "ATP Tour" and event_level.startswith("ATP"):
        return 18
    return -8

def entry_status_label(event):
    if "entry_deadline" in event:
        return f"Entry deadline listed: {event['entry_deadline']}"
    return "Use official acceptance list / fact sheet for live deadline confirmation"

def recommend_tournaments(player_ranking, player_region, preferred_surface, target_level):
    scored = []

    for event in UPCOMING_TOURNAMENTS:
        score = 0
        rank_score, rank_note = ranking_fit_score(player_ranking, event)
        score += rank_score
        score += region_match_score(player_region, event["region"])
        score += surface_match_score(preferred_surface, event["surface"])
        score += level_preference_score(target_level, event["level"])

        scored.append({
            **event,
            "score": score,
            "ranking_note": rank_note,
        })

    return sorted(scored, key=lambda x: x["score"], reverse=True)

def physio_guidance(area, pain_score, symptoms):
    base = {
        "Knee": {
            "stretch": "gentle quad + calf stretch",
            "mobility": "controlled knee extension/flexion and ankle mobility",
            "support": "ice 15-20 minutes after activity, reduce jumping and deep knee bend if painful",
            "watch": "swelling, instability, locking, or pain that gets sharper with weight-bearing",
        },
        "Ankle / foot": {
            "stretch": "calf stretch and gentle ankle circles",
            "mobility": "alphabet ankle mobility and slow calf raises if tolerated",
            "support": "ice 15-20 minutes, compress if swollen, avoid hard cutting or sprinting",
            "watch": "major swelling, inability to hop, inability to bear weight, visible deformity",
        },
        "Hamstring": {
            "stretch": "very gentle hamstring mobility only, not aggressive stretching",
            "mobility": "heel digs and easy bridge holds if comfortable",
            "support": "reduce sprinting/explosive work, use ice after training if irritated",
            "watch": "sudden sharp pain, bruising, or pain with normal walking",
        },
        "Quad": {
            "stretch": "gentle standing quad stretch",
            "mobility": "easy leg swings and controlled bodyweight sit-to-stand",
            "support": "reduce explosive work, ice after activity if sore",
            "watch": "bruising, major tightness after a pop sensation, or pain climbing stairs",
        },
        "Hip / groin": {
            "stretch": "adductor rock-back and light hip flexor stretch",
            "mobility": "90/90 transitions and controlled adductor movement",
            "support": "avoid lateral explosions and change-of-direction if symptoms increase",
            "watch": "pain with walking, sharp groin pain, or reduced range strongly affecting movement",
        },
        "Lower back": {
            "stretch": "gentle child's pose or knees-to-chest only if it feels relieving",
            "mobility": "cat-cow and controlled pelvic tilts",
            "support": "avoid heavy axial loading and high-impact rotation until calmer",
            "watch": "pain shooting down the leg, numbness, weakness, or bowel/bladder issues",
        },
        "Shoulder": {
            "stretch": "cross-body posterior shoulder stretch and pec mobility",
            "mobility": "wall slides and light band external rotation",
            "support": "reduce overhead hitting/serving/pressing for now, ice after loading if irritated",
            "watch": "night pain, weakness, instability, or pain raising the arm overhead",
        },
        "Elbow / forearm": {
            "stretch": "wrist flexor/extensor stretch",
            "mobility": "light forearm rotation and grip opening/closing",
            "support": "reduce repetitive hitting/throwing volume, ice after activity if sore",
            "watch": "pain that keeps worsening with gripping, swelling, or notable loss of strength",
        },
        "Wrist / hand": {
            "stretch": "gentle wrist flexion/extension mobility",
            "mobility": "tendon glides and easy wrist circles",
            "support": "reduce impact loading and repetitive contact, ice after activity if needed",
            "watch": "sharp pain on grip, visible swelling, or pain after a fall",
        },
        "Neck": {
            "stretch": "gentle upper-trap and levator scap stretch",
            "mobility": "slow neck rotations and chin tucks",
            "support": "avoid heavy shrugging/contact and monitor headache or radiating symptoms",
            "watch": "tingling, dizziness, radiating arm symptoms, or severe restricted movement",
        },
        "Other": {
            "stretch": "gentle mobility only",
            "mobility": "controlled pain-free range of motion",
            "support": "reduce load and monitor how symptoms change over 24-48h",
            "watch": "worsening pain, swelling, bruising, or normal movement becoming difficult",
        },
    }

    plan = base.get(area, base["Other"])

    severity_line = "Low pain profile."
    if pain_score >= 8:
        severity_line = "High pain profile. Do not train through this."
    elif pain_score >= 6:
        severity_line = "Moderate-to-high pain profile. Sport work should be paused or reduced substantially."
    elif pain_score >= 4:
        severity_line = "Moderate pain profile. Keep activity submaximal and avoid aggravating actions."

    red_flags = [
        "heard a pop",
        "cannot bear weight",
        "can’t bear weight",
        "numbness",
        "tingling",
        "severe swelling",
        "locking",
        "giving way",
        "fever",
    ]
    red_flag_found = any(flag in symptoms.lower() for flag in red_flags)

    return {
        "severity": severity_line,
        "stretch": plan["stretch"],
        "mobility": plan["mobility"],
        "support": plan["support"],
        "watch": plan["watch"],
        "red_flag_found": red_flag_found,
    }

def safety_message(injury_status, pain_score):
    if injury_status == "No":
        return None
    if pain_score >= 8:
        return (
            "You reported high pain. Today's session should be replaced by rest, light mobility, "
            "and professional evaluation before returning to normal training."
        )
    if pain_score >= 5:
        return (
            "You reported moderate pain. The session below should be treated as reduced-intensity only. "
            "Avoid explosive work, hard impact, and anything that increases pain."
        )
    return (
        "You reported a minor issue. Keep intensity controlled, reduce volume slightly, "
        "and stop if symptoms increase."
    )

def get_group_context_text(role, trains_alone, people_training, age_group=None, coach_level=None):
    if role == "Coach":
        return {
            "title_suffix": " — Coach Session",
            "coach_notes": [
                f"Organize the field and rotations for approximately {people_training} player(s).",
                f"Target age band: {age_group}.",
                f"Target team/player level: {coach_level}/10.",
                "Keep explanation short, demo clear, and restarts quick.",
            ],
        }

    if trains_alone == "Yes":
        return {
            "title_suffix": " — Solo Session",
            "coach_notes": [
                "Session adapted for solo training where possible.",
                "Use walls, cones, targets, self-feed work, or repeated patterns.",
            ],
        }

    return {
        "title_suffix": " — Small Group Session",
        "coach_notes": [
            f"Session adapted for a group of about {people_training} people.",
            "Use partner work, rotation stations, and short competitive games where relevant.",
        ],
    }

# =========================
# SOCCER COUNSELLING HELPERS
# =========================
def normalize_text(text):
    return text.strip().lower()

def parse_contract_offers(offers_text):
    raw = offers_text.strip()
    if not raw:
        return []
    return [item.strip() for item in raw.split(",") if item.strip()]

def map_current_level_to_band(current_level):
    mapping = {
        "School / recreational": "academy",
        "Academy / youth competitive": "academy",
        "Semi-pro / amateur senior": "semi-pro",
        "2nd division / strong pro pathway": "second-tier",
        "1st division / top domestic level": "top-tier",
    }
    return mapping.get(current_level, "semi-pro")

def conservative_allowed_targets(current_band, age_band):
    if current_band == "academy":
        if age_band in ["U8-U10", "U11-U13", "U14-U16"]:
            return ["academy"]
        if age_band == "U17-U19":
            return ["academy", "semi-pro"]
        return ["academy", "semi-pro"]

    if current_band == "semi-pro":
        if age_band in ["U17-U19", "Senior"]:
            return ["semi-pro", "second-tier"]
        return ["semi-pro"]

    if current_band == "second-tier":
        return ["second-tier", "top-tier"]

    return ["top-tier"]

def country_fit_bonus(player_country_pref, offer_country):
    if not player_country_pref or not offer_country:
        return 0
    return 18 if player_country_pref.lower() == offer_country.lower() else 0

def extract_country_from_offer_text(offer, chosen_country):
    # conservative shortcut: if chosen country appears in text, treat as that country
    if chosen_country.lower() in offer.lower():
        return chosen_country
    # fallback: if any known country appears
    for continent, countries in SOCCER_COUNTRIES_BY_CONTINENT.items():
        for c in countries:
            if c.lower() in offer.lower():
                return c
    return chosen_country

def band_from_offer_text(offer_text):
    offer = offer_text.lower()
    if any(x in offer for x in ["academy", "u19", "u21", "u23", "reserves", "ii", "b team"]):
        return "academy"
    if any(x in offer for x in ["premier league", "la liga", "serie a", "bundesliga", "ligue 1", "serie a brazil", "mls", "j1", "top division", "first division"]):
        return "top-tier"
    if any(x in offer for x in ["championship", "segunda", "serie b", "2nd division", "second division", "ligue 2", "2. bundesliga", "usl championship"]):
        return "second-tier"
    if any(x in offer for x in ["semi-pro", "amateur", "national league", "league of ireland first division", "serie c", "regional"]):
        return "semi-pro"
    return "semi-pro"

def choose_recommended_band(current_band, age_band, ambition):
    allowed = conservative_allowed_targets(current_band, age_band)

    if ambition == "Most realistic development step":
        return allowed[0]

    if ambition == "Best level I can still realistically compete in":
        return allowed[-1]

    if ambition == "Max minutes and development":
        return allowed[0]

    if ambition == "Use existing offer intelligently":
        return allowed[-1]

    return allowed[0]

def recommend_soccer_move(
    current_team,
    current_level,
    age_band,
    position,
    target_continent,
    target_country,
    contract_offers_text,
    ambition,
):
    current_band = map_current_level_to_band(current_level)
    allowed_bands = conservative_allowed_targets(current_band, age_band)
    desired_band = choose_recommended_band(current_band, age_band, ambition)

    offers = parse_contract_offers(contract_offers_text)
    evaluated_offers = []

    for offer in offers:
        offer_band = band_from_offer_text(offer)
        offer_country = extract_country_from_offer_text(offer, target_country)
        score = 0

        if offer_band in allowed_bands:
            score += 35
        else:
            score -= 25

        score += country_fit_bonus(target_country, offer_country)

        if desired_band == offer_band:
            score += 15

        if position == "Goalkeeper":
            score += 2
        elif position in ["Centre back", "Defensive midfielder"]:
            score += 3
        elif position in ["Winger", "Striker"]:
            score += 1

        evaluated_offers.append({
            "offer": offer,
            "band": offer_band,
            "country": offer_country,
            "score": score,
        })

    club_pool = SOCCER_CLUB_POOLS.get(target_country, {})
    conservative_pool = club_pool.get(desired_band, [])

    recommended_offer = None
    if evaluated_offers:
        evaluated_offers = sorted(evaluated_offers, key=lambda x: x["score"], reverse=True)
        if evaluated_offers[0]["score"] >= 20:
            recommended_offer = evaluated_offers[0]

    club_suggestion = None
    if conservative_pool:
        club_suggestion = random.choice(conservative_pool)

    summary_lines = []

    summary_lines.append(f"Current team entered: {current_team}")
    summary_lines.append(f"Current level profile interpreted as: {current_level}")
    summary_lines.append(f"Recommended movement band: {desired_band}")
    summary_lines.append(f"Allowed realistic step(s): {', '.join(allowed_bands)}")

    if recommended_offer:
        final_team = recommended_offer["offer"]
        reasoning = (
            f"The best fit among the current offers is **{final_team}** because it stays within a realistic "
            f"competitive jump, matches the destination preference better, and is safer development-wise "
            f"than overreaching."
        )
        verdict_type = "offer"
    else:
        final_team = club_suggestion if club_suggestion else f"a {desired_band} club in {target_country}"
        reasoning = (
            f"The safest recommendation is **{final_team}**. Based on the current level and age band, "
            f"this is a more realistic next step than jumping too aggressively."
        )
        verdict_type = "profile"

    conservative_warning = (
        "This engine is intentionally conservative. It avoids unrealistic jumps between levels. "
        "For example, a player coming from a small senior or semi-pro environment should usually target "
        "a step-by-step move, not an immediate jump to a major top-tier club."
    )

    return {
        "final_team": final_team,
        "verdict_type": verdict_type,
        "reasoning": reasoning,
        "evaluated_offers": evaluated_offers,
        "summary_lines": summary_lines,
        "conservative_warning": conservative_warning,
    }

# =========================
# TRAINING GENERATOR FUNCTIONS
# =========================
def _original_generate_running_plan(role, goal, level, injury_status, pain_score, session_time, running_focus, running_distance, context):
    minutes = time_to_minutes(session_time)
    category = running_distance_category(running_distance)

    if goal_is_learning(goal):
        return format_plan(
            title=f"Running Foundation Session{context['title_suffix']}",
            focus=f"Learn how to run better for {running_distance}",
            warmup=[
                "5 min brisk walk",
                "5 min easy jog",
                "Dynamic mobility: ankle circles, leg swings, hip openers",
                "2 x 20m marching drills",
            ],
            main_work=[
                "Technique block: 3 x 20m A-march",
                "Technique block: 3 x 20m skipping",
                "4 x 60m relaxed strides at controlled pace",
                "Main set: 12-20 min easy run focused on posture, cadence, and relaxed arms",
            ],
            strength=[
                "2 x 10 split squats each side",
                "2 x 10 calf raises each side",
                "2 x 30 sec front plank",
            ],
            cooldown=[
                "5 min walk",
                "Gentle calf, hip flexor, and hamstring mobility",
            ],
            coach_block=context["coach_notes"],
            notes=[
                "Focus on rhythm, posture, and relaxed shoulders.",
                "Do not force speed while learning mechanics.",
            ],
        )

    if category == "short":
        main = [
            "Drill block: 3 x 20m A-skips",
            "Drill block: 3 x 20m fast-feet build-ups",
            "4 x 60m progressive accelerations",
            choose(
                "6 x 100m at strong but controlled speed, 90 sec rest",
                "8 x 60m acceleration runs, walk-back recovery",
                "5 x 150m at 800m rhythm, 2 min rest",
            ),
        ]
        strength = [
            "3 x 5 goblet squats",
            "3 x 6 Romanian deadlifts",
            "3 x 8 calf raises",
            "2 x 20 sec hollow hold",
        ]
        focus = f"Speed / power development for {running_distance}"

    elif category == "medium":
        main = [
            "10 min easy run build-up",
            choose(
                "5 x 3 min at threshold effort, 90 sec easy jog",
                "6 x 800m at controlled pace, 2 min recovery",
                "4 x 5 min steady-hard tempo, 2 min easy jog",
            ),
        ]
        strength = [
            "3 x 8 reverse lunges each side",
            "3 x 8 step-ups each side",
            "2 x 30 sec side plank each side",
        ]
        focus = f"Tempo / aerobic support for {running_distance}"

    elif category == "long":
        long_run_time = max(45, int(minutes * 0.75))
        main = [
            f"Steady run: {minutes_to_readable(long_run_time)} at sustainable pace",
            "Finish with 4 x 20 sec controlled strides if legs still feel good",
        ]
        strength = [
            "2 x 8 split squats each side",
            "2 x 10 glute bridges",
            "2 x 30 sec plank",
        ]
        focus = f"Endurance support for {running_distance}"

    else:
        ultra_time = max(60, int(minutes * 0.80))
        main = [
            f"Main endurance run: {minutes_to_readable(ultra_time)} at very controlled conversational pace",
            "Practice fueling and hydration during the run if relevant",
            "Last 10 min: focus on calm rhythm and efficient form",
        ]
        strength = [
            "2 x 8 single-leg RDL each side",
            "2 x 10 calf raises each side",
            "2 x 30 sec dead bug hold",
        ]
        focus = f"Ultra-endurance support for {running_distance}"

    if beginner_modifier(level):
        main.insert(0, "Reduce pace emphasis and keep all reps controlled.")
    if injury_caution(injury_status):
        main = [item for item in main if "strides" not in item.lower()]

    if role == "Coach":
        main.insert(0, "Use lane organization, start intervals on a whistle, and keep rest predictable for the group.")

    return format_plan(
        title=f"Running Session{context['title_suffix']}",
        focus=focus,
        warmup=[
            "5-10 min easy jog or brisk walk",
            "Dynamic mobility: hips, ankles, hamstrings",
            "Running drills: march, skip, leg swings",
        ],
        main_work=main,
        strength=strength,
        cooldown=[
            "5-10 min easy walk/jog down",
            "Gentle lower-body mobility",
        ],
        coach_block=context["coach_notes"],
        notes=[
            "Keep mechanics clean even when tired.",
            "Stop if pain increases during the session.",
        ],
    )

def _original_generate_gym_plan(role, goal, level, injury_status, pain_score, session_time, gym_style, context):
    if goal_is_learning(goal):
        return format_plan(
            title=f"Gym Fundamentals Session{context['title_suffix']}",
            focus="Learn how to train properly in the gym",
            warmup=[
                "5 min bike or treadmill walk",
                "Dynamic mobility for hips, shoulders, and ankles",
                "1 light familiarization set for each major movement",
            ],
            main_work=[
                "3 x 8 goblet squat",
                "3 x 8 dumbbell bench press",
                "3 x 8 seated row",
                "3 x 8 Romanian deadlift with light-moderate load",
            ],
            strength=[
                "2 x 10 split squat each side",
                "2 x 10 dumbbell shoulder press",
                "2 x 30 sec plank",
            ],
            cooldown=[
                "5 min easy walk",
                "Gentle mobility for quads, chest, and hips",
            ],
            coach_block=context["coach_notes"],
            notes=[
                "Prioritize correct technique over heavy load.",
                "Leave 2-3 reps in reserve on each set.",
            ],
        )

    if gym_style == "General strength":
        main = [
            "4 x 6 squat or leg press",
            "4 x 6 bench press or dumbbell press",
            "4 x 8 row variation",
            "3 x 6 Romanian deadlift",
        ]
        secondary = [
            "3 x 8 split squat each side",
            "3 x 10 hamstring curl",
            "3 x 12 face pulls",
            "2 x 30 sec plank",
        ]
        focus = "Full-body strength"

    elif gym_style == "Sport-specific strength":
        main = [
            "4 x 5 trap-bar deadlift or squat",
            "4 x 5 push press or landmine press",
            "4 x 6 pull-ups / assisted pull-ups or lat pulldown",
            "3 x 6 rear-foot elevated split squat",
        ]
        secondary = [
            "3 x 8 medicine-ball rotational throws or cable rotations",
            "3 x 10 single-leg RDL each side",
            "3 x 10 Copenhagen plank short lever or side plank",
        ]
        focus = "Athletic strength and transfer"

    else:
        main = [
            "3 x 8 squat pattern",
            "3 x 8 horizontal press",
            "3 x 10 row pattern",
            "3 x 10 hinge pattern",
        ]
        secondary = [
            "2 x 10 calf raises",
            "2 x 10 reverse lunges each side",
            "2 x 20 sec dead bug",
        ]
        focus = "Return to training with controlled load"

    if beginner_modifier(level):
        main = [item.replace("4 x", "3 x") for item in main]
    if injury_caution(injury_status):
        secondary.append("Reduce load 10-20% and avoid painful ranges")
    if role == "Coach":
        secondary.append("Set athletes in stations if equipment is limited")

    return format_plan(
        title=f"Gym Session{context['title_suffix']}",
        focus=focus,
        warmup=[
            "5 min easy cardio",
            "Dynamic mobility for main joints involved",
            "2 progressive warm-up sets before first compound lift",
        ],
        main_work=main,
        strength=secondary,
        cooldown=[
            "5 min easy walk",
            "Gentle mobility for worked muscle groups",
        ],
        coach_block=context["coach_notes"],
        notes=[
            "Quality reps only.",
            "Rest 60-120 sec on most sets; longer on heavy compounds.",
        ],
    )

def _original_generate_tennis_plan(role, goal, level, injury_status, pain_score, session_time, tennis_focus, context):
    if goal_is_learning(goal):
        return format_plan(
            title=f"Tennis Beginner Session{context['title_suffix']}",
            focus="Learn how to play tennis",
            warmup=[
                "5 min light jog and side shuffles",
                "Shoulder circles, trunk rotations, ankle mobility",
                "Mini-tennis for feel and control",
            ],
            main_work=[
                "10 min forehand technique from short court",
                "10 min backhand technique from short court",
                "10 min rallying crosscourt with control target",
                "10 min serve fundamentals: toss, rhythm, and contact point",
            ],
            strength=[
                "2 x 8 split squat each side",
                "2 x 10 band rows",
                "2 x 20 sec side plank each side",
            ],
            cooldown=[
                "Easy walk and shoulder mobility",
                "Light forearm and hip stretching",
            ],
            coach_block=context["coach_notes"],
            notes=[
                "Focus on timing, balance, and clean contact.",
                "Consistency matters more than power.",
            ],
        )

    focus_map = {
        "Technique": [
            "15 min rallying with one technical cue only",
            "12 min forehand repetition block",
            "12 min backhand repetition block",
            "10 min serve rhythm work",
        ],
        "Match play": [
            "10 min controlled crosscourt patterns",
            "15 min point construction from neutral ball",
            "20 min live points with first-ball objective",
            "10 min return + first shot patterns",
        ],
        "Movement": [
            "8 x lateral recovery patterns",
            "8 x approach + recovery footwork patterns",
            "12 min live-ball movement emphasis",
            "10 min open-stance to neutral recovery drills",
        ],
        "Serve / return": [
            "15 min serve targets",
            "15 min second-serve repetition",
            "15 min return block against varied placement",
            "10 min serve + first forehand pattern",
        ],
    }

    main = focus_map.get(tennis_focus, focus_map["Technique"])

    if beginner_modifier(level):
        main.insert(0, "Reduce live intensity and prioritize basket-fed repetitions.")
    if injury_caution(injury_status):
        main = [m for m in main if "serve" not in m.lower()]
    if role == "Coach":
        main.insert(0, "Use basket feeding, clear lanes, and short rotations for better repetition density.")

    return format_plan(
        title=f"Tennis Session{context['title_suffix']}",
        focus=f"Tennis development — {tennis_focus}",
        warmup=[
            "5 min light jog, shuffle, carioca",
            "Dynamic shoulder, hip, and thoracic mobility",
            "Mini-tennis and rhythm hitting",
        ],
        main_work=main,
        strength=[
            "2 x 8 reverse lunges each side",
            "2 x 10 band external rotations",
            "2 x 20 sec anti-rotation hold each side",
        ],
        cooldown=[
            "Walk and breathing reset",
            "Light shoulder, forearm, hip mobility",
        ],
        coach_block=context["coach_notes"],
        notes=[
            "Keep feet active before every shot.",
            "Stop if shoulder, elbow, or wrist pain rises during hitting.",
        ],
    )

def _original_generate_baseball_plan(role, goal, level, injury_status, pain_score, session_time, baseball_focus, context):
    if goal_is_learning(goal):
        return format_plan(
            title=f"Baseball Fundamentals Session{context['title_suffix']}",
            focus="Learn how to play baseball",
            warmup=[
                "5 min jog and dynamic movement",
                "Shoulder activation and hip mobility",
                "Easy throwing progression",
            ],
            main_work=[
                "10 min throwing mechanics fundamentals",
                "10 min glove-work basics / receiving drills",
                "10 min hitting stance and swing path fundamentals",
                "10 min base running and athletic movement patterns",
            ],
            strength=[
                "2 x 10 split squat each side",
                "2 x 10 band rows",
                "2 x 20 sec plank",
            ],
            cooldown=[
                "Shoulder and forearm mobility",
                "Light lower-body stretching",
            ],
            coach_block=context["coach_notes"],
            notes=[
                "Learn rhythm and coordination before adding intensity.",
                "Do not force throwing volume early.",
            ],
        )

    focus_map = {
        "Hitting": [
            "Tee work: 4 x 8 quality swings",
            "Front toss: 4 x 6 swings",
            "Bat path / contact-point drill: 3 rounds",
            "Live timing drill or machine work: 3 rounds",
        ],
        "Throwing": [
            "Progressive throwing build-up",
            "4 x 6 position-specific throws",
            "3 x 5 crow-hop or momentum throws",
            "3 x 6 accuracy-focused throws",
        ],
        "Fielding": [
            "10 min glove presentation work",
            "4 x 6 ground-ball reps",
            "4 x 6 throw-after-field reps",
            "3 x 5 reaction reps",
        ],
        "General skills": [
            "Throwing progression",
            "Fielding fundamentals block",
            "Hitting contact block",
            "Base-running acceleration block",
        ],
    }

    main = focus_map.get(baseball_focus, focus_map["General skills"])
    if role == "Coach":
        main.insert(0, "Split the group by station to control arm volume and waiting time.")

    return format_plan(
        title=f"Baseball Session{context['title_suffix']}",
        focus=f"Baseball development — {baseball_focus}",
        warmup=[
            "Jog, skips, and lateral movement",
            "Shoulder activation with band",
            "Hip and thoracic mobility",
        ],
        main_work=main,
        strength=[
            "3 x 8 split squat each side",
            "3 x 8 rows",
            "2 x 8 med-ball rotations or cable rotations",
        ],
        cooldown=[
            "Forearm, shoulder, and hip mobility",
            "Easy walk",
        ],
        coach_block=context["coach_notes"],
        notes=[
            "Protect the arm by keeping total throwing volume reasonable.",
            "Quality mechanics first.",
        ],
    )

def _original_generate_rowing_plan(role, goal, level, injury_status, pain_score, session_time, rowing_focus, context):
    if goal_is_learning(goal):
        return format_plan(
            title=f"Rowing Beginner Session{context['title_suffix']}",
            focus="Learn how to row with better rhythm and sequence",
            warmup=[
                "5 min easy erg or bike",
                "Hip, ankle, and thoracic mobility",
                "Arms-only and legs-only sequence drills",
            ],
            main_work=[
                "10 min pick drill progression",
                "3 x 5 min steady rowing at controlled rate",
                "3 x 2 min pause rowing emphasizing body position",
                "5 min easy flush",
            ],
            strength=[
                "2 x 10 goblet squat",
                "2 x 10 seated row",
                "2 x 20 sec side plank each side",
            ],
            cooldown=[
                "Easy erg or walk",
                "Light posterior-chain mobility",
            ],
            coach_block=context["coach_notes"],
            notes=[
                "Legs-body-arms on the drive; arms-body-legs on the recovery.",
                "Do not rush the slide.",
            ],
        )

    focus_map = {
        "Technique": [
            "10 min pick drill progression",
            "4 x 4 min steady rowing at low stroke rate with form focus",
            "3 x 2 min pause drills",
        ],
        "Aerobic base": [
            "20-40 min continuous steady rowing",
            "5 x 1 min at slightly higher rate with full control",
        ],
        "Power": [
            "8 x 250m or 45 sec strong strokes, 75 sec easy",
            "4 x 10 power strokes from low rate",
        ],
        "Race prep": [
            "3 x 6 min at projected race rhythm, 3 min easy",
            "4 starts of 10-15 hard strokes",
        ],
    }

    main = focus_map.get(rowing_focus, focus_map["Technique"])
    if role == "Coach":
        main.insert(0, "Keep stroke-rate targets visible and synchronize starts for the crew.")

    return format_plan(
        title=f"Rowing Session{context['title_suffix']}",
        focus=f"Rowing development — {rowing_focus}",
        warmup=[
            "5-8 min easy erg",
            "Mobility for hips, ankles, lats, thoracic spine",
            "Progressive build strokes",
        ],
        main_work=main,
        strength=[
            "3 x 8 Romanian deadlift",
            "3 x 10 seated row",
            "2 x 30 sec hollow hold",
        ],
        cooldown=[
            "5 min easy row",
            "Hamstring, glute, and lat mobility",
        ],
        coach_block=context["coach_notes"],
        notes=[
            "Sequence and rhythm matter more than muscling each stroke.",
            "Keep the catch controlled and connected.",
        ],
    )

def _original_generate_weightlifting_plan(role, goal, level, injury_status, pain_score, session_time, wl_focus, context):
    if goal_is_learning(goal):
        return format_plan(
            title=f"Weightlifting Fundamentals Session{context['title_suffix']}",
            focus="Learn Olympic lifting basics",
            warmup=[
                "5 min easy cardio",
                "Ankle, hip, thoracic, and wrist mobility",
                "PVC/bar-only movement prep",
            ],
            main_work=[
                "3 x 5 front squat with light load",
                "4 x 3 hang power clean with technique emphasis",
                "4 x 3 muscle snatch or overhead drill with PVC/bar",
                "3 x 5 strict press or push press technique work",
            ],
            strength=[
                "2 x 8 Romanian deadlift",
                "2 x 8 split squat each side",
                "2 x 20 sec front-rack hold or plank",
            ],
            cooldown=[
                "Easy walk",
                "Wrist, hip, and thoracic mobility",
            ],
            coach_block=context["coach_notes"],
            notes=[
                "Technique before load always.",
                "Catch positions must be stable and pain-free.",
            ],
        )

    focus_map = {
        "Snatch": [
            "5 x 2 hang snatch",
            "5 x 2 snatch pull",
            "4 x 2 overhead squat or snatch balance variation",
        ],
        "Clean & jerk": [
            "5 x 2 clean",
            "5 x 1 jerk from rack",
            "4 x 3 clean pull",
        ],
        "General Olympic lifting": [
            "4 x 2 power snatch",
            "4 x 2 power clean + jerk",
            "4 x 3 front squat",
        ],
        "Strength support": [
            "5 x 3 front squat",
            "4 x 4 push press",
            "4 x 4 pull variation",
        ],
    }

    main = focus_map.get(wl_focus, focus_map["General Olympic lifting"])
    if role == "Coach":
        main.insert(0, "Run athletes in waves by bar availability and technical level.")

    return format_plan(
        title=f"Weightlifting Session{context['title_suffix']}",
        focus=f"Weightlifting development — {wl_focus}",
        warmup=[
            "5-8 min easy cardio",
            "Joint prep: wrists, ankles, hips, thoracic spine",
            "Bar-only technical sets",
        ],
        main_work=main,
        strength=[
            "3 x 5 Romanian deadlift or pull variation",
            "3 x 6 split squat each side",
            "2 x 30 sec overhead stability or core hold",
        ],
        cooldown=[
            "Easy walk",
            "Mobility for wrists, hips, shoulders",
        ],
        coach_block=context["coach_notes"],
        notes=[
            "Fast elbows, stable receiving positions, controlled bar path.",
            "Do not chase load if positions break down.",
        ],
    )

def _original_generate_water_polo_plan(role, goal, level, injury_status, pain_score, session_time, wp_focus, context):
    if goal_is_learning(goal):
        return format_plan(
            title=f"Water Polo Beginner Session{context['title_suffix']}",
            focus="Learn how to play water polo",
            warmup=[
                "200m easy swim",
                "Shoulder circles and trunk rotation on deck",
                "Eggbeater basics and body-position prep",
            ],
            main_work=[
                "4 x 25m head-up swim technique",
                "4 x 30 sec eggbeater holds",
                "10 min passing mechanics and catching",
                "10 min shooting fundamentals with controlled form",
            ],
            strength=[
                "2 x 10 band external rotations",
                "2 x 10 split squat each side",
                "2 x 20 sec side plank each side",
            ],
            cooldown=[
                "100-200m easy swim",
                "Shoulder and hip mobility",
            ],
            coach_block=context["coach_notes"],
            notes=[
                "Stay tall in the water.",
                "Build shoulder volume gradually.",
            ],
        )

    focus_map = {
        "Swimming conditioning": [
            "6 x 50m moderate head-up swim, 20 sec rest",
            "6 x 25m fast swim, 30 sec rest",
            "4 x 30 sec eggbeater holds",
        ],
        "Shooting": [
            "10 min passing progression",
            "5 x 5 controlled shooting reps",
            "4 x 20 sec leg-drive + shot setup",
        ],
        "Match skills": [
            "Passing under pressure block",
            "Drive-and-recover repetitions",
            "2v2 or 3v3 tactical sequence work",
        ],
        "General development": [
            "Swimming conditioning block",
            "Eggbeater block",
            "Passing + shooting block",
            "Short tactical sequence block",
        ],
    }

    main = focus_map.get(wp_focus, focus_map["General development"])
    if role == "Coach":
        main.insert(0, "Use clear lanes and half-pool organization to increase repetition density.")

    return format_plan(
        title=f"Water Polo Session{context['title_suffix']}",
        focus=f"Water polo development — {wp_focus}",
        warmup=[
            "200-300m easy swim",
            "Dynamic shoulder prep",
            "Ball-handling and eggbeater activation",
        ],
        main_work=main,
        strength=[
            "3 x 10 band external rotation",
            "3 x 8 push-up variation",
            "2 x 30 sec hollow hold",
        ],
        cooldown=[
            "100-200m easy swim",
            "Shoulder, chest, and hip mobility",
        ],
        coach_block=context["coach_notes"],
        notes=[
            "Shoulder health and leg drive are priorities.",
            "Stop hard throwing if shoulder pain rises.",
        ],
    )

def generate_soccer_player_plan(goal, level, injury_status, pain_score, session_time, soccer_focus, soccer_position, context):
    if goal_is_learning(goal):
        solo_block = [
            "Ball mastery: 6 x 45 sec touches (inside, outside, sole, pull-push)",
            "Wall passing or target passing: 4 x 2 min",
            "First-touch setup into dribble: 4 x 6 reps each side",
            "Finishing or target strike block: 4 x 5 reps if a goal/wall is available",
        ] if "Solo" in context["title_suffix"] else [
            "Partner passing and receiving fundamentals: 8-10 min",
            "First-touch direction drill in pairs: 4 rounds",
            "1v1 protection / turning basics: 4 rounds",
            "Small technical game with gates or mini goals: 10-12 min",
        ]

        return format_plan(
            title=f"Soccer Beginner Session{context['title_suffix']}",
            focus=f"Learn how to play soccer better — {soccer_position}",
            warmup=[
                "5 min light jog, skips, side shuffles",
                "Dynamic mobility: hips, groin, hamstrings, ankles",
                "2-3 min easy touches with the ball",
            ],
            main_work=solo_block,
            strength=[
                "2 x 8 split squats each side",
                "2 x 10 calf raises each side",
                "2 x 20 sec plank",
            ],
            cooldown=[
                "Easy walk and breathing reset",
                "Light lower-body mobility",
            ],
            coach_block=context["coach_notes"],
            notes=[
                "Keep the ball close and body shape balanced.",
                "Technique before speed.",
            ],
        )

    focus_map = {
        "General development": [
            "Ball mastery / scanning warm block: 6 min",
            "Passing pattern with movement: 10 min",
            "Directional possession or dribble-transfer game: 12 min",
            "Short finishing or final-action block: 10 min",
        ],
        "Technical development": [
            "Ball mastery series: 6 x 45 sec",
            "Receiving across the body: 4 x 5 reps each side",
            "Passing technique under movement: 4 x 2 min",
            "Turn + accelerate action: 4 x 5 reps each side",
        ],
        "Finishing": [
            "Finishing from cutback: 5 x 3 reps",
            "Finishing after first touch out of feet: 5 x 3 reps",
            "Quick-reaction rebound finish: 4 x 4 reps",
            "Competition block: first to 6 clean finishes",
        ],
        "First touch & passing": [
            "Wall or partner passing rhythm block: 3 x 3 min",
            "Open-body first touch and play: 4 x 5 reps each side",
            "Pass-move-receive triangle pattern: 4 rounds",
            "One-touch / two-touch control challenge",
        ],
        "1v1 attacking / defending": [
            "Acceleration and deceleration prep",
            "1v1 beat-the-line reps: 6 each side",
            "1v1 channel duels: 6 rounds",
            "Recovery defending / delay and tackle drill: 5 rounds",
        ],
        "Possession": [
            "Rondo or reduced possession game: 10-12 min",
            "Directional keep-ball with end target: 12 min",
            "Transition-on-loss rule game: 12 min",
            "Short conditioned game on touch limit",
        ],
        "Build-up play": [
            "Passing pattern through thirds: 8-10 min",
            "Build from back under passive pressure: 10 min",
            "Positional game with progression targets: 12 min",
            "Conditioned game: score only after playing through zones",
        ],
        "Pressing & defending": [
            "Body shape and pressing angles walk-through",
            "2v2 or 3v3 pressing trap block: 10 min",
            "Defend-forward transition game: 12 min",
            "Conditioned match: immediate pressure after loss",
        ],
        "Transition": [
            "Win-it-and-go drill: 6 rounds",
            "3v2 or 4v3 transition waves: 10-12 min",
            "Counterattack decision block: 8-10 min",
            "Counter-press reaction game: 8 min",
        ],
        "Small-sided games": [
            "3v3 / 4v4 conditioned game block 1",
            "3v3 / 4v4 conditioned game block 2 with scoring rule",
            "Game block 3 with transition bonus",
            "Final free-play with one coaching focus",
        ],
        "Conditioning with the ball": [
            "Repeated dribble-relay efforts: 6 rounds",
            "Passing + movement intervals: 6 x 90 sec",
            "Small-sided high-tempo game: 3 x 3 min",
            "Short shuttle with ball recoveries",
        ],
        "Set pieces": [
            "Service quality block: 10 min",
            "Movement timing on corners/free kicks: 10 min",
            "Second-ball reaction: 8 min",
            "Defensive organization on restart: 8 min",
        ],
    }

    main = focus_map.get(soccer_focus, focus_map["General development"])

    if soccer_position == "Goalkeeper":
        main = [
            "Footwork and set-position prep",
            "Handling block: front, low, and collapse saves",
            "Distribution block with hands and feet",
            "Reaction / recovery action",
        ]
        if soccer_focus in ["Build-up play", "First touch & passing"]:
            main.append("Press-resistant first touch + passing under pressure")
        if soccer_focus in ["Transition", "Pressing & defending"]:
            main.append("Starting position and sweeping decisions")

    if beginner_modifier(level):
        main.insert(0, "Keep opposition light and prioritize clean repetition.")
    if injury_caution(injury_status):
        main = [m for m in main if "high-tempo" not in m.lower() and "1v1 channel duels" not in m.lower()]

    if "Solo" in context["title_suffix"]:
        solo_adjustments = [
            "Adapt group actions into wall work, cone patterns, self-serve touches, or repeated striking patterns."
        ]
    else:
        solo_adjustments = [
            "Use competition, constraints, and rotation to raise realism."
        ]

    return format_plan(
        title=f"Soccer Session{context['title_suffix']}",
        focus=f"Soccer development — {soccer_focus} — {soccer_position}",
        warmup=[
            "5 min movement prep: jog, shuffle, open/close gate, skips",
            "Dynamic mobility for groin, hips, hamstrings, ankles",
            "Ball activation: touches, short passes, or first-touch prep",
        ],
        main_work=main,
        strength=[
            "2 x 8 split squat each side",
            "2 x 8 single-leg RDL each side",
            "2 x 10 calf raises",
            "2 x 20 sec side plank each side",
        ],
        cooldown=[
            "Easy walk or easy touches with heart rate coming down",
            "Mobility for calves, hip flexors, adductors, hamstrings",
        ],
        coach_block=context["coach_notes"],
        notes=[
            "Main football themes: scanning, body shape, timing, and decision-making.",
            "Keep work game-relevant where possible.",
        ] + solo_adjustments,
    )

def generate_soccer_coach_plan(goal, session_time, soccer_focus, soccer_position, age_group, coach_level, people_training, context):
    age_label = age_group
    minutes = time_to_minutes(session_time)

    # More coach-specific, structured session templates
    if goal_is_learning(goal):
        return format_plan(
            title=f"Soccer Coach Session{context['title_suffix']}",
            focus=f"Teach soccer basics clearly — {age_label}",
            warmup=[
                "Arrival game with the ball: each player active immediately",
                "Movement prep with ball and fun coordination races",
                "2-3 demo moments only, then let them play",
            ],
            main_work=[
                "Technical station 1: dribbling and ball control",
                "Technical station 2: passing and receiving",
                "Small opposed game: 1v1 or 2v2 to mini goals",
                "Conditioned game with one simple theme only",
            ],
            strength=[
                "Use bodyweight movement quality only if age-appropriate",
            ],
            cooldown=[
                "Short fun finish, easy walk, regroup",
            ],
            coach_block=[
                f"Age band: {age_label}",
                f"Level: {coach_level}/10",
                f"Players: {people_training}",
                "Keep the session simple, active, and enjoyable.",
            ],
            notes=[
                "For younger players, keep lines short and touches high.",
                "Correct one key detail at a time.",
            ],
        )

    if soccer_focus == "Possession":
        main = [
            "Rondo / keep-ball starter with clear support angles",
            "Directional possession game with gates or end targets",
            "Positional game with transition on loss",
            "Conditioned match: extra point after a sequence of passes",
        ]
    elif soccer_focus == "Build-up play":
        main = [
            "Unopposed pattern through lines",
            "Opposed progression game from defensive third",
            "Build-up under pressing trigger",
            "Conditioned match: score only after progressing through zones",
        ]
    elif soccer_focus == "Pressing & defending":
        main = [
            "Pressing angle walk-through",
            "Small-unit defending / cover and balance",
            "Press-and-trap game in channels",
            "Conditioned match: reward regains in advanced areas",
        ]
    elif soccer_focus == "Transition":
        main = [
            "Win it and go exercise",
            "Wave game 3v2 / 4v3 in transition",
            "Counter-press reaction drill",
            "Conditioned match with immediate restart after turnovers",
        ]
    elif soccer_focus == "Finishing":
        main = [
            "Finishing technique from different services",
            "Finishing after movement / timing run",
            "Small opposed finishing game",
            "Conditioned match: bonus for cutback or quick final action",
        ]
    elif soccer_focus == "Set pieces":
        main = [
            "Service quality and target zones",
            "Attack timing and blocking/movement detail",
            "Second-ball reactions",
            "Defensive organization and communication",
        ]
    elif soccer_focus == "Small-sided games":
        main = [
            "3v3 or 4v4 game block 1 with one theme",
            "Game block 2 with different scoring condition",
            "Game block 3 with transition emphasis",
            "Free game with targeted freeze-and-correct moments",
        ]
    else:
        main = [
            "Technical starter linked to session theme",
            "Main opposed exercise",
            "Progressed exercise with more realism",
            "Conditioned match with same theme",
        ]

    coach_block = [
        f"Players: {people_training}",
        f"Age band: {age_label}",
        f"Level: {coach_level}/10",
        "Shape area size to the number and level of players.",
        "Use clear work:rest ratios and quick restarts.",
        "Coach the session theme, not everything at once.",
    ]

    if people_training <= 4:
        coach_block.append("Very small group: use more repetitions, partner detail, and many ball contacts.")
    elif people_training <= 10:
        coach_block.append("Small squad: use 2v2, 3v3, 4v4, and position rotations.")
    else:
        coach_block.append("Larger squad: organize two grids or split units to reduce waiting time.")

    notes = [
        "Modern football sessions should connect technique, decision-making, and game realism.",
        "Use progression: simple -> opposed -> game-like.",
    ]

    if age_group in ["U8-U10", "U11-U13"]:
        notes.append("For younger ages, prioritize repetition, enjoyment, and simple coaching points.")
    else:
        notes.append("For older ages, increase tactical detail and transition speed.")

    if soccer_position == "Goalkeeper":
        notes.append("Add goalkeeper-specific reps inside the session if a keeper is present.")

    return format_plan(
        title=f"Soccer Coach Session{context['title_suffix']}",
        focus=f"Soccer coaching session — {soccer_focus} — {age_label}",
        warmup=[
            "Ball-based activation",
            "Dynamic movement prep",
            "Short starter game linked to the session objective",
        ],
        main_work=main,
        strength=[
            "Optional athletic support block: landing mechanics, deceleration, core, hamstrings",
        ],
        cooldown=[
            "Short debrief, breathing reset, light mobility",
        ],
        coach_block=coach_block,
        notes=notes,
    )

def generate_soccer_plan(
    role,
    goal,
    level,
    injury_status,
    pain_score,
    session_time,
    soccer_focus,
    soccer_position,
    age_group,
    coach_level,
    people_training,
    context,
):
    if role == "Coach":
        return generate_soccer_coach_plan(
            goal=goal,
            session_time=session_time,
            soccer_focus=soccer_focus,
            soccer_position=soccer_position,
            age_group=age_group,
            coach_level=coach_level,
            people_training=people_training,
            context=context,
        )

    return generate_soccer_player_plan(
        goal=goal,
        level=level,
        injury_status=injury_status,
        pain_score=pain_score,
        session_time=session_time,
        soccer_focus=soccer_focus,
        soccer_position=soccer_position,
        context=context,
    )

def generate_plan(
    role,
    sport,
    goal,
    level,
    injury_status,
    pain_score,
    session_time,
    sport_inputs,
    context,
):
    if sport == "Running":
        return generate_running_plan(
            role=role,
            goal=goal,
            level=level,
            injury_status=injury_status,
            pain_score=pain_score,
            session_time=session_time,
            running_focus=sport_inputs["running_focus"],
            running_distance=sport_inputs["running_distance"],
            context=context,
        )

    if sport == "Gym":
        return generate_gym_plan(
            role=role,
            goal=goal,
            level=level,
            injury_status=injury_status,
            pain_score=pain_score,
            session_time=session_time,
            gym_style=sport_inputs["gym_style"],
            context=context,
        )

    if sport == "Tennis":
        return generate_tennis_plan(
            role=role,
            goal=goal,
            level=level,
            injury_status=injury_status,
            pain_score=pain_score,
            session_time=session_time,
            tennis_focus=sport_inputs["tennis_focus"],
            context=context,
        )

    if sport == "Baseball":
        return generate_baseball_plan(
            role=role,
            goal=goal,
            level=level,
            injury_status=injury_status,
            pain_score=pain_score,
            session_time=session_time,
            baseball_focus=sport_inputs["baseball_focus"],
            context=context,
        )

    if sport == "Rowing":
        return generate_rowing_plan(
            role=role,
            goal=goal,
            level=level,
            injury_status=injury_status,
            pain_score=pain_score,
            session_time=session_time,
            rowing_focus=sport_inputs["rowing_focus"],
            context=context,
        )

    if sport == "Weightlifting":
        return generate_weightlifting_plan(
            role=role,
            goal=goal,
            level=level,
            injury_status=injury_status,
            pain_score=pain_score,
            session_time=session_time,
            wl_focus=sport_inputs["wl_focus"],
            context=context,
        )

    if sport == "Water Polo":
        return generate_water_polo_plan(
            role=role,
            goal=goal,
            level=level,
            injury_status=inury_status if False else injury_status,
            pain_score=pain_score,
            session_time=session_time,
            wp_focus=sport_inputs["wp_focus"],
            context=context,
        )

    if sport == "Soccer":
        return generate_soccer_plan(
            role=role,
            goal=goal,
            level=level,
            injury_status=injury_status,
            pain_score=pain_score,
            session_time=session_time,
            soccer_focus=sport_inputs["soccer_focus"],
            soccer_position=sport_inputs["soccer_position"],
            age_group=sport_inputs.get("age_group"),
            coach_level=sport_inputs.get("coach_level"),
            people_training=sport_inputs.get("people_training", 1),
            context=context,
        )

    return "Sport not supported yet."


# =========================
# ENHANCEMENTS / OVERRIDES
# =========================

# Extra session options for every sport
RUNNING_SESSION_STYLES = [
    "Best fit for my goal",
    "Intervals / tempo",
    "Hill work",
    "Technique + efficiency",
]
GYM_STYLES_EXTENDED = [
    "General strength",
    "Sport-specific strength",
    "Return to training",
    "Power / explosiveness",
]
TENNIS_FOCUS_OPTIONS = [
    "Technique",
    "Match play",
    "Movement",
    "Serve / return",
    "Net play / transition",
]
BASEBALL_FOCUS_OPTIONS = [
    "General skills",
    "Hitting",
    "Throwing",
    "Fielding",
    "Base running",
]
ROWING_FOCUS_OPTIONS = [
    "Technique",
    "Aerobic base",
    "Power",
    "Race prep",
    "Starts / rate change",
    "Race-pace endurance",
]
WEIGHTLIFTING_FOCUS_OPTIONS = [
    "General Olympic lifting",
    "Snatch",
    "Clean & jerk",
    "Strength support",
    "Pulls & positions",
    "Power from the floor",
]
WATER_POLO_FOCUS_OPTIONS = [
    "General development",
    "Swimming conditioning",
    "Shooting",
    "Match skills",
    "Defending / counterattack",
    "Leg drive & eggbeater power",
]

VOLLEYBALL_FOCUS_OPTIONS = [
    "General volleyball development",
    "Serving & first ball pressure",
    "Serve receive / passing",
    "Setting & second contact",
    "Attacking / hitting",
    "Blocking / net defense",
    "Backcourt defense & transition",
    "Game-like rally training",
]


BOXING_FOCUS_OPTIONS = [
    "General boxing development",
    "Footwork & movement",
    "Jab & straight punches",
    "Defense & countering",
    "Combinations on bag/pads",
    "Conditioning for boxing",
    "Ring craft / tactics",
    "Inside fighting / short range work",
]

SPORT_SPECIFIC_GYM_SPORTS = [
    "Running",
    "Tennis",
    "Baseball",
    "Rowing",
    "Weightlifting",
    "Water Polo",
    "Soccer",
    "Boxing",
    "Volleyball",
]
SOCCER_FOCUS_OPTIONS = [
    "General development",
    "Technical development",
    "Finishing",
    "First touch & passing",
    "1v1 attacking / defending",
    "Possession",
    "Build-up play",
    "Pressing & defending",
    "Transition",
    "Small-sided games",
    "Conditioning with the ball",
    "Set pieces",
    "Finishing under pressure",
    "Wide play & crossing",
]

ATP_TOUR_URL = "https://www.atptour.com/en/tournaments"
ATP_CHALLENGER_URL = "https://www.atptour.com/en/atp-challenger-tour/calendar"
ITF_MEN_URL = "https://www.itftennis.com/en/tournament-calendar/mens-world-tennis-tour-calendar/"

def safe_get(url, params=None, timeout=12):
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept-Language": "en-US,en;q=0.9",
    }
    try:
        return requests.get(url, params=params, headers=headers, timeout=timeout)
    except Exception:
        return None

def normalize_text_strict(text):
    text = (text or "").lower().strip()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

def compact_name(text):
    return normalize_text_strict(text).replace(" football club", "").replace(" fc", "").replace(" cf", "").replace(" afc", "").replace(" sc", "").strip()

EXTENDED_SOCCER_CLUB_POOLS = {
    "England": {
        "academy": ["Sunderland Academy", "Blackburn Rovers Academy", "Middlesbrough Academy", "Burnley Academy", "Sheffield United Academy"],
        "semi-pro": ["York City", "Oldham Athletic", "Southend United", "Barnet", "Aldershot Town", "Woking"],
        "second-tier": ["Preston North End", "Bristol City", "Millwall", "Plymouth Argyle", "West Bromwich Albion", "Coventry City"],
        "top-tier": ["Brentford", "Bournemouth", "Brighton", "Fulham", "Wolverhampton Wanderers", "Crystal Palace"],
    },
    "Spain": {
        "academy": ["Sporting Gijon B", "Zaragoza Academy", "Malaga Academy", "Villarreal B", "Levante Academy"],
        "semi-pro": ["Castellon", "Cordoba", "Cultural Leonesa", "Real Murcia", "Ponferradina"],
        "second-tier": ["Eibar", "Oviedo", "Tenerife", "Sporting Gijon", "Burgos", "Huesca"],
        "top-tier": ["Getafe", "Rayo Vallecano", "Osasuna", "Mallorca", "Las Palmas", "Alaves"],
    },
    "Germany": {
        "academy": ["Nurnberg Academy", "Karlsruher SC Academy", "Hannover Academy", "St. Pauli Academy", "Bochum Academy"],
        "semi-pro": ["1860 Munich", "Saarbrucken", "Dynamo Dresden", "Alemannia Aachen", "Rot-Weiss Essen"],
        "second-tier": ["Paderborn", "Fortuna Dusseldorf", "Greuther Furth", "Hamburger SV", "Hannover 96", "Karlsruher SC"],
        "top-tier": ["Augsburg", "Mainz", "Freiburg", "Heidenheim", "Union Berlin", "Werder Bremen"],
    },
    "Italy": {
        "academy": ["Parma Primavera", "Brescia Academy", "Modena Academy", "Empoli Primavera", "Genoa Primavera"],
        "semi-pro": ["Cesena", "Padova", "Pescara", "Vicenza", "Perugia"],
        "second-tier": ["Palermo", "Bari", "Modena", "Sampdoria", "Sudtirol", "Cremonese"],
        "top-tier": ["Torino", "Udinese", "Bologna", "Lecce", "Genoa", "Cagliari"],
    },
    "France": {
        "academy": ["Toulouse Academy", "Auxerre Academy", "Le Havre Academy", "Lorient Academy", "Rennes Academy"],
        "semi-pro": ["Red Star", "Nancy", "Versailles", "Sochaux", "Rouen"],
        "second-tier": ["Caen", "Guingamp", "Amiens", "Paris FC", "Grenoble", "Pau FC"],
        "top-tier": ["Nantes", "Reims", "Strasbourg", "Brest", "Le Havre", "Lens"],
    },
    "Portugal": {
        "academy": ["Braga B", "Vitoria Guimaraes B", "Famalicao U23", "Estoril U23", "Gil Vicente Academy"],
        "semi-pro": ["Leiria", "Academico Viseu", "Oliveirense", "Felgueiras", "Belenenses"],
        "second-tier": ["Tondela", "Maritimo", "Penafiel", "Torreense", "Feirense", "Leixoes"],
        "top-tier": ["Casa Pia", "Rio Ave", "Estoril", "Moreirense", "Farense", "Boavista"],
    },
    "Netherlands": {
        "academy": ["Heerenveen Academy", "Groningen Academy", "Utrecht Academy", "AZ Academy", "Twente Academy"],
        "semi-pro": ["ADO Den Haag", "FC Eindhoven", "MVV Maastricht", "TOP Oss", "Helmond Sport"],
        "second-tier": ["Cambuur", "De Graafschap", "Roda JC", "Emmen", "Den Bosch", "Excelsior"],
        "top-tier": ["NEC Nijmegen", "Go Ahead Eagles", "Sparta Rotterdam", "Heracles", "PEC Zwolle", "Fortuna Sittard"],
    },
    "Belgium": {
        "academy": ["Genk Academy", "Standard Liege Academy", "Gent Academy", "Club Brugge NXT", "Anderlecht Futures"],
        "semi-pro": ["Lierse", "RFC Liege", "Patro Eisden", "RWDM Futures", "Lommel"],
        "second-tier": ["Zulte Waregem", "Beerschot", "Lommel", "Francs Borains", "Deinze"],
        "top-tier": ["Mechelen", "Charleroi", "Cercle Brugge", "OH Leuven", "Westerlo", "Sint-Truiden"],
    },
    "Scotland": {
        "academy": ["Hibernian Academy", "Dundee United Academy", "Aberdeen Academy", "Hearts Academy", "Motherwell Academy"],
        "semi-pro": ["Falkirk", "Partick Thistle", "Raith Rovers", "Queen's Park", "Airdrieonians"],
        "second-tier": ["Inverness", "Dunfermline", "Greenock Morton", "Ayr United", "Hamilton Academical"],
        "top-tier": ["Motherwell", "St Mirren", "Kilmarnock", "Dundee", "Ross County", "Livingston"],
    },
    "Ireland": {
        "academy": ["Shamrock Rovers Academy", "St Patrick's Athletic Academy", "Bohemians Academy", "Derry City Academy"],
        "semi-pro": ["Cobh Ramblers", "Treaty United", "Wexford FC", "Athlone Town", "Finn Harps"],
        "second-tier": ["Waterford", "Galway United", "Cork City", "Shelbourne", "Drogheda United"],
        "top-tier": ["Shamrock Rovers", "St Patrick's Athletic", "Bohemians", "Derry City", "Shelbourne", "Sligo Rovers"],
    },
    "Turkey": {
        "academy": ["Altinordu Academy", "Trabzonspor Academy", "Besiktas Academy"],
        "semi-pro": ["Sakaryaspor", "Boluspor", "Keciorengucu"],
        "second-tier": ["Goztepe", "Erzurumspor", "Bandirmaspor", "Genclerbirligi"],
        "top-tier": ["Kasimpasa", "Alanyaspor", "Sivasspor", "Kayserispor"],
    },
    "Greece": {
        "academy": ["PAOK Academy", "Olympiacos Academy", "Panathinaikos Academy"],
        "semi-pro": ["AEL", "Kissamikos", "Panachaiki"],
        "second-tier": ["Levadiakos", "Kallithea", "AEL"],
        "top-tier": ["Atromitos", "Asteras Tripolis", "OFI Crete", "Volos"],
    },
    "Croatia": {
        "academy": ["Dinamo Zagreb Academy", "Hajduk Split Academy", "Rijeka Academy"],
        "semi-pro": ["Sesvete", "Dubrava", "Orijent"],
        "second-tier": ["Varazdin", "Sibenik", "Vukovar 1991"],
        "top-tier": ["Osijek", "Rijeka", "Slaven Belupo", "Lokomotiva Zagreb"],
    },
    "Poland": {
        "academy": ["Lech Poznan Academy", "Legia Academy", "Pogon Academy"],
        "semi-pro": ["Motor Lublin", "Wisla Plock", "Polonia Warsaw"],
        "second-tier": ["Arka Gdynia", "Wisla Krakow", "GKS Tychy"],
        "top-tier": ["Piast Gliwice", "Widzew Lodz", "Pogon Szczecin", "Cracovia"],
    },
    "Brazil": {
        "academy": ["Athletico Paranaense U20", "Corinthians U20", "Palmeiras U20", "Sao Paulo U20", "Flamengo U20"],
        "semi-pro": ["Portuguesa", "Ferroviaria", "Ypiranga", "Volta Redonda", "Nautico"],
        "second-tier": ["Avai", "Sport Recife", "Ceara", "Goias", "Ponte Preta", "Novorizontino"],
        "top-tier": ["Bragantino", "Bahia", "Fortaleza", "Fluminense", "Atletico Mineiro", "Internacional"],
    },
    "Argentina": {
        "academy": ["River Plate Academy", "Boca Juniors Academy", "Velez Academy", "Talleres Academy"],
        "semi-pro": ["Temperley", "Quilmes", "San Martin Tucuman", "Estudiantes Rio Cuarto"],
        "second-tier": ["Defensa y Justicia", "Belgrano", "Huracan", "Rosario Central"],
        "top-tier": ["Lanus", "Argentinos Juniors", "Talleres", "Newell's Old Boys", "Velez Sarsfield"],
    },
    "Uruguay": {
        "academy": ["Defensor Sporting Academy", "Danubio Academy", "Nacional Academy"],
        "semi-pro": ["Rampla Juniors", "Sud America", "Albion"],
        "second-tier": ["Racing Club Montevideo", "Plaza Colonia", "Cerrito"],
        "top-tier": ["Liverpool Montevideo", "Defensor Sporting", "Boston River", "Cerro Largo"],
    },
    "Colombia": {
        "academy": ["Envigado Academy", "Deportivo Cali Academy", "Atletico Nacional Academy"],
        "semi-pro": ["Llaneros", "Real Cartagena", "Bogota FC"],
        "second-tier": ["Cucuta Deportivo", "Patriotas", "Orsomarso"],
        "top-tier": ["Once Caldas", "Junior", "Deportivo Pasto", "Independiente Medellin"],
    },
    "Chile": {
        "academy": ["Universidad Catolica Academy", "Colo-Colo Academy", "Union Espanola Academy"],
        "semi-pro": ["Rangers de Talca", "San Marcos", "Deportes Temuco"],
        "second-tier": ["Santiago Wanderers", "Cobreloa", "Union San Felipe"],
        "top-tier": ["Huachipato", "Everton de Vina", "Palestino", "Audax Italiano"],
    },
    "Paraguay": {
        "academy": ["Libertad Academy", "Cerro Porteno Academy", "Olimpia Academy"],
        "semi-pro": ["Sportivo Luqueno", "Atyra FC", "Rubio Nu"],
        "second-tier": ["Resistencia", "Guairena", "San Lorenzo"],
        "top-tier": ["Nacional Asuncion", "Guarani", "Libertad", "Cerro Porteno"],
    },
    "Peru": {
        "academy": ["Sporting Cristal Academy", "Alianza Lima Academy", "Universitario Academy"],
        "semi-pro": ["Juan Aurich", "Deportivo Coopsol", "Union Huaral"],
        "second-tier": ["Alianza Universidad", "Santos FC Nazca", "Llacuabamba"],
        "top-tier": ["Sport Huancayo", "Melgar", "Cienciano", "Alianza Atletico"],
    },
    "Ecuador": {
        "academy": ["Independiente del Valle Academy", "LDU Quito Academy", "Barcelona SC Academy"],
        "semi-pro": ["Manta FC", "Imbabura", "Leones del Norte"],
        "second-tier": ["Macara", "Chacaritas", "9 de Octubre"],
        "top-tier": ["Aucas", "Delfin", "El Nacional", "Universidad Catolica"],
    },
    "USA": {
        "academy": ["Philadelphia Union II", "New York Red Bulls II", "FC Dallas Academy", "Atlanta United 2"],
        "semi-pro": ["Richmond Kickers", "Union Omaha", "Northern Colorado Hailstorm", "Forward Madison"],
        "second-tier": ["Louisville City", "Tampa Bay Rowdies", "Sacramento Republic", "Charleston Battery", "Pittsburgh Riverhounds"],
        "top-tier": ["Real Salt Lake", "Colorado Rapids", "Austin FC", "FC Dallas", "Houston Dynamo", "Minnesota United"],
    },
    "Canada": {
        "academy": ["Toronto FC II", "CF Montreal Academy", "Vancouver Whitecaps Academy"],
        "semi-pro": ["Valour FC", "York United", "Pacific FC"],
        "second-tier": ["Forge FC", "HFX Wanderers", "Atletico Ottawa"],
        "top-tier": ["Toronto FC", "CF Montreal", "Vancouver Whitecaps"],
    },
    "Mexico": {
        "academy": ["Pachuca Academy", "Santos Laguna Academy", "Monterrey Academy"],
        "semi-pro": ["Atlante", "Leones Negros", "Celaya"],
        "second-tier": ["Venados", "Cancun FC", "Tepatitlan"],
        "top-tier": ["Pachuca", "Toluca", "Santos Laguna", "Necaxa", "Queretaro", "Mazatlan"],
    },
    "Japan": {
        "academy": ["Kashiwa Reysol Academy", "FC Tokyo Academy", "Yokohama Academy"],
        "semi-pro": ["Iwaki FC", "Ehime FC", "Nagano Parceiro"],
        "second-tier": ["JEF United", "Shimizu S-Pulse", "V-Varen Nagasaki"],
        "top-tier": ["Sagan Tosu", "Gamba Osaka", "Cerezo Osaka", "Avispa Fukuoka"],
    },
    "South Korea": {
        "academy": ["Pohang Academy", "Jeonbuk Academy", "Ulsan Academy"],
        "semi-pro": ["Gimpo FC", "Bucheon FC", "Seoul E-Land"],
        "second-tier": ["Jeonnam Dragons", "Busan IPark", "Anyang"],
        "top-tier": ["Daegu FC", "Gangwon FC", "Incheon United", "Jeju United"],
    },
    "Saudi Arabia": {
        "academy": ["Al Hilal Academy", "Al Nassr Academy", "Al Ittihad Academy"],
        "semi-pro": ["Al Jabalain", "Al Batin", "Al Najma"],
        "second-tier": ["Al Arabi", "Al Faisaly", "Al Qadsiah"],
        "top-tier": ["Al Taawoun", "Al Ettifaq", "Al Fateh", "Al Shabab"],
    },
    "UAE": {
        "academy": ["Al Ain Academy", "Shabab Al Ahli Academy", "Al Jazira Academy"],
        "semi-pro": ["Dubai City", "Gulf FC", "Masfout"],
        "second-tier": ["Al Urooba", "Dibba", "Hatta"],
        "top-tier": ["Al Wahda", "Baniyas", "Al Wasl", "Sharjah"],
    },
    "Qatar": {
        "academy": ["Aspire-linked academy route", "Al Sadd Academy", "Al Duhail Academy"],
        "semi-pro": ["Muaither", "Al Shahaniya", "Al Markhiya"],
        "second-tier": ["Al Khor", "Al Wakrah developmental route", "Mesaimeer"],
        "top-tier": ["Al Gharafa", "Qatar SC", "Umm Salal", "Al Rayyan"],
    },
    "Morocco": {
        "academy": ["Mohammed VI Academy route", "Raja Academy", "Wydad Academy"],
        "semi-pro": ["IZK Khemisset", "Racing Casablanca", "Chabab Mohammedia B"],
        "second-tier": ["Raja Beni Mellal", "Widad Temara", "Olympique Dcheira"],
        "top-tier": ["FUS Rabat", "Maghreb Fez", "Renaissance Zemamra", "Hassania Agadir"],
    },
    "Egypt": {
        "academy": ["Al Ahly Academy", "Zamalek Academy", "Pyramids Academy"],
        "semi-pro": ["Petrojet", "La Viena", "Asyut Petroleum"],
        "second-tier": ["Haras El Hodood", "Tanta", "Misr Lel Makkasa"],
        "top-tier": ["Smouha", "ENPPI", "Ceramica Cleopatra", "Future FC"],
    },
    "South Africa": {
        "academy": ["Mamelodi Sundowns Academy", "SuperSport Academy", "Cape Town City Academy"],
        "semi-pro": ["JDR Stars", "Casric Stars", "Pretoria Callies"],
        "second-tier": ["University of Pretoria", "Orbit College", "Upington City"],
        "top-tier": ["Sekhukhune United", "Stellenbosch", "Cape Town City", "Richards Bay"],
    },
    "Australia": {
        "academy": ["Melbourne City Academy", "Sydney FC Academy", "Central Coast Mariners Academy"],
        "semi-pro": ["South Melbourne", "APIA Leichhardt", "Oakleigh Cannons"],
        "second-tier": ["Canberra United route", "Gold Coast Knights", "Wollongong Wolves"],
        "top-tier": ["Adelaide United", "Western United", "Macarthur FC", "Central Coast Mariners"],
    },
    "New Zealand": {
        "academy": ["Wellington Phoenix Academy", "Auckland Academy route", "Canterbury United Academy"],
        "semi-pro": ["Team Wellington", "Cashmere Technical", "Eastern Suburbs"],
        "second-tier": ["Auckland United", "Christchurch United", "Hamilton Wanderers"],
        "top-tier": ["Wellington Phoenix", "Auckland FC", "Western Springs route"],
    },
}
SOCCER_CLUB_POOLS = EXTENDED_SOCCER_CLUB_POOLS

def build_soccer_team_catalog():
    catalog = []
    for country, bands in SOCCER_CLUB_POOLS.items():
        continent = None
        for cont, countries in SOCCER_COUNTRIES_BY_CONTINENT.items():
            if country in countries:
                continent = cont
                break
        for band, clubs in bands.items():
            for club in clubs:
                aliases = {
                    compact_name(club),
                    compact_name(club.replace("Academy", "").replace(" U20", "").replace(" U23", "")),
                    compact_name(club.replace(" FC", "").replace(" CF", "").replace(" SC", "")),
                }
                catalog.append({
                    "name": club,
                    "country": country,
                    "continent": continent or "",
                    "band": band,
                    "aliases": [a for a in aliases if a],
                })
    return catalog

SOCCER_TEAM_CATALOG = build_soccer_team_catalog()

def search_catalog_team(team_query, max_results=5):
    query = compact_name(team_query)
    if not query:
        return []
    scored = []
    for entry in SOCCER_TEAM_CATALOG:
        names = [compact_name(entry["name"])] + entry.get("aliases", [])
        best = max(difflib.SequenceMatcher(None, query, nm).ratio() for nm in names if nm)
        if query in names or query in compact_name(entry["name"]):
            best = max(best, 0.98)
        if best >= 0.52:
            scored.append({**entry, "match_score": round(best, 3)})
    scored.sort(key=lambda x: x["match_score"], reverse=True)
    return scored[:max_results]

def fetch_online_team_candidates(team_query, max_results=5):
    results = []
    if not team_query.strip():
        return results

    # TheSportsDB
    resp = safe_get("https://www.thesportsdb.com/api/v1/json/3/searchteams.php", params={"t": team_query}, timeout=10)
    if resp and resp.ok:
        try:
            data = resp.json()
            for team in data.get("teams", [])[:max_results]:
                if (team.get("strSport") or "").lower() != "soccer":
                    continue
                results.append({
                    "name": team.get("strTeam"),
                    "country": team.get("strCountry") or "",
                    "league": team.get("strLeague") or "",
                    "stadium": team.get("strStadium") or "",
                    "source": "TheSportsDB",
                })
        except Exception:
            pass

    # Wikipedia opensearch fallback
    if len(results) < max_results:
        wiki = safe_get(
            "https://en.wikipedia.org/w/api.php",
            params={
                "action": "opensearch",
                "search": f"{team_query} football club",
                "limit": max_results,
                "namespace": 0,
                "format": "json",
            },
            timeout=10,
        )
        if wiki and wiki.ok:
            try:
                data = wiki.json()
                titles = data[1] if len(data) > 1 else []
                descs = data[2] if len(data) > 2 else []
                for title, desc in zip(titles, descs):
                    results.append({
                        "name": title,
                        "country": "",
                        "league": desc,
                        "stadium": "",
                        "source": "Wikipedia",
                    })
            except Exception:
                pass

    unique = []
    seen = set()
    for item in results:
        key = compact_name(item.get("name", ""))
        if key and key not in seen:
            seen.add(key)
            unique.append(item)
    return unique[:max_results]

def infer_band_from_team_name(text):
    t = normalize_text_strict(text)
    if any(k in t for k in ["academy", "u17", "u18", "u19", "u20", "u21", "u23", "ii", "b team", "reserves"]):
        return "academy"
    if any(k in t for k in ["premier league", "serie a", "la liga", "bundesliga", "ligue 1", "mls", "j1 league", "pro league", "super lig", "champions league"]):
        return "top-tier"
    if any(k in t for k in ["championship", "segunda", "serie b", "2nd division", "second division", "ligue 2", "2. bundesliga", "j2", "usl championship", "primeira liga 2", "first league"]):
        return "second-tier"
    if any(k in t for k in ["semi", "amateur", "regional", "national league", "league one", "league two", "serie c", "third division", "non league"]):
        return "semi-pro"
    return "semi-pro"

def resolve_team_profile(team_query):
    query = (team_query or "").strip()
    if not query:
        return {
            "query": "",
            "best_name": "Unknown team",
            "country": "",
            "continent": "",
            "band": "semi-pro",
            "confidence": "low",
            "catalog_matches": [],
            "online_matches": [],
        }

    catalog_matches = search_catalog_team(query, max_results=5)
    online_matches = fetch_online_team_candidates(query, max_results=5)
    if catalog_matches:
        best = catalog_matches[0]
        confidence = "high" if best["match_score"] >= 0.82 else "medium"
        return {
            "query": query,
            "best_name": best["name"],
            "country": best["country"],
            "continent": best["continent"],
            "band": best["band"],
            "confidence": confidence,
            "catalog_matches": catalog_matches,
            "online_matches": online_matches,
        }

    fallback_band = infer_band_from_team_name(query)
    guessed_country = ""
    for continent, countries in SOCCER_COUNTRIES_BY_CONTINENT.items():
        for country in countries:
            if country.lower() in query.lower():
                guessed_country = country
                break
        if guessed_country:
            break

    if online_matches:
        best = online_matches[0]
        return {
            "query": query,
            "best_name": best["name"],
            "country": best.get("country", "") or guessed_country,
            "continent": "",
            "band": fallback_band,
            "confidence": "medium",
            "catalog_matches": [],
            "online_matches": online_matches,
        }

    return {
        "query": query,
        "best_name": query,
        "country": guessed_country,
        "continent": "",
        "band": fallback_band,
        "confidence": "low",
        "catalog_matches": [],
        "online_matches": [],
    }

def parse_contract_offers_richer(offers_text):
    raw = (offers_text or "").strip()
    if not raw:
        return []
    offers = re.split(r",|\n|;", raw)
    return [x.strip() for x in offers if x.strip()]

def recommend_soccer_move(
    current_team,
    current_level,
    age_band,
    position,
    target_continent,
    target_country,
    contract_offers_text,
    ambition,
):
    current_team_profile = resolve_team_profile(current_team)
    current_band_default = map_current_level_to_band(current_level)
    current_band = current_team_profile["band"] if current_team_profile["confidence"] != "low" else current_band_default

    allowed_bands = conservative_allowed_targets(current_band, age_band)
    desired_band = choose_recommended_band(current_band, age_band, ambition)

    evaluated_offers = []
    for offer in parse_contract_offers_richer(contract_offers_text):
        offer_profile = resolve_team_profile(offer)
        offer_band = offer_profile["band"] if offer_profile["confidence"] != "low" else band_from_offer_text(offer)
        offer_country = offer_profile.get("country") or extract_country_from_offer_text(offer, target_country)

        score = 0
        if offer_band in allowed_bands:
            score += 35
        else:
            score -= 20

        if desired_band == offer_band:
            score += 18
        score += country_fit_bonus(target_country, offer_country)

        if current_team_profile.get("country") and offer_country and current_team_profile["country"] == offer_country:
            score += 4

        if position == "Goalkeeper":
            score += 3
        elif position in ["Centre back", "Defensive midfielder", "Central midfielder"]:
            score += 4
        elif position in ["Winger", "Striker"]:
            score += 2

        if "academy" in offer.lower() and age_band == "Senior":
            score -= 10

        evaluated_offers.append({
            "offer": offer,
            "resolved_name": offer_profile["best_name"],
            "band": offer_band,
            "country": offer_country,
            "score": score,
            "confidence": offer_profile["confidence"],
        })

    target_pool = SOCCER_CLUB_POOLS.get(target_country, {})
    conservative_pool = target_pool.get(desired_band, [])
    club_suggestion = random.choice(conservative_pool) if conservative_pool else f"a {desired_band} club in {target_country}"

    recommended_offer = None
    if evaluated_offers:
        evaluated_offers = sorted(evaluated_offers, key=lambda x: x["score"], reverse=True)
        if evaluated_offers[0]["score"] >= 18:
            recommended_offer = evaluated_offers[0]

    if recommended_offer:
        final_team = recommended_offer["resolved_name"] or recommended_offer["offer"]
        reasoning = (
            f"The best fit is **{final_team}** because it looks like a realistic step from the current profile, "
            f"fits the requested destination better, and does not over-jump the player's stage."
        )
        verdict_type = "offer"
    else:
        final_team = club_suggestion
        reasoning = (
            f"The safest recommendation is **{final_team}**. Based on the current profile, age band, and target country, "
            f"this looks like a more realistic next step than forcing an aggressive jump."
        )
        verdict_type = "catalog"

    summary_lines = [
        f"Current team search result: {current_team_profile['best_name']} ({current_team_profile['confidence']} confidence)",
        f"Current level interpreted as: {current_level}",
        f"Movement band recommended: {desired_band}",
        f"Allowed realistic band(s): {', '.join(allowed_bands)}",
    ]
    if current_team_profile.get("country"):
        summary_lines.append(f"Detected current country: {current_team_profile['country']}")

    conservative_warning = (
        "This engine is intentionally conservative. It tries to avoid jumps that look impressive on paper "
        "but are weak development decisions in reality."
    )
    return {
        "final_team": final_team,
        "verdict_type": verdict_type,
        "reasoning": reasoning,
        "evaluated_offers": evaluated_offers,
        "summary_lines": summary_lines,
        "conservative_warning": conservative_warning,
        "current_team_profile": current_team_profile,
        "catalog_suggestions": conservative_pool[:6],
    }

def extract_live_events_from_atp_page(url, page_label):
    response = safe_get(url, timeout=12)
    events = []
    if not response or not response.ok:
        return events

    html = response.text
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(" ", strip=True)

    display_year = TODAY.year
    month_blocks = re.split(r"(January|February|March|April|May|June|July|August|September|October|November|December),?\s+" + str(display_year), text)
    if len(month_blocks) < 3:
        return events

    current_month = None
    for part in month_blocks:
        if part in ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]:
            current_month = part
            continue
        if not current_month:
            continue
        # catch patterns like "Monza, Italy 14-20 Apr, 2026 Challenger Tour-125"
        for match in re.finditer(r"([A-Z][A-Za-z\-\.\' ]+),\s*([A-Z][A-Za-z\-\.\' ]+)\s+(\d{1,2})-(\d{1,2})\s+" + current_month[:3] + r",\s*" + str(display_year) + r"\s+([^\.]{3,90})", part):
            city = match.group(1).strip()
            country = match.group(2).strip()
            day1 = int(match.group(3))
            day2 = int(match.group(4))
            name = match.group(5).strip()
            try:
                month_num = datetime.strptime(current_month[:3], "%b").month
                start = date(display_year, month_num, day1)
            except Exception:
                continue
            surface = "Hard"
            label = page_label
            if "challenger" in name.lower():
                level = "Challenger"
            else:
                if "masters" in name.lower():
                    level = "ATP Masters 1000"
                elif "500" in name:
                    level = "ATP 500"
                elif "250" in name:
                    level = "ATP 250"
                else:
                    level = page_label
            events.append({
                "name": name.title(),
                "tour": page_label,
                "level": "Challenger" if "Challenger" in page_label else level,
                "city": city.title(),
                "country": country.title(),
                "surface": surface,
                "region": infer_region_from_country(country.title()),
                "start_date": start.isoformat(),
                "estimated_direct_acceptance_best_fit": (1, 350) if "ATP" in page_label else (120, 420),
                "estimated_qualifying_fit": (250, 800) if "ATP" in page_label else (250, 950),
                "notes": "Pulled from official calendar page. Confirm entry list and deadlines on the live event page.",
            })
    return events

def infer_region_from_country(country):
    for continent, countries in SOCCER_COUNTRIES_BY_CONTINENT.items():
        if country in countries:
            return continent
    country = (country or "").lower()
    if country in ["tunisia", "morocco", "egypt", "south africa"]:
        return "Africa"
    if country in ["australia", "new zealand"]:
        return "Oceania"
    return "Europe"

def fetch_live_itf_calendar(limit=40):
    resp = safe_get(ITF_MEN_URL, timeout=12)
    events = []
    if not resp or not resp.ok:
        return events
    text = BeautifulSoup(resp.text, "html.parser").get_text(" ", strip=True)

    display_year = TODAY.year
    pattern = re.compile(r"([A-Z][A-Za-z\-\.\' ]+),\s*([A-Z][A-Za-z\-\.\' ]+)\s*\|\s*(\d{1,2})\s*-\s*(\d{1,2})\s*([A-Za-z]{3})\s*" + str(display_year))
    for match in pattern.finditer(text):
        city = match.group(1).strip()
        country = match.group(2).strip()
        day1 = int(match.group(3))
        mon = match.group(5)
        try:
            month_num = datetime.strptime(mon, "%b").month
            start = date(display_year, month_num, day1)
        except Exception:
            continue
        events.append({
            "name": f"ITF M15/M25 event - {city.title()}",
            "tour": "ITF World Tennis Tour",
            "level": "ITF",
            "city": city.title(),
            "country": country.title(),
            "surface": "No confirmed surface yet",
            "region": infer_region_from_country(country.title()),
            "start_date": start.isoformat(),
            "estimated_direct_acceptance_best_fit": (250, 1800),
            "estimated_qualifying_fit": (600, 3000),
            "notes": "Pulled from the official ITF men's calendar. Open the live page to confirm category and acceptance list.",
        })
        if len(events) >= limit:
            break
    return events

def fetch_live_tennis_events():
    live_events = []
    # keep static curated events as fallback and for richer metadata
    fallback = [e for e in UPCOMING_TOURNAMENTS if parse_date(e["start_date"]) >= TODAY - timedelta(days=7)]

    live_atp = extract_live_events_from_atp_page(ATP_TOUR_URL, "ATP Tour")
    live_ch = extract_live_events_from_atp_page(ATP_CHALLENGER_URL, "ATP Challenger Tour")
    live_itf = fetch_live_itf_calendar(limit=24)

    combined = fallback + live_atp + live_ch + live_itf
    deduped = {}
    for e in combined:
        key = (e.get("name", "").lower(), e.get("city", "").lower(), e.get("country", "").lower(), e.get("start_date"))
        deduped[key] = e
    fresh = [e for e in deduped.values() if parse_date(e["start_date"]) >= TODAY - timedelta(days=7)]
    return sorted(fresh, key=lambda x: parse_date(x["start_date"]))

def level_preference_score(target_level, event_level):
    if target_level == "Best fit":
        return 0
    if target_level == event_level:
        return 18
    if target_level == "ITF" and event_level in ["ITF", "M15", "M25"]:
        return 18
    if target_level == "Challenger" and "challenger" in event_level.lower():
        return 18
    if target_level == "ATP Tour" and event_level.startswith("ATP"):
        return 18
    return -8

def recommend_tournaments(player_ranking, player_region, preferred_surface, target_level, main_goal=None, travel_style=None):
    scored = []
    source_events = fetch_live_tennis_events()
    for event in source_events:
        score = 0
        rank_score, rank_note = ranking_fit_score(player_ranking, event)
        score += rank_score
        score += region_match_score(player_region, event["region"])
        if event["surface"] in ["Clay", "Hard", "Grass"]:
            score += surface_match_score(preferred_surface, event["surface"])
        score += level_preference_score(target_level, event["level"])

        if main_goal == "Get into the draw":
            score += 10 if "direct" in rank_note.lower() else 0
        elif main_goal == "Get matches and confidence":
            score += 8 if event["level"] in ["ITF", "M15", "M25", "Challenger"] else -3
        elif main_goal == "Stay on preferred surface":
            score += 8 if event["surface"] == preferred_surface else 0

        if travel_style == "Stay close / reduce travel":
            score += region_match_score(player_region, event["region"]) // 2
        elif travel_style == "Surface matters most" and event["surface"] == preferred_surface:
            score += 6

        scored.append({**event, "score": score, "ranking_note": rank_note})
    return sorted(scored, key=lambda x: (x["score"], -parse_date(x["start_date"]).toordinal()), reverse=True)

def generate_running_plan(role, goal, level, injury_status, pain_score, session_time, running_focus, running_distance, context, running_session_style="Best fit for my goal"):
    minutes = time_to_minutes(session_time)
    category = running_distance_category(running_distance)

    if goal_is_learning(goal) or running_session_style == "Technique + efficiency":
        return format_plan(
            title=f"Running Mechanics Session{context['title_suffix']}",
            focus=f"Efficient running mechanics for {running_distance}",
            warmup=[
                "5 min brisk walk",
                "5 min easy jog",
                "Dynamic ankle and hip mobility",
                "2 x 20m marching + 2 x 20m skips",
            ],
            main_work=[
                "3 x 20m A-march",
                "3 x 20m A-skip",
                "4 x 60m relaxed strides focusing on posture and arm rhythm",
                "12-18 min easy running with cadence and relaxation focus",
            ],
            strength=[
                "2 x 8 split squats each side",
                "2 x 8 single-leg calf raises each side",
                "2 x 25 sec plank",
            ],
            cooldown=["5 min walk", "Gentle calf and hip mobility"],
            coach_block=context["coach_notes"],
            notes=["Stay relaxed through the shoulders.", "Do not force speed while cleaning up mechanics."],
        )

    if running_session_style == "Hill work":
        main = [
            "8-10 min easy build run",
            "6-10 x 10-20 sec hill sprint or strong hill stride, full walk-back rest",
            "8-12 min easy aerobic running after hills",
        ]
        strength = [
            "3 x 6 goblet squats",
            "3 x 8 calf raises",
            "2 x 8 reverse lunges each side",
        ]
        focus = f"Hill power and mechanics for {running_distance}"
    elif running_session_style == "Intervals / tempo":
        if category == "short":
            main = ["4 x 60m build-ups", "6 x 100m fast but relaxed, 90 sec rest", "4 x 150m rhythm work, 2 min rest"]
        elif category == "medium":
            main = ["10 min easy run", "5 x 3 min threshold, 90 sec jog", "4 x 200m quicker but smooth finish"]
        else:
            main = [f"20 min steady run", "3 x 8 min strong aerobic work, 2 min easy", "5-10 min easy cool extension"]
        strength = [
            "3 x 8 step-ups each side",
            "2 x 8 single-leg RDL each side",
            "2 x 30 sec side plank each side",
        ]
        focus = f"Controlled interval support for {running_distance}"
    else:
        return generate_running_plan.__wrapped__(role, goal, level, injury_status, pain_score, session_time, running_focus, running_distance, context)  # type: ignore

    if beginner_modifier(level):
        main.insert(0, "Keep intensity controlled and leave some reserve.")
    if role == "Coach":
        main.insert(0, "Start reps on a whistle and keep recoveries identical for the group.")

    return format_plan(
        title=f"Running Session{context['title_suffix']}",
        focus=focus,
        warmup=["5-10 min easy jog", "Dynamic mobility", "Running drills: march, skip, leg swings"],
        main_work=main,
        strength=strength,
        cooldown=["5-8 min easy jog or walk", "Gentle lower-body mobility"],
        coach_block=context["coach_notes"],
        notes=["Quality mechanics first.", "Stop if pain rises during the workout."],
    )

# attach original as fallback
generate_running_plan.__wrapped__ = _original_generate_running_plan

def generate_gym_plan(role, goal, level, injury_status, pain_score, session_time, gym_style, context):
    if gym_style == "Power / explosiveness":
        return format_plan(
            title=f"Gym Power Session{context['title_suffix']}",
            focus="Explosive power with safe strength support",
            warmup=[
                "5 min bike or rower",
                "Dynamic ankle, hip, and shoulder prep",
                "2 progressive medicine-ball throw sets",
            ],
            main_work=[
                "4 x 3 trap-bar jump or light jump squat",
                "4 x 4 push press or landmine push press",
                "4 x 4 med-ball scoop toss / chest throw",
                "4 x 5 box step-up drive each side",
            ],
            strength=[
                "3 x 5 Romanian deadlift",
                "3 x 6 pull-up / pulldown",
                "2 x 20 sec Copenhagen plank or side plank",
            ],
            cooldown=["Easy walk", "Hip flexor, glute, and pec mobility"],
            coach_block=context["coach_notes"],
            notes=["Move fast with good positions.", "Stop explosive work if pain or technique falls off."],
        )
    return generate_gym_plan.__wrapped__(role, goal, level, injury_status, pain_score, session_time, gym_style, context)
generate_gym_plan.__wrapped__ = _original_generate_gym_plan

def generate_tennis_plan(role, goal, level, injury_status, pain_score, session_time, tennis_focus, context):
    if tennis_focus == "Net play / transition":
        return format_plan(
            title=f"Tennis Transition Session{context['title_suffix']}",
            focus="Approach, first volley, and transition confidence",
            warmup=[
                "5 min easy movement and shadow swings",
                "Mini-tennis emphasizing touch",
                "Split-step and first-step activation",
            ],
            main_work=[
                "Approach-shot pattern: 4 x 6 reps each side",
                "Approach + first volley + recovery: 5 rounds",
                "2-ball transition drill: deep ball then close to net",
                "Short points starting with an approach opportunity",
            ],
            strength=[
                "3 x 8 split squat each side",
                "3 x 8 band row or TRX row",
                "2 x 20 sec lateral core hold each side",
            ],
            cooldown=["Easy rally or walk", "Shoulder, forearm, and hip mobility"],
            coach_block=context["coach_notes"],
            notes=["First volley should be balanced, not rushed.", "Recover after the volley, do not admire the shot."],
        )
    return generate_tennis_plan.__wrapped__(role, goal, level, injury_status, pain_score, session_time, tennis_focus, context)
generate_tennis_plan.__wrapped__ = _original_generate_tennis_plan

def generate_baseball_plan(role, goal, level, injury_status, pain_score, session_time, baseball_focus, context):
    if baseball_focus == "Base running":
        return format_plan(
            title=f"Baseball Base-Running Session{context['title_suffix']}",
            focus="First-step speed, turns, and smart base running",
            warmup=[
                "5 min easy jog",
                "Dynamic hip, ankle, and hamstring prep",
                "2 x 20m acceleration build-ups",
            ],
            main_work=[
                "6 x first-step reactions from base-running stance",
                "6 x 15-20m acceleration with hard first three steps",
                "Round-first-base turn drill: 6 reps each direction",
                "Read-and-go reactions on coach clap/visual cue",
            ],
            strength=[
                "3 x 6 goblet squat",
                "3 x 8 reverse lunge each side",
                "2 x 20 sec plank",
            ],
            cooldown=["Easy walk", "Calf, hamstring, and hip flexor mobility"],
            coach_block=context["coach_notes"],
            notes=["Explode early, stay low, and run through decisions clearly."],
        )
    return generate_baseball_plan.__wrapped__(role, goal, level, injury_status, pain_score, session_time, baseball_focus, context)
generate_baseball_plan.__wrapped__ = _original_generate_baseball_plan

def generate_rowing_plan(role, goal, level, injury_status, pain_score, session_time, rowing_focus, context):
    if rowing_focus == "Starts / rate change":
        return format_plan(
            title=f"Rowing Rate-Change Session{context['title_suffix']}",
            focus="Starts, bursts, and rate shifts without losing sequence",
            warmup=[
                "8 min easy erg",
                "Pick drill progression",
                "Progressive 10-stroke builds",
            ],
            main_work=[
                "6 practice starts of 10-15 hard strokes",
                "5 x (20 hard strokes + settle into 90 sec controlled rowing)",
                "4 x 3 min at race rhythm with planned rate changes",
            ],
            strength=[
                "3 x 6 Romanian deadlift",
                "3 x 8 seated row",
                "2 x 20 sec hollow hold",
            ],
            cooldown=["5 min very easy row", "Hamstring, glute, and lat mobility"],
            coach_block=context["coach_notes"],
            notes=["The sequence must stay clean even when the rate changes."],
        )
    return generate_rowing_plan.__wrapped__(role, goal, level, injury_status, pain_score, session_time, rowing_focus, context)
generate_rowing_plan.__wrapped__ = _original_generate_rowing_plan

def generate_weightlifting_plan(role, goal, level, injury_status, pain_score, session_time, wl_focus, context):
    if wl_focus == "Pulls & positions":
        return format_plan(
            title=f"Weightlifting Positions Session{context['title_suffix']}",
            focus="Bar path, pull quality, and receiving positions",
            warmup=[
                "5 min easy cardio",
                "Ankle, hip, thoracic, and wrist prep",
                "Bar-only position drills",
            ],
            main_work=[
                "4 x 3 snatch pull from floor or blocks",
                "4 x 3 clean pull",
                "4 x 2 pause front squat",
                "4 x 2 muscle snatch or tall clean technique work",
            ],
            strength=[
                "3 x 5 Romanian deadlift",
                "3 x 6 strict press or push press",
                "2 x 20 sec overhead stability hold",
            ],
            cooldown=["Easy walk", "Wrist, thoracic, and hip mobility"],
            coach_block=context["coach_notes"],
            notes=["Stay patient to the power position and finish tall."],
        )
    return generate_weightlifting_plan.__wrapped__(role, goal, level, injury_status, pain_score, session_time, wl_focus, context)
generate_weightlifting_plan.__wrapped__ = _original_generate_weightlifting_plan

def generate_water_polo_plan(role, goal, level, injury_status, pain_score, session_time, wp_focus, context):
    if wp_focus == "Defending / counterattack":
        return format_plan(
            title=f"Water Polo Defensive Session{context['title_suffix']}",
            focus="Defensive body position and fast counterattack reactions",
            warmup=[
                "200-300m easy swim",
                "Dynamic shoulder prep",
                "Eggbeater activation and head-up swim prep",
            ],
            main_work=[
                "4 x 30 sec defensive leg-drive holds",
                "6 x 15m head-up reaction sprint",
                "Mirror-defending footwork and body-position drill",
                "Defend then break into counterattack: 6-8 reps",
            ],
            strength=[
                "3 x 10 band external rotation",
                "3 x 8 push-up variation",
                "2 x 20 sec hollow hold",
            ],
            cooldown=["100-200m easy swim", "Shoulder and hip mobility"],
            coach_block=context["coach_notes"],
            notes=["Stay balanced with hands active, then explode forward in transition."],
        )
    return generate_water_polo_plan.__wrapped__(role, goal, level, injury_status, pain_score, session_time, wp_focus, context)
generate_water_polo_plan.__wrapped__ = _original_generate_water_polo_plan

def generate_soccer_player_plan(goal, level, injury_status, pain_score, session_time, soccer_focus, soccer_position, context):
    minutes = time_to_minutes(session_time)
    small_group = "Small Group" in context["title_suffix"]
    solo = "Solo" in context["title_suffix"]

    if goal_is_learning(goal):
        main = [
            "Ball mastery ladder: 8 x 40 sec (inside-inside, outside-outside, sole rolls, pull-push)",
            "Passing and receiving block: wall / target / partner, 10-12 min",
            "First touch away from pressure: 4 x 5 reps each side",
            "Small finishing block: 5 x 3 reps or 8-10 target strikes",
            "Short conditioned game or directional dribble challenge",
        ]
        return format_plan(
            title=f"Soccer Fundamentals Session{context['title_suffix']}",
            focus=f"Learn how to play better - {soccer_position}",
            warmup=[
                "5 min easy movement with the ball",
                "Dynamic mobility: ankles, hips, groin",
                "2 x 20m skips + 2 x 20m build runs",
            ],
            main_work=main,
            strength=[
                "3 x 6 goblet squats",
                "3 x 10m acceleration sprints",
                "2 x 8 split squats each side",
                "2 x 20 sec side plank each side",
            ],
            cooldown=["Light ball touches and walk", "Adductor, calf, and hip flexor mobility"],
            coach_block=context["coach_notes"],
            notes=["A good first touch creates the next action.", "Keep the head up between contacts."],
        )

    if solo:
        focus_map = {
            "Technical development": [
                "Ball mastery matrix: 10 x 30-40 sec",
                "Wall or target passing: 5 x 2 min",
                "Receive across the body into next action: 5 x 5 reps each side",
                "Acceleration out of touch: 6 x 10-15m",
            ],
            "Finishing": [
                "First touch into strike setup: 5 x 4 reps each side",
                "Finishing on the move or into mini-targets: 18-24 total strikes",
                "Rebound finish or second-action finish: 8-10 reps",
                "3 x 15m sprint after shot to simulate recovery",
            ],
            "First touch & passing": [
                "Wall passing both feet: 6 x 90 sec",
                "One-touch / two-touch alternation: 4 rounds",
                "Open body receive into next pass: 5 x 6 reps",
                "Scan-touch-pass pattern with cone gates",
            ],
            "1v1 attacking / defending": [
                "Change-of-direction dribble circuit: 6 rounds",
                "Explosive first-step exit after feint: 8 reps each side",
                "Defensive footwork shadowing pattern: 6 x 20 sec",
                "Recovery sprint after each rep: 6 x 12m",
            ],
            "Possession": [
                "Tight-space receiving circuit with gates",
                "Two-touch rhythm block: 5 x 90 sec",
                "Half-turn receiving pattern: 5 x 5 reps",
                "Tempo dribble plus release pass to target",
            ],
            "Build-up play": [
                "Back-foot receiving pattern: 5 x 5 reps each side",
                "Open-body passing sequence: 5 rounds",
                "Receive under passive time pressure then play out",
                "10 x 15m support movement before next pass",
            ],
            "Pressing & defending": [
                "Approach angle footwork: 6 x 15 sec",
                "Press-stop-press reactions: 6 reps",
                "Recovery run and body-shape drill: 6 x 15m",
                "Tackle technique on stationary ball or cone target",
            ],
            "Transition": [
                "Win-it-and-go dribble bursts: 8 reps",
                "Turn and accelerate: 6 x 15m",
                "Receive then attack space immediately: 6 reps",
                "Recovery sprint back to start after each action",
            ],
            "Small-sided games": [
                "Cone-gate dribble and decision circuit",
                "Touch-limit technical challenge",
                "Pass-move-receive pattern with time pressure",
                "1 min work / 30 sec rest technical competition rounds",
            ],
            "Conditioning with the ball": [
                "4 x 3 min ball-carry circuits, 75 sec rest",
                "6 x 20 sec dribble speed burst / 40 sec easy touches",
                "4 x 15m sprint after technical action",
            ],
            "Set pieces": [
                "Crossing / driven-ball target practice: 12-20 reps",
                "Corners or free-kick delivery into zones: 10-16 reps",
                "Rebound second-ball action after each service",
            ],
            "Finishing under pressure": [
                "First touch from awkward angle into finish: 10 reps each side",
                "Quick reset + second finish within 4 sec: 8 reps",
                "Sprint before finish to raise heart rate: 6 rounds",
            ],
            "General development": [
                "Ball mastery block",
                "Passing/receiving block",
                "Acceleration and change-of-direction block",
                "Short finishing block",
            ],
        }
    else:
        focus_map = {
            "Technical development": [
                "Rondo progression: 8-12 min",
                "Passing-and-move pattern with third-man option: 10 min",
                "Directional possession game with touch limit: 3 x 3-4 min",
                "Small game with technical scoring bonus",
            ],
            "Finishing": [
                "Combination into finish: 8-12 reps each side",
                "Crossing and finishing or cutback finishing block",
                "Transition finish after a regain: 6-10 reps",
                "Small-sided game where goals count double after fast finish",
            ],
            "First touch & passing": [
                "4-corner receive-play-move circuit",
                "Rondo with body orientation coaching point",
                "Receive under pressure into next pass: 4 x 3 min",
                "Directional keep-ball with limited touches",
            ],
            "1v1 attacking / defending": [
                "1v1 lane duels both sides",
                "Defender recovery angle starts",
                "2v2 to mini-goals with immediate transition",
                "Short conditioned game rewarding successful duels",
            ],
            "Possession": [
                "Rondo progression 4v2 / 5v2",
                "Positional keep-ball with zone targets",
                "7v7 or adapted possession game with support rules",
                "Final free game with touch/spacing focus",
            ],
            "Build-up play": [
                "Back-line + midfielder circulation pattern",
                "Play through lines into target player",
                "Build-up against pressing unit in a half-pitch scenario",
                "Conditioned game starting from goalkeeper or back line",
            ],
            "Pressing & defending": [
                "Pressing triggers walk-through then live reps",
                "Front-foot defending in channels",
                "Unit compactness drill: press, delay, cover",
                "Conditioned game where regain in target zone gives bonus",
            ],
            "Transition": [
                "3-team transition game",
                "Regain-and-attack in 6 seconds challenge",
                "Recovery-run and counterpress block",
                "Transition-focused conditioned match",
            ],
            "Small-sided games": [
                "3v3 / 4v4 game with mini-goals",
                "Directional overload game",
                "Neutral-player possession game",
                "Final game with one coaching point only",
            ],
            "Conditioning with the ball": [
                "4 x 4 min conditioned possession, 90 sec rest",
                "Repeated dribble-sprint-return circuits",
                "Wave game with work:rest control",
            ],
            "Set pieces": [
                "Corners: attacking and defensive jobs",
                "Wide free-kick delivery and second-ball reaction",
                "Throw-in or restart pattern work",
                "Short game after every restart ball",
            ],
            "Finishing under pressure": [
                "Finish after contact or chase: 8-12 reps",
                "2v1 / 3v2 fast-break finishing",
                "Chaos-box finishing with rebounds and second balls",
                "Conditioned game where shots must come within 6 sec of entry",
            ],
            "General development": [
                "Rondo warm technical block",
                "Passing-and-moving pattern",
                "Small-sided directional game",
                "Short finishing / sprint block",
            ],
        }

    main = focus_map.get(soccer_focus, focus_map["General development"])

    if soccer_position == "Goalkeeper":
        main = [
            "Footwork and set-position prep with the ball",
            "Handling/distribution block",
            "Collapse/diving or reaction save block if safe and relevant",
            "GK + team-build-up involvement pattern",
        ]

    return format_plan(
        title=f"Soccer Session{context['title_suffix']}",
        focus=f"Soccer development - {soccer_focus} - {soccer_position}",
        warmup=[
            "5-8 min dynamic movement with ball",
            "Mobility: ankles, hips, groin",
            "Passing activation or technical rhythm block",
        ],
        main_work=main,
        strength=[
            "3 x 5 goblet squats or split squats",
            "6 x 10-20m sprints with full quality",
            "2 x 6 single-leg RDL each side",
            "2 x 20 sec Copenhagen or side plank",
        ],
        cooldown=[
            "Light possession / walking recovery",
            "Adductor, calf, hamstring, and hip flexor mobility",
        ],
        coach_block=context["coach_notes"],
        notes=[
            "A real soccer session needs ball actions, decisions, and game-like actions, not only generic fitness.",
            "Keep sprint quality high and do not turn every rep into conditioning for no reason.",
        ],
    )

def generate_soccer_coach_plan(goal, session_time, soccer_focus, soccer_position, age_group, coach_level, people_training, context):
    age_label = age_group or "Mixed group"
    base_strength = [
        "3 x 5 squats or split squats",
        "5-6 x 10-15m quality sprints",
        "2 x 20 sec trunk stability hold",
    ]

    if goal_is_learning(goal):
        return format_plan(
            title=f"Soccer Coach Session{context['title_suffix']}",
            focus=f"Teach soccer basics clearly - {age_label}",
            warmup=[
                "Arrival ball game - every player active immediately",
                "Dynamic movement prep and tag game with ball",
            ],
            main_work=[
                "Ball mastery in grids",
                "Passing and receiving in pairs / triangles",
                "1v1 or 2v1 simple directional game",
                "Small-sided game with one simple coaching point",
            ],
            strength=base_strength,
            cooldown=["Walk, light stretches, positive recap"],
            coach_block=[
                f"Players: about {people_training}",
                f"Age band: {age_label}",
                f"Level: {coach_level}/10",
                "Keep lines short and touches high.",
                "Explain briefly, demonstrate, then let them play.",
            ],
            notes=["For younger groups, repetition and enjoyment matter a lot."],
        )

    if soccer_focus == "Possession":
        main = [
            "Rondo progression with clear body-shape cues",
            "Positional game with overload",
            "7v7 or adapted possession game with pitch zones",
            "Final game where bonus comes from switching or line-breaking pass",
        ]
    elif soccer_focus == "Build-up play":
        main = [
            "Back-line circulation pattern unopposed",
            "Build-up vs pressing unit in waves",
            "Play through midfield targets and attack mini-goals",
            "Conditioned game restarting from goalkeeper each time",
        ]
    elif soccer_focus == "Pressing & defending":
        main = [
            "Pressing triggers walk-through",
            "Channel defending 1v1 / 2v2",
            "Unit compactness and cover-shadow drill",
            "Game where regain in target zone is worth bonus points",
        ]
    elif soccer_focus == "Transition":
        main = [
            "Win-it-and-go transition exercise",
            "Counterpress for 5-6 seconds after loss",
            "3-team transition game",
            "Fast-break conditioned game",
        ]
    elif soccer_focus == "Finishing":
        main = [
            "Combination into finish both sides",
            "Crossing / cutback finishing",
            "Transition finish after regain",
            "Finishing competition or conditioned game",
        ]
    elif soccer_focus == "Set pieces":
        main = [
            "Corner delivery and jobs",
            "Wide free-kick attacking and defensive shape",
            "Second-ball reaction work",
            "Restart game with repeated restarts",
        ]
    elif soccer_focus == "Small-sided games":
        main = [
            "3v3 / 4v4 game with coaching theme",
            "Neutral-player overload game",
            "Directional transition game",
            "Final competitive game",
        ]
    elif soccer_focus == "Finishing under pressure":
        main = [
            "Finish after chase/contact",
            "2v1 / 3v2 fast-break finishing",
            "Chaos-box second-ball finishing",
            "Game where shots must come quickly after entry",
        ]
    else:
        main = [
            "Rondo or technical activation",
            "Themed main exercise",
            "Game-related exercise",
            "Final conditioned game",
        ]

    coach_block = [
        f"Players: about {people_training}",
        f"Age band: {age_label}",
        f"Level: {coach_level}/10",
        "Size the area based on player number and quality.",
        "Coach the few key details that matter most for the exercise.",
    ]
    if people_training <= 6:
        coach_block.append("Small group: maximize reps and rotate roles quickly.")
    elif people_training >= 16:
        coach_block.append("Bigger group: split the area or run two stations to reduce waiting.")

    if soccer_position == "Goalkeeper":
        coach_block.append("Add a goalkeeper detail block: set position, distribution, and communication.")

    return format_plan(
        title=f"Soccer Coach Session{context['title_suffix']}",
        focus=f"Soccer coaching session - {soccer_focus} - {age_label}",
        warmup=[
            "Dynamic movement and ball activation",
            "Short technical block linked to the theme",
        ],
        main_work=main,
        strength=base_strength,
        cooldown=["Short down-regulation jog/walk", "Mobility and recap"],
        coach_block=coach_block,
        notes=[
            "The session should feel like football: ball, direction, decisions, space, timing, and teammates/opponents.",
            "Use strength and sprint work as support, not as the whole session.",
        ],
    )

def generate_soccer_plan(
    role,
    goal,
    level,
    injury_status,
    pain_score,
    session_time,
    soccer_focus,
    soccer_position,
    age_group,
    coach_level,
    people_training,
    context,
):
    if role == "Coach":
        return generate_soccer_coach_plan(goal, session_time, soccer_focus, soccer_position, age_group, coach_level, people_training, context)
    return generate_soccer_player_plan(goal, level, injury_status, pain_score, session_time, soccer_focus, soccer_position, context)

def generate_plan(
    role,
    sport,
    goal,
    level,
    injury_status,
    pain_score,
    session_time,
    sport_inputs,
    context,
):
    if sport == "Running":
        return generate_running_plan(
            role=role,
            goal=goal,
            level=level,
            injury_status=injury_status,
            pain_score=pain_score,
            session_time=session_time,
            running_focus=sport_inputs["running_focus"],
            running_distance=sport_inputs["running_distance"],
            running_session_style=sport_inputs.get("running_session_style", "Best fit for my goal"),
            context=context,
        )
    if sport == "Gym":
        return generate_gym_plan(role, goal, level, injury_status, pain_score, session_time, sport_inputs["gym_style"], context)
    if sport == "Tennis":
        return generate_tennis_plan(role, goal, level, injury_status, pain_score, session_time, sport_inputs["tennis_focus"], context)
    if sport == "Baseball":
        return generate_baseball_plan(role, goal, level, injury_status, pain_score, session_time, sport_inputs["baseball_focus"], context)
    if sport == "Rowing":
        return generate_rowing_plan(role, goal, level, injury_status, pain_score, session_time, sport_inputs["rowing_focus"], context)
    if sport == "Weightlifting":
        return generate_weightlifting_plan(role, goal, level, injury_status, pain_score, session_time, sport_inputs["wl_focus"], context)
    if sport == "Water Polo":
        return generate_water_polo_plan(role, goal, level, injury_status, pain_score, session_time, sport_inputs["wp_focus"], context)
    if sport == "Soccer":
        return generate_soccer_plan(
            role=role,
            goal=goal,
            level=level,
            injury_status=injury_status,
            pain_score=pain_score,
            session_time=session_time,
            soccer_focus=sport_inputs["soccer_focus"],
            soccer_position=sport_inputs["soccer_position"],
            age_group=sport_inputs.get("age_group"),
            coach_level=sport_inputs.get("coach_level"),
            people_training=sport_inputs.get("people_training", 1),
            context=context,
        )
    return "Sport not supported yet."



# =========================
# FINAL ENHANCEMENTS — COACH FLOW / SPORT-SPECIFIC GYM / BOXING / NEXT-WEEK TENNIS
# =========================
BOXING_STYLE_NOTES = {
    "Footwork & movement": "Use stance, balance, entries/exits, pivots, and ring movement.",
    "Jab & straight punches": "Build clean mechanics, distance control, and fast recovery to guard.",
    "Defense & countering": "Use slips, rolls, blocks, parries, then immediate counters.",
    "Combinations on bag/pads": "Blend rhythm, balance, and punch selection without arm-punching.",
    "Conditioning for boxing": "Keep rounds and rests boxing-specific, not random exhaustion.",
    "Ring craft / tactics": "Train feints, angle changes, distance, and decision-making.",
    "General boxing development": "Blend footwork, offense, defense, and conditioning."
}

def get_next_week_window(base_date):
    days_until_next_monday = (7 - base_date.weekday()) % 7
    if days_until_next_monday == 0:
        days_until_next_monday = 7
    start = base_date + timedelta(days=days_until_next_monday)
    end = start + timedelta(days=6)
    return start, end

def fetch_live_tennis_events_next_week():
    start, end = get_next_week_window(TODAY)
    all_events = fetch_live_tennis_events()
    filtered = []
    for event in all_events:
        d = parse_date(event["start_date"])
        if start <= d <= end:
            filtered.append(event)
    return filtered

def generate_boxing_plan(role, goal, level, injury_status, pain_score, session_time, boxing_focus, context):
    rounds_2 = 6
    rounds_3 = 4
    if goal_is_learning(goal):
        return format_plan(
            title=f"Boxing Fundamentals Session{context['title_suffix']}",
            focus="Learn the basics of stance, movement, guard, and clean straight punches",
            warmup=[
                "5 min skipping or light jog",
                "Dynamic ankle, hip, thoracic, and shoulder mobility",
                "Shadowboxing: stance, guard, jab-cross mechanics",
            ],
            main_work=[
                "Footwork ladder or cone pattern: 4 x 45 sec",
                "Shadowboxing technical rounds: 4 x 2 min, 45 sec rest",
                "Bag or pad rounds: jab-cross only, 4 x 2 min",
                "Defense basics: slip, block, reset to stance, 3 x 1 min",
            ],
            strength=[
                "3 x 6 goblet squats",
                "3 x 8 push-ups",
                "3 x 8 split squats each side",
                "2 x 20 sec plank",
            ],
            cooldown=[
                "Easy walk and breathing reset",
                "Shoulder, calf, and hip mobility",
            ],
            coach_block=context["coach_notes"],
            notes=[
                "Technique first. Balance, guard recovery, and breathing matter.",
                "Do not load hard sparring into a beginner fundamentals session.",
            ],
        )

    focus_map = {
        "Footwork & movement": [
            f"Cone / ring movement rounds: {rounds_2} x 2 min, 45 sec rest",
            f"Shadowboxing with step-in, step-out, pivot, angle change: {rounds_2} x 2 min",
            f"Bag or pad entry-exit rounds: {rounds_3} x 3 min, 60 sec rest",
        ],
        "Jab & straight punches": [
            f"Shadowboxing jab emphasis: {rounds_2} x 2 min",
            f"Heavy bag jab-cross rounds: {rounds_3} x 3 min",
            "Distance-control drill: jab to body/head height targets, 5 rounds of 45 sec",
        ],
        "Defense & countering": [
            f"Slip-line or rope defense: {rounds_2} x 2 min",
            f"Block/parry/slip to counter rounds on pads or shadowboxing: {rounds_2} x 2 min",
            f"Bag rounds: defend-reset-counter pattern, {rounds_3} x 3 min",
        ],
        "Combinations on bag/pads": [
            f"Pad/bag combinations 1-2, 1-2-3, 1-1-2: {rounds_3} x 3 min",
            f"Add level change or angle exit: {rounds_2} x 2 min",
            "Finish each round with 15 sec sharp but clean output, not sloppy flurries",
        ],
        "Conditioning for boxing": [
            f"Bag intervals: 8 x 90 sec on / 45 sec off",
            "Shuttle or bounce-step conditioning between rounds: 6 x 20 sec",
            "Shadowboxing under fatigue with form priority: 3 x 2 min",
        ],
        "Ring craft / tactics": [
            f"Feint-entry-exit shadowboxing: {rounds_2} x 2 min",
            "Angle-change and reset drill: 6 x 30 sec",
            f"Situational rounds: long range, mid range, defensive round, {rounds_3} x 3 min",
        ],
        "General boxing development": [
            f"Shadowboxing technical rounds: {rounds_2} x 2 min",
            f"Bag or pad rounds: {rounds_3} x 3 min",
            "Defense and counter drill: 4 x 45 sec",
            "Footwork finisher: 4 x 20 sec quick feet / 40 sec easy",
        ],
    }

    main = focus_map.get(boxing_focus, focus_map["General boxing development"])
    if role == "Coach":
        main.insert(0, "Set athletes in lanes or stations by bag/pad availability and skill level.")
    if beginner_modifier(level):
        main.insert(0, "Keep power moderate and prioritize stance, balance, and clean guard recovery.")
    if injury_caution(injury_status):
        main.append("Reduce punch volume and avoid painful ranges or hard impact.")

    return format_plan(
        title=f"Boxing Session{context['title_suffix']}",
        focus=f"Boxing development — {boxing_focus}",
        warmup=[
            "3-5 min skipping or easy run",
            "Dynamic mobility for ankles, hips, thoracic spine, shoulders",
            "Shadowboxing activation",
        ],
        main_work=main,
        strength=[
            "3 x 6 goblet squats",
            "3 x 8 push-ups or DB press",
            "3 x 8 split squats each side",
            "2 x 20 sec anti-rotation or plank hold",
        ],
        cooldown=[
            "Easy walk or light skip-down",
            "Shoulder, calf, hip, and thoracic mobility",
        ],
        coach_block=context["coach_notes"],
        notes=[
            BOXING_STYLE_NOTES.get(boxing_focus, BOXING_STYLE_NOTES["General boxing development"]),
            "Good boxing work should feel technical and specific, not just tiredness.",
        ],
    )



VOLLEYBALL_STYLE_NOTES = {
    "Serving & first ball pressure": "Build a serve that creates trouble and sets up the rally from ball one.",
    "Serve receive / passing": "Passing quality shapes the whole offense, so posture, angles, and platform control matter.",
    "Setting & second contact": "Good setting is footwork plus location, not just hand speed.",
    "Attacking / hitting": "Approach rhythm, arm speed, and smart hitting zones matter more than random power.",
    "Blocking / net defense": "Blocking starts with reading and footwork before the jump.",
    "Backcourt defense & transition": "Defense should turn into playable transition balls, not just panic touches.",
    "Game-like rally training": "Volleyball training should include realistic rally flow and communication.",
    "General volleyball development": "Blend serving, first contact, second contact, attacking, and defense.",
}

def generate_volleyball_plan(role, goal, level, injury_status, pain_score, session_time, volleyball_focus, context):
    if goal_is_learning(goal):
        return format_plan(
            title=f"Volleyball Fundamentals Session{context['title_suffix']}",
            focus="Learn the base technical actions of volleyball with clean repetition and simple rally flow",
            warmup=[
                "5 min light jog, shuffle, backpedal, and skipping",
                "Dynamic mobility for ankles, hips, thoracic spine, shoulders, and wrists",
                "Ball familiarization: self-toss, platform angles, overhead touch rhythm",
            ],
            main_work=[
                "Movement prep: shuffle-stop-balance pattern, 4 x 20 sec",
                "Passing basics: partner or wall passing, 5 x 12 contacts",
                "Setting basics: high target sets, 5 x 10 clean contacts",
                "Serve introduction: 6-10 controlled serves to zones",
                "Simple rally sequence: pass-set-free ball over, 6-10 reps",
            ],
            strength=[
                "3 x 6 goblet squats",
                "3 x 8 split squats each side",
                "3 x 8 push-ups",
                "2 x 20 sec plank or dead bug hold",
            ],
            cooldown=[
                "Easy walk and breathing reset",
                "Calf, hip flexor, adductor, thoracic, and shoulder mobility",
            ],
            coach_block=context["coach_notes"],
            notes=[
                "Beginners should prioritize clean contacts, posture, and timing before jump volume.",
                "Volleyball improvement comes from repeating first contact and second contact under control.",
            ],
        )

    focus_map = {
        "Serving & first ball pressure": [
            "Serve mechanics warm-up: 12-20 controlled contacts",
            "Zone serving: 5 rounds x 6 serves to target areas",
            "Pressure serving: 3 rounds where missed serves restart the count",
            "First-ball scoring drill: serve then defend the first attack pattern",
        ],
        "Serve receive / passing": [
            "Platform angle refresh: 3 x 45 sec",
            "Serve receive reps from zones 1/5/6, 5 rounds x 6 balls",
            "Pass-to-target challenge: 20 total quality passes goal",
            "Pass then move into transition base, 4 rounds x 5 reps",
        ],
        "Setting & second contact": [
            "Footwork into setting window: 4 x 30 sec",
            "High-ball and tempo set reps to pins/middle, 5 rounds x 8 balls",
            "Out-of-system setting drill: chase-set-recover, 4 rounds x 5 reps",
            "Setter decision drill: front / back / high based on coach call",
        ],
        "Attacking / hitting": [
            "Approach rhythm without jump: 3 x 5 reps each side",
            "Approach + jump timing with toss, 4 x 4 reps",
            "Controlled spike placement to zones 1/5 deep, 5 rounds x 5 balls",
            "Transition attack after block move or defensive touch, 4 rounds x 4 reps",
        ],
        "Blocking / net defense": [
            "Block footwork: step-close and swing block pattern, 4 x 20 sec",
            "Read-and-jump drill vs coach toss or set, 5 rounds x 4 reps",
            "Hands-over-net and press timing drill, 4 rounds x 5 reps",
            "Block then defensive transition, 4 rounds x 4 reps",
        ],
        "Backcourt defense & transition": [
            "Reaction posture drill: drop-step, sprawl control, recover, 4 x 20 sec",
            "Digging reps from tossed / hit balls, 5 rounds x 6 balls",
            "Defend then transition to playable second contact, 4 rounds x 5 reps",
            "Free-ball organization into attack pattern, 4 rounds",
        ],
        "Game-like rally training": [
            "Wash drill or sideout game to target score",
            "Serve-receive to live rally sequence, 6-10 rallies per block",
            "Transition point game with bonus for first-ball sideout",
            "Constraint game focused on communication and structure",
        ],
        "General volleyball development": [
            "Serve reps to target zones",
            "Pass-set-hit pattern work",
            "Block / defend transition sequence",
            "Short live game emphasizing first two contacts",
        ],
    }

    main = list(focus_map.get(volleyball_focus, focus_map["General volleyball development"]))
    if role == "Coach":
        main.insert(0, "Organize players by position or technical need and keep lines short for high ball-contact volume.")
    if beginner_modifier(level):
        main.insert(0, "Keep jump volume controlled and favor technique before max power.")
    if injury_caution(injury_status):
        main.append("Reduce landing volume and overhead load if pain is present.")

    return format_plan(
        title=f"Volleyball Session{context['title_suffix']}",
        focus=f"Volleyball development — {volleyball_focus}",
        warmup=[
            "5 min movement prep: shuffle, crossover, backpedal, low defensive posture",
            "Dynamic ankle, hip, thoracic, shoulder, and wrist mobility",
            "Ball-control activation: passing and setting touches",
        ],
        main_work=main,
        strength=[
            "3 x 5 squat jumps or low pogo hops",
            "3 x 6 split squats each side",
            "3 x 8 push-ups or DB press",
            "3 x 20 sec plank / anti-rotation hold",
        ],
        cooldown=[
            "Easy walk and breathing reset",
            "Calf, quad, adductor, shoulder, and thoracic mobility",
        ],
        coach_block=context["coach_notes"],
        notes=[
            VOLLEYBALL_STYLE_NOTES.get(volleyball_focus, VOLLEYBALL_STYLE_NOTES["General volleyball development"]),
            "A good volleyball session should connect first contact, second contact, and the next action.",
        ],
    )

def generate_sport_specific_gym_plan(role, goal, level, injury_status, pain_score, session_time, target_sport, context):
    sport_map = {
        "Running": {
            "focus": "Lower-body stiffness, unilateral strength, and posture transfer for running",
            "main": ["4 x 5 trap-bar deadlift or squat", "3 x 6 split squat each side", "3 x 8 calf raises each side", "4 x 10-20m sled march or resisted drive"],
            "secondary": ["3 x 6 single-leg RDL each side", "3 x 20 sec plank", "4 x 10 sec low-volume jumps or pogos"],
        },
        "Tennis": {
            "focus": "Rotational strength, deceleration, and single-leg power for tennis",
            "main": ["4 x 5 rear-foot elevated split squat", "4 x 5 landmine press", "4 x 6 seated row or pull-up", "4 x 5 med-ball rotational throw each side"],
            "secondary": ["3 x 6 lateral lunge each side", "3 x 8 cuff / scap stability work", "4 x 10m acceleration to split-step finish"],
        },
        "Baseball": {
            "focus": "Rotational power, lower-half force, and shoulder support for baseball",
            "main": ["4 x 5 trap-bar deadlift", "4 x 5 med-ball scoop toss each side", "3 x 6 split squat each side", "3 x 8 row or pull-up"],
            "secondary": ["3 x 8 cuff / scap stability work", "3 x 6 landmine press", "3 x 20 sec anti-rotation hold"],
        },
        "Rowing": {
            "focus": "Posterior-chain strength, trunk stiffness, and pulling support for rowing",
            "main": ["4 x 5 Romanian deadlift", "4 x 6 front squat", "4 x 8 seated row", "3 x 8 lat pulldown or pull-up"],
            "secondary": ["3 x 8 single-leg hinge each side", "3 x 20 sec hollow hold", "3 x 8 hip thrust"],
        },
        "Weightlifting": {
            "focus": "Olympic lifting support with leg strength, pulling strength, and overhead stability",
            "main": ["5 x 3 front squat", "4 x 4 clean pull or snatch pull", "4 x 4 push press", "3 x 6 Romanian deadlift"],
            "secondary": ["3 x 20 sec overhead hold", "3 x 6 split squat each side", "3 x 8 trunk stability drill"],
        },
        "Water Polo": {
            "focus": "Shoulder health, trunk control, leg drive, and power for water polo",
            "main": ["4 x 5 goblet squat or front squat", "4 x 5 landmine press", "4 x 8 row", "4 x 5 med-ball chest pass or scoop throw"],
            "secondary": ["3 x 8 cuff / scap stability work", "3 x 8 split squat each side", "3 x 20 sec hollow hold"],
        },
        "Soccer": {
            "focus": "Sprint support, unilateral strength, deceleration, and groin/core support for soccer",
            "main": ["4 x 5 trap-bar deadlift or squat", "4 x 6 split squat each side", "4 x 10m acceleration sprint", "3 x 5 lateral bound each side"],
            "secondary": ["3 x 6 Copenhagen plank short lever each side", "3 x 8 calf raises each side", "3 x 6 single-leg RDL each side"],
        },
        "Boxing": {
            "focus": "Leg drive, rotation, stiffness, and conditioning support for boxing",
            "main": ["4 x 5 trap-bar deadlift or squat", "4 x 5 landmine press", "4 x 5 med-ball rotational throw each side", "4 x 20 sec battle-rope or fast-feet effort"],
            "secondary": ["3 x 6 split squat each side", "3 x 8 pull-up / row", "3 x 20 sec anti-rotation hold"],
        },
        "Volleyball": {
            "focus": "Jump support, landing control, lateral movement, and shoulder stability for volleyball",
            "main": ["4 x 5 trap-bar deadlift or squat", "4 x 5 box jump or countermovement jump", "3 x 6 split squat each side", "3 x 8 DB push press or landmine press"],
            "secondary": ["3 x 8 row or pull-up", "3 x 8 cuff / scap stability work", "3 x 20 sec anti-rotation hold"],
        },
    }
    block = sport_map.get(target_sport)
    if not block:
        return generate_gym_plan.__wrapped__(role, goal, level, injury_status, pain_score, session_time, "Sport-specific strength", context)

    main = list(block["main"])
    secondary = list(block["secondary"])
    if role == "Coach":
        secondary.append("Organize athletes in stations if equipment is limited.")
    if beginner_modifier(level):
        main = [m.replace("4 x", "3 x").replace("5 x", "4 x") for m in main]
    if injury_caution(injury_status):
        secondary.append("Reduce load 10-20% and avoid painful ranges.")

    return format_plan(
        title=f"{target_sport} Sport-Specific Gym Session{context['title_suffix']}",
        focus=block["focus"],
        warmup=[
            "5 min easy cardio",
            "Dynamic mobility for ankles, hips, thoracic spine, shoulders",
            "2 progressive warm-up sets before first main lift",
        ],
        main_work=main,
        strength=secondary,
        cooldown=[
            "5 min easy walk or bike",
            "Mobility for the main joints used",
        ],
        coach_block=context["coach_notes"],
        notes=[
            "This gym session is built to transfer better to the chosen sport.",
            "Quality movement and crisp intent matter more than random volume.",
        ],
    )

def generate_gym_plan(role, goal, level, injury_status, pain_score, session_time, gym_style, context, gym_is_sport_specific=False, gym_target_sport=None):
    if gym_is_sport_specific and gym_target_sport:
        return generate_sport_specific_gym_plan(role, goal, level, injury_status, pain_score, session_time, gym_target_sport, context)
    return generate_gym_plan.__wrapped__(role, goal, level, injury_status, pain_score, session_time, gym_style, context)
generate_gym_plan.__wrapped__ = _original_generate_gym_plan

def generate_plan(
    role,
    sport,
    goal,
    level,
    injury_status,
    pain_score,
    session_time,
    sport_inputs,
    context,
):
    if sport == "Running":
        return generate_running_plan(
            role=role,
            goal=goal,
            level=level,
            injury_status=injury_status,
            pain_score=pain_score,
            session_time=session_time,
            running_focus=sport_inputs["running_focus"],
            running_distance=sport_inputs["running_distance"],
            running_session_style=sport_inputs.get("running_session_style", "Best fit for my goal"),
            context=context,
        )
    if sport == "Gym":
        return generate_gym_plan(
            role,
            goal,
            level,
            injury_status,
            pain_score,
            session_time,
            sport_inputs["gym_style"],
            context,
            gym_is_sport_specific=sport_inputs.get("gym_is_sport_specific", False),
            gym_target_sport=sport_inputs.get("gym_target_sport"),
        )
    if sport == "Tennis":
        return generate_tennis_plan(role, goal, level, injury_status, pain_score, session_time, sport_inputs["tennis_focus"], context)
    if sport == "Baseball":
        return generate_baseball_plan(role, goal, level, injury_status, pain_score, session_time, sport_inputs["baseball_focus"], context)
    if sport == "Rowing":
        return generate_rowing_plan(role, goal, level, injury_status, pain_score, session_time, sport_inputs["rowing_focus"], context)
    if sport == "Weightlifting":
        return generate_weightlifting_plan(role, goal, level, injury_status, pain_score, session_time, sport_inputs["wl_focus"], context)
    if sport == "Water Polo":
        return generate_water_polo_plan(role, goal, level, injury_status, pain_score, session_time, sport_inputs["wp_focus"], context)
    if sport == "Soccer":
        return generate_soccer_plan(
            role=role,
            goal=goal,
            level=level,
            injury_status=injury_status,
            pain_score=pain_score,
            session_time=session_time,
            soccer_focus=sport_inputs["soccer_focus"],
            soccer_position=sport_inputs["soccer_position"],
            age_group=sport_inputs.get("age_group"),
            coach_level=sport_inputs.get("coach_level"),
            people_training=sport_inputs.get("people_training", 1),
            context=context,
        )
    if sport == "Boxing":
        return generate_boxing_plan(
            role=role,
            goal=goal,
            level=level,
            injury_status=injury_status,
            pain_score=pain_score,
            session_time=session_time,
            boxing_focus=sport_inputs["boxing_focus"],
            context=context,
        )
    if sport == "Volleyball":
        return generate_volleyball_plan(
            role=role,
            goal=goal,
            level=level,
            injury_status=injury_status,
            pain_score=pain_score,
            session_time=session_time,
            volleyball_focus=sport_inputs["volleyball_focus"],
            context=context,
        )
    return "Sport not supported yet."

# =========================
# TOP NAVIGATION
# =========================
st.session_state.active_section = st.radio(
    "Choose section",
    SECTION_OPTIONS,
    index=SECTION_OPTIONS.index(st.session_state.active_section),
    horizontal=True,
)

# =========================
# SECTION 1 — TRAINING GENERATOR
# =========================

if st.session_state.active_section == "Training Generator":
    st.header("Training Generator")

    st.markdown("### Main questions")
    role = st.selectbox("Are you a player or coach?", ROLES)

    c1, c2 = st.columns(2)

    trains_alone = "Yes"
    people_training = 1
    age_group = None
    coach_level = None

    with c1:
        if role == "Coach":
            sport = st.selectbox("What sport do you train?", SPORTS)
            goal = "Improve performance"
            level = "Intermediate"
        else:
            sport = st.selectbox("What sport do you want to train?", SPORTS)
            goal = st.selectbox("What is your goal with this sport?", COMMON_GOALS)
            level = st.selectbox("What is your level?", SKILL_LEVELS)

    with c2:
        if role == "Player":
            beginner_or_learning = (goal == "Learn how to play") or (level == "Beginner")
            training_days_label = "How many times do you play sports per week?" if beginner_or_learning else "How many times do you train this sport per week?"
            training_days_default = 3 if beginner_or_learning else 4
            training_days = st.slider(training_days_label, 1, 7, training_days_default)
            injury_status = st.selectbox("Any injury or limitation?", INJURY_OPTIONS)
            pain_score = 0
            if injury_status != "No":
                pain_score = st.slider("Pain scale from 1 to 10", 1, 10, 3)
            session_time = st.selectbox(
                "How much time do you have for this session?",
                TIME_OPTIONS_ENDURANCE if sport in ["Running", "Rowing"] else TIME_OPTIONS_GENERAL,
            )
        else:
            training_days = st.slider("How many times does your team play per week?", 1, 7, 3)
            injury_status = "No"
            pain_score = 0
            session_time = st.selectbox(
                "What's the time of this session?",
                TIME_OPTIONS_ENDURANCE if sport in ["Running", "Rowing"] else TIME_OPTIONS_GENERAL,
            )

    st.markdown("### Training context")
    tc1, tc2 = st.columns(2)

    if role == "Player":
        with tc1:
            trains_alone = st.radio("Will you train alone?", ["Yes", "No"], horizontal=True)
        with tc2:
            if trains_alone == "No":
                people_training = st.number_input("How many more people will train?", min_value=1, max_value=60, value=1, step=1)
            else:
                people_training = 1
    else:
        with tc1:
            age_group = st.selectbox("Age group", SOCCER_AGE_BANDS if sport == "Soccer" else ["U8-U10", "U11-U13", "U14-U16", "U17-U19", "Senior"])
            coach_level = st.slider("Level of the team/player (1 to 10)", 1, 10, 5)
        with tc2:
            people_training = st.number_input("How many players are in the session?", min_value=1, max_value=60, value=12, step=1)

    sport_inputs = {"people_training": people_training, "training_days": training_days}

    st.markdown("### Sport-specific questions")

    if sport == "Running":
        rc1, rc2, rc3 = st.columns(3)
        with rc1:
            running_focus = st.selectbox("What's the focus?", RUNNING_FOCUS_OPTIONS)
        with rc2:
            running_distance = st.selectbox("Choose the event / distance", RUNNING_DISTANCE_MAP[running_focus])
        with rc3:
            sport_inputs["running_session_style"] = st.selectbox("What kind of running session?", RUNNING_SESSION_STYLES)
        sport_inputs["running_focus"] = running_focus
        sport_inputs["running_distance"] = running_distance

    elif sport == "Gym":
        gc1, gc2 = st.columns(2)
        with gc1:
            sport_inputs["gym_style"] = st.selectbox("What type of gym session do you want?", GYM_STYLES_EXTENDED)
            sport_inputs["gym_is_sport_specific"] = st.radio("Do you want this gym session to be sport specific?", ["No", "Yes"], horizontal=True) == "Yes"
        with gc2:
            if sport_inputs["gym_is_sport_specific"]:
                sport_inputs["gym_target_sport"] = st.selectbox("What sport?", SPORT_SPECIFIC_GYM_SPORTS)
                st.info("This builds the gym session around the chosen sport, while keeping the gym structure.")
            else:
                sport_inputs["gym_target_sport"] = None

    elif sport == "Tennis":
        sport_inputs["tennis_focus"] = st.selectbox("What is the main tennis focus today?", TENNIS_FOCUS_OPTIONS)

    elif sport == "Baseball":
        sport_inputs["baseball_focus"] = st.selectbox("What is the main baseball focus today?", BASEBALL_FOCUS_OPTIONS)

    elif sport == "Rowing":
        sport_inputs["rowing_focus"] = st.selectbox("What is the main rowing focus today?", ROWING_FOCUS_OPTIONS)

    elif sport == "Weightlifting":
        sport_inputs["wl_focus"] = st.selectbox("What is the main weightlifting focus today?", WEIGHTLIFTING_FOCUS_OPTIONS)

    elif sport == "Water Polo":
        sport_inputs["wp_focus"] = st.selectbox("What is the main water polo focus today?", WATER_POLO_FOCUS_OPTIONS)

    elif sport == "Soccer":
        sc1, sc2 = st.columns(2)
        with sc1:
            sport_inputs["soccer_focus"] = st.selectbox("What is the main soccer focus today?", SOCCER_FOCUS_OPTIONS)
            sport_inputs["soccer_position"] = st.selectbox("What position best describes the player/team focus?", SOCCER_POSITIONS)
        with sc2:
            if role == "Coach":
                sport_inputs["age_group"] = age_group
                sport_inputs["coach_level"] = coach_level
                st.info("For coaches, the session is shaped mainly by age band, level, player count, and game model theme.")
            else:
                st.info("For players, the session is shaped mainly by position, session theme, and solo/group context.")

    elif sport == "Boxing":
        bc1, bc2 = st.columns(2)
        with bc1:
            sport_inputs["boxing_focus"] = st.selectbox("What is the main boxing focus today?", BOXING_FOCUS_OPTIONS)
        with bc2:
            st.info("Boxing sessions now emphasize footwork, bag/pad structure, defense, and realistic boxing conditioning.")

    elif sport == "Volleyball":
        vc1, vc2 = st.columns(2)
        with vc1:
            sport_inputs["volleyball_focus"] = st.selectbox("What is the main volleyball focus today?", VOLLEYBALL_FOCUS_OPTIONS)
        with vc2:
            st.info("Volleyball sessions now emphasize first contact, second contact, attacking rhythm, blocking, transition, and realistic rally flow.")

    if st.button("Generate training session", use_container_width=True):
        safety = safety_message(injury_status, pain_score) if role == "Player" else None
        if safety:
            st.warning(safety)

        context = get_group_context_text(
            role=role,
            trains_alone=trains_alone,
            people_training=people_training,
            age_group=age_group,
            coach_level=coach_level,
        )

        plan = generate_plan(
            role=role,
            sport=sport,
            goal=goal,
            level=level,
            injury_status=injury_status,
            pain_score=pain_score,
            session_time=session_time,
            sport_inputs=sport_inputs,
            context=context,
        )

        st.subheader("Your training plan")
        st.markdown(plan)

        st.caption(
            "This planner gives general training guidance and is not medical advice. "
            "If pain is sharp, worsening, or affecting normal movement, stop and seek qualified help."
        )


# =========================
# SECTION 2 — VIDEO REVIEW
# =========================
elif st.session_state.active_section == "Video Review":
    st.header("Video Review")
    st.write("Upload a sports video for a basic form review.")

    review_sport = st.selectbox(
        "Which sport is this video for?",
        ["Tennis", "Running", "Gym / strength", "Baseball", "Rowing", "Weightlifting", "Water Polo", "Soccer", "Boxing", "Volleyball"]
    )

    review_focus = st.selectbox(
        "What do you want reviewed?",
        [
            "General technique",
            "Serve / shot mechanics",
            "Running mechanics",
            "Lifting form",
            "Movement efficiency",
            "Injury-risk cues",
            "Soccer technical actions",
            "Soccer movement / scanning / body shape",
            "Volleyball contact quality / approach / blocking timing",
        ]
    )

    uploaded_video = st.file_uploader("Upload video (.mp4, .mov, .avi)", type=["mp4", "mov", "avi"])

    if uploaded_video:
        st.success("Video uploaded.")
        st.markdown(
            f"""
### Preliminary review structure
- **Sport:** {review_sport}
- **Review focus:** {review_focus}
- **Next version recommendation:** add MediaPipe/OpenCV pipeline for pose extraction, joint angles, frame-by-frame checkpoints, and annotated feedback.
- **Current version behavior:** keep this as a review shell so the app architecture is ready without breaking your current app.
"""
        )
        st.info(
            "For now this section is structured professionally but does not yet run automated biomechanics. "
            "The architecture is here so you can plug your CV pipeline in later."
        )
    else:
        st.info("Upload a file to use this review shell.")

# =========================
# SECTION 3 — COUNSELLING
# =========================

elif st.session_state.active_section == "Counselling":
    st.header("Counselling")

    counselling_mode = st.radio("Choose counselling mode", ["Tennis", "Soccer"], horizontal=True)

    if counselling_mode == "Tennis":
        st.subheader("Tennis Counselling")
        st.write("Helping a tennis player choose the most logical tournament for the following competitive week only, using official ATP, Challenger, and ITF sources when available.")

        c1, c2 = st.columns(2)
        with c1:
            player_ranking = st.number_input("What ATP ranking does the player have? (Use 0 if unranked)", min_value=0, max_value=5000, value=450, step=1)
            player_region = st.selectbox("Where is the player today?", ["South America", "North America", "Europe", "Asia", "Africa", "Oceania"])
            preferred_surface = st.selectbox("Preferred surface", ["Clay", "Hard", "Grass", "No preference"])

        with c2:
            target_level = st.selectbox("What tournament level is the player realistically targeting?", ["Best fit", "ITF", "Challenger", "ATP Tour"])
            main_goal = st.selectbox(
                "Main tournament objective",
                ["Get into the draw", "Get matches and confidence", "Chase points", "Prepare for a higher tier soon", "Stay on preferred surface"],
            )
            travel_style = st.selectbox(
                "Travel logic",
                ["Stay close / reduce travel", "Best competitive fit matters most", "Surface matters most"],
            )

        if st.button("Generate tennis tournament advice", use_container_width=True):
            next_week_events = fetch_live_tennis_events_next_week()
            ranked_events = recommend_tournaments(
                player_ranking=player_ranking,
                player_region=player_region,
                preferred_surface=preferred_surface,
                target_level=target_level,
                main_goal=main_goal,
                travel_style=travel_style,
            )
            start_window, end_window = get_next_week_window(TODAY)
            ranked_events = [event for event in ranked_events if start_window <= parse_date(event["start_date"]) <= end_window]

            st.caption(f"Window analyzed (next competitive week only): {format_date(start_window)} to {format_date(end_window)}")

            st.subheader("Best tournament fits for the next week")
            if not ranked_events:
                st.warning("No official next-week events were parsed right now. The engine may need a selector update for the live calendars.")
            else:
                for event in ranked_events[:6]:
                    st.markdown(
                        f"""
### {event['name']}
- **Tour / level:** {event['tour']} - {event['level']}
- **City:** {event['city']}, {event['country']}
- **Surface:** {event['surface']}
- **Week starts:** {format_date(event['start_date'])}
- **Why it fits:** {event['ranking_note']}
- **Estimated direct-acceptance band:** {event['estimated_direct_acceptance_best_fit'][0]}-{event['estimated_direct_acceptance_best_fit'][1]}
- **Estimated qualifying/alternate band:** {event['estimated_qualifying_fit'][0]}-{event['estimated_qualifying_fit'][1]}
- **Travel / route note:** {event['notes']}
- **Entry note:** {entry_status_label(event)}
- **Practical filter:** This list is already filtered away from the current week, so events that have already started should not appear here.
"""
                    )

            st.markdown("### Recommendation summary")
            if player_ranking == 0:
                st.warning("An unranked player should usually prioritize ITF-level opportunities and local/regional events first.")
            elif player_ranking <= 120:
                st.success("This ranking profile is naturally closer to ATP 250 qualifying/direct-entry logic or strong Challenger scheduling.")
            elif player_ranking <= 300:
                st.success("This profile usually fits Challenger scheduling best, with ATP 250 qualifying as a selective stretch.")
            elif player_ranking <= 900:
                st.info("This profile is usually better served by stronger ITF scheduling and selective Challenger attempts.")
            else:
                st.info("This profile should usually prioritize ITF entries and match volume before aggressively chasing Challenger events.")

            st.info(
                "This version no longer leaves official links exposed in the interface. "
                "Instead, it uses the official ATP Tour, ATP Challenger Tour, and ITF calendar pages behind the scenes and filters to the next 7 days only."
            )

    else:
        st.subheader("Soccer Counselling")
        st.write("This mode uses a large internal club catalog plus live team-name lookup fallbacks so it handles less famous teams much better.")

        c1, c2 = st.columns(2)
        with c1:
            current_team = st.text_input("Which team are you in now?", placeholder="Example: Derry City academy, local semi-pro club, school team...")
            target_continent = st.selectbox("Which continent do you want to go to?", list(SOCCER_COUNTRIES_BY_CONTINENT.keys()))
            target_country = st.selectbox("What country?", SOCCER_COUNTRIES_BY_CONTINENT[target_continent])
            contract_offers = st.text_area(
                "What contract offers do you have today?",
                placeholder="Write offers separated by commas or lines. Example: Cork City, Shamrock Rovers academy, semi-pro club in Portugal",
            )

        with c2:
            current_level = st.selectbox(
                "What best describes your current level?",
                ["School / recreational", "Academy / youth competitive", "Semi-pro / amateur senior", "2nd division / strong pro pathway", "1st division / top domestic level"],
            )
            player_age_band = st.selectbox("Age band", SOCCER_AGE_BANDS)
            soccer_position = st.selectbox("Main position", SOCCER_POSITIONS)
            ambition = st.selectbox(
                "Main objective",
                ["Most realistic development step", "Best level I can still realistically compete in", "Max minutes and development", "Use existing offer intelligently"],
            )

        if st.button("Generate soccer team advice", use_container_width=True):
            result = recommend_soccer_move(
                current_team=current_team if current_team else "No current team entered",
                current_level=current_level,
                age_band=player_age_band,
                position=soccer_position,
                target_continent=target_continent,
                target_country=target_country,
                contract_offers_text=contract_offers,
                ambition=ambition,
            )

            st.subheader("Best fit recommendation")
            st.markdown(f"### {result['final_team']}")
            st.write(result["reasoning"])

            st.markdown("### Search and profile interpretation")
            team_profile = result["current_team_profile"]
            st.write(
                f"Detected current team profile: **{team_profile['best_name']}** | "
                f"band: **{team_profile['band']}** | confidence: **{team_profile['confidence']}**"
            )
            if team_profile.get("country"):
                st.write(f"Detected country: **{team_profile['country']}**")

            if team_profile["catalog_matches"]:
                st.markdown("**Best catalog matches found**")
                for item in team_profile["catalog_matches"][:5]:
                    st.write(f"- {item['name']} ({item['country']}) - {item['band']} - match {item['match_score']}")
            elif team_profile["online_matches"]:
                st.markdown("**Live search fallback matches**")
                for item in team_profile["online_matches"][:5]:
                    country_label = item.get("country") or "country not detected"
                    st.write(f"- {item['name']} ({country_label}) - source: {item.get('source', 'web')}")

            if result["evaluated_offers"]:
                st.markdown("### Offer evaluation")
                for item in result["evaluated_offers"][:6]:
                    st.write(
                        f"- {item['offer']} -> resolved as **{item['resolved_name']}**, band **{item['band']}**, "
                        f"country **{item['country']}**, score **{item['score']}**"
                    )

            if result["catalog_suggestions"]:
                st.markdown("### Other realistic catalog options in the target country")
                for club in result["catalog_suggestions"]:
                    st.write(f"- {club}")

            st.info(result["conservative_warning"])


# =========================
# SECTION 4 — PHYSIO
# =========================
else:
    st.header("Physio")
    st.write("Basic symptom-based support guidance. This is not diagnosis or treatment.")

    p1, p2 = st.columns(2)
    with p1:
        body_area = st.selectbox("Where is the pain?", PHYSIO_BODY_AREAS)
        pain_score = st.slider("Pain scale from 1 to 10", 1, 10, 3)
    with p2:
        symptoms = st.text_area("Describe symptoms", placeholder="Example: tight when I sprint, pain on stairs, slight swelling, heard no pop...")

    physio_photo = st.file_uploader("Optional: upload a photo of the painful area", type=["jpg", "jpeg", "png"])

    if st.button("Generate physio guidance", use_container_width=True):
        guidance = physio_guidance(body_area, pain_score, symptoms)

        st.subheader("Support guidance")
        st.markdown(
            f"""
- **Severity:** {guidance['severity']}
- **Mobility / stretch idea:** {guidance['stretch']}
- **Movement / exercise idea:** {guidance['mobility']}
- **Support action:** {guidance['support']}
- **Watch for:** {guidance['watch']}
"""
        )
        if physio_photo:
            st.info("Photo received. In this version the photo is stored by Streamlit only; image-based assessment is not yet automated.")
        if guidance["red_flag_found"] or pain_requires_physio(pain_score):
            st.error("There may be red flags or a higher-pain profile here. This should be checked by a qualified professional.")
