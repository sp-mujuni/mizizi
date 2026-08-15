"use client";

import { useEffect, useRef, useState } from "react";

interface RecorderProps {
  onRecorded: (file: File | null) => void;
}

const MIME_CANDIDATES = [
  "audio/webm;codecs=opus",
  "audio/webm",
  "audio/ogg;codecs=opus",
  "audio/mp4",
];

function pickMime(): { mime: string; ext: string } {
  for (const mime of MIME_CANDIDATES) {
    if (typeof MediaRecorder !== "undefined" && MediaRecorder.isTypeSupported(mime)) {
      return { mime, ext: mime.includes("mp4") ? "m4a" : mime.includes("ogg") ? "ogg" : "webm" };
    }
  }
  return { mime: "", ext: "webm" };
}

export default function Recorder({ onRecorded }: RecorderProps) {
  const [supported] = useState(() => typeof MediaRecorder !== "undefined");
  const [permissionDenied, setPermissionDenied] = useState(false);
  const [recording, setRecording] = useState(false);
  const [paused, setPaused] = useState(false);
  const [starting, setStarting] = useState(false);
  const [elapsed, setElapsed] = useState(0);
  const [done, setDone] = useState(false);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const recorderRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
      streamRef.current?.getTracks().forEach((t) => t.stop());
      if (audioUrl) URL.revokeObjectURL(audioUrl);
    };
  }, [audioUrl]);

  function startTimer() {
    setElapsed(0);
    timerRef.current = setInterval(() => setElapsed((s) => s + 1), 1000);
  }

  async function start() {
    setStarting(true);
    setError(null);
    setPermissionDenied(false);
    setDone(false);
    setAudioUrl(null);
    chunksRef.current = [];
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
      const { mime } = pickMime();
      const rec = mime
        ? new MediaRecorder(stream, { mimeType: mime })
        : new MediaRecorder(stream);
      recorderRef.current = rec;
      rec.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data);
      };
      rec.onstop = () => {
        stream.getTracks().forEach((t) => t.stop());
        streamRef.current = null;
        const { ext } = pickMime();
        const blob = new Blob(chunksRef.current, { type: rec.mimeType || "audio/webm" });
        const file = new File([blob], `mizizi-recording-${Date.now()}.${ext}`, {
          type: rec.mimeType || "audio/webm",
        });
        const url = URL.createObjectURL(blob);
        setAudioUrl(url);
        setDone(true);
        onRecorded(file);
        if (timerRef.current) {
          clearInterval(timerRef.current);
          timerRef.current = null;
        }
      };
      rec.start();
      setRecording(true);
      startTimer();
    } catch (err) {
      const name = err instanceof DOMException ? err.name : "";
      if (name === "NotAllowedError" || name === "PermissionDeniedError") {
        setPermissionDenied(true);
        setError("Microphone access was denied. Allow the mic in your browser, then try again.");
      } else {
        setError("Could not access the microphone.");
      }
      setRecording(false);
    } finally {
      setStarting(false);
    }
  }

  function pause() {
    recorderRef.current?.pause();
    setPaused(true);
  }

  function resume() {
    recorderRef.current?.resume();
    setPaused(false);
  }

  function stop() {
    recorderRef.current?.stop();
    setRecording(false);
    setPaused(false);
  }

  function discard() {
    if (audioUrl) {
      URL.revokeObjectURL(audioUrl);
      setAudioUrl(null);
    }
    setDone(false);
    onRecorded(null);
  }

  function format(s: number) {
    const m = Math.floor(s / 60).toString().padStart(2, "0");
    const sec = (s % 60).toString().padStart(2, "0");
    return `${m}:${sec}`;
  }

  if (!supported) {
    return (
      <p className="rounded-lg bg-amber-50 px-4 py-3 text-sm text-amber-800">
        Live recording is not supported in this browser. Please upload an audio file instead.
      </p>
    );
  }

  if (!recording && !done) {
    return (
      <div>
        <button
          type="button"
          onClick={start}
          disabled={starting}
          className="inline-flex items-center gap-2 rounded-full bg-rose-600 px-6 py-2.5 text-sm font-semibold text-white transition hover:bg-rose-700 disabled:opacity-50"
        >
          <span className="h-2.5 w-2.5 rounded-full bg-white animate-pulse" />
          {starting ? "Requesting microphone..." : "Start recording"}
        </button>
        {error && <p className="mt-2 text-sm text-rose-600">{error}</p>}
        {permissionDenied && (
          <p className="mt-2 text-xs text-stone-500">
            Tip: click the padlock in the address bar to re-enable the microphone.
          </p>
        )}
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-stone-200 bg-stone-50 p-4">
      <div className="mb-3 flex items-center gap-3">
        <span className={`h-3 w-3 rounded-full ${recording ? (paused ? "bg-amber-500" : "animate-pulse bg-rose-500") : "bg-stone-400"}`} />
        <span className="font-mono text-lg font-semibold tabular-nums text-stone-700">
          {format(elapsed)}
        </span>
        <span className="text-sm text-stone-500">
          {recording ? (paused ? "Paused" : "Recording…") : "Ready"}
        </span>
      </div>

      {audioUrl && (
        <audio controls src={audioUrl} className="mb-3 w-full" />
      )}

      <div className="flex flex-wrap gap-2">
        {recording ? (
          <>
            {paused ? (
              <button type="button" onClick={resume}
                className="rounded-lg bg-brand px-4 py-2 text-sm font-semibold text-white hover:bg-brand-dark">
                Resume
              </button>
            ) : (
              <button type="button" onClick={pause}
                className="rounded-lg border border-stone-300 bg-white px-4 py-2 text-sm font-semibold text-stone-700 hover:bg-stone-100">
                Pause
              </button>
            )}
            <button type="button" onClick={stop}
              className="rounded-lg bg-rose-600 px-4 py-2 text-sm font-semibold text-white hover:bg-rose-700">
              ■ Stop
            </button>
          </>
        ) : (
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium text-emerald-700">✓ Recording captured</span>
            <button type="button" onClick={discard}
              className="rounded-lg border border-stone-300 bg-white px-4 py-2 text-sm font-semibold text-stone-600 hover:bg-stone-100">
              Discard
            </button>
          </div>
        )}
      </div>
    </div>
  );
}