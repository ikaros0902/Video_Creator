import React from "react";
import { AbsoluteFill, Composition, interpolate, useCurrentFrame } from "remotion";
import { Main, MainProps } from "./Main";

// 環境冒煙測試用：1 秒淡入文字，確認 Remotion 能在這台電腦渲染
const Smoke: React.FC = () => {
  const frame = useCurrentFrame();
  const opacity = interpolate(frame, [0, 15], [0, 1], { extrapolateRight: "clamp" });
  return (
    <AbsoluteFill style={{ backgroundColor: "#0b1220", justifyContent: "center", alignItems: "center" }}>
      <div style={{ color: "white", fontSize: 64, fontFamily: "Segoe UI, sans-serif", opacity }}>Remotion OK</div>
    </AbsoluteFill>
  );
};

const defaultMain: MainProps = {
  variant: "main", fps: 30, size: [1920, 1080], total_frames: 30, rec_size: [1920, 1080],
  audio: [], cues: [], scenes: [],
};

export const Root: React.FC = () => (
  <>
    <Composition id="Smoke" component={Smoke} durationInFrames={30} fps={30} width={640} height={360} />
    <Composition
      id="Main"
      component={Main}
      defaultProps={defaultMain}
      durationInFrames={30}
      fps={30}
      width={1920}
      height={1080}
      // 長度、影格率、尺寸都由 vc render 產生的 props（來自 timeline.json）決定
      calculateMetadata={({ props }) => ({
        durationInFrames: props.total_frames,
        fps: props.fps,
        width: props.size[0],
        height: props.size[1],
      })}
    />
  </>
);
