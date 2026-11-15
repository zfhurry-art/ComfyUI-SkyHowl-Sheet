import {app} from '../../scripts/app.js';

const MODES = ['fixed', 'increment', 'decrement', 'randomize'];
const installed = new WeakMap();

/** Surface the existing sampler's native control; never run a second seed hook. */
export function attachSeedControl(node) {
  const nodes = node.subgraph?.nodes;
  if (!Array.isArray(nodes) || !nodes.some(n => n.type === 'SkyHowlSheetCanvasV4')) return null;
  const samplers = nodes.filter(n => n.type === 'SamplerCustom' && n.widgets?.some(w => w.name === 'noise_seed'));
  if (samplers.length !== 1 || !node.widgets?.some(w => w.name === 'noise_seed')) return null;
  const sampler = samplers[0];
  const source = sampler.widgets.find(w => w.name === 'control_after_generate');
  if (!source || typeof source.afterQueued !== 'function') return null;
  const current = installed.get(node);
  if (current?.source === source && node.widgets.includes(current.widget)) {
    current.widget.value = source.value;
    return current;
  }
  if (current) node.removeWidget?.(current.widget);
  // Prefer the source's saved mode. Old workflows already save it inside the sampler.
  const mode = MODES.includes(source.value) ? source.value : 'fixed';
  const widget = node.addWidget('combo', 'control_after_generate', mode, value => {
    if (!MODES.includes(value)) { widget.value = source.value; return; }
    source.value = value;
    source.callback?.(value);
    node.setDirtyCanvas?.(true, true);
  }, {values: [...MODES], serialize: false});
  widget.label = '运行后控制';
  widget.tooltip = 'fixed 固定；randomize 随机；increment 递增；decrement 递减。由子图内原生采样器执行种子控制。';
  const record = {widget, source, sampler};
  installed.set(node, record);
  // Inner edits are reflected when returning to the parent graph or serializing.
  const previousDraw = node.onDrawForeground;
  node.onDrawForeground = function (...args) {
    const result = previousDraw?.apply(this, args);
    if (installed.get(this) === record && widget.value !== source.value) widget.value = source.value;
    return result;
  };
  return record;
}

export function installGraphSeedControls(graph) {
  for (const node of graph?.nodes ?? graph?._nodes ?? []) {
    attachSeedControl(node);
    if (node.subgraph) installGraphSeedControls(node.subgraph);
  }
}

app.registerExtension({
  name: 'SkyHowl.SheetSeedControl',
  nodeCreated(node) { queueMicrotask(() => attachSeedControl(node)); },
  loadedGraphNode(node) { attachSeedControl(node); },
  afterConfigureGraph() { installGraphSeedControls(app.graph); },
});
