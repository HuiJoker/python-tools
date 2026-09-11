document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll("form.tool-form").forEach((form) => {
    form.autocomplete = "off";
  });

  const themeToggle = document.querySelector(".theme-toggle");
  if (localStorage.getItem("toolbox-theme") === "dark") document.body.classList.add("dark");
  themeToggle?.addEventListener("click", () => {
    document.body.classList.toggle("dark");
    localStorage.setItem("toolbox-theme", document.body.classList.contains("dark") ? "dark" : "light");
  });

  document.querySelectorAll("form.tool-form").forEach((form) => {
    const key = `toolbox-templates-${form.dataset.tool}`;
    const getTemplates = () => JSON.parse(localStorage.getItem(key) || "[]");
    const writeTemplates = (items) => localStorage.setItem(key, JSON.stringify(items));
    const bar = document.createElement("div");
    bar.className = "form-template-bar";
    bar.innerHTML = '<select aria-label="已保存参数"><option value="">选择已保存参数…</option></select><button type="button" class="template-save">保存当前参数</button><button type="button" class="template-delete" disabled>删除</button>';
    form.prepend(bar);
    const selector = bar.querySelector("select");
    const refreshTemplates = () => {
      selector.innerHTML = '<option value="">选择已保存参数…</option>';
      getTemplates().forEach((item, index) => selector.add(new Option(item.name, String(index))));
    };
    refreshTemplates();
    selector.addEventListener("change", () => {
      bar.querySelector(".template-delete").disabled = selector.value === "";
      if (selector.value === "") return;
      const values = getTemplates()[Number(selector.value)].values;
      Object.entries(values).forEach(([name, value]) => {
        const control = form.elements.namedItem(name);
        if (!control) return;
        if (control.type === "checkbox") control.checked = value;
        else control.value = value;
      });
    });
    bar.querySelector(".template-save").addEventListener("click", () => {
      const name = window.prompt("为这组参数命名：", "常用参数");
      if (!name) return;
      const values = {};
      new FormData(form).forEach((value, field) => { values[field] = value; });
      form.querySelectorAll("input[type=checkbox]").forEach((field) => { values[field.name] = field.checked; });
      const templates = getTemplates();
      templates.push({ name, values });
      writeTemplates(templates.slice(-12));
      refreshTemplates();
    });
    bar.querySelector(".template-delete").addEventListener("click", () => {
      const index = Number(selector.value);
      const templates = getTemplates();
      const item = templates[index];
      if (!item || !window.confirm(`删除参数模板“${item.name}”？`)) return;
      templates.splice(index, 1);
      writeTemplates(templates);
      refreshTemplates();
      bar.querySelector(".template-delete").disabled = true;
    });

    form.addEventListener("submit", (event) => {
      if (form.dataset.submitting === "true") {
        event.preventDefault();
        return;
      }

      form.dataset.submitting = "true";
      // Disabled form inputs are omitted from the HTTP request.  Keep every
      // user-entered field enabled and only block the submit button.
      form.querySelectorAll("button[type='submit'], button:not([type])").forEach((element) => {
        element.disabled = true;
      });

      const overlay = document.createElement("section");
      overlay.id = "run-progress";
      overlay.innerHTML = '<div class="run-progress-card" role="status" aria-live="polite"><h2>正在处理文件</h2><p>任务仍在本机运行，请不要关闭此页面。</p><div class="progress-track"><div class="progress-bar"></div></div><span class="run-elapsed">已用时 00:00</span></div>';
      document.body.appendChild(overlay);

      const elapsed = overlay.querySelector(".run-elapsed");
      const startedAt = Date.now();
      window.setInterval(() => {
        const seconds = Math.floor((Date.now() - startedAt) / 1000);
        elapsed.textContent = `已用时 ${String(Math.floor(seconds / 60)).padStart(2, "0")}:${String(seconds % 60).padStart(2, "0")}`;
      }, 1000);

      // Do not re-submit the form through JavaScript.  Native submission keeps
      // all successful controls (including the folder path) in the request.
    });
  });
});
