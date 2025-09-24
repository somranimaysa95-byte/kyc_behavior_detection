document.addEventListener("DOMContentLoaded", () => {
  const startTime = Date.now();
  const sessionId = generateSessionId();
  const fieldData = {};
  const fieldOrder = [];
  let mouseMoved = false;
  let mouseClickCount = 0;
  let scrollCount = 0;
  let viewportChanges = 0;
  let tabKeyCount = 0;
  let enterPressed = false;
  let lastInteractionTime = startTime;

  document.addEventListener("mousemove", () => mouseMoved = true);
  document.addEventListener("click", () => mouseClickCount++);
  window.addEventListener("scroll", () => scrollCount++);
  window.addEventListener("resize", () => viewportChanges++);
  document.addEventListener("keydown", (e) => {
    lastInteractionTime = Date.now();
    if (e.key === "Tab") tabKeyCount++;
    if (e.key === "Enter") enterPressed = true;
  });

  const form = document.querySelector("form");
  if (!form) return;

  const inputs = form.querySelectorAll("input, textarea, select");
  inputs.forEach(input => {
    const name = input.name || input.id || "unnamed";
    let focusStart = 0;
    let hoverStart = 0;
    let valueBefore = "";
    let changes = 0;
    let deleteCount = 0;
    let copyCount = 0;
    let pasteCount = 0;
    let focusCount = 0;

    fieldData[name] = {
      value: "",
      timeSpentMs: 0,
      hoverDurationMs: 0,
      copy: 0,
      paste: 0,
      delete: 0,
      changes: 0,
      focusCount: 0
    };

    input.addEventListener("focus", () => {
      focusStart = Date.now();
      focusCount++;
      if (!fieldOrder.includes(name)) {
        fieldOrder.push(name);
      }
    });

    input.addEventListener("blur", () => {
      const duration = Date.now() - focusStart;
      fieldData[name].timeSpentMs += duration;
      fieldData[name].value = input.value;
      fieldData[name].focusCount = focusCount;
    });

    input.addEventListener("mouseover", () => hoverStart = Date.now());
    input.addEventListener("mouseout", () => {
      const hoverTime = Date.now() - hoverStart;
      fieldData[name].hoverDurationMs += hoverTime;
    });

    input.addEventListener("input", () => {
      lastInteractionTime = Date.now();
      const newValue = input.value;
      if (newValue !== valueBefore) {
        changes++;
        valueBefore = newValue;
      }
      fieldData[name].changes = changes;
    });

    input.addEventListener("keydown", (e) => {
      lastInteractionTime = Date.now();
      if (e.key === "Backspace" || e.key === "Delete") deleteCount++;
      fieldData[name].delete = deleteCount;
    });

    input.addEventListener("copy", () => {
      copyCount++;
      fieldData[name].copy = copyCount;
    });

    input.addEventListener("paste", () => {
      pasteCount++;
      fieldData[name].paste = pasteCount;
    });
  });

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const endTime = Date.now();
    const durationMs = endTime - startTime;
    const submitDelay = endTime - lastInteractionTime;

    const fastFill = durationMs < 8000 && Object.values(fieldData).every(f => f.value);

    const payload = {
      session_id: sessionId,
      start_time: startTime,
      end_time: endTime,
      duration_ms: durationMs,
      submit_delay_ms: submitDelay,
      fast_fill: fastFill,
      mouseMoved,
      mouseClickCount,
      scrollCount,
      viewportChanges,
      tabKeyCount,
      enterPressed,
      deviceType: detectDeviceType(),
      field_order: fieldOrder,
      fields: fieldData
    };

    try {
      const saveRes = await fetch("/api/save", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      if (!saveRes.ok) throw new Error("Erreur lors de l’enregistrement");

      const predictRes = await fetch("/api/predict", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      if (!predictRes.ok) throw new Error("Erreur lors de la prédiction");

      const result = await predictRes.json();

      // Message neutre pour l’utilisateur
      document.getElementById("client-message").innerText =
        "Merci. Votre demande a été transmise à nos équipes pour analyse.";

      // Résultat caché pour debug ou analyste
      document.getElementById("prediction-result").innerText =
        `Score : ${result.score} | Label : ${result.label}`;
      document.getElementById("prediction-result").style.display = "none";

      console.log("🔍 Résultat interne :", result);
    } catch (error) {
      console.error("❌ Erreur d'envoi :", error);
      document.getElementById("client-message").innerText =
        "Une erreur est survenue. Veuillez réessayer plus tard.";
    }
  });

  function generateSessionId() {
    return "sess_" + Math.random().toString(36).substr(2, 9);
  }

  function detectDeviceType() {
    const ua = navigator.userAgent;
    if (/mobile/i.test(ua)) return "mobile";
    if (/tablet/i.test(ua)) return "tablet";
    return "desktop";
  }
});
