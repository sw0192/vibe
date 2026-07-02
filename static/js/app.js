const form = document.querySelector("#converter-form");
const dropzone = document.querySelector("#dropzone");
const fileInput = document.querySelector("#image");
const fileName = document.querySelector("#file-name");
const formMessage = document.querySelector("#form-message");
const jobList = document.querySelector("#job-list");
const queueCount = document.querySelector("#queue-count");
const convertButton = document.querySelector("#convert-button");
const recommendationList = document.querySelector("#recommendation-list");
const recommendationSummary = document.querySelector("#recommendation-summary");

const IMAGE_OUTPUTS = ["jpg", "png", "webp"];
const PDF_OUTPUTS = ["jpg", "png", "webp"];
const VIDEO_OUTPUTS = ["mp4", "webm", "gif", "mp3"];
const AUDIO_OUTPUTS = ["mp3", "wav", "ogg"];
const MAX_PARALLEL_CONVERSIONS = 4;

const EXTENSION_HINTS = {
  jpg: ["image", "JPG image"],
  jpeg: ["image", "JPG image"],
  png: ["image", "PNG image"],
  webp: ["image", "WEBP image"],
  bmp: ["image", "BMP image"],
  tif: ["image", "TIFF image"],
  tiff: ["image", "TIFF image"],
  gif: ["image", "GIF image"],
  mp4: ["video", "MP4 video"],
  mov: ["video", "QuickTime video"],
  webm: ["video", "WEBM video"],
  mp3: ["audio", "MP3 audio"],
  wav: ["audio", "WAV audio"],
  flac: ["audio", "FLAC audio"],
  ogg: ["audio", "OGG audio"],
  pdf: ["document", "PDF document"],
  zip: ["archive", "ZIP archive"],
};

function startsWith(bytes, signature) {
  return signature.every((value, index) => bytes[index] === value);
}

function textAt(bytes, start, end) {
  return String.fromCharCode(...bytes.slice(start, end));
}

function detectMagic(bytes) {
  if (startsWith(bytes, [0xff, 0xd8, 0xff])) return ["image", "JPG image"];
  if (startsWith(bytes, [0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a])) return ["image", "PNG image"];
  if (textAt(bytes, 0, 6) === "GIF87a" || textAt(bytes, 0, 6) === "GIF89a") return ["image", "GIF image"];
  if (textAt(bytes, 0, 2) === "BM") return ["image", "BMP image"];
  if (startsWith(bytes, [0x49, 0x49, 0x2a, 0x00]) || startsWith(bytes, [0x4d, 0x4d, 0x00, 0x2a])) return ["image", "TIFF image"];
  if (textAt(bytes, 0, 4) === "RIFF" && textAt(bytes, 8, 12) === "WEBP") return ["image", "WEBP image"];
  if (textAt(bytes, 0, 5) === "%PDF-") return ["document", "PDF document"];
  if (startsWith(bytes, [0x50, 0x4b, 0x03, 0x04])) return ["archive", "ZIP archive"];
  if (textAt(bytes, 4, 8) === "ftyp") return ["video", "MP4 video"];
  if (textAt(bytes, 0, 3) === "ID3" || startsWith(bytes, [0xff, 0xfb]) || startsWith(bytes, [0xff, 0xf3]) || startsWith(bytes, [0xff, 0xf2])) return ["audio", "MP3 audio"];
  if (textAt(bytes, 0, 4) === "RIFF" && textAt(bytes, 8, 12) === "WAVE") return ["audio", "WAV audio"];
  if (textAt(bytes, 0, 4) === "fLaC") return ["audio", "FLAC audio"];
  if (textAt(bytes, 0, 4) === "OggS") return ["audio", "OGG audio"];
  return null;
}

function outputsForKind(kind) {
  if (kind === "image") return IMAGE_OUTPUTS;
  if (kind === "document") return PDF_OUTPUTS;
  if (kind === "video") return VIDEO_OUTPUTS;
  if (kind === "audio") return AUDIO_OUTPUTS;
  return [];
}

async function inspectFile(file) {
  const extension = file.name.split(".").pop()?.toLowerCase() || "";
  const extensionHint = EXTENSION_HINTS[extension] || null;
  const header = new Uint8Array(await file.slice(0, 64).arrayBuffer());
  const magicHint = detectMagic(header);
  const hint = magicHint || extensionHint || ["unknown", "Unknown file"];
  const outputs = outputsForKind(hint[0]);

  return {
    name: file.name,
    kind: hint[0],
    label: hint[1],
    outputs,
    magicLabel: magicHint?.[1] || "",
    extensionLabel: extensionHint?.[1] || "",
  };
}

