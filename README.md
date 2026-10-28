# AirWise — A Personalised Comfort Learning System for Fans

**AtomQUEST 2026 Round 2 Competition Prototype**  
**Track:** Track 1 — Fan  
**Institution:** Nutan Maharashtra Institute of Engineering and Technology (NMIET), Pune, Maharashtra, India  
**Team Members:**
* **Rohit Ingale** (Team Lead & Full-Stack / ML Developer)
* **Sarthak Avhad** (Systems Architecture & ML Engineer)
* **Gargi Rane** (UI/UX Design & Frontend Integration)
* **Hitesh Yuvare** (Software Testing & Data Validation)

---

## 1. Project Description

**AirWise** is an intelligent, software-based comfort recommendation prototype developed for the AtomQUEST 2026 Round 2 competition. The system dynamically computes one of five optimal fan-speed levels (Level 1 to Level 5) based on real-time ambient inputs:
* **Room Temperature** (°C)
* **Relative Humidity** (%)
* **Time of Day** (Morning, Afternoon, Evening, Night)
* **Saved User Feedback History** (Contextual Personalisation)

### ⚠️ Important Simulation Notice
> **Notice:** AirWise is an initial **software-only simulation prototype**. It does **not** directly interface with or control a physical ceiling/table fan, and does **not** poll physical IoT sensors in this round. All sensor inputs are simulated via software controls, and training labels are generated through documented psychrometric assumptions. Fan speeds represent algorithmic recommendations rather than electrical actuator commands. Hardware fail-safe behaviors and high-voltage motor decoupling have not yet been physically validated.

---

## 2. Features

* **Feature 1 — Professional Engineering Dashboard:** Modern deep navy-blue aesthetic (`#060c18`), clean typography (Outfit & JetBrains Mono), vibrant cyan accents (`#00f0ff`), responsive cards, animated rotating fan speed gauge, and clear state indicators (loading, success, empty, error).
* **Feature 2 — Comfort Inputs & Dual Validation:** Interactive continuous sliders and numeric fields with client-side and server-side range validation (12°C–45°C temperature, 10%–95% relative humidity, 4 time-of-day categories).
* **Feature 3 — Scikit-Learn DecisionTreeClassifier:** Real machine learning classification trained on a reproducible synthetic thermal comfort dataset (1,200 records, fixed random seed `42`, 80/20 stratified split).
* **Feature 4 — Deterministic Rule-Based Baseline:** Heuristic benchmark evaluated on the exact same held-out test split, complete with an interactive side-by-side scenario playground.
* **Feature 5 — User Feedback & Personalisation Engine:** Transparent instance-based memory offset logic that stores user comfort ratings (Too Slow, Comfortable, Too Fast) and preferred speeds in SQLite, automatically adjusting future predictions for similar ambient conditions without requiring costly in-place model retraining.
* **Feature 6 — Persistent History Store:** Full SQLite history table of past recommendations, applied adjustments, and user preferences with filterable views and empty-state messaging.
* **Feature 7 — Genuine Model Evaluation:** Live metrics dashboard displaying real held-out test accuracy, macro precision, recall, F1-score, and a 5×5 multi-class confusion matrix.
* **Feature 8 — Safety & Limitations Transparency:** Clear disclaimers and an architectural roadmap detailing planned optical isolation and hardware watchdogs for Round 3.
* **Feature 9 — Automated Testing Suite:** Comprehensive `unittest` suite covering validation, model training, baseline logic, personalization, database persistence, and web routes.

---

## 3. Technology Stack

* **Language:** Python 3.12 (standard local CPython runtime)
* **Web Framework:** Flask 3.1
* **Machine Learning:** scikit-learn 1.9 (DecisionTreeClassifier, train_test_split, metrics)
* **Scientific Computing:** NumPy 2.5, pandas 3.1, SciPy 1.18
* **Database:** SQLite 3 (parameterized SQL queries via Python standard library)
* **Frontend:** Semantic HTML5, Vanilla CSS3 (Custom Design System, Glassmorphic Navy Cards, Keyframe Animations), Vanilla JavaScript (ES6+ Fetch API, DOM manipulation)
* **Testing:** Python `unittest` framework

*Note: Free and 100% locally runnable. No external paid APIs, cloud services, or API keys are required.*

---

## 4. Project Folder Structure

