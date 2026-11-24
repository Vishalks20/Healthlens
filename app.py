"""Flask backend:  python app.py  ->  http://127.0.0.1:5000"""
import json
import os
import urllib.error
import urllib.request
from pathlib import Path

import joblib
import numpy as np
from flask import Flask, jsonify, request

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from prompts import build_prompt
from rules import bmi_from, clean, evaluate

BASE = Path(__file__).parent
app = Flask(__name__, static_folder="public", static_url_path="")

MODELS = {}
for name in ("diabetes", "heart"):
    p = BASE / "models" / f"{name}.joblib"
    if p.exists():
        MODELS[name] = joblib.load(p)


def band(p):
    return "Lower" if p < 0.33 else "Moderate" if p < 0.66 else "Higher"


def ml_risks(v):
    """Run each model only when its minimum inputs exist; other features are imputed."""
    out, nan = [], float("nan")

    m = MODELS.get("diabetes")
    bmi = bmi_from(v)
    if m and "glu" in v and "age" in v:
        row = {"glucose": v["glu"], "bp": v.get("dia", nan), "bmi": bmi if bmi else nan, "age": v["age"]}
        x = [[row.get(f, nan) for f in m["features"]]]
        p = float(m["pipeline"].predict_proba(np.array(x, dtype=float))[0, 1])
        used = ["blood sugar", "age"] + (["BMI"] if bmi else []) + (["diastolic BP"] if "dia" in v else [])
        out.append({"id": "diabetes", "title": "Diabetes screening", "probability": p, "band": band(p),
                    "used": used, "metrics": m["metrics"],
                    "note": "Trained on 2-hour glucose values; a fasting value may under-estimate risk."})

    m = MODELS.get("heart")
    if m and all(k in v for k in ("age", "sex", "sys", "chol")):
        fbs = nan
        if "glu" in v and v.get("glutype") == "Fasting":
            fbs = 1.0 if v["glu"] > 120 else 0.0
        row = {"age": v["age"], "sex": 1.0 if v["sex"] == "Male" else 0.0,
               "trestbps": v["sys"], "chol": v["chol"], "fbs": fbs}
        x = [[row[f] for f in m["features"]]]
        p = float(m["pipeline"].predict_proba(np.array(x, dtype=float))[0, 1])
        out.append({"id": "heart", "title": "Heart disease screening", "probability": p, "band": band(p),
                    "used": ["age", "sex", "systolic BP", "cholesterol"] + (["fasting sugar"] if fbs == fbs else []),
                    "metrics": m["metrics"],
                    "note": "A basic model from only five check-up values, so it is weaker than the full clinical picture."})
    return out


def ask_claude(prompt):
    """Written explanation. LLM_PROVIDER=groq (default), anthropic, or openai (any OpenAI-compatible
    service: Ollama, Groq, Gemini, OpenRouter ...). See .env.example."""
    provider = os.environ.get("LLM_PROVIDER", "groq").lower()
    try:
        if provider == "anthropic":
            key = os.environ.get("ANTHROPIC_API_KEY")
            if not key:
                return None, "No AI provider configured, so the written explanation is switched off. See README."
            import anthropic
            client = anthropic.Anthropic(api_key=key)
            msg = client.messages.create(
                model=os.environ.get("CLAUDE_MODEL", "claude-sonnet-5-5"),
                max_tokens=1200,
                messages=[{"role": "user", "content": prompt}],
            )
            return "".join(b.text for b in msg.content if b.type == "text"), None

        # OpenAI-compatible chat endpoint (free options: Ollama / Groq / Gemini / OpenRouter)
        if provider == "groq":
            base = os.environ.get("GROQ_BASE_URL", "https://api.groq.com/openai/v1").rstrip("/")
            model = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")
            key = os.environ.get("GROQ_API_KEY")
            if not key:
                return None, "No GROQ_API_KEY found, so the written explanation is switched off. See README."
        else:
            base = os.environ.get("LLM_BASE_URL", "http://localhost:11434/v1").rstrip("/")
            model = os.environ.get("LLM_MODEL", "llama3.2")
            key = os.environ.get("LLM_API_KEY", "none")
        body = json.dumps({
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 1200,
        }).encode()
        req = urllib.request.Request(base + "/chat/completions", data=body, headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer " + key,
            "User-Agent": "healthlens/1.0",
        })
        with urllib.request.urlopen(req, timeout=180) as r:
            data = json.load(r)
        return data["choices"][0]["message"]["content"], None
    except urllib.error.HTTPError as e:
        try:
            detail = json.load(e).get("error", {}).get("message", "")
        except Exception:
            detail = ""
        return None, f"The AI service replied with error {e.code}: {detail or e.reason}"
    except Exception as e:  # network, auth, rate limit, model not found ...
        return None, f"The AI service could not be reached ({type(e).__name__}). Check your .env settings. The checks above are still valid."


@app.get("/")
def index():
    return app.send_static_file("index.html")


@app.post("/api/analyze")
def analyze():
    try:
        v = clean(request.get_json(silent=True))
    except ValueError as e:
        return jsonify(error=str(e)), 400
    if not v:
        return jsonify(error="Please enter at least one value."), 400
    flags, alerts = evaluate(v)
    risks = ml_risks(v)
    ai, ai_error = ask_claude(build_prompt(v, flags, risks))
    return jsonify(flags=flags, alerts=alerts, risks=risks, ai=ai, ai_error=ai_error)


if __name__ == "__main__":
    app.run(debug=True)