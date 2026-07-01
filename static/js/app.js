const form = document.querySelector("#converter-form");
const dropzone = document.querySelector("#dropzone");
const fileInput = document.querySelector("#image");
const fileName = document.querySelector("#file-name");
const formMessage = document.querySelector("#form-message");
const jobList = document.querySelector("#job-list");
const queueCount = document.querySelector("#queue-count");
const convertButton = document.querySelector("#convert-button");

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
    return;
  }

  fileName.textContent = files.length === 1 ? files[0].name : `${files.length}개 파일 선택됨`;
  dropzone.classList.add("has-file");
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
  card.querySelector(".job-title span").textContent = `${targetFormat.toUpperCase()}로 변환`;
  return card;
}

function updateJob(card, status, progress, message) {
  const badge = card.querySelector(".status-badge");
  const progressBar = card.querySelector(".progress");
  const progressFill = card.querySelector(".progress span");
  const jobMessage = card.querySelector(".job-message");
  const clampedProgress = Math.max(0, Math.min(100, progress));

  card.classList.remove("is-processing", "is-completed", "is-failed");
  badge.classList.remove("status-processing", "status-completed", "status-failed");

  if (status === "completed") {
    card.classList.add("is-completed");
    badge.classList.add("status-completed");
    badge.textContent = "완료";
  } else if (status === "failed") {
    card.classList.add("is-failed");
    badge.classList.add("status-failed");
    badge.textContent = "실패";
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

function convertOneFile(file, targetFormat, onDone) {
  const card = createJobCard(file, targetFormat);
  jobList.appendChild(card);

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

  request.addEventListener("load", () => {
    const result = request.response;

    if (request.status >= 200 && request.status < 300 && result?.status === "completed") {
      finishJob(card, result);
    } else {
      failJob(card, result?.message);
    }

    onDone();
  });

  request.addEventListener("error", () => {
    failJob(card, "서버에 연결하지 못했어요.");
    onDone();
  });

  request.addEventListener("timeout", () => {
    failJob(card, "변환 시간이 너무 오래 걸려 중단됐어요.");
    onDone();
  });

  updateJob(card, "processing", 5, "업로드 시작");
  request.send(payload);
}

function setBusy(isBusy) {
  if (!convertButton) {
    return;
  }

  convertButton.disabled = isBusy;
  convertButton.textContent = isBusy ? "변환 중" : "변환하기";
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
      showMessage("변환할 이미지 파일을 먼저 선택해 주세요.");
      return;
    }

    const targetFormat = getSelectedFormat();
    let remainingJobs = files.length;

    jobList.innerHTML = "";
    queueCount.textContent = `${files.length}개 파일`;
    setBusy(true);

    files.forEach((file) => {
      convertOneFile(file, targetFormat, () => {
        remainingJobs -= 1;

        if (remainingJobs === 0) {
          setBusy(false);
        }
      });
    });
  });
}