function renderRecommendation(info) {
  const item = document.createElement("article");
  item.className = "recommendation-item";

  const outputs = info.outputs.length > 0
    ? info.outputs.map((output) => `<span>${output.toUpperCase()}</span>`).join("")
    : "<em>아직 변환 지원 예정</em>";

  item.innerHTML = `
    <div class="recommendation-title">
      <strong></strong>
      <span></span>
    </div>
    <div class="recommendation-formats">${outputs}</div>
  `;

  item.querySelector("strong").textContent = info.name;
  item.querySelector(".recommendation-title span").textContent = `${info.label}로 인식`;
  return item;
}

async function updateRecommendations(files) {
  if (!recommendationList || !recommendationSummary) {
    return;
  }

  recommendationList.innerHTML = "";

  if (files.length === 0) {
    recommendationSummary.textContent = "파일을 선택하면 목록과 추천 포맷이 표시됩니다.";
    return;
  }

  const inspections = await Promise.all(Array.from(files).map(inspectFile));
  const convertibleCount = inspections.filter((info) => info.outputs.length > 0).length;
  recommendationSummary.textContent = `${files.length}개 중 ${convertibleCount}개 파일 변환 가능`;
  inspections.forEach((info) => recommendationList.appendChild(renderRecommendation(info)));
}

function showMessage(message) {
  if (!formMessage) {
    return;
  }

  formMessage.textContent = message;
  formMessage.hidden = false;
}

function clearMessage() {
  if (!formMessage) {
    return;
  }

  formMessage.textContent = "";
  formMessage.hidden = true;
}

function getSelectedFormat() {
  const selectedFormat = form?.querySelector("input[name='target_format']:checked");
  return selectedFormat ? selectedFormat.value : "jpg";
}

function updateSelectedFileText(files) {
  if (!fileName || !dropzone) {
    return;
  }

  if (files.length === 0) {
    fileName.textContent = "선택된 파일 없음";
    dropzone.classList.remove("has-file");
    updateRecommendations(files);
    return;
  }

  fileName.textContent = files.length === 1 ? files[0].name : `${files.length}개 파일 선택됨`;
  dropzone.classList.add("has-file");
  updateRecommendations(files);
}

function setSelectedFiles(files) {
  if (!fileInput || files.length === 0) {
    return;
  }

  const transfer = new DataTransfer();
  Array.from(files).forEach((file) => transfer.items.add(file));
  fileInput.files = transfer.files;
  updateSelectedFileText(fileInput.files);
}

function createJobCard(file, targetFormat) {
  const card = document.createElement("article");
  card.className = "job-card is-processing";
  card.innerHTML = `
    <div class="job-header">
      <div class="job-title">
        <strong></strong>
        <span></span>
      </div>
      <span class="status-badge status-processing">처리 중</span>
    </div>
    <div class="progress" role="progressbar" aria-valuemin="0" aria-valuemax="100" aria-valuenow="0">
      <span></span>
    </div>
    <div class="job-footer">
      <span class="job-message">업로드 준비 중</span>
      <a class="download-button" hidden>다운로드</a>
    </div>
  `;

  card.querySelector(".job-title strong").textContent = file.name;
  card.querySelector(".job-title span").textContent = `${targetFormat.toUpperCase()}로 변환 대기`;
  updateJob(card, "processing", 0, "대기 중");
  return card;
}

function updateJob(card, status, progress, message) {
  const badge = card.querySelector(".status-badge");
  const progressBar = card.querySelector(".progress");
  const progressFill = card.querySelector(".progress span");
  const jobMessage = card.querySelector(".job-message");
  const clampedProgress = Math.max(0, Math.min(100, progress));

  card.classList.remove("is-processing", "is-completed", "is-failed", "is-not-ready");
  badge.classList.remove("status-processing", "status-completed", "status-failed", "status-not-ready");

  if (status === "completed") {
    card.classList.add("is-completed");
    badge.classList.add("status-completed");
    badge.textContent = "완료";
  } else if (status === "failed") {
    card.classList.add("is-failed");
    badge.classList.add("status-failed");
    badge.textContent = "실패";
  } else if (status === "not-ready") {
    card.classList.add("is-not-ready");
    badge.classList.add("status-not-ready");
    badge.textContent = "지원 예정";
  } else {
    card.classList.add("is-processing");
    badge.classList.add("status-processing");
    badge.textContent = "처리 중";
  }

  progressBar.setAttribute("aria-valuenow", String(clampedProgress));
  progressFill.style.width = `${clampedProgress}%`;
  jobMessage.textContent = message;
}

