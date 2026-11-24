"""Rule-based reference-range checks (general adult ranges, educational use only)."""

# plausible limits used to reject typos / nonsense before anything runs
LIMITS = {
    "age": (0, 120), "height": (50, 250), "weight": (2, 400),
    "sys": (50, 300), "dia": (30, 200), "hr": (20, 250), "glu": (10, 1000),
    "spo2": (50, 100), "temp": (25, 115), "a1c": (3, 20), "hb": (3, 25),
    "chol": (50, 600), "ldl": (10, 500), "hdl": (5, 150), "tg": (20, 2000),
    "creat": (0.1, 15), "tsh": (0.001, 150),
}


def clean(raw):
    """Turn the request body into floats/strings; empty fields are dropped. Raises ValueError."""
    out = {}
    for k, v in (raw or {}).items():
        if v is None or str(v).strip() == "":
            continue
        if k in LIMITS:
            try:
                x = float(v)
            except ValueError:
                raise ValueError(f"'{k}' must be a number")
            lo, hi = LIMITS[k]
            if not lo <= x <= hi:
                raise ValueError(f"'{k}' value {x:g} looks unrealistic (expected {lo}-{hi})")
            out[k] = x
        elif k == "notes":
            out[k] = str(v)[:4000]
        else:
            out[k] = str(v)
    return out


def bmi_from(v):
    if "height" in v and "weight" in v:
        return v["weight"] / (v["height"] / 100) ** 2
    return None


def _range(x, lo, hi):
    return ("warn", "Low") if x < lo else ("warn", "High") if x > hi else ("ok", "In range")


def evaluate(v):
    """Return (flags, alerts). A flag = dict(label, value, status, text, group)."""
    flags, alerts = [], []

    def add(group, label, value, st):
        flags.append({"group": group, "label": label, "value": value, "status": st[0], "text": st[1]})

    b = bmi_from(v)
    if b is not None:
        st = (("warn", "Underweight") if b < 18.5 else ("ok", "Healthy range") if b < 25
              else ("warn", "Overweight") if b < 30 else ("bad", "Obese range"))
        add("Body", "BMI (calculated)", f"{b:.1f} kg/m²", st)

    if "sys" in v and "dia" in v:
        s, d = v["sys"], v["dia"]
        if s >= 180 or d >= 120:
            st = ("bad", "Crisis range")
            alerts.append("Blood pressure this high needs prompt medical attention. With headache, chest pain, "
                          "vision changes or breathlessness, go to emergency care.")
        elif s >= 140 or d >= 90: st = ("bad", "Stage 2 high")
        elif s >= 130 or d >= 80: st = ("warn", "Stage 1 high")
        elif s >= 120: st = ("warn", "Elevated")
        elif s < 90 or d < 60: st = ("warn", "Low")
        else: st = ("ok", "Normal")
        add("Vitals", "Blood pressure", f"{s:g}/{d:g} mm Hg", st)

    if "hr" in v:
        if v["hr"] > 130 or v["hr"] < 40:
            alerts.append("A heart rate this far outside the usual range should be checked promptly.")
        add("Vitals", "Heart rate", f"{v['hr']:g} bpm", _range(v["hr"], 60, 100))

    if "glu" in v:
        g, t = v["glu"], v.get("glutype", "Random")
        if t == "Fasting":
            st = ("warn", "Low") if g < 70 else ("ok", "Normal") if g < 100 else ("warn", "Prediabetes range") if g < 126 else ("bad", "Diabetes range")
        elif t.startswith("After"):
            st = ("warn", "Low") if g < 70 else ("ok", "Normal") if g < 140 else ("warn", "Prediabetes range") if g < 200 else ("bad", "Diabetes range")
        else:
            st = ("warn", "Low") if g < 70 else ("ok", "Normal") if g < 140 else ("warn", "High") if g < 200 else ("bad", "Very high")
        if g < 54: alerts.append("Blood sugar this low can be dangerous. Take fast-acting sugar if you can and get medical help.")
        if g >= 300: alerts.append("Blood sugar this high needs same-day medical advice, especially with thirst, vomiting or drowsiness.")
        add("Vitals", f"Blood sugar ({t.lower()})", f"{g:g} mg/dL", st)

    if "temp" in v:
        unit = v.get("tunit", "°C")
        c = (v["temp"] - 32) * 5 / 9 if unit == "°F" else v["temp"]
        st = ("bad", "Low") if c < 35 else ("ok", "Normal") if c < 37.8 else ("warn", "Fever") if c < 39.4 else ("bad", "High fever")
        if c >= 39.4: alerts.append("A temperature this high should be assessed by a doctor soon.")
        add("Vitals", "Temperature", f"{v['temp']:g} {unit}", st)

    if "spo2" in v:
        if v["spo2"] < 92: alerts.append("An oxygen level below 92% needs urgent medical assessment.")
        add("Vitals", "SpO₂", f"{v['spo2']:g} %", _range(v["spo2"], 95, 100))

    if "a1c" in v:
        a = v["a1c"]
        add("Blood tests", "HbA1c", f"{a:g} %",
            ("ok", "Normal") if a < 5.7 else ("warn", "Prediabetes range") if a < 6.5 else ("bad", "Diabetes range"))
    if "hb" in v:
        lo, hi = {"Female": (12, 15.5), "Male": (13.5, 17.5)}.get(v.get("sex"), (12, 17.5))
        add("Blood tests", "Hemoglobin", f"{v['hb']:g} g/dL", _range(v["hb"], lo, hi))
    if "chol" in v:
        c = v["chol"]
        add("Blood tests", "Total cholesterol", f"{c:g} mg/dL",
            ("ok", "Desirable") if c < 200 else ("warn", "Borderline high") if c < 240 else ("bad", "High"))
    if "ldl" in v:
        c = v["ldl"]
        add("Blood tests", "LDL cholesterol", f"{c:g} mg/dL",
            ("ok", "Optimal") if c < 100 else ("ok", "Near optimal") if c < 130 else ("warn", "Borderline high") if c < 160 else ("bad", "High"))
    if "hdl" in v:
        add("Blood tests", "HDL cholesterol", f"{v['hdl']:g} mg/dL", ("bad", "Low") if v["hdl"] < 40 else ("ok", "Fine"))
    if "tg" in v:
        c = v["tg"]
        add("Blood tests", "Triglycerides", f"{c:g} mg/dL",
            ("ok", "Normal") if c < 150 else ("warn", "Borderline high") if c < 200 else ("bad", "High"))
    if "creat" in v:
        add("Blood tests", "Creatinine", f"{v['creat']:g} mg/dL", _range(v["creat"], 0.5, 1.3))
    if "tsh" in v:
        add("Blood tests", "TSH", f"{v['tsh']:g} mIU/L", _range(v["tsh"], 0.4, 4.5))
    return flags, alerts
