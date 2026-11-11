import * as S from "./sprite";

export type PetState = "idle" | "look" | "sit" | "stretch" | "sleep" | "think" | "talk" | "happy" | "sad" | "walk" | "jump";
type Handler = () => void;

export class Pet {
  private readonly canvas: HTMLCanvasElement;
  private readonly ctx: CanvasRenderingContext2D;
  private readonly reducedMotion: boolean;
  private frame = 0;
  private behaviorTimer = 0;
  private modeSince = performance.now();
  private state: PetState = "idle";
  private scale = window.innerWidth > 640 ? 3 : 2;
  private x = 20;
  private direction = 1;
  private dragging = false;
  private dragOffset = 0;
  private down: { x: number; y: number } | null = null;
  private clickTimer = 0;
  private handlers: Partial<Record<"click" | "doubleClick", Handler>> = {};
  private readonly onResize = () => { this.scale = window.innerWidth > 640 ? 3 : 2; this.resize(); };
  private readonly onVisibility = () => { if (!document.hidden) this.schedule(); };

  constructor(canvas: HTMLCanvasElement) {
    this.canvas = canvas;
    const ctx = canvas.getContext("2d");
    if (!ctx) throw new Error("Canvas is unavailable.");
    this.ctx = ctx;
    this.reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    this.ctx.imageSmoothingEnabled = false;
    this.resize();
    this.bind();
    this.behaviorTimer = window.setInterval(() => this.behave(), 1000);
    this.schedule();
  }
  on(event: "click" | "doubleClick", handler: Handler) { this.handlers[event] = handler; }
  act(state: Extract<PetState, "think" | "talk" | "happy" | "sad">) { if (!this.dragging) { this.state = state; this.modeSince = performance.now(); } }
  jump() { if (!this.dragging) { this.state = "jump"; this.modeSince = performance.now(); } }
  destroy() {
    cancelAnimationFrame(this.frame); window.clearInterval(this.behaviorTimer);
    window.removeEventListener("resize", this.onResize); document.removeEventListener("visibilitychange", this.onVisibility);
    this.canvas.removeEventListener("pointerdown", this.onDown); this.canvas.removeEventListener("pointermove", this.onMove);
    this.canvas.removeEventListener("pointerup", this.onUp); this.canvas.removeEventListener("pointercancel", this.onUp);
  }
  private resize() { this.canvas.width = 40 * this.scale; this.canvas.height = 40 * this.scale; this.placeBottom(); }
  private placeBottom() {
    this.x = Math.max(0, Math.min(window.innerWidth - this.canvas.width / devicePixelRatio, this.x));
    this.canvas.style.left = "0";
    this.canvas.style.transform = `translateX(${this.x}px)`;
    this.canvas.style.bottom = "8px";
  }
  private bind() {
    window.addEventListener("resize", this.onResize); document.addEventListener("visibilitychange", this.onVisibility);
    this.canvas.addEventListener("pointerdown", this.onDown); this.canvas.addEventListener("pointermove", this.onMove);
    this.canvas.addEventListener("pointerup", this.onUp); this.canvas.addEventListener("pointercancel", this.onUp);
  }
  private onDown = (event: PointerEvent) => { if (event.button !== 0) return; this.down = { x: event.clientX, y: event.clientY }; this.dragOffset = event.clientX - this.x; this.canvas.setPointerCapture(event.pointerId); };
  private onMove = (event: PointerEvent) => {
    if (!this.down) return;
    if (!this.dragging && Math.hypot(event.clientX - this.down.x, event.clientY - this.down.y) > 6) this.dragging = true;
    if (this.dragging) {
      this.state = "walk"; this.canvas.style.bottom = `${Math.max(0, window.innerHeight - event.clientY - this.canvas.height)}px`;
      this.x = Math.max(0, Math.min(window.innerWidth - this.canvas.width / devicePixelRatio, event.clientX - this.dragOffset));
      this.canvas.style.left = "0";
      this.canvas.style.transform = `translateX(${this.x}px)`;
    }
  };
  private onUp = () => {
    if (!this.down) return;
    const dragged = this.dragging; this.down = null; this.dragging = false;
    if (dragged) { this.placeBottom(); this.state = "idle"; return; }
    if (this.clickTimer) { window.clearTimeout(this.clickTimer); this.clickTimer = 0; this.handlers.doubleClick?.(); }
    else this.clickTimer = window.setTimeout(() => { this.clickTimer = 0; this.handlers.click?.(); }, 220);
  };
  private behave() {
    if (this.state !== "idle" || this.reducedMotion || document.hidden) return;
    if (Math.random() < 0.1) { this.state = ["look", "sit", "stretch", "sleep"][Math.floor(Math.random() * 4)] as PetState; this.modeSince = performance.now(); }
    else if (Math.random() < 0.1) { this.state = "walk"; this.direction = Math.random() < 0.5 ? -1 : 1; this.modeSince = performance.now(); }
  }
  private schedule() { if (!document.hidden) this.frame = requestAnimationFrame((time) => this.loop(time)); }
  private loop(time: number) {
    if (document.hidden) return;
    const age = time - this.modeSince;
    if (this.state === "walk") {
      this.x += this.direction * 1.5;
      if (this.x <= 0 || this.x >= window.innerWidth - this.canvas.width) this.direction *= -1;
      this.placeBottom();
    }
    if (this.state === "jump" && age > 650) this.state = "idle";
    if (["look", "sit", "stretch"].includes(this.state) && age > 1800) this.state = "idle";
    if (this.state === "sleep" && age > 7000) this.state = "idle";
    this.draw(time); this.schedule();
  }
  private draw(time: number) {
    const tick = Math.floor(time / 300); const bob = this.reducedMotion ? 0 : (tick % 2);
    const state = this.state; const options = {
      eyes: state === "sleep" ? "sleep" : state === "sad" ? "sad" : state === "think" ? "up" : "open",
      mouth: state === "sad" ? "frown" : state === "talk" ? ["open", "talk", "small"][tick % 3] : "smile",
      blush: state === "happy", legs: state === "sit" || state === "sleep" ? "sit" : state === "walk" ? ["walkA", "stand", "walkB", "stand"][tick % 4] : "stand",
      arms: state === "happy" ? "wave" : "down", bob, look: state === "walk" ? this.direction : 0, sit: state === "sit" || state === "sleep",
    };
    this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
    S.draw(this.ctx, S.compose(options), 4, 8, this.scale);
    if (state === "think") S.draw(this.ctx, S.effectGrid("cloud"), 28, 0, this.scale);
    if (state === "sleep") S.draw(this.ctx, S.effectGrid("z"), 29, 8, this.scale);
  }
}
