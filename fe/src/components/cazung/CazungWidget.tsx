"use client";

import { useEffect, useRef, useState } from "react";
import type { KeyboardEvent } from "react";
import { ChatPanel } from "./ChatPanel";
import { Pet } from "./pet";

export function CazungWidget() {
  const canvas = useRef<HTMLCanvasElement>(null); const pet = useRef<Pet | null>(null);
  const [open, setOpen] = useState(false); const [mountedPet, setMountedPet] = useState<Pet | null>(null);
  useEffect(() => {
    if (!canvas.current) return;
    const instance = new Pet(canvas.current); pet.current = instance;
    setMountedPet(instance);
    instance.on("click", () => setOpen((current) => !current));
    instance.on("doubleClick", () => instance.jump());
    return () => { instance.destroy(); pet.current = null; setMountedPet(null); };
  }, []);
  function keyboard(event: KeyboardEvent<HTMLCanvasElement>) {
    if (event.key === "Enter" || event.key === " ") { event.preventDefault(); setOpen((current) => !current); }
  }
  return <div className="cazung-widget">
    <canvas ref={canvas} className="cazung-canvas" role="button" tabIndex={0} aria-label="Open chat with Cazung" onKeyDown={keyboard} />
    <ChatPanel open={open} onClose={() => setOpen(false)} pet={mountedPet} />
  </div>;
}