```
AIRWISE_ATOMQUEST/
│
├── app.py                     # Main Flask web application, routing, error handlers, and REST APIs
├── config.py                  # Project metadata, physical ranges, fan level definitions, and constants
├── database.py                # SQLite database management, schema creation, and parameterized queries
├── ml_model.py                # Synthetic dataset generator, DecisionTreeClassifier training and evaluation
├── baseline.py                # Deterministic rule-based baseline and comparative test set evaluation
├── personalizer.py            # Contextual instance-based personalisation engine and memory offset logic
├── test_app.py                # Automated test suite (24 tests covering all components)
├── requirements.txt           # Project dependencies
├── README.md                  # Complete documentation and setup manual
│
├── static/
│   ├── css/
│   │   └── style.css          # Deep navy theme, cyan highlights, responsive layouts, fan animations
│   └── js/
│       └── main.js            # Input synchronization, AJAX predictions, fan blade speed updates, feedback
│
└── templates/
    ├── base.html              # Base layout with persistent simulation notice, navigation, and footer
    ├── index.html             # Main engineering dashboard, input form, fan visualizer, feedback widget
    ├── compare.html           # Side-by-side ML vs. Rule-based comparator and benchmark table
    ├── history.html           # Filterable SQLite history log with clear empty states
    ├── evaluation.html        # Model evaluation report, confusion matrix, per-class metrics
    ├── about.html             # Safety and limitations notice, team roster, Round 3 roadmap
    ├── 404.html               # Custom 404 Not Found error template
    └── 500.html               # Custom 500 Server Error template
```

---

## 5. Installation Instructions for Windows

Follow these simple steps using the Windows Command Prompt or PowerShell:

### Step 1: Open PowerShell or Command Prompt
Navigate to your project directory:
```powershell
cd "c:\Users\Rohit Ingale\OneDrive\Desktop\AIRWISE_ATOMQUEST"
```

### Step 2: Verify Python 3.12
Check that Python 3.12 is available on your machine:
```powershell
py -3.12 --version
```

---

## 6. Virtual Environment Instructions

Creating and isolating dependencies inside a virtual environment prevents version conflicts:

### Step 1: Create the Virtual Environment
```powershell
py -3.12 -m venv .venv
```

### Step 2: Activate the Virtual Environment
In PowerShell:
```powershell
.\.venv\Scripts\Activate.ps1
```
*(If you encounter a script execution policy error, run `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser` or simply call the venv Python executable directly as shown below).*

### Step 3: Install Required Dependencies
```powershell
.\.venv\Scripts\pip install -r requirements.txt
```

---

## 7. How to Run the Application

Start the local Flask development web server:

```powershell
$env:OMP_NUM_THREADS="1"; .\.venv\Scripts\python app.py
```

Once started, open your web browser (Chrome, Edge, Firefox) and navigate to:
```
http://127.0.0.1:5000
```

To run the automated test suite at any time:
```powershell
.\.venv\Scripts\python -m unittest test_app.py
```

### 7.1 Deploying to Render (Cloud Hosting)

