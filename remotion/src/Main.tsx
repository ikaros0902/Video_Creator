import React from "react";
import {
  AbsoluteFill, Audio, Easing, Img, interpolate, OffthreadVideo, Sequence, spring, staticFile,
  useCurrentFrame, useVideoConfig,
} from "remotion";

// 由 vc/render.py 從 work/timeline.json 轉出；檔案路徑都相對於 --public-dir（專案的 work/）
export type Clip = {
  src: string; start_frame: number; duration_frames: number;
  crop: [number, number, number, number] | null; label: string | null;
  camera?: string | null;
  rec_size?: [number, number];   // 來源錄影尺寸，每支錄影不同
};
export type Callout = { frame: number; box: [number, number, number, number]; text: string; clip: number };
export type Scene = {
  id: string; start_frame: number; duration_frames: number; kind: "anim" | "recording" | "manim";
  anim_src: string | null; clips: Clip[]; callouts: Callout[];
  timer: { clip: number; text: string } | null;
  bg_image?: string | null; overlay_title?: string | null; logo?: boolean;
};
export type WordCue = { word: string; start_frame: number; end_frame: number };
export type Cue = { text: string; start_frame: number; end_frame: number; words?: WordCue[] };
// 音量倍率由 vc/render.py 依實測響度算出（配樂比旁白低 20 dB / 停頓時低 14 dB）
export type BgmConfig = { src: string; speech_volume: number; gap_volume: number };
export type MainProps = {
  variant: "main";
  fps: number; size: [number, number]; total_frames: number; rec_size: [number, number];
  audio: { src: string; start_frame: number; duration_frames: number }[];
  cues: Cue[]; scenes: Scene[]; bgm?: BgmConfig;
};

// 顏色規則與 Manim 一致：一種顏色只代表一件事
const NAVY = "#06213D";
const CYAN = "#1EB8EC";
const AMBER = "#F5B841";
const CORAL = "#FF6B5A";
const FONT = "Segoe UI, sans-serif";

// 錄影浮動視窗的可用區域：上方留 40 px，下方留 170 px 給字幕
const WIN = { top: 40, maxW: 1760, maxH: 870 };
const ease = Easing.inOut(Easing.cubic);

const Background: React.FC = () => (
  <AbsoluteFill style={{
    background: `radial-gradient(1600px 1000px at 25% 15%, #0B3360 0%, ${NAVY} 60%, #031529 100%)`,
  }}>
    <AbsoluteFill style={{
      backgroundImage: "linear-gradient(rgba(255,255,255,0.045) 1px, transparent 1px), "
        + "linear-gradient(90deg, rgba(255,255,255,0.045) 1px, transparent 1px)",
      backgroundSize: "108px 108px",
    }} />
  </AbsoluteFill>
);

const windowRect = (rec: [number, number]) => {
  const s = Math.min(WIN.maxW / rec[0], WIN.maxH / rec[1]);
  const w = rec[0] * s, h = rec[1] * s;
  return { s, w, h, left: (1920 - w) / 2, top: WIN.top + (WIN.maxH - h) / 2 };
};

// 運鏡：一個鏡頭只做一種移動，全部加緩動；錄影是平面畫面，只用推近、拉遠、搖攝
const cameraTransform = (cam: string, frame: number, dur: number, fps: number) => {
  const p = ease(Math.min(1, Math.max(0, frame / Math.max(dur - 1, 1))));
  switch (cam) {
    case "dolly_in": return { s: 1 + 0.15 * p, x: 0, y: 0 };
    case "dolly_out": return { s: 1.15 - 0.15 * p, x: 0, y: 0 };
    case "zoom_in": {
      const q = ease(Math.min(1, frame / (0.35 * fps)));   // 0.35 秒快推後停住
      return { s: 1 + 0.6 * q, x: 0, y: 0 };
    }
    case "pan_right": return { s: 1.12, x: 5 - 10 * p, y: 0 };
    case "tilt_down": return { s: 1.12, x: 0, y: 5 - 10 * p };
    case "follow": return { s: 1 + 0.1 * p, x: 0, y: 0 };
    case "steadicam": return { s: 1 + 0.06 * p, x: 0, y: 0 };
    default: return { s: 1, x: 0, y: 0 };
  }
};

const isAct = (label: string | null) => !!label && (/ACT|Validator|Auto/i.test(label) || /^\d/.test(label));

