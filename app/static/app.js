const form = document.getElementById("gen-form");
const statusBox = document.getElementById("status");
const statusText = document.getElementById("status-text");
const bar = document.getElementById("bar");
const scriptPreview = document.getElementById("script-preview");
const resultBox = document.getElementById("result");
const errorBox = document.getElementById("error");
const errorText = document.getElementById("error-text");
const player = document.getElementById("player");
const downloadLink = document.getElementById("download");

const STAGES = {
  queued: { label: "Queued…", pct: 5 },
  writing_script: { label: "Writing narration script…", pct: 15 },
  generating_voiceover: { label: "Generating voiceover…", pct: 45 },
  rendering_video: { label: "Rendering pencil-sketch video (this takes a bit)…", pct: 80 },
  done: { label: "Done!", pct: 100 },
  error: { label: "Error", pct: 0 },
};

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  resultBox.hidden = true; errorBox.hidden = true;
  statusBox.hidden = false;
  statusText.textContent = "Submitting…"; bar.value = 2;
  const fd = new FormData(form);
  const res = await fetch("/api/generate", { method: "POST", body: fd });
  if (!res.ok) {
    errorBox.hidden = false; errorText.textContent = await res.text();
    statusBox.hidden = true; return;
  }
  const { job_id } = await res.json();
  poll(job_id);
});

async function poll(id) {
  try {
    const r = await fetch(`/api/status/${id}`);
    const job = await r.json();
    const stage = STAGES[job.status] || { label: job.status, pct: 50 };
    let label = stage.label;
    if (job.status === "generating_voiceover" && job.scenes_total) {
      label += ` (${job.scenes_done}/${job.scenes_total} scenes)`;
    }
    statusText.textContent = label;
    bar.value = stage.pct;
    if (job.script) scriptPreview.textContent = job.script.join("\n\n");
    if (job.status === "done") {
      resultBox.hidden = false;
      player.src = job.video_url;
      downloadLink.href = `/api/download/${id}`;
      return;
    }
    if (job.status === "error") {
      errorBox.hidden = false; errorText.textContent = job.error || "Unknown error";
      return;
    }
    setTimeout(() => poll(id), 2500);
  } catch (e) {
    errorBox.hidden = false; errorText.textContent = String(e);
  }
}
