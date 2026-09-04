"""
Spoilage Curve Model — Published shelf-life data se value decay calculate karta hai
Yeh ML model NAHI hai — yeh formula hai jo research papers ke numbers use karta hai

v2 fix: temperature adjustment ab EXPONENTIAL (Q10-style) hai, LINEAR nahi.

Purana formula: adjusted_k = base_k + (temp_sensitivity * temp_diff)
Masla: crops jinka ideal_temp bohot kam hai (jaise potato = 5C), unke liye
Pakistan ke garam ambient (30C+) se temp_diff bohot bara ho jata hai (25C+),
jo linear addition ko base_k se kai guna zyada bana deta hai - matlab
crop-specific research (base_k) ka koi asar hi nahi rehta, formula sirf
temperature dominate karta hai. Ye exactly wahi masla tha jab potato
(base_k=0.012, dheeme decay wala) 4 din mein 0% dikhane laga tha jabke
research batati hai potato ambient heat mein bhi hafton tak theek rehta hai.

Naya formula: adjusted_k = base_k * 2^(temp_diff / temp_halving_celsius)

Ye IRRI ke apne stated rule se match karta hai ("rice shelf life halves
har 5C pe") aur food-science ka standard Q10 temperature-coefficient
concept follow karta hai. Har crop ka apna "halving_temp" hai (kitne C
pe uska decay rate double hota hai) - potato ka 34.2C (bohot gentle),
mango ka sirf 9.4C (bohot steep), jo unki asal physiology (dormant tuber
vs heat-sensitive climacteric fruit) ko sahi reflect karta hai.
"""
import json
import math
from pathlib import Path
from datetime import datetime, date


def load_crop_profiles():
    """crop_profiles.json load karo"""
    data_path = Path(__file__).parent.parent / "data" / "crop_profiles.json"
    with open(data_path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_crop_profile(crop_id: str) -> dict:
    """Specific crop ka profile nikal ke do"""
    profiles = load_crop_profiles()
    for profile in profiles:
        if profile["crop_id"] == crop_id:
            return profile
    raise ValueError(f"Crop '{crop_id}' not found in profiles")


def get_storage_profile(crop_profile: dict, storage_type: str) -> dict:
    """Specific storage type ka profile nikal ke do"""
    for sp in crop_profile["storage_profiles"]:
        if sp["storage_type"] == storage_type:
            return sp
    # Agar exact match nahi mila toh pehla profile de do
    return crop_profile["storage_profiles"][0]


def calculate_decay_rate(crop_profile: dict, current_temp: float, storage_type: str) -> float:
    """
    Decay rate (k) calculate karo based on:
    - Base decay constant from crop profile (research-derived, per crop)
    - Temperature difference from ideal - EXPONENTIAL (Q10-style) scaling,
      using each crop's own "halving temperature" rather than one linear
      rate applied to every crop equally.
    - Storage type
    """
    base_k = crop_profile["decay_constant_k"]
    ideal_temp = crop_profile["ideal_temp_celsius"]

    # temp_halving_celsius: degrees above ideal needed for decay rate to
    # double. Falls back to 10C (standard Q10=2 default) if an older
    # crop_profiles.json without this field is ever loaded, so this
    # function doesn't hard-crash on stale data - but every crop in our
    # actual dataset has a real, research-derived value for this.
    halving_temp = crop_profile.get("temp_halving_celsius", 10.0)

    temp_diff = max(0, current_temp - ideal_temp)
    adjusted_k = base_k * (2 ** (temp_diff / halving_temp))

    # Storage type se adjustment (unchanged from v1)
    if "cold" in storage_type:
        adjusted_k *= 0.2  # Cold storage mein 5x slow decay
    elif "covered" in storage_type or "shed" in storage_type:
        adjusted_k *= 0.7  # Covered shed mein thoda slow

    return adjusted_k


def generate_spoilage_curve(
    crop_id: str,
    harvest_date: str,
    current_temp: float,
    storage_type: str,
    days_to_project: int = 14,
) -> dict:
    """
    MAIN FUNCTION — Spoilage curve generate karo
    
    Returns:
    {
        "crop_id": "mango_sindhri",
        "decay_rate_k": 0.25,
        "days_since_harvest": 1,
        "current_value_pct": 92.3,
        "critical_day": 4,          ← jab value 60% se neeche giregi
        "curve": [                  ← har din ki value
            {"day": 0, "value_pct": 100.0, "status": "premium"},
            {"day": 1, "value_pct": 77.9, "status": "premium"},
            ...
        ],
        "risk_score": 82,           ← 0-100 risk score
        "risk_level": "HIGH"        ← LOW / MEDIUM / HIGH
    }
    """
    crop_profile = get_crop_profile(crop_id)
    k = calculate_decay_rate(crop_profile, current_temp, storage_type)

    # Days since harvest calculate karo
    if isinstance(harvest_date, str):
        harvest_dt = datetime.strptime(harvest_date, "%Y-%m-%d").date()
    else:
        harvest_dt = harvest_date
    
    days_elapsed = (date.today() - harvest_dt).days
    days_elapsed = max(0, days_elapsed)

    # Curve generate karo
    curve = []
    critical_day = None

    for day in range(0, days_to_project + 1):
        value_pct = round(100 * math.exp(-k * day), 1)
        
        # Status decide karo
        if value_pct >= 80:
            status = "premium"
        elif value_pct >= 60:
            status = "acceptable"
        elif value_pct >= 40:
            status = "distressed"
        else:
            status = "waste"
        
        # Critical day track karo (pehli baar 60% se neeche)
        if value_pct < 60 and critical_day is None:
            critical_day = day

        curve.append({
            "day": day,
            "value_pct": value_pct,
            "status": status,
        })

    # Current value
    current_value_pct = round(100 * math.exp(-k * days_elapsed), 1)

    # Risk score (0-100)
    # v2 fix: purana formula 'temp_risk' aur 'time_risk' generic/linear the
    # aur crop-specific halving_temp ko ignore karte the - isi wajah se
    # potato jaisa slow-decay crop bhi 97/100 HIGH dikha raha tha, jabke
    # current_value_pct (jo ab crop-specific formula se sahi calculate
    # hota hai) sirf 28.7% risk dikhata tha - do formulas disagree kar
    # rahe the. Fix: ek hi "source of truth" rakho - risk_score ko seedha
    # current_value_pct se derive karo (jo already crop-specific
    # temperature/time sab incorporate kar chuka hai), sirf storage_type
    # ka thoda forward-looking weight add karo.
    value_based_risk = 100 - current_value_pct
    storage_risk = {"open_air": 90, "ambient_hot": 95, "ambient_moderate": 60,
                    "covered_shed": 40, "cold_storage": 10, "refrigerated_transport": 15,
                    "hermetic_storage": 5}.get(storage_type, 70)

    risk_score = int((value_based_risk * 0.7) + (storage_risk * 0.3))
    risk_score = min(100, max(0, risk_score))

    risk_level = "LOW" if risk_score < 35 else "MEDIUM" if risk_score < 65 else "HIGH"

    return {
        "crop_id": crop_id,
        "crop_name": crop_profile["crop_name"],
        "decay_rate_k": round(k, 4),
        "days_since_harvest": days_elapsed,
        "current_value_pct": current_value_pct,
        "critical_day": critical_day or days_to_project,
        "curve": curve,
        "risk_score": risk_score,
        "risk_level": risk_level,
        "ideal_temp": crop_profile["ideal_temp_celsius"],
        "current_temp": current_temp,
        "storage_type": storage_type,
    }