The application is pre-configured for deployment on [Render](https://render.com) using the included `Procfile`, `.python-version`, and `render.yaml`:

1. **Push your code to a Git repository** (GitHub or GitLab).
2. **Log into Render** (https://dashboard.render.com/) and click **New +** -> **Web Service**.
3. **Connect your Git repository**.
4. Configure the Web Service settings:
   * **Name:** `airwise-fan-comfort` (or your choice)
   * **Region:** Any close region (e.g., Singapore, Frankfurt, Oregon)
   * **Branch:** `main`
   * **Runtime:** `Python 3`
   * **Build Command:** `pip install -r requirements.txt`
   * **Start Command:** `gunicorn app:app`
   * **Plan:** Free
5. In **Advanced** -> **Environment Variables**, optionally set:
   * `PYTHON_VERSION`: `3.12.10`
   * `FLASK_DEBUG`: `0`
   * `OMP_NUM_THREADS`: `1`
6. Click **Create Web Service**.

> **⚠️ Critical Persistence Note for Render Free Tier:**  
> Render's free tier uses an **ephemeral container filesystem**. While the application will run and save predictions to SQLite during an active session, **all database records (`airwise.db`) will reset to their initial state whenever the container restarts, redeploys, or spins down due to inactivity** (15 minutes of idle time). To guarantee persistent SQLite storage across restarts on Render, a paid **Render Persistent Disk** must be mounted, or an external managed database (e.g. PostgreSQL) would be required. On the free tier, the application starts cleanly with fresh tables upon every restart.

---

## 8. How to Use Each Feature

### 1. Generating Comfort Recommendations
1. Navigate to the **Dashboard** (`/`).
2. Adjust the **Room Temperature** slider (12.0°C to 45.0°C) or type a value directly into the numeric field.
3. Adjust the **Relative Humidity** slider (10% to 95%).
4. Click one of the **Time of Day** pills (Morning, Afternoon, Evening, or Night).
5. Alternatively, click any of the **Quick Scenario Presets** (e.g., *Hot Afternoon: 33°C, 80%* or *Cool Morning: 18°C, 40%*).
6. Click **⚡ Compute Comfort Recommendation**.
7. The animated fan visualizer will immediately alter its rotational speed (Level 1: 2.4s gentle rotation, Level 5: 0.22s rapid rotation), and display the simulated RPM and scientific physical rationale.

### 2. Submitting Feedback & Observing Personalisation
1. Beneath the recommendation card, observe the **Save Your Comfort Feedback** widget.
2. Select how the airflow feels: **🐢 Too Slow**, **👌 Comfortable**, or **⚡ Too Fast**.
3. Choose your preferred speed level (1 to 5).
4. Click **💾 Save Feedback to Memory**.
5. The feedback is persisted into `airwise.db`.
6. Now, enter similar ambient conditions (within ±3°C and ±15% humidity). When you click **Compute Comfort Recommendation**, the **Personalisation Engine** applies an adjustment offset (e.g., *+1 Level from past feedback*), displaying a green active personalisation badge!

### 3. Comparing ML vs. Rule-Based Baseline
1. Click **ML vs Rules** in the top navigation bar (`/compare`).
2. Review the fair evaluation benchmark table showing genuine metrics on the exact same held-out test split.
3. Use the **Interactive Side-by-Side Scenario Tester** sliders to view both engines' outputs in real time and see why the Decision Tree better handles continuous multi-variable boundaries.

### 4. Viewing History
1. Click **History** in the navigation bar (`/history`).
2. View previous recommendations, user ratings, preferred speeds, and applied offsets.
3. Use the filter buttons to isolate records with feedback or pending feedback.

### 5. Reviewing Model Evaluation
1. Click **Model Evaluation** (`/evaluation`).
2. Inspect the held-out test accuracy, macro F1-score, the 5×5 Confusion Matrix, and per-class precision and recall.

---

## 9. How the Model Works

The core machine learning engine uses a scikit-learn `DecisionTreeClassifier`:

1. **Feature Vector:** Each input state consists of:
   * $x_1$: Room Temperature in °C ($\in [12.0, 45.0]$)
   * $x_2$: Relative Humidity in % ($\in [10.0, 95.0]$)
   * $x_3$: Time of Day (Categorically encoded: Morning=0, Afternoon=1, Evening=2, Night=3)
2. **Decision Tree Architecture:** The tree is configured with `max_depth=5` and `min_samples_leaf=4` using the Gini impurity criterion. This prevents overfitting while discovering non-linear interaction boundaries between humidity and temperature.
3. **Inference & Explanations:** The tree outputs both a discrete predicted speed (1 to 5) and class probability distributions across all five levels. An objective explanation generator translates the psychrometric parameters into clear physical terms (e.g., explaining why high humidity inhibits evaporative cooling).

---

## 10. How Evaluation is Calculated

* **Reproducibility:** A fixed pseudo-random seed (`RANDOM_SEED = 42`) is used for synthetic data generation and train-test splitting.
* **Stratified Split:** The 1,200 synthetic instances are split into 80% training (960 samples) and 20% held-out testing (240 samples), stratified to ensure equal class proportions.
* **No Fabricated Metrics:** The metrics displayed on the dashboard, comparison page, and evaluation report are computed live via scikit-learn:
  $$\text{Accuracy} = \frac{\sum_{i=1}^{N} \mathbb{I}(y_i = \hat{y}_i)}{N}$$
  $$\text{Macro } F_1 = \frac{1}{K} \sum_{k=1}^{K} F_{1, k}$$
* **Fair Baseline Benchmarking:** The rule-based baseline is tested on the identical 240 test instances without altering any conditions.

---

## 11. Synthetic-Data Limitations

1. **Approximation Assumptions:** Synthetic comfort labels are derived from a simplified heat-index formula proxy ($S = T + 0.14 \times (H - 40) + \text{offset}$) with 10% stochastic human variation.
2. **No Direct Biological Sensing:** Synthetic data models simplified thermal physics, but real-world comfort (as standardized by ASHRAE 55 and ISO 7730) depends on clothing insulation (clo), metabolic activity (met), radiant wall temperatures, and localized drafts.
3. **Purpose of Prototype:** The synthetic dataset proves the mathematical and software viability of adaptive fan control, but should not be mistaken for empirical clinical human trials.

---

## 12. Known Limitations & Future Improvements (Round 3 Roadmap)

| Current Prototype Limitation | Planned Round 3 Physical Improvement |
| :--- | :--- |
| **Software-only simulation** | Connect an ESP32 microcontroller with an I2C SHT31 sensor (±0.2°C accuracy). |
| **No physical actuator** | Interface a 12V/24V BLDC fan with a 25 kHz PWM speed controller. |
| **Actuator safety untested** | Deploy optocouplers (optical isolation) and hardware thermal fuses to isolate high-voltage mains. |
| **PC-dependent Flask server** | Quantize Decision Tree into C/C++ (TinyML) to run standalone on the ESP32. |
| **Simplified human modeling** | Incorporate radiant temperature sensors (MLX90614) and wearable heart-rate telemetry. |

---

## 13. Team & Academic Credits

* **Institution:** Nutan Maharashtra Institute of Engineering and Technology (NMIET), Pune
* **Department:** Artificial Intelligence and Data Science
* **Affiliation:** Savitribai Phule Pune University (SPPU)
* **Competition:** AtomQUEST 2026 Round 2 — Track 1: Fan
* **Student Developers:** Rohit Ingale, Sarthak Avhad, Gargi Rane, Hitesh Yuvare
