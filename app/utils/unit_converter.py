import re
from typing import Tuple, Optional

UNIT_MAP = {
    # Torque
    r'\b(newton[\s-]?meter[s]?|newton[\s-]?metre[s]?|n[\.\s]?m|nm)\b': 'Nm',
    r'\b(inch[\s-]?pound[s]?|in[\s-]?lb[s]?|in-lbs)\b': 'in-lb',
    r'\b(foot[\s-]?pound[s]?|ft[\s-]?lb[s]?|ft-lbs)\b': 'ft-lb',
    
    # Speed
    r'\b(rpm|revolutions\s+per\s+minute|rev/min|r/min)\b': 'RPM',
    r'\b(bpm|blows\s+per\s+minute|strokes\s+per\s+minute|spm)\b': 'BPM',

    # Electrical & Power
    r'\b(volt[s]?|v\s*dc|v\s*ac|v)\b': 'V',
    r'\b(millivolt[s]?|mv)\b': 'mV',
    r'\b(watt[s]?|w)\b': 'W',
    r'\b(kilowatt[s]?|kw)\b': 'kW',
    r'\b(ampere[\s-]?hour[s]?|amp[\s-]?hour[s]?|ah)\b': 'Ah',
    r'\b(milliampere[\s-]?hour[s]?|mah)\b': 'mAh',
    r'\b(watt[\s-]?hour[s]?|wh)\b': 'Wh',
    r'\b(amp[s]?|ampere[s]?|a)\b': 'A',
    r'\b(milliamp[s]?|ma)\b': 'mA',
    r'\b(hertz|hz)\b': 'Hz',
    r'\b(kilohertz|khz)\b': 'kHz',
    r'\b(gigahertz|ghz)\b': 'GHz',

    # Weight / Mass
    r'\b(kilogram[s]?|kilo[s]?|kg)\b': 'kg',
    r'\b(gram[s]?|g)\b': 'g',
    r'\b(pound[s]?|lb[s]?)\b': 'lbs',
    r'\b(ounce[s]?|oz)\b': 'oz',

    # Dimensions
    r'\b(millimeter[s]?|millimetre[s]?|mm)\b': 'mm',
    r'\b(centimeter[s]?|centimetre[s]?|cm)\b': 'cm',
    r'\b(meter[s]?|metre[s]?|m)\b': 'm',
    r'\b(inch[e]?s?|in|\")\b': 'in',

    # Sound & Pressure
    r'\b(decibel[s]?|db\(a\)|dba|db)\b': 'dB(A)',
    r'\b(psi|pounds\s+per\s+square\s+inch)\b': 'PSI',
    r'\b(bar)\b': 'bar',
}

def normalize_unit(raw_unit_str: str) -> Optional[str]:
    if not raw_unit_str:
        return None
    cleaned = raw_unit_str.strip().lower()
    for pattern, std_unit in UNIT_MAP.items():
        if re.search(pattern, cleaned):
            return std_unit
    return raw_unit_str.strip()

def extract_numeric_and_unit(raw_val: str) -> Tuple[str, Optional[str]]:
    """
    Given a raw string e.g. "55 Nm", "1800 rpm", "1.5 kg", "18 Volts",
    returns (normalized_numeric_str, normalized_unit).
    """
    if not raw_val:
        return ("", None)
    
    # Check pattern like "55 Nm", "1,800 RPM", "1.5 kg", "1/2 inch"
    match = re.search(r'^\s*([0-9]+(?:\.[0-9]+)?(?:\s*/\s*[0-9]+)?)\s*([a-zA-Z°"\(\)\s/-]+)?$', raw_val.strip())
    if match:
        num_part = match.group(1).strip()
        unit_part = match.group(2)
        std_unit = normalize_unit(unit_part) if unit_part else None
        return (num_part, std_unit)
    
    # If no clean split, return raw_val as value
    return (raw_val.strip(), None)
