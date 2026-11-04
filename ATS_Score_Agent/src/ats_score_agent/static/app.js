const form = document.getElementById("score-form");
const errorEl = document.getElementById("form-error");
const results = document.getElementById("results");
const scoreBtn = document.getElementById("score-btn");

document.getElementById("resume-file").addEventListener("change", (event) => {
  maybeFillTextarea(event.target.files[0], "resume-text");
});
document.getElementById("job-file").addEventListener("change", (event) => {
  maybeFillTextarea(event.target.files[0], "job-text");
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  errorEl.hidden = true;
  scoreBtn.disabled = true;
  scoreBtn.textContent = "Scoring…";

  const resumeFile = document.getElementById("resume-file").files[0];
  const jobFile = document.getElementById("job-file").files[0];
  const resumeText = document.getElementById("resume-text").value.trim();
  const jobText = document.getElementById("job-text").value.trim();

  try {
    let payload;
    if (resumeFile || jobFile) {
      const body = new FormData();
      body.set("resume_text", resumeText);
      body.set("job_text", jobText);
      if (resumeFile) body.set("resume_file", resumeFile);
      if (jobFile) body.set("job_file", jobFile);
      payload = await request("/api/score-files", { method: "POST", body });
    } else {
      payload = await request("/api/score", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ resume_text: resumeText, job_text: jobText }),
      });
    }
    render(payload);
  } catch (err) {
    errorEl.hidden = false;
    errorEl.textContent = err.message;
  } finally {
    scoreBtn.disabled = false;
    scoreBtn.textContent = "Score resume";
  }
});

async function request(url, options) {
  const response = await fetch(url, options);
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.detail || "Scoring failed.");
  }
  return data;
}

function maybeFillTextarea(file, textareaId) {
  if (!file) return;
  const name = file.name.toLowerCase();
  if (!(name.endsWith(".txt") || name.endsWith(".md"))) return;
  const reader = new FileReader();
  reader.onload = () => {
    document.getElementById(textareaId).value = String(reader.result);
  };
  reader.readAsText(file);
}

function render(data) {
  results.hidden = false;
  const score = data.score;
  document.getElementById("score-value").textContent = `${score}%`;
  const color = score >= 90 ? "#3f6b4b" : score >= 70 ? "#b45309" : "#9f1239";
  document.getElementById("gauge").style.background =
    `conic-gradient(${color} ${score * 3.6}deg, #e8dfd2 0deg)`;

  const gap = Math.max(0, data.target - score);
  document.getElementById("score-caption").textContent =
    gap === 0
      ? "This resume is already in the 90%+ ATS target range for this posting."
      : `${gap} points below the 90% target. Apply the high-priority edits first.`;
  document.getElementById("projected").textContent =
    `Projected score if recommended keywords and sections are added: ${data.projected_score}%.`;
  document.getElementById("title-line").textContent = data.job_title
    ? `Detected job title: ${data.job_title}${data.years_required ? ` · ${data.years_required}+ years requested` : ""}`
    : "";

  const warnings = document.getElementById("warnings");
  if (data.warnings?.length) {
    warnings.hidden = false;
    warnings.replaceChildren(...data.warnings.map((w) => Object.assign(document.createElement("p"), { textContent: w })));
  } else {
    warnings.hidden = true;
    warnings.replaceChildren();
  }

  const breakdown = document.getElementById("breakdown");
  breakdown.replaceChildren(
    ...data.breakdown.map((row) => {
      const wrap = document.createElement("div");
      wrap.className = "bar";
      wrap.innerHTML = `<span>${row.label} (${row.weight}%)</span>
        <div class="bar-track"><div class="bar-fill" style="width:${row.score}%"></div></div>
        <span>${row.score}%</span>`;
      return wrap;
    }),
  );

  fillChips("matched", data.matched_keywords, false);
  fillChips("missing", data.missing_required, true);

  const recs = document.getElementById("recs");
  recs.replaceChildren(
    ...data.recommendations.map((rec) => {
      const item = document.createElement("li");
      const priority = document.createElement("span");
      priority.className = "priority";
      priority.textContent = rec.priority;
      const title = document.createElement("strong");
      title.textContent = rec.title;
      const detail = document.createElement("div");
      detail.textContent = rec.estimated_gain
        ? `${rec.detail} ~+${rec.estimated_gain} pts`
        : rec.detail;
      item.append(priority, title, detail);
      if (rec.suggested_text) {
        const pre = document.createElement("pre");
        pre.className = "suggest";
        pre.textContent = rec.suggested_text;
        item.appendChild(pre);
      }
      return item;
    }),
  );
  results.scrollIntoView({ behavior: "smooth", block: "start" });
}

function fillChips(id, items, missing) {
  const root = document.getElementById(id);
  if (!items?.length) {
    root.textContent = missing ? "None — required keywords are covered." : "None yet.";
    return;
  }
  root.replaceChildren(
    ...items.map((term) => {
      const chip = document.createElement("span");
      chip.className = missing ? "chip missing" : "chip";
      chip.textContent = term;
      return chip;
    }),
  );
}
