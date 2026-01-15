const examples = [
  { label: "Pedido de status", text: "Ola time, poderiam confirmar o status do contrato enviado ontem? Precisamos do retorno para seguir com o projeto." },
  { label: "Solicitacao de ajuste", text: "Bom dia, preciso atualizar o cadastro do fornecedor. Em anexo segue a planilha com os dados corrigidos." },
  { label: "Agradecimento", text: "Obrigado pelo suporte de hoje. Tudo certo por aqui." },
  { label: "Fora do tema", text: "Pessoal, parabens pelo aniversario da empresa! Foi um evento incrivel." },
];

const storageKey = "emailtriage-history";
let lastResult = null;

const byId = (id) => document.getElementById(id);

function showLoading(isLoading) {
  const loader = byId("loading");
  if (loader) loader.classList.toggle("hidden", !isLoading);
}

function setError(message) {
  const errorBox = byId("client-error");
  if (!errorBox) return;
  errorBox.textContent = message || "";
  errorBox.classList.toggle("hidden", !message);
}

function renderTags(tags) {
  const container = byId("result-tags");
  if (!container) return;
  container.innerHTML = "";
  (tags || []).forEach((tag) => {
    const span = document.createElement("span");
    span.className = "tag";
    span.textContent = tag;
    container.appendChild(span);
  });
}

function renderReasons(reasons) {
  const container = byId("result-reasons");
  if (!container) return;
  container.innerHTML = "";
  (reasons || []).forEach((reason) => {
    const li = document.createElement("li");
    li.textContent = reason;
    container.appendChild(li);
  });
}

function renderResult(data) {
  if (!data || !data.result) return;
  lastResult = data;
  const category = data.result.category;
  const confidence = Number(data.result.confidence || 0);
  const source = data.source || "llm";
  byId("result-category").textContent = category;
  byId("result-confidence").textContent = confidence.toFixed(2);
  byId("result-source").textContent = source;
  const categoryPill = byId("result-category-pill");
  if (categoryPill) categoryPill.textContent = category;
  const actionPill = byId("result-action-pill");
  if (actionPill) actionPill.textContent = category === "Produtivo" ? "Acao necessaria" : "Sem acao imediata";
  const reviewPill = byId("result-review-pill");
  if (reviewPill) reviewPill.textContent = data.result.needs_human_review ? "Revisao humana" : "Auto aprovado";
  byId("result-summary").textContent = data.result.summary;
  byId("result-review").textContent = data.result.needs_human_review ? "Sim" : "Nao";
  byId("suggested-reply").value = data.result.suggested_reply;
  const actionText = byId("result-action");
  if (actionText) {
    actionText.textContent =
      category === "Produtivo"
        ? "Priorize resposta com prazo ou status."
        : "Responda de forma cordial e encerre.";
  }
  const confidenceFill = byId("result-confidence-fill");
  if (confidenceFill) confidenceFill.style.width = `${Math.round(confidence * 100)}%`;
  renderTags(data.result.tags);
  renderReasons(data.result.reasons);
  const feedback = document.querySelector(".feedback");
  if (feedback) feedback.dataset.emailHash = data.email_hash || "";
  const section = byId("result-section");
  if (section) section.classList.remove("hidden");
  pushHistory(data);
}

function getHistory() {
  try {
    return JSON.parse(sessionStorage.getItem(storageKey)) || [];
  } catch (err) {
    return [];
  }
}

function saveHistory(items) {
  sessionStorage.setItem(storageKey, JSON.stringify(items.slice(0, 5)));
}

function pushHistory(data) {
  const history = getHistory();
  history.unshift({ category: data.result.category, summary: data.result.summary, confidence: data.result.confidence });
  saveHistory(history);
  renderHistory(history);
}

function renderHistory(history) {
  const list = byId("history-list");
  if (!list) return;
  list.innerHTML = "";
  if (!history.length) {
    const empty = document.createElement("p");
    empty.className = "muted";
    empty.textContent = "Sem analises ainda.";
    list.appendChild(empty);
    return;
  }
  history.forEach((item) => {
    const card = document.createElement("div");
    card.className = "history-item";
    card.innerHTML = `
      <strong>${item.category}</strong>
      <span>Confianca: ${Number(item.confidence).toFixed(2)}</span>
      <p class="muted">${item.summary}</p>
    `;
    list.appendChild(card);
  });
}

