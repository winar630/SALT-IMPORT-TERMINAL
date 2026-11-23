window.dash = (function () {
  const loaders = {}, calcs = {}, order = [], draws = new Map(), state = {};
  const colors = ['#19e68c', '#ffb020', '#35d0ff', '#b07cff'];
  const data = (id) => state[id] || { status: 'loading', data: calcs[id] ? null : [] };
  const runDraw = (name) => {
    const d = draws.get(name); if (!d) return;
    document.querySelectorAll('[data-draw="' + name + '"]').forEach((el) => {
      try {
        if (typeof d === 'function') d(el);
        else { if (!el.__mounted) { el.__made = d.mount ? d.mount(el) : undefined; el.__mounted = true; } if (d.update) d.update(el, el.__made); }
      } catch (e) { console.error('draw ' + name, e); }
    });
  };
  const all = () => draws.forEach((_, n) => runDraw(n));
  async function load(url) {
    try {
      const res = await fetch(url, { cache: 'no-store' });
      if (!res.ok) throw new Error('HTTP ' + res.status);
      const text = await res.text();
      const out = loaders.imports ? await loaders.imports.fn({ answer: text }) : text;
      state.imports = { status: 'ok', data: Array.isArray(out) ? out : out.rows };
    } catch (e) { console.error(e); state.imports = { status: 'error', data: [], message: String(e) }; }
    for (const id of order) {
      const c = calcs[id], ins = c.inputs.map((i) => state[i]);
      if (ins.some((x) => !x || x.status !== 'ok')) { state[id] = { status: ins.some((x) => x && x.status === 'error') ? 'error' : 'loading', data: null }; continue; }
      try { state[id] = { status: 'ok', data: c.fn(...ins.map((x) => x.data)) }; } catch (e) { console.error(id, e); state[id] = { status: 'error', data: null }; }
    }
    all();
  }
  let rz; window.addEventListener('resize', () => { clearTimeout(rz); rz = setTimeout(all, 150); });
  return {
    data, colors, load,
    loader: (id, o) => { loaders[id] = o; },
    calc: (id, o) => { calcs[id] = o; order.push(id); },
    draw: (name, fn) => { if (fn === undefined) { runDraw(name); return; } draws.set(name, fn); runDraw(name); },
    onData() {}, params: () => ({}), setParams() {}, setLink() {}
  };
})();
