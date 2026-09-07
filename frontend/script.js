const dropzone = document.getElementById("dropzone");
const fileInput = document.getElementById("file-input");
const dzEmpty = document.getElementById("dz-empty");
const previewWrap = document.getElementById("preview-wrap");
const previewImg = document.getElementById("preview-img");
const scanLine = document.getElementById("scan-line");
const scanBtn = document.getElementById("scan-btn");
const resetBtn = document.getElementById("reset-btn");
const errorBox = document.getElementById("error-box");
const processingNote = document.getElementById("processing-note");
const resultPanel = document.getElementById("result-panel");
const verdictBanner = document.getElementById("verdict-banner");
const verdictMark = document.getElementById("verdict-mark");
const verdictCopy = document.getElementById("verdict-copy");
const fieldList = document.getElementById("field-list");
const rawText = document.getElementById("raw-text");

let selectedFile = null;

dropzone.addEventListener("click", () => fileInput.click());

fileInput.addEventListener("change", (e) => {
  const file = e.target.files?.[0];
  if (file) handleFile(file);
});

function handleFile(file) {
  selectedFile = file;
  previewImg.src = URL.createObjectURL(file);
  dzEmpty.hidden = true;
  previewWrap.hidden = false;
  scanBtn.disabled = false;
  resetBtn.hidden = false;
  errorBox.hidden = true;
  resultPanel.hidden = true;
}

resetBtn.addEventListener("click", (e) => {
  e.stopPropagation();
  selectedFile = null;
  fileInput.value = "";
  dzEmpty.hidden = false;
  previewWrap.hidden = true;
  scanBtn.disabled = true;
  resetBtn.hidden = true;
  resultPanel.hidden = true;
});

const STATUS_LABEL = {
  compliant: "OK",
  non_compliant: "!",
  not_detected: "X",
};

scanBtn.addEventListener("click", async () => {
  if (!selectedFile) return;

  errorBox.hidden = true;
  resultPanel.hidden = true;
  scanBtn.disabled = true;
  processingNote.hidden = false;
  scanLine.hidden = false;

  const form = new FormData();
  form.append("image", selectedFile);

  try {
    const res = await fetch("/api/scan", { method: "POST", body: form });
    const data = await res.json().catch(() => ({}));

    if (!res.ok) {
      throw new Error(data.detail || "Scan failed. Please try again.");
    }

    renderResult(data);
  } catch (err) {
    errorBox.textContent = err.message;
    errorBox.hidden = false;
  } finally {
    scanBtn.disabled = false;
    processingNote.hidden = true;
    scanLine.hidden = true;
  }
});

function renderResult(data) {
  verdictBanner.className = `verdict-banner ${data.verdict}`;
  verdictMark.textContent = data.verdict === "compliant" ? "Compliant" : "Non-Compliant";
  verdictCopy.textContent = data.summary;

  fieldList.innerHTML = "";
  data.fields.forEach((f) => {
    const li = document.createElement("li");
    li.className = "field-row";
    li.innerHTML = `
      <span class="field-badge ${f.status}">${STATUS_LABEL[f.status] || "?"}</span>
      <span class="field-body">
        <span class="field-label">${f.label}</span>
        ${f.detected_value ? `<div class="field-value">${escapeHtml(f.detected_value)}</div>` : ""}
        <div class="field-note">${escapeHtml(f.note)}</div>
      </span>
    `;
    fieldList.appendChild(li);
  });

  rawText.textContent = data.raw_text;
  resultPanel.hidden = false;
  resultPanel.scrollIntoView({ behavior: "smooth", block: "start" });
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}
