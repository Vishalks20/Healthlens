# AI-Based Disease Risk Prediction System

A web app where a patient picks **only the tests they actually have** (blood pressure, sugar, heart rate,
temperature, SpO₂, HbA1c, cholesterol, hemoglobin, creatinine, TSH, prescription text …) and gets:

1. **Rule-based checks** – each value compared with general adult reference ranges, plus emergency alerts.
2. **ML screening scores** – logistic-regression models (diabetes, heart disease) trained on public datasets.
   Missing inputs are imputed, and a model only runs when its minimum inputs exist.
3. **Claude's explanation** – plain-language interpretation, everyday steps, when to seek care, and questions
   to ask the doctor. Claude never changes or prescribes medicines.

> Educational prototype. Not a diagnosis and not medical advice.

## Run it (5 minutes)

```bash
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt

python train_models.py            # downloads the datasets and trains models (models/ is included already)

cp .env.example .env              # then paste your ANTHROPIC_API_KEY into .env  (optional, see below)
python app.py                     # open http://127.0.0.1:5000
```

Without an API key everything works except the written Claude explanation, which shows a notice instead.
Get a key at https://console.anthropic.com.

## Project structure

| File | Purpose |
|---|---|
| `train_models.py` | Downloads data, cleans it, trains and evaluates both models, saves `models/*.joblib` |
| `rules.py` | Input validation (rejects unrealistic values) and reference-range rules |
| `prompts.py` | Builds the instruction sent to Claude, with safety rules |
| `app.py` | Flask server: `POST /api/analyze` combines rules + ML + Claude |
| `static/` | Frontend (`index.html`, `style.css`, `app.js`): test picker, input cards, results |

## How it works

```
patient picks tests -> enters values -> POST /api/analyze
   -> validate (rules.clean)  -> reference-range flags + alerts (rules.evaluate)
   -> ML risk models (only if minimum inputs exist)  -> Claude interpretation (prompts.py)
   -> JSON -> results page
```

**Design choice (good viva point):** safety-critical checks are deterministic rules; the language model is used only
for explanation, with instructions not to diagnose or alter medication. User-typed notes are wrapped in
`<user_notes>` tags and treated as data, not instructions.

## Models and honest limitations

| Model | Dataset | Test accuracy | AUC |
|---|---|---|---|
| Diabetes | Pima Indians Diabetes (768 rows) | 71% | 0.81 |
| Heart (lite: age, sex, BP, cholesterol, fasting sugar) | Cleveland Heart Disease (303 rows) | 69% | 0.76 |

- Datasets are small and not representative of all populations; real tools use far larger validated data.
- Pima glucose is a 2-hour test value, so fasting sugar may under-estimate diabetes risk.
- The Kaggle copy of the heart dataset has **inverted labels** (`target=1` means no disease); `train_models.py` flips them.
- Recall for diabetes is only 50%, meaning the model misses half the cases. That is why it is labelled "screening".
- Reference ranges are generic adult values (not for children or pregnancy).

## Ideas for extension
SHAP explanations, more diseases, larger datasets (e.g. NHANES), user accounts, PDF export, lab-report OCR.
