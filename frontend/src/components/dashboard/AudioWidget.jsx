import React, { useEffect, useRef, useState } from "react";
import { Volume2 } from "lucide-react";

const AudioWidget = () => {
  const [data, setData] = useState({
    top_class: "Listening...",
    confidence: 0,
    category: "NORMAL TRAFFIC",
    dominant_freq: 440,
    wavelength: 0
  });

  const [levels, setLevels] = useState(Array(24).fill(10));

  const canvasRef = useRef(null);
  const audioCtxRef = useRef(null);
  const gainRef = useRef(null);
  const oscMainRef = useRef(null);
  const osc2Ref = useRef(null);
  const osc3Ref = useRef(null);
  const animationRef = useRef(null);

  /* ===============================
     AUDIO ENGINE (ONCE)
  =============================== */
  useEffect(() => {
    const AudioContext = window.AudioContext || window.webkitAudioContext;
    audioCtxRef.current = new AudioContext();

    const ctx = audioCtxRef.current;

    oscMainRef.current = ctx.createOscillator();
    osc2Ref.current = ctx.createOscillator();
    osc3Ref.current = ctx.createOscillator();

    oscMainRef.current.type = "sine";
    osc2Ref.current.type = "sine";
    osc3Ref.current.type = "sine";

    gainRef.current = ctx.createGain();
    gainRef.current.gain.value = 0.2;

    oscMainRef.current.connect(gainRef.current);
    osc2Ref.current.connect(gainRef.current);
    osc3Ref.current.connect(gainRef.current);

    gainRef.current.connect(ctx.destination);

    oscMainRef.current.start();
    osc2Ref.current.start();
    osc3Ref.current.start();

    return () => {
      oscMainRef.current.stop();
      osc2Ref.current.stop();
      osc3Ref.current.stop();
      cancelAnimationFrame(animationRef.current);
      ctx.close();
    };
  }, []);

  /* ===============================
     BACKEND POLLING
  =============================== */
  useEffect(() => {
    const interval = setInterval(() => {
      fetch("http://127.0.0.1:8000/latest")
        .then(res => res.json())
        .then(json => setData(json))
        .catch(() =>
          setData(prev => ({
            ...prev,
            category: "ERROR",
            confidence: 0
          }))
        );
    }, 500);
    return () => clearInterval(interval);
  }, []);

  /* ===============================
     PITCH & AMPLITUDE CONTROL
  =============================== */
  useEffect(() => {
    if (!audioCtxRef.current) return;

    const now = audioCtxRef.current.currentTime;
    const baseFreq = data.dominant_freq || 440;

    oscMainRef.current.frequency.setValueAtTime(baseFreq, now);
    osc2Ref.current.frequency.setValueAtTime(baseFreq * 2, now);
    osc3Ref.current.frequency.setValueAtTime(baseFreq * 3, now);

    gainRef.current.gain.setValueAtTime(
      Math.max(0.05, (data.confidence / 100) * 0.6),
      now
    );
  }, [data.dominant_freq, data.confidence]);

  /* ===============================
     WAVE CREATION BASED ON FREQUENCY & PITCH
  =============================== */
  useEffect(() => {
    const canvas = canvasRef.current;
    const ctx = canvas.getContext("2d");

    const draw = () => {
      animationRef.current = requestAnimationFrame(draw);

      ctx.fillStyle = "#060b12";
      ctx.fillRect(0, 0, canvas.width, canvas.height);

      ctx.lineWidth = 3;
      ctx.strokeStyle = data.category === "SIREN" ? "#ff2d2d" : "#00ffd5";
      ctx.shadowBlur = 25;
      ctx.shadowColor = ctx.strokeStyle;

      ctx.beginPath();

      const freq = data.dominant_freq || 440;
      const amplitude = Math.max(20, (data.confidence / 100) * 80);
      const wavelengthPx = canvas.width / (freq / 50);

      let x = 0;
      while (x < canvas.width) {
        const y =
          canvas.height / 2 +
          amplitude * Math.sin((2 * Math.PI * x) / wavelengthPx);

        if (x === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);

        x += 2;
      }

      ctx.stroke();
    };

    draw();
    return () => cancelAnimationFrame(animationRef.current);
  }, [data.dominant_freq, data.confidence, data.category]);

  /* ===============================
     LEVELS VISUALIZATION (Bars)
     Driven by confidence + frequency
  =============================== */
  useEffect(() => {
    const interval = setInterval(() => {
      setLevels(prev =>
        prev.map((_, i) => {
          const base = (data.confidence / 100) * 80;
          const variation = Math.sin((Date.now() / 100) + i) * 20;
          return Math.max(10, base + variation);
        })
      );
    }, 100);
    return () => clearInterval(interval);
  }, [data.confidence]);

  /* ===============================
     UI
  =============================== */
  return (
    <div className="p-6 rounded-2xl bg-dark-surface border border-white/10 relative overflow-hidden h-full flex flex-col justify-between">
      {/* Background Glow */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-48 h-48 bg-neon-blue/5 rounded-full blur-3xl" />

      <div className="flex items-center justify-between mb-4 z-10">
        <div className="flex items-center gap-2">
          <Volume2 className="text-neon-blue w-5 h-5" />
          <h3 className="text-white font-medium">Audio Detection</h3>
        </div>
        <span className="text-xs px-2 py-1 rounded bg-neon-blue/10 text-neon-blue border border-neon-blue/20">
          {data.category === "SIREN" ? "🚨 Siren Active" : "Live Mic 01"}
        </span>
      </div>

      {/* Waveform Visualization (Bars) */}
      <div className="flex items-center justify-center gap-1 h-24 z-10">
        {levels.map((height, i) => (
          <div
            key={i}
            className="w-1.5 bg-neon-blue rounded-full transition-all duration-100 ease-in-out"
            style={{
              height: `${height}%`,
              opacity: Math.max(0.3, height / 100)
            }}
          />
        ))}
      </div>

      {/* Canvas Wave */}
      <canvas
        ref={canvasRef}
        width={window.innerWidth * 0.9}
        height={120}
        style={{
          width: "100%",
          height: 120,
          borderRadius: 12,
          marginTop: "1rem"
        }}
      />

      {/* Siren Probability */}
      <div className="mt-4 flex items-center justify-between z-10">
        <div>
          <div className="text-2xl font-bold text-white">
            {data.confidence}%
          </div>
          <div className="text-xs text-gray-400">Siren Probability</div>
        </div>
        <div className="w-24 h-2 bg-gray-800 rounded-full overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-neon-blue to-neon-red"
            style={{ width: `${data.confidence}%` }}
          />
        </div>
      </div>

      {/* Extra Info */}
      <div className="mt-4 grid grid-cols-2 gap-2 text-xs text-gray-400">
        <div><b>Class:</b> {data.top_class}</div>
        <div><b>Freq:</b> {data.dominant_freq} Hz</div>
        <div><b>Category:</b> {data.category}</div>
        <div><b>Wavelength:</b> {data.wavelength} m</div>
      </div>
    </div>
  );
};

export default AudioWidget;