function finishJob(card, result) {
  const title = card.querySelector(".job-title span");
  const downloadButton = card.querySelector(".download-button");

  title.textContent = result.output_name;
  downloadButton.href = result.download_url;
  downloadButton.hidden = false;
  updateJob(card, "completed", 100, "변환이 끝났어요.");
}

function failJob(card, message) {
  updateJob(card, "failed", 100, message || "변환하지 못했어요.");
}

function markNotReady(card, result) {
  const title = card.querySelector(".job-title span");
  const outputs = result?.recommended_outputs || [];

  if (outputs.length > 0) {
    title.textContent = `추천: ${outputs.map((output) => output.toUpperCase()).join(", ")}`;
  }

  updateJob(card, "not-ready", 100, result?.message || "이 파일 형식의 변환 엔진은 준비 중이에요.");
}

function convertOneFile(file, targetFormat, card) {
  const request = new XMLHttpRequest();
  const payload = new FormData();
  payload.append("image", file);
  payload.append("target_format", targetFormat);

  request.open("POST", "/api/convert");
  request.responseType = "json";

  request.upload.addEventListener("progress", (event) => {
    if (!event.lengthComputable) {
      updateJob(card, "processing", 35, "업로드 중");
      return;
    }

    const uploadPercent = Math.round((event.loaded / event.total) * 80);
    updateJob(card, "processing", uploadPercent, "업로드 중");
  });

  request.upload.addEventListener("load", () => {
    updateJob(card, "processing", 88, "변환 중");
  });

  return new Promise((resolve) => {
    request.addEventListener("load", () => {
      const result = request.response;

      if (request.status >= 200 && request.status < 300 && result?.status === "completed") {
        finishJob(card, result);
      } else if (request.status >= 200 && request.status < 300 && result?.status === "not_ready") {
        markNotReady(card, result);
      } else {
        failJob(card, result?.message);
      }

      resolve();
    });

    request.addEventListener("error", () => {
      failJob(card, "서버에 연결하지 못했어요.");
      resolve();
    });

    request.addEventListener("timeout", () => {
      failJob(card, "변환 시간이 너무 오래 걸려 중단됐어요.");
      resolve();
    });

    card.querySelector(".job-title span").textContent = `${targetFormat.toUpperCase()}로 변환`;
    updateJob(card, "processing", 5, "업로드 시작");
    request.send(payload);
  });
}

function setBusy(isBusy) {
  if (!convertButton) {
    return;
  }

  convertButton.disabled = isBusy;
  convertButton.textContent = isBusy ? "일괄 변환 중" : "모두 변환";
}

async function runBatchConversion(files, targetFormat) {
  const jobs = files.map((file) => {
    const card = createJobCard(file, targetFormat);
    jobList.appendChild(card);
    return { file, card };
  });

  let nextIndex = 0;

  async function worker() {
    while (nextIndex < jobs.length) {
      const job = jobs[nextIndex];
      nextIndex += 1;
      await convertOneFile(job.file, targetFormat, job.card);
    }
  }

  const workerCount = Math.min(MAX_PARALLEL_CONVERSIONS, jobs.length);
  await Promise.all(Array.from({ length: workerCount }, worker));
}

if (dropzone && fileInput && fileName) {
  fileInput.addEventListener("change", () => {
    clearMessage();
    updateSelectedFileText(fileInput.files);
  });

  ["dragenter", "dragover"].forEach((eventName) => {
    dropzone.addEventListener(eventName, (event) => {
      event.preventDefault();
      dropzone.classList.add("is-dragging");
    });
  });

  ["dragleave", "drop"].forEach((eventName) => {
    dropzone.addEventListener(eventName, (event) => {
      event.preventDefault();
      dropzone.classList.remove("is-dragging");
    });
  });

  dropzone.addEventListener("drop", (event) => {
    clearMessage();
    setSelectedFiles(event.dataTransfer.files);
  });
}

["dragover", "drop"].forEach((eventName) => {
  document.addEventListener(eventName, (event) => {
    event.preventDefault();
  });
});

if (form && fileInput && jobList && queueCount) {
  form.addEventListener("submit", (event) => {
    event.preventDefault();
    clearMessage();

    const files = Array.from(fileInput.files);
    if (files.length === 0) {
      showMessage("변환할 파일을 먼저 선택해 주세요.");
      return;
    }

    const targetFormat = getSelectedFormat();

    jobList.innerHTML = "";
    queueCount.textContent = `${files.length}개 파일`;
    setBusy(true);

    runBatchConversion(files, targetFormat).finally(() => {
      setBusy(false);
    });
  });
}
