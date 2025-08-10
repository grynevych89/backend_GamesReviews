(function () {
  function set100Attrs(node) {
    if (node && node.nodeName === 'IMG') {
      node.removeAttribute('width');
      node.removeAttribute('height');
      node.setAttribute('width', '100%');
      node.setAttribute('height', '100%');
    }
  }

  function set100InHtml(html) {
    if (!html) return html;
    return html.replace(/<img\b([^>]*)>/gi, (m, attrs) => {
      let out = attrs
        .replace(/\swidth\s*=\s*["'][^"']*["']/i, '')
        .replace(/\sheight\s*=\s*["'][^"']*["']/i, '');
      return `<img${out} width="100%" height="100%">`;
    });
  }

  tinymce.PluginManager.add('img100', function (editor) {
    // Любая вставка/установка контента — правим img на 100%
    editor.on('BeforeSetContent', e => {
      if (e.content && e.content.includes('<img')) {
        e.content = set100InHtml(e.content);
      }
    });
    editor.on('BeforeExecCommand', e => {
      if (typeof e.value === 'string' && e.value.includes('<img')) {
        e.value = set100InHtml(e.value);
      }
    });
    editor.on('NodeChange SetContent PastePostProcess', () => {
      set100Attrs(editor.selection.getNode());
    });
    editor.on('ExecCommand', e => {
      if ((e.command || '').toLowerCase().includes('image') || e.command === 'mceInsertContent') {
        setTimeout(() => set100Attrs(editor.selection.getNode()), 0);
      }
    });

    // Диалог Image: держим поля = 100% и перед сохранением ещё раз проставляем %
    function forceDialog100(e) {
  const api = e.dialogApi || e.api;
  const started = Date.now();
  const id = setInterval(() => {
    try {
      const data = api.getData ? api.getData() : {};
      api.setData && api.setData({ ...data, width: '100%', height: '100%' });
    } catch (_) {}
    const dlg = document.querySelector('.tox-dialog');
    if (dlg) {
      const w = dlg.querySelector('input[name="width"], [aria-label="Width"]');
      const h = dlg.querySelector('input[name="height"], [aria-label="Height"]');

      // Перебиваем значения
      if (w && w.value !== '100%') { w.value = '100%'; w.dispatchEvent(new Event('input', {bubbles:true})); }
      if (h && h.value !== '100%') { h.value = '100%'; h.dispatchEvent(new Event('input', {bubbles:true})); }

      // 🔹 Новое: если TinyMCE меняет пиксели, мы их сразу подменяем
      [w, h].forEach(input => {
        if (input && !input.__img100Bound) {
          input.addEventListener('input', () => {
            if (input.value && !input.value.includes('%')) {
              input.value = '100%';
              input.dispatchEvent(new Event('input', { bubbles: true }));
            }
          });
          input.__img100Bound = true;
        }
      });
    }
    if (Date.now() - started > 2000) clearInterval(id);
  }, 80);
  editor.once('CloseDialog', () => clearInterval(id));
}


    editor.on('OpenDialog', forceDialog100);
    editor.on('OpenWindow', forceDialog100);
  });
})();