const LabelChip: React.FC<{ text: string; color: string }> = ({ text, color }) => {
  const frame = useCurrentFrame();
  const o = interpolate(frame, [0, 8], [0, 1], { extrapolateRight: "clamp" });
  return (
    <div style={{
      position: "absolute", top: 22, left: 22, opacity: o, background: "rgba(6,33,61,0.9)",
      borderLeft: `6px solid ${color}`, borderRadius: 8, padding: "8px 20px",
      color: "#fff", fontFamily: FONT, fontSize: 30, fontWeight: 700, whiteSpace: "nowrap",
      boxShadow: "0 6px 20px rgba(0,0,0,0.35)",
    }}>{text}</div>
  );
};

const CalloutBox: React.FC<{ box: [number, number, number, number]; text: string; s: number; color: string }> = (
  { box, text, s, color }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const pop = spring({ frame, fps, config: { damping: 16, stiffness: 170 } });
  const [x, y, w, h] = box;
  const right = x + w / 2 > 1000;
  return (
    <div style={{
      position: "absolute", left: x * s, top: y * s, width: w * s, height: h * s, opacity: pop,
      border: `4px solid ${color}`, borderRadius: 10, transform: `scale(${0.92 + 0.08 * pop})`,
      boxShadow: `0 0 0 3000px rgba(3,21,41,${0.35 * pop})`,
    }}>
      <div style={{
        position: "absolute", top: -54, ...(right ? { right: -4 } : { left: -4 }), background: color,
        color: NAVY, fontFamily: FONT, fontSize: 30, fontWeight: 700, padding: "4px 14px", borderRadius: 8,
        whiteSpace: "nowrap",
      }}>{text}</div>
    </div>
  );
};

const TimerCard: React.FC<{ text: string }> = ({ text }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const pop = spring({ frame, fps, config: { damping: 18 } });
  return (
    <div style={{ position: "absolute", top: 24, left: 0, right: 0, display: "flex", justifyContent: "center",
      opacity: pop }}>
      <div style={{
        background: "rgba(6,33,61,0.92)", border: `3px solid ${AMBER}`, borderRadius: 40,
        padding: "10px 32px", color: "#fff", fontFamily: FONT, fontSize: 38, fontWeight: 700,
      }}>{text}</div>
    </div>
  );
};

// 裁切片段（例如結果視窗第一行）放大成橫幅
const CropBanner: React.FC<{ clip: Clip }> = ({ clip }) => {
  const frame = useCurrentFrame();
  const [, , cw, ch] = clip.crop!;
  const scale = 1640 / cw;
  const o = interpolate(frame, [0, 10], [0, 1], { extrapolateRight: "clamp" });
  return (
    <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", paddingBottom: 170, opacity: o }}>
      <div style={{ color: "#C9D6E8", fontFamily: FONT, fontSize: 34, marginBottom: 22 }}>{clip.label}</div>
      <div style={{ background: "#fff", padding: 16, borderRadius: 14, boxShadow: "0 20px 60px rgba(0,0,0,0.45)" }}>
        <OffthreadVideo src={staticFile(clip.src)} muted style={{ width: cw * scale, height: ch * scale, display: "block" }} />
      </div>
    </AbsoluteFill>
  );
};

const ClipWindow: React.FC<{ clip: Clip; rec: [number, number]; callouts: Callout[]; timer: string | null }> = (
  { clip, rec, callouts, timer }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  if (clip.crop) return <CropBanner clip={clip} />;
  const r = windowRect(rec);
  const cam = cameraTransform(clip.camera || "fixed", frame, clip.duration_frames, fps);
  // 推近時以第一個標註框為中心，讓重點留在畫面內
  const target = callouts[0]?.box;
  const origin = target
    ? `${((target[0] + target[2] / 2) / rec[0]) * 100}% ${((target[1] + target[3] / 2) / rec[1]) * 100}%`
    : "50% 50%";
  const fadeIn = interpolate(frame, [0, 6], [0, 1], { extrapolateRight: "clamp" });
  const color = isAct(clip.label) ? CYAN : CORAL;
  return (
    <div style={{
      position: "absolute", left: r.left, top: r.top, width: r.w, height: r.h, borderRadius: 18,
      overflow: "hidden", opacity: fadeIn, border: "1px solid rgba(255,255,255,0.18)",
      boxShadow: "0 30px 80px rgba(0,0,0,0.5)", background: "#fff",
    }}>
      <div style={{
        position: "absolute", inset: 0, transformOrigin: origin,
        transform: `scale(${cam.s}) translate(${cam.x}%, ${cam.y}%)`,
      }}>
        <OffthreadVideo src={staticFile(clip.src)} muted style={{ width: "100%", height: "100%", display: "block" }} />
        {callouts.map((co) => (
          <Sequence key={co.text} from={co.frame} layout="none">
            <CalloutBox box={co.box} text={co.text} s={r.s} color={color} />
          </Sequence>
        ))}
      </div>
      {clip.label ? <LabelChip text={clip.label} color={color} /> : null}
      {timer ? <TimerCard text={timer} /> : null}
    </div>
  );
};

