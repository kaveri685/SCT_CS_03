# password_strength.py
import math
import re

# Small list of extremely common passwords (extend with a larger file if you want)
COMMON_PASSWORDS = {
    "123456", "password", "12345678", "qwerty", "abc123", "111111",
    "1234567", "dragon", "123123", "baseball", "iloveyou", "trustno1",
    "letmein", "sunshine", "master", "welcome", "shadow", "ashley",
    "football", "jesus", "michael"
}

SYMBOLS = r"""~`!@#$%^&*()-_=+[{]}\|;:'",<.>/?"""

def charset_size(password: str) -> int:
    size = 0
    if re.search(r'[a-z]', password): size += 26
    if re.search(r'[A-Z]', password): size += 26
    if re.search(r'\d', password): size += 10
    # treat printable symbols as one block (common approach)
    if re.search(r'[' + re.escape(SYMBOLS) + r']', password): size += 32
    # if nothing matched (weird unicode), assume at least 1
    return max(size, 1)

def entropy_bits(password: str) -> float:
    # estimate bits of entropy based on charset size
    L = len(password)
    csize = charset_size(password)
    bits = L * math.log2(csize) if csize > 1 else 0.0
    return bits

def has_long_repeat(password: str, repeat_threshold: int = 4) -> bool:
    # check for same character repeated many times
    return re.search(r'(.)\1{' + str(repeat_threshold-1) + ',}', password) is not None

def has_sequence(password: str, seq_len: int = 4) -> bool:
    # detects simple increasing/decreasing sequences in alpha or digits
    s = password.lower()
    # sliding window
    for i in range(len(s) - seq_len + 1):
        sub = s[i:i+seq_len]
        # only check alnum
        if not re.match(r'^[a-z0-9]+$', sub):
            continue
        # create ord sequence
        ords = [ord(c) for c in sub]
        diffs = [ords[i+1]-ords[i] for i in range(len(ords)-1)]
        # all diffs equal to 1 (abcd, 4567) or -1 (dcba, 7654)
        if all(d == 1 for d in diffs) or all(d == -1 for d in diffs):
            return True
    return False

def assess_password(password: str) -> dict:
    """
    Returns a dict with:
      - score (0..100)
      - label (Very weak .. Very strong)
      - entropy_bits
      - details and suggestions
    """
    if not isinstance(password, str):
        raise TypeError("password must be a string")

    L = len(password)
    bits = entropy_bits(password)
    size = charset_size(password)

    # base score from entropy (map bits to 0..60)
    # We map bits to a base contribution: 0 bits -> 0; 60+ bits -> 60 (cap)
    base = min(60, (bits / 60) * 60) if bits > 0 else 0

    # bonuses for having multiple character classes
    classes = 0
    classes += 1 if re.search(r'[a-z]', password) else 0
    classes += 1 if re.search(r'[A-Z]', password) else 0
    classes += 1 if re.search(r'\d', password) else 0
    classes += 1 if re.search(r'[' + re.escape(SYMBOLS) + r']', password) else 0
    class_bonus = (classes - 1) * 5  # each extra class beyond 1 gives +5 (max 15)
    class_bonus = max(class_bonus, 0)

    # length bonus (encourage >=12)
    if L >= 16:
        length_bonus = 15
    elif L >= 12:
        length_bonus = 10
    elif L >= 8:
        length_bonus = 5
    else:
        length_bonus = 0

    # start with sum of positives
    score = base + class_bonus + length_bonus  # roughly up to 90

    # penalties
    reasons = []
    penalty = 0

    # 1) common password
    if password.lower() in COMMON_PASSWORDS:
        penalty += 40
        reasons.append("Very common password")

    # 2) too short
    if L < 8:
        penalty += (8 - L) * 3  # small penalty per missing char
        reasons.append("Too short (recommend >= 12 chars)")

    # 3) long repeats
    if has_long_repeat(password, repeat_threshold=4):
        penalty += 15
        reasons.append("Long repeated characters")

    # 4) simple sequences
    if has_sequence(password, seq_len=4):
        penalty += 20
        reasons.append("Sequence detected (e.g., 'abcd' or '1234')")

    # 5) low charset (only letters or only digits)
    if size <= 26:
        penalty += 10
        reasons.append("Limited character variety")

    # apply penalty
    score = score - penalty

    # normalize score to 0..100
    score = max(0, min(100, int(round(score))))

    # label mapping
    if score < 20:
        label = "Very weak"
    elif score < 40:
        label = "Weak"
    elif score < 60:
        label = "Fair"
    elif score < 80:
        label = "Strong"
    else:
        label = "Very strong"

    # suggestions
    suggestions = []
    if L < 12:
        suggestions.append("Make it longer (12+ characters recommended).")
    if not re.search(r'[A-Z]', password):
        suggestions.append("Add uppercase letters.")
    if not re.search(r'[a-z]', password):
        suggestions.append("Add lowercase letters.")
    if not re.search(r'\d', password):
        suggestions.append("Add digits.")
    if not re.search(r'[' + re.escape(SYMBOLS) + r']', password):
        suggestions.append("Add special characters (e.g., !@#$%).")
    if has_long_repeat(password, 4):
        suggestions.append("Avoid long repeated characters.")
    if has_sequence(password, 4):
        suggestions.append("Avoid simple sequences like 'abcd' or '1234'.")
    if password.lower() in COMMON_PASSWORDS:
        suggestions.append("Don't use common passwords (e.g., 'password', '123456').")

    details = {
        "length": L,
        "charset_size": size,
        "entropy_bits": round(bits, 2),
        "classes": classes,
        "base_entropy_score": round(base, 2),
        "class_bonus": class_bonus,
        "length_bonus": length_bonus,
        "penalty": penalty,
        "reasons_for_penalty": reasons
    }

    return {
        "score": score,
        "label": label,
        "suggestions": suggestions,
        "details": details
    }

# quick CLI demonstration
if __name__ == "__main__":
    import getpass
    pw = getpass.getpass("Enter password to assess: ")
    out = assess_password(pw)
    print(f"\nScore: {out['score']} / 100  — {out['label']}")
    print("Entropy (bits):", out['details']['entropy_bits'])
    print("Suggestions:")
    for s in out['suggestions'][:5]:
        print(" -", s)
    if out['details']['reasons_for_penalty']:
        print("Penalties:", ", ".join(out['details']['reasons_for_penalty']))
