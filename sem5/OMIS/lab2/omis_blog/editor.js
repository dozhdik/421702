(() => {
  const form = document.querySelector('#editor');
  const status = document.querySelector('#autosave');
  let revision = 0;
  let saved = 0;
  let pending = null;
  let submitting = false;
  const show = text => { status.textContent = text; };
  form.addEventListener('input', () => { revision++; show('Есть несохранённые изменения'); });
  form.addEventListener('change', () => { revision++; show('Есть несохранённые изменения'); });
  form.addEventListener('click', event => {
    const command = event.target.closest('[data-markdown]')?.dataset.markdown;
    if (!command) return;
    const text = form.querySelector('[name=content]');
    const end = text.selectionEnd;
    if (command === 'heading') {
      const start = text.selectionStart;
      const line = start === 0 ? 0 : text.value.lastIndexOf('\n', start - 1) + 1;
      const heading = '## ';
      if (!text.value.startsWith(heading, line)) text.setRangeText(heading, line, line, 'preserve');
    } else {
      const start = text.selectionStart;
      const marker = command === 'bold' ? '**' : '*';
      text.setRangeText(marker + text.value.slice(start, end) + marker, start, end, 'preserve');
      text.setSelectionRange(start + marker.length, end + marker.length);
    }
    text.focus();
    text.dispatchEvent(new Event('input', {bubbles: true}));
  });
  async function autosave() {
    if (pending || submitting || revision === saved) return;
    const sent = revision;
    const data = new FormData(form);
    data.set('action', 'autosave');
    data.delete('media');
    show('Сохранение…');
    pending = (async () => {
      try {
        const response = await fetch('/article/save', {method: 'POST', body: data});
        if (!response.ok) throw new Error('save failed');
        const id = response.headers.get('X-Article-ID');
        if (id) {
          form.querySelector('[name=id]').value = id;
          history.replaceState(null, '', '/editor/' + id);
        }
        saved = sent;
        show(revision === saved ? 'Сохранено' : 'Есть несохранённые изменения');
      } catch (_) { show('Ошибка сохранения'); }
    })();
    await pending;
    pending = null;
  }
  form.addEventListener('submit', async event => {
    if (submitting) { event.preventDefault(); return; }
    event.preventDefault();
    submitting = true;
    const button = event.submitter;
    if (pending) await pending;
    if (button && button.name) {
      const action = document.createElement('input');
      action.type = 'hidden'; action.name = button.name; action.value = button.value;
      form.appendChild(action);
    }
    form.submit();
  });
  setInterval(autosave, 30000);
})();
