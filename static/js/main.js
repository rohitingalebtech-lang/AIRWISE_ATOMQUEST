/**
 * AirWise — Client-side Interactive Engine
 * Handles real-time input synchronization, client validation,
 * async AJAX predictions, animated fan speed updates, and feedback submission.
 */

document.addEventListener("DOMContentLoaded", function () {
    // -------------------------------------------------------------
    // 1. Elements & DOM References
    // -------------------------------------------------------------
    const tempSlider = document.getElementById("temperature-slider");
    const tempInput = document.getElementById("temperature-input");
    const tempDisplay = document.getElementById("temp-display");
    const tempError = document.getElementById("temp-error");

    const humSlider = document.getElementById("humidity-slider");
    const humInput = document.getElementById("humidity-input");
    const humDisplay = document.getElementById("hum-display");
    const humError = document.getElementById("hum-error");

    const predictionForm = document.getElementById("prediction-form");
    const btnPredict = document.getElementById("btn-predict");
    const btnSpinner = document.getElementById("btn-spinner");
    const btnPredictText = document.getElementById("btn-predict-text");

    const fanBlades = document.getElementById("animated-fan-blades");
    const fanCenterLevel = document.getElementById("fan-center-level");
    const speedPill = document.getElementById("speed-pill");
    const speedTitle = document.getElementById("speed-title");
    const speedRpm = document.getElementById("speed-rpm");
    const activeMechanism = document.getElementById("active-mechanism");

    const persBox = document.getElementById("pers-box");
    const persTitle = document.getElementById("pers-title");
    const persDesc = document.getElementById("pers-desc");
    const persMeta = document.getElementById("pers-meta");

    const explanationText = document.getElementById("explanation-text");

    // KPI Displays
    const kpiTempVal = document.getElementById("kpi-temp-val");
    const kpiHumVal = document.getElementById("kpi-hum-val");
    const kpiTimeVal = document.getElementById("kpi-time-val");
    const kpiSpeedVal = document.getElementById("kpi-speed-val");
    const kpiSpeedName = document.getElementById("kpi-speed-name");
    const kpiFeedbackCount = document.getElementById("kpi-feedback-count");

    // Feedback Widget Elements
    const feedbackRecordId = document.getElementById("feedback-record-id");
    const feedbackButtons = document.querySelectorAll(".btn-feedback");
    const speedChoices = document.querySelectorAll(".speed-choice");
    const btnSubmitFeedback = document.getElementById("btn-submit-feedback");
    const feedbackStatusMsg = document.getElementById("feedback-status-msg");

    // Limits
    const TEMP_MIN = 12.0;
    const TEMP_MAX = 45.0;
    const HUM_MIN = 10.0;
    const HUM_MAX = 95.0;

    let selectedFeedbackType = "comfortable";

    // -------------------------------------------------------------
    // 2. Input Synchronization & Client Validation
    // -------------------------------------------------------------
    function syncTemp(val) {
        let num = parseFloat(val);
        if (isNaN(num)) num = 25.0;
        num = Math.max(TEMP_MIN, Math.min(TEMP_MAX, num));
        if (tempSlider) tempSlider.value = num;
        if (tempInput) tempInput.value = num.toFixed(1);
        if (tempDisplay) tempDisplay.textContent = num.toFixed(1) + " °C";
        validateTemp();
    }

    function syncHum(val) {
        let num = parseFloat(val);
        if (isNaN(num)) num = 50.0;
        num = Math.max(HUM_MIN, Math.min(HUM_MAX, num));
        if (humSlider) humSlider.value = num;
        if (humInput) humInput.value = num.toFixed(1);
        if (humDisplay) humDisplay.textContent = Math.round(num) + " %";
        validateHum();
    }

    function validateTemp() {
        if (!tempInput || !tempError) return true;
        const val = parseFloat(tempInput.value);
        if (isNaN(val) || val < TEMP_MIN || val > TEMP_MAX) {
            tempError.textContent = `Temperature must be between ${TEMP_MIN}°C and ${TEMP_MAX}°C.`;
            tempError.classList.add("active");
            return false;
        }
        tempError.classList.remove("active");
        return true;
    }

    function validateHum() {
        if (!humInput || !humError) return true;
        const val = parseFloat(humInput.value);
        if (isNaN(val) || val < HUM_MIN || val > HUM_MAX) {
            humError.textContent = `Humidity must be between ${HUM_MIN}% and ${HUM_MAX}%.`;
            humError.classList.add("active");
            return false;
        }
        humError.classList.remove("active");
        return true;
    }

    if (tempSlider && tempInput) {
        tempSlider.addEventListener("input", (e) => syncTemp(e.target.value));
        tempInput.addEventListener("change", (e) => syncTemp(e.target.value));
    }

    if (humSlider && humInput) {
        humSlider.addEventListener("input", (e) => syncHum(e.target.value));
        humInput.addEventListener("change", (e) => syncHum(e.target.value));
    }

    // Time-of-day radio pill selection
    const pillRadios = document.querySelectorAll(".pill-radio");
    pillRadios.forEach((pill) => {
        pill.addEventListener("click", function () {
            pillRadios.forEach((p) => p.classList.remove("active"));
            this.classList.add("active");
            const radio = this.querySelector('input[type="radio"]');
            if (radio) radio.checked = true;
        });
    });

    // Preset Scenario Buttons
    const presetButtons = document.querySelectorAll(".btn-preset");
    presetButtons.forEach((btn) => {
        btn.addEventListener("click", function () {
            const t = parseFloat(this.getAttribute("data-temp"));
            const h = parseFloat(this.getAttribute("data-hum"));
            const timeVal = this.getAttribute("data-time");

            syncTemp(t);
            syncHum(h);

            pillRadios.forEach((pill) => {
                const radio = pill.querySelector('input[type="radio"]');
                if (radio && radio.value === timeVal) {
                    pillRadios.forEach((p) => p.classList.remove("active"));
                    pill.classList.add("active");
                    radio.checked = true;
                }
            });
        });
    });

    // -------------------------------------------------------------
    // 3. Form Submission via AJAX (Async Prediction)
    // -------------------------------------------------------------
    if (predictionForm) {
        predictionForm.addEventListener("submit", async function (e) {
            e.preventDefault();

            if (!validateTemp() || !validateHum()) {
                return;
            }

            const activeRadio = document.querySelector('input[name="time_of_day"]:checked');
            const timeVal = activeRadio ? activeRadio.value : "Afternoon";
            const tempVal = parseFloat(tempInput.value);
            const humVal = parseFloat(humInput.value);

            // Set loading state
            if (btnSpinner) btnSpinner.style.display = "inline-block";
            if (btnPredictText) btnPredictText.textContent = "Computing...";
            btnPredict.disabled = true;

            try {
                const response = await fetch("/predict", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        "Accept": "application/json"
                    },
                    body: JSON.stringify({
                        temperature: tempVal,
                        humidity: humVal,
                        time_of_day: timeVal
                    })
                });

                const data = await response.json();

                if (!response.ok || data.status !== "success") {
                    alert(data.message || "An error occurred during prediction.");
                    return;
                }

                // Update UI Components
                updateDashboardWithPrediction(data);

            } catch (err) {
                console.error("Prediction Error:", err);
                alert("Network error: Could not reach the AirWise local server.");
            } finally {
                if (btnSpinner) btnSpinner.style.display = "none";
                if (btnPredictText) btnPredictText.textContent = "⚡ Compute Comfort Recommendation";
                btnPredict.disabled = false;
            }
        });
    }

    function updateDashboardWithPrediction(data) {
        const activeSpeed = data.active_speed;
        const speedInfo = data.active_speed_info;
        const pers = data.personalization;
        const ml = data.ml;

        // 1. Update KPI Card Values
        if (kpiTempVal) kpiTempVal.textContent = `${data.inputs.temperature}°C`;
        if (kpiHumVal) kpiHumVal.textContent = `${data.inputs.humidity}% Humidity`;
        if (kpiTimeVal) kpiTimeVal.textContent = data.inputs.time_of_day;
        if (kpiSpeedVal) kpiSpeedVal.textContent = `Level ${activeSpeed}`;
        if (kpiSpeedName) kpiSpeedName.textContent = speedInfo.name;
        if (kpiFeedbackCount) kpiFeedbackCount.textContent = data.feedback_count;

        // 2. Update Animated Fan Visualizer
        if (fanBlades) {
            fanBlades.className = `fan-blades fan-speed-${activeSpeed}`;
        }
        if (fanCenterLevel) fanCenterLevel.textContent = activeSpeed;
        if (speedPill) speedPill.textContent = `Level ${activeSpeed}`;
        if (speedTitle) speedTitle.textContent = speedInfo.name;
        if (speedRpm) speedRpm.textContent = speedInfo.rpm_range;
        if (activeMechanism) {
            activeMechanism.textContent = pers.has_personalization
                ? "Personalised (ML + Feedback Offset)"
                : "Baseline Decision Tree ML";
        }

        // 3. Update Personalisation Status Box
        if (persBox) {
            if (pers.has_personalization) {
                persBox.classList.add("active-offset");
            } else {
                persBox.classList.remove("active-offset");
            }
            if (persDesc) persDesc.textContent = pers.explanation;
            if (persMeta) {
                const sign = pers.adjustment > 0 ? `+${pers.adjustment}` : `${pers.adjustment}`;
                persMeta.textContent = `Decision Tree Base: Level ${ml.speed} | Offset Applied: ${sign} Level(s)`;
            }
        }

        // 4. Update Explanation Box
        if (explanationText) {
            explanationText.textContent = ml.explanation;
        }

        // 5. Update Feedback Widget
        if (feedbackRecordId) {
            feedbackRecordId.value = data.record_id;
        }
        if (feedbackStatusMsg) {
            feedbackStatusMsg.textContent = "";
        }

        // Auto-select recommended speed in preferred speed selector
        selectPreferredSpeed(activeSpeed);
    }

    // -------------------------------------------------------------
    // 4. User Feedback Submission (Feature 5)
    // -------------------------------------------------------------
    feedbackButtons.forEach((btn) => {
        btn.addEventListener("click", function () {
            feedbackButtons.forEach((b) => b.classList.remove("active"));
            this.classList.add("active");
            selectedFeedbackType = this.getAttribute("data-type");

            // Intuitive speed adjustment suggestions
            const currentSpeed = parseInt(fanCenterLevel ? fanCenterLevel.textContent : "3", 10);
            if (selectedFeedbackType === "too_slow") {
                selectPreferredSpeed(Math.min(5, currentSpeed + 1));
            } else if (selectedFeedbackType === "too_fast") {
                selectPreferredSpeed(Math.max(1, currentSpeed - 1));
            } else {
                selectPreferredSpeed(currentSpeed);
            }
        });
    });

    speedChoices.forEach((choice) => {
        choice.addEventListener("click", function () {
            const radio = this.querySelector('input[type="radio"]');
            if (radio) {
                selectPreferredSpeed(parseInt(radio.value, 10));
            }
        });
    });

    function selectPreferredSpeed(level) {
        speedChoices.forEach((choice) => {
            const radio = choice.querySelector('input[type="radio"]');
            if (radio && parseInt(radio.value, 10) === level) {
                choice.classList.add("selected");
                radio.checked = true;
            } else {
                choice.classList.remove("selected");
                if (radio) radio.checked = false;
            }
        });
    }

    if (btnSubmitFeedback) {
        btnSubmitFeedback.addEventListener("click", async function () {
            let recordId = feedbackRecordId ? feedbackRecordId.value : "";

            // If user hasn't computed a recommendation yet, auto-trigger one first
            if (!recordId) {
                if (predictionForm) {
                    await predictionForm.dispatchEvent(new Event("submit"));
                    recordId = feedbackRecordId ? feedbackRecordId.value : "";
                }
            }

            if (!recordId) {
                alert("Please click 'Compute Comfort Recommendation' first before submitting feedback.");
                return;
            }

            const activeSpeedRadio = document.querySelector('input[name="preferred_speed"]:checked');
            const preferredLevel = activeSpeedRadio ? parseInt(activeSpeedRadio.value, 10) : 3;

            btnSubmitFeedback.disabled = true;
            btnSubmitFeedback.textContent = "Saving...";

            try {
                const response = await fetch("/feedback", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        "Accept": "application/json"
                    },
                    body: JSON.stringify({
                        record_id: parseInt(recordId, 10),
                        preferred_speed: preferredLevel,
                        feedback_type: selectedFeedbackType
                    })
                });

                const resData = await response.json();

                if (!response.ok || resData.status !== "success") {
                    alert(resData.message || "Failed to save feedback.");
                    return;
                }

                if (feedbackStatusMsg) {
                    feedbackStatusMsg.textContent = `✅ Saved! Preferred Level ${preferredLevel} logged in SQLite memory.`;
                }

                if (kpiFeedbackCount && resData.new_feedback_count !== undefined) {
                    kpiFeedbackCount.textContent = resData.new_feedback_count;
                }

            } catch (err) {
                console.error("Feedback Save Error:", err);
                alert("Network error: Could not save feedback to SQLite database.");
            } finally {
                btnSubmitFeedback.disabled = false;
                btnSubmitFeedback.textContent = "💾 Save Feedback to Memory";
            }
        });
    }

    // -------------------------------------------------------------
    // 5. Interactive Comparison Tester (/compare page)
    // -------------------------------------------------------------
    const compTempSlider = document.getElementById("comp-temp-slider");
    const compHumSlider = document.getElementById("comp-hum-slider");
    const compTimeSelect = document.getElementById("comp-time-select");

    const compTempVal = document.getElementById("comp-temp-val");
    const compHumVal = document.getElementById("comp-hum-val");
    const compMlSpeed = document.getElementById("comp-ml-speed");
    const compMlName = document.getElementById("comp-ml-name");
    const compRuleSpeed = document.getElementById("comp-rule-speed");
    const compRuleName = document.getElementById("comp-rule-name");
    const compRuleDesc = document.getElementById("comp-rule-desc");
    const compAgreementBanner = document.getElementById("comp-agreement-banner");
    const compAgreementIcon = document.getElementById("comp-agreement-icon");
    const compAgreementText = document.getElementById("comp-agreement-text");

    const SPEED_NAMES = {
        1: "Level 1 — Whisper Breeze",
        2: "Level 2 — Gentle Breeze",
        3: "Level 3 — Moderate Flow",
        4: "Level 4 — High Cooling",
        5: "Level 5 — Turbo Airflow"
    };

    function runRuleBasedClient(temp, hum, time) {
        let speed = 1;
        if (temp < 20.0) speed = 1;
        else if (temp < 25.0) speed = 2;
        else if (temp < 30.0) speed = 3;
        else if (temp < 35.0) speed = 4;
        else speed = 5;

        if (hum >= 70.0 && speed < 5) speed += 1;
        else if (hum <= 30.0 && speed > 1) speed -= 1;

        if (time.toLowerCase() === "night" && speed > 1) speed -= 1;

        return Math.max(1, Math.min(5, speed));
    }

    function runMLProxyClient(temp, hum, time) {
        // Continuous model approximation for fluid slider comparison
        const timeOffsets = { morning: 0.0, afternoon: 1.5, evening: 0.5, night: -2.0 };
        const offset = timeOffsets[time.toLowerCase()] || 0.0;
        const score = temp + 0.14 * (hum - 40.0) + offset;

        if (score < 21.0) return 1;
        if (score < 25.5) return 2;
        if (score < 30.5) return 3;
        if (score < 36.0) return 4;
        return 5;
    }

    function updateComparisonPlayground() {
        if (!compTempSlider || !compHumSlider || !compTimeSelect) return;

        const temp = parseFloat(compTempSlider.value);
        const hum = parseFloat(compHumSlider.value);
        const time = compTimeSelect.value;

        if (compTempVal) compTempVal.textContent = temp.toFixed(1);
        if (compHumVal) compHumVal.textContent = Math.round(hum);

        const mlSpeed = runMLProxyClient(temp, hum, time);
        const ruleSpeed = runRuleBasedClient(temp, hum, time);

        if (compMlSpeed) compMlSpeed.textContent = `Level ${mlSpeed}`;
        if (compMlName) compMlName.textContent = SPEED_NAMES[mlSpeed] || `Level ${mlSpeed}`;

        if (compRuleSpeed) compRuleSpeed.textContent = `Level ${ruleSpeed}`;
        if (compRuleName) compRuleName.textContent = SPEED_NAMES[ruleSpeed] || `Level ${ruleSpeed}`;

        if (compRuleDesc) {
            let humNote = hum >= 70 ? "+1 humidity shift applied" : (hum <= 30 ? "-1 dry shift applied" : "no humidity shift");
            let nightNote = time.toLowerCase() === "night" ? ", -1 night quiet mode" : "";
            compRuleDesc.textContent = `Evaluated: ${temp.toFixed(1)}°C base, ${humNote}${nightNote}.`;
        }

        if (compAgreementText && compAgreementBanner) {
            if (mlSpeed === ruleSpeed) {
                compAgreementBanner.style.borderColor = "var(--green-accent)";
                compAgreementIcon.textContent = "✅";
                compAgreementText.innerHTML = `<strong>Full Agreement:</strong> Both the Decision Tree and the Rule-Based Baseline recommend <strong>Level ${mlSpeed}</strong>.`;
            } else {
                compAgreementBanner.style.borderColor = "var(--border-highlight)";
                compAgreementIcon.textContent = "⚡";
                const diff = mlSpeed - ruleSpeed;
                const sign = diff > 0 ? `+${diff}` : `${diff}`;
                compAgreementText.innerHTML = `<strong>Divergent Boundary:</strong> Decision Tree outputs <strong>Level ${mlSpeed}</strong> vs. Baseline <strong>Level ${ruleSpeed}</strong> (${sign} level diff). The Decision Tree models continuous heat accumulation rather than hard steps.`;
            }
        }
    }

    if (compTempSlider && compHumSlider && compTimeSelect) {
        compTempSlider.addEventListener("input", updateComparisonPlayground);
        compHumSlider.addEventListener("input", updateComparisonPlayground);
        compTimeSelect.addEventListener("change", updateComparisonPlayground);
        updateComparisonPlayground();
    }
});
