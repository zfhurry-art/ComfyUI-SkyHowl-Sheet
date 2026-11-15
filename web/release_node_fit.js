import {app} from '../../scripts/app.js';
// Only opt-in nodes in the supplied workflow are affected.
app.registerExtension({
 name: 'SkyHowl.ReleaseNodeFit',
 async beforeRegisterNodeDef(NodeType) {
  const previous = NodeType.prototype.onConfigure;
  NodeType.prototype.onConfigure = function(...args) {
   const result = previous?.apply(this, args);
   if (this.properties?.skyhowl_auto_fit === true) {
    requestAnimationFrame(() => {
     if (!this.graph || typeof this.computeSize !== 'function') return;
     const size = this.computeSize();
     if (Array.isArray(size) && size.every(Number.isFinite)) {
      this.setSize([Math.max(280, size[0]), Math.max(72, size[1])]);
      this.setDirtyCanvas(true, true);
     }
    });
   }
   return result;
  };
 }
});
