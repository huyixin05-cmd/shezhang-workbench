/* Original Teach Agent helpers; no upstream implementation copied.
MIT License
Copyright (c) 2026 Teach Agent contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
*/
(() => {
  'use strict';
  // Coalesce expensive visual writes without losing the most recent value.
  function frame(write) {
    let handle = null, args;
    function flush() {
      if (handle !== null) cancelAnimationFrame(handle);
      handle = null;
      if (args) { const latest = args; args = null; write(...latest); }
    }
    function schedule(...latest) {
      args = latest;
      if (handle === null) handle = requestAnimationFrame(flush);
    }
    schedule.flush = flush;
    schedule.cancel = () => { if (handle !== null) cancelAnimationFrame(handle); handle = null; args = null; };
    return schedule;
  }

  function drag(element, options) {
    const {surface, read, write, onCommit = () => {}, step = 1, snap = [], radius = 12} = options;
    if (!surface || !read || !write) throw new Error('drag requires surface, read and write');
    const oldTouch = element.style.touchAction, oldTab = element.getAttribute('tabindex');
    element.style.touchAction = 'none';
    if (oldTab === null) element.tabIndex = 0;
    let active = null;
    const paint = frame(write);
    function point(event) {
      if (options.point) return options.point(event);
      if (surface instanceof SVGGraphicsElement) {
        const matrix = surface.getScreenCTM();
        if (!matrix) throw new Error('SVG surface must be visible');
        return new DOMPoint(event.clientX, event.clientY).matrixTransform(matrix.inverse());
      }
      const box = surface.getBoundingClientRect();
      // Padding-box coordinates, including CSS scale and scrolling.
      const sx = box.width / (surface.offsetWidth || box.width);
      const sy = box.height / (surface.offsetHeight || box.height);
      return {x:(event.clientX-box.left)/sx-surface.clientLeft+surface.scrollLeft,
              y:(event.clientY-box.top)/sy-surface.clientTop+surface.scrollTop};
    }
    function constrain(position) {
      const b = typeof options.bounds === 'function' ? options.bounds() : options.bounds;
      return b ? {x:Math.max(b.minX,Math.min(b.maxX,position.x)),
                  y:Math.max(b.minY,Math.min(b.maxY,position.y))} : position;
    }
    function snapped(position) {
      let best = radius, result = position;
      const targets = typeof snap === 'function' ? snap() : snap;
      for (const target of targets) {
        const distance = Math.hypot(position.x-target.x,position.y-target.y);
        if (distance <= best) { best = distance; result = {x:target.x,y:target.y}; }
      }
      return constrain(result);
    }
    function move(event) {
      if (!active || event.pointerId !== active.id) return;
      const p = point(event);
      active.position = constrain({x:active.start.x+p.x-active.pointer.x,y:active.start.y+p.y-active.pointer.y});
      paint({...active.position});
    }
    function finish(cancelled) {
      if (!active) return;
      const previous = active;
      active = null;
      paint.cancel();
      const result = cancelled ? previous.start : snapped(previous.position);
      write({...result});
      element.removeAttribute('data-dragging');
      if (element.hasPointerCapture(previous.id)) element.releasePointerCapture(previous.id);
      if (!cancelled) onCommit({...result});
    }
    function down(event) {
      if (active || event.button !== 0 || event.isPrimary === false) return;
      const start = {...read()};
      active = {id:event.pointerId,start,pointer:point(event),position:start};
      element.setPointerCapture(event.pointerId);
      element.setAttribute('data-dragging','true');
      element.focus({preventScroll:true});
      event.preventDefault();
    }
    function up(event) { if (active && event.pointerId === active.id) { move(event); finish(false); } }
    function cancel(event) { if (active && event.pointerId === active.id) finish(true); }
    function key(event) {
      if (event.key === 'Escape' && active) { event.preventDefault(); finish(true); return; }
      if (active) return;
      const delta = {ArrowLeft:[-1,0],ArrowRight:[1,0],ArrowUp:[0,-1],ArrowDown:[0,1]}[event.key];
      if (!delta) return;
      event.preventDefault();
      const old = read(), amount = step * (event.shiftKey ? 10 : 1);
      const next = constrain({x:old.x+delta[0]*amount,y:old.y+delta[1]*amount});
      write(next); onCommit({...next});
    }
    const listeners = {pointerdown:down,pointermove:move,pointerup:up,pointercancel:cancel,lostpointercapture:cancel,keydown:key};
    for (const [name, handler] of Object.entries(listeners)) element.addEventListener(name,handler);
    return {
      cancel:() => finish(true),
      destroy:() => {
        finish(true); paint.cancel();
        for (const [name, handler] of Object.entries(listeners)) element.removeEventListener(name,handler);
        element.style.touchAction = oldTouch;
        if (oldTab === null) element.removeAttribute('tabindex'); else element.setAttribute('tabindex',oldTab);
      }
    };
  }

  function simulation({update, render, dt = 1/120, maxSteps = 12}) {
    if (!(dt > 0 && Number.isFinite(dt)) || !Number.isInteger(maxSteps) || maxSteps < 1 || maxSteps > 1000)
      throw new Error('Invalid simulation timestep');
    let running = false, handle = null, last = null, accumulated = 0, destroyed = false;
    function tick(now) {
      handle = null;
      if (!running || document.hidden) return;
      if (last !== null) accumulated = Math.min(accumulated+(now-last)/1000,dt*maxSteps);
      last = now;
      let steps = 0;
      while (accumulated >= dt && steps++ < maxSteps) { update(dt); accumulated -= dt; }
      render(accumulated/dt);
      if (running && !destroyed) handle = requestAnimationFrame(tick);
    }
    function clear() { if (handle !== null) cancelAnimationFrame(handle); handle = null; last = null; accumulated = 0; }
    function visible() { clear(); if (running && !document.hidden) handle = requestAnimationFrame(tick); }
    document.addEventListener('visibilitychange',visible);
    return {
      start() { if (destroyed || running) return; running = true; visible(); },
      pause() { running = false; clear(); },
      reset(resetModel) { clear(); resetModel(); render(0); if (running && !document.hidden) handle = requestAnimationFrame(tick); },
      destroy() { running = false; destroyed = true; clear(); document.removeEventListener('visibilitychange',visible); }
    };
  }
  window.TeachInteraction = Object.freeze({frame, drag, simulation});
})();
