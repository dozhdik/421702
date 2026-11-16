// Run with Node: node tests/js/editor_autosave.js
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

(async () => {
  const handlers = {};
  const status = {textContent: ''};
  const id = {value: ''};
  let tick, resolveFetch, requests = 0, submitted = false;
  const form = {
    addEventListener: (name, fn) => { handlers[name] = fn; },
    querySelector: () => id,
    appendChild: () => {},
    submit: () => { submitted = true; },
  };
  class FormDataMock { set() {} delete(key) { assert.equal(key, 'media'); } }
  const context = {
    document: {querySelector: selector => selector === '#editor' ? form : status,
      createElement: () => ({})},
    history: {replaceState() {}}, FormData: FormDataMock,
    setInterval: fn => { tick = fn; },
    fetch: () => { requests++; return new Promise(resolve => { resolveFetch = resolve; }); },
  };
  vm.runInNewContext(fs.readFileSync('omis_blog/editor.js', 'utf8'), context);
  handlers.input();
  assert.equal(status.textContent, 'Есть несохранённые изменения');
  const first = tick();
  assert.equal(status.textContent, 'Сохранение…');
  handlers.input();
  await tick();
  assert.equal(requests, 1);
  resolveFetch({ok: true, headers: {get: () => 'article-id'}});
  await first;
  assert.equal(status.textContent, 'Есть несохранённые изменения');
  const second = tick();
  const send = handlers.submit({preventDefault() {}, submitter: {name: 'action', value: 'submit'}});
  assert.equal(submitted, false);
  await tick();
  assert.equal(requests, 2);
  resolveFetch({ok: true, headers: {get: () => 'article-id'}});
  await second;
  await send;
  assert.equal(submitted, true);
  assert.equal(status.textContent, 'Сохранено');
  console.log('editor autosave: OK');
})().catch(error => { console.error(error); process.exitCode = 1; });