async function submitFeedback(correctLabel) {
  const feedbackStatus = byId("feedback-status");
  if (!lastResult || !lastResult.email_hash) return;
  const payload = {
    email_hash: lastResult.email_hash,
    correct_label: correctLabel,
    previous_label: lastResult.result.category,
    source: lastResult.source,
  };
  try {
    const response = await fetch("/feedback", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (feedbackStatus) feedbackStatus.textContent = response.ok ? "Feedback registrado." : "Falha ao salvar feedback.";
  } catch (err) {
    if (feedbackStatus) feedbackStatus.textContent = "Falha ao salvar feedback.";
  }
}

function wireFeedback() {
  const correctBtn = byId("feedback-correct");
  const wrongBtn = byId("feedback-wrong");
  const choice = byId("feedback-choice");
  if (correctBtn) {
    correctBtn.addEventListener("click", () => {
      if (!lastResult) return;
      submitFeedback(lastResult.result.category);
    });
  }
  if (wrongBtn && choice) {
    wrongBtn.addEventListener("click", () => choice.classList.toggle("hidden"));
    choice.querySelectorAll("button").forEach((btn) => {
      btn.addEventListener("click", () => {
        submitFeedback(btn.dataset.correct);
        choice.classList.add("hidden");
      });
    });
  }
}

function wireExamples() {
  const container = byId("example-buttons");
  if (!container) return;
  examples.forEach((example) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "btn ghost";
    button.textContent = example.label;
    button.addEventListener("click", () => (byId("text-input").value = example.text));
    container.appendChild(button);
  });
}

function wireCopy() {
  const copyBtn = byId("copy-reply");
  if (!copyBtn) return;
  copyBtn.addEventListener("click", async () => {
    const text = byId("suggested-reply").value;
    try {
      await navigator.clipboard.writeText(text);
      copyBtn.textContent = "Copiado!";
    } catch (err) {
      copyBtn.textContent = "Nao foi possivel copiar";
    } finally {
      setTimeout(() => (copyBtn.textContent = "Copiar resposta"), 2000);
    }
  });
}

function wireForm() {
  const form = byId("triage-form");
  const clearBtn = byId("clear-btn");
  const submitBtn = byId("submit-btn");
  const textInput = byId("text-input");
  const fileInput = form ? form.querySelector("input[type=file]") : null;
  const charCount = byId("char-count");
  const fileMeta = byId("file-meta");
  const maxChars = Number(form?.dataset.maxChars || 40000);
  const maxFileMb = Number(form?.dataset.maxFileMb || 2);
  if (!form) return;

  const updateCharCount = () => {
    if (!textInput || !charCount) return;
    const count = textInput.value.length;
    charCount.textContent = `${count} / ${maxChars} caracteres`;
    textInput.classList.toggle("is-invalid", count > maxChars);
  };

  const updateFileMeta = () => {
    if (!fileInput || !fileMeta) return;
    if (!fileInput.files || !fileInput.files.length) {
      fileMeta.textContent = "Nenhum arquivo selecionado.";
      fileMeta.classList.remove("error");
      return;
    }
    const file = fileInput.files[0];
    const sizeMb = file.size / (1024 * 1024);
    if (sizeMb > maxFileMb) {
      fileMeta.textContent = `Arquivo muito grande (${sizeMb.toFixed(2)} MB). Limite: ${maxFileMb} MB.`;
      fileMeta.classList.add("error");
    } else {
      fileMeta.textContent = `${file.name} (${sizeMb.toFixed(2)} MB)`;
      fileMeta.classList.remove("error");
    }
  };

  const syncSubmitState = () => {
    if (!submitBtn || !textInput || !fileInput) return;
    const hasText = textInput.value.trim().length > 0;
    const hasFile = fileInput.files && fileInput.files.length > 0;
    submitBtn.disabled = !hasText && !hasFile;
  };

  if (textInput) {
    textInput.addEventListener("input", () => {
      updateCharCount();
      syncSubmitState();
    });
    updateCharCount();
  }
  if (fileInput) {
    fileInput.addEventListener("change", () => {
      updateFileMeta();
      syncSubmitState();
    });
    updateFileMeta();
  }
  syncSubmitState();

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    showLoading(true);
    setError("");
    if (submitBtn) submitBtn.disabled = true;
    const data = new FormData(form);
    try {
      if (textInput && textInput.value.length > maxChars) {
        throw new Error(`Texto acima do limite de ${maxChars} caracteres.`);
      }
      if (fileInput && fileInput.files && fileInput.files.length) {
        const file = fileInput.files[0];
        const sizeMb = file.size / (1024 * 1024);
        if (sizeMb > maxFileMb) {
          throw new Error(`Arquivo acima do limite de ${maxFileMb} MB.`);
        }
      }
      const response = await fetch("/api/analyze", { method: "POST", body: data });
      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || "Falha ao analisar");
      }
      const payload = await response.json();
      renderResult(payload);
    } catch (err) {
      setError(err.message || "Falha ao analisar");
    } finally {
      showLoading(false);
      syncSubmitState();
    }
  });
  if (clearBtn) {
    clearBtn.addEventListener("click", () => {
      if (textInput) textInput.value = "";
      if (fileInput) fileInput.value = "";
      setError("");
      updateCharCount();
      updateFileMeta();
      syncSubmitState();
    });
  }
}

function initFromServer() {
  const raw = byId("server-result");
  if (!raw) return;
  try {
    const data = JSON.parse(raw.textContent || "{}");
    if (data.result) renderResult(data);
  } catch (err) {
    return;
  }
}

document.addEventListener("DOMContentLoaded", () => {
  wireExamples();
  wireForm();
  wireCopy();
  wireFeedback();
  renderHistory(getHistory());
  initFromServer();
});