const Recording: React.FC<{ scene: Scene; rec: [number, number] }> = ({ scene, rec }) => (
  <AbsoluteFill>
    {scene.clips.map((c, i) => {
      // 標註框的影格改成相對於該片段起點；落在片段之前的標註從片段開頭出現
      const cos = scene.callouts.filter((co) => co.clip === i)
        .map((co) => ({ ...co, frame: Math.max(0, co.frame - c.start_frame) }))
        .filter((co) => co.frame < c.duration_frames);
      return (
        <Sequence key={`${c.src}-${i}`} from={c.start_frame} durationInFrames={c.duration_frames}>
          <ClipWindow clip={c} rec={c.rec_size ?? rec} callouts={cos}
            timer={scene.timer && scene.timer.clip === i ? scene.timer.text : null} />
        </Sequence>
      );
    })}
    {scene.overlay_title ? (
      <div style={{
        position: "absolute", top: 62, right: 102, background: "rgba(6,33,61,0.88)", borderRadius: 8,
        padding: "6px 16px", color: "#C9D6E8", fontFamily: FONT, fontSize: 24, fontWeight: 600,
      }}>{scene.overlay_title}</div>
    ) : null}
  </AbsoluteFill>
);

const Captions: React.FC<{ cues: Cue[] }> = ({ cues }) => {
  const frame = useCurrentFrame();
  const cue = cues.find((c) => frame >= c.start_frame && frame < c.end_frame);
  if (!cue) return null;
  return (
    <div style={{ position: "absolute", bottom: 46, left: 0, right: 0, display: "flex", justifyContent: "center" }}>
      <div style={{
        background: "rgba(6,33,61,0.86)", color: "#fff", fontFamily: FONT, fontSize: 42, fontWeight: 600,
        padding: "10px 30px", borderRadius: 12, maxWidth: 1500, textAlign: "center", lineHeight: 1.25,
      }}>{cue.text}</div>
    </div>
  );
};

// 旁白出現時配樂降到 speech_volume，停頓時回升到 gap_volume，片尾 1.5 秒淡出
const bgmVolume = (frame: number, p: MainProps) => {
  const base = p.bgm?.gap_volume ?? 0;
  const duck = p.bgm?.speech_volume ?? 0;
  const fade = 10;
  let d = Infinity;
  for (const a of p.audio) {
    if (frame >= a.start_frame && frame <= a.start_frame + a.duration_frames) return duck;
    d = Math.min(d, frame < a.start_frame ? a.start_frame - frame : frame - a.start_frame - a.duration_frames);
  }
  const fadeOut = interpolate(frame, [p.total_frames - 45, p.total_frames], [1, 0], { extrapolateLeft: "clamp" });
  return (d >= fade ? base : duck + (base - duck) * (d / fade)) * fadeOut;
};

const SceneFade: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const frame = useCurrentFrame();
  return <AbsoluteFill style={{ opacity: interpolate(frame, [0, 8], [0, 1], { extrapolateRight: "clamp" }) }}>
    {children}</AbsoluteFill>;
};

export const Main: React.FC<MainProps> = (p) => (
  <AbsoluteFill>
    <Background />
    {p.scenes.map((s) => (
      <Sequence key={s.id} from={s.start_frame} durationInFrames={s.duration_frames}>
        <SceneFade>
          {s.kind === "recording" ? <Recording scene={s} rec={p.rec_size} />
            : s.anim_src ? <OffthreadVideo src={staticFile(s.anim_src)} muted />
              : <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", color: "#5d6b85",
                fontSize: 80, fontFamily: FONT }}>{s.id}</AbsoluteFill>}
        </SceneFade>
      </Sequence>
    ))}
    {p.bgm ? <Audio src={staticFile(p.bgm.src)} volume={(f) => bgmVolume(f, p)} loop /> : null}
    {p.audio.map((a) => (
      <Sequence key={a.src} from={a.start_frame} durationInFrames={a.duration_frames + p.fps}>
        <Audio src={staticFile(a.src)} />
      </Sequence>
    ))}
    <Captions cues={p.cues} />
  </AbsoluteFill>
);
