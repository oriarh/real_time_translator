"use client";

import { useMemo, useState } from "react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import ReactPlayer from "react-player";
import { CheckCircle2, Circle, Loader2, TriangleAlert } from "lucide-react";

type UiPhase = "idle" | "requesting" | "processing" | "success" | "error";

type TranslationMeta = {
  cacheHit: boolean | null;
  regenerated: boolean | null;
  localFile: string;
  originalTranscript: string;
  translatedTranscript: string;
};

const PIPELINE_STEPS = ["Validate URL", "Request sent", "Processing", "Ready"] as const;

export default function Home() {
  const [youtubeUrl, setYoutubeUrl] = useState("");
  const [videoId, setVideoId] = useState("");
  const [targetLanguage, setTargetLanguage] = useState("en");
  const [translatedVideoUrl, setTranslatedVideoUrl] = useState("");
  const [forceRegenerate, setForceRegenerate] = useState(false);
  const [uiPhase, setUiPhase] = useState<UiPhase>("idle");
  const [lastError, setLastError] = useState<string | null>(null);
  const [translationMeta, setTranslationMeta] = useState<TranslationMeta>({
    cacheHit: null,
    regenerated: null,
    localFile: "",
    originalTranscript: "",
    translatedTranscript: "",
  });
  const [transcriptTab, setTranscriptTab] = useState<"original" | "translated">(
    "translated"
  );

  const SERVER_ADDRESS =
    process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000";

  const languages = [
    { label: "Urdu", code: "ur" },
    { label: "Punjabi", code: "pa" },
    { label: "Spanish", code: "es" },
    { label: "French", code: "fr" },
    { label: "German", code: "de" },
    { label: "Chinese", code: "zh-CN" },
    { label: "Japanese", code: "ja" },
    { label: "Korean", code: "ko" },
    { label: "Hindi", code: "hi" },
    { label: "Arabic", code: "ar" },
    { label: "Portuguese", code: "pt" },
    { label: "Italian", code: "it" },
    { label: "Russian", code: "ru" },
    { label: "Turkish", code: "tr" },
    { label: "Bengali", code: "bn" },
    { label: "Dutch", code: "nl" },
    { label: "Persian", code: "fa" },
    { label: "Swedish", code: "sv" },
    { label: "Polish", code: "pl" },
    { label: "Thai", code: "th" },
    { label: "English", code: "en" },
  ];

  const selectedLanguageLabel =
    languages.find((language) => language.code === targetLanguage)?.label || "Unknown";

  const extractVideoId = (url: string) => {
    const match = url.match(
      /(?:youtu\.be\/|youtube\.com\/(?:.*v=|.*\/|.*vi\/|.*watch\?v=))([^&?\/]+)/
    );
    return match ? match[1] : "";
  };

  const handleUrlChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setYoutubeUrl(event.target.value);
    const id = extractVideoId(event.target.value);
    setVideoId(id);
    setUiPhase("idle");
    setLastError(null);
  };

  const handleTranslate = async () => {
    if (!videoId) {
      setUiPhase("error");
      setLastError("Please enter a valid YouTube URL.");
      return;
    }

    setUiPhase("requesting");
    setLastError(null);

    try {
      setTimeout(() => {
        setUiPhase((current) => (current === "requesting" ? "processing" : current));
      }, 350);

      const response = await fetch(`${SERVER_ADDRESS}/translate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          video_id: videoId,
          target_language: targetLanguage,
          force_regenerate: forceRegenerate,
        }),
      });

      const data = await response.json().catch(() => null);
      if (!response.ok) {
        const detail = data?.details ? `\n\nDetails:\n${data.details}` : "";
        throw new Error((data?.error || `Request failed (${response.status})`) + detail);
      }
      if (!data?.output) {
        throw new Error("Translation completed but no output URL was returned.");
      }

      setTranslatedVideoUrl(data.output);
      setTranslationMeta({
        cacheHit: data?.cache_hit ?? null,
        regenerated: data?.regenerated ?? null,
        localFile: data?.local_file ?? "",
        originalTranscript: data?.original_transcript ?? "",
        translatedTranscript: data?.translated_transcript ?? "",
      });
      setUiPhase("success");
    } catch (error) {
      let message =
        error instanceof Error ? error.message : "Error fetching translated video.";
      if (message === "Failed to fetch") {
        message = `Failed to fetch from ${SERVER_ADDRESS}/translate. Verify backend is running and reachable on this exact URL.`;
      }
      setLastError(message);
      setUiPhase("error");
    }
  };

  const activeStepIndex = useMemo(() => {
    if (uiPhase === "idle") return 0;
    if (uiPhase === "requesting") return 1;
    if (uiPhase === "processing") return 2;
    if (uiPhase === "success") return 3;
    return 2;
  }, [uiPhase]);

  return (
    <main className="mx-auto max-w-6xl px-4 pb-12 pt-8 sm:px-6 lg:px-8">
      <section className="reveal-up space-y-4">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div className="space-y-3">
            <h1 className="font-display text-4xl font-semibold tracking-tight text-[var(--text-primary)] sm:text-5xl">
              YouTube Translator Studio
            </h1>
            <p className="max-w-2xl text-sm text-[var(--text-muted)] sm:text-base">
              Convert any YouTube video into your preferred language with clear progress feedback and
              production-style controls.
            </p>
          </div>
        </div>
      </section>

      <section className="reveal-up mt-7 rounded-2xl p-5 surface-card sm:p-6">
        <div className="grid gap-4 lg:grid-cols-[1.2fr_220px]">
          <div className="space-y-4">
            <label className="text-sm font-medium text-[var(--text-primary)]" htmlFor="youtube-url">
              YouTube URL
            </label>
            <Input
              id="youtube-url"
              className="border-[var(--border-soft)] bg-white/70 placeholder:text-[var(--text-muted)]"
              placeholder="https://www.youtube.com/watch?v=..."
              value={youtubeUrl}
              onChange={handleUrlChange}
            />
          </div>

          <div className="space-y-4">
            <label className="text-sm font-medium text-[var(--text-primary)]">Target Language</label>
            <Select onValueChange={setTargetLanguage} value={targetLanguage}>
              <SelectTrigger className="w-full border-[var(--border-soft)] bg-white/70">
                <SelectValue placeholder="Select Language" />
              </SelectTrigger>
              <SelectContent>
                {languages.map((language) => (
                  <SelectItem key={language.code} value={language.code}>
                    {language.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>

        <div className="mt-5 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <label className="inline-flex items-center gap-2 text-sm text-[var(--text-primary)]">
            <input
              type="checkbox"
              checked={forceRegenerate}
              onChange={(event) => setForceRegenerate(event.target.checked)}
            />
            Force regenerate (ignore cache)
          </label>

          <Button
            className="bg-[var(--accent-brand)] text-white hover:bg-[var(--accent-strong)]"
            onClick={handleTranslate}
            disabled={uiPhase === "requesting" || uiPhase === "processing"}
          >
            {uiPhase === "requesting" || uiPhase === "processing" ? (
              <>
                <Loader2 className="h-5 w-5 animate-spin" />
                Translating...
              </>
            ) : (
              "Translate Video"
            )}
          </Button>
        </div>
      </section>

      <section className="reveal-up mt-6 rounded-2xl p-5 surface-card sm:p-6">
        <h2 className="font-display text-2xl font-semibold text-[var(--text-primary)]">Pipeline Status</h2>
        <ol className="mt-4 grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
          {PIPELINE_STEPS.map((step, index) => {
            const isDone = index < activeStepIndex || (uiPhase === "success" && index === activeStepIndex);
            const isActive = index === activeStepIndex && uiPhase !== "success";

            return (
              <li
                key={step}
                className={`rounded-xl border px-3 py-2 text-sm transition-colors ${
                  isDone
                    ? "chip-ok"
                    : isActive
                    ? "chip-warn"
                    : "border-[var(--border-soft)] bg-white/60 text-[var(--text-muted)]"
                }`}
              >
                <div className="flex items-center gap-2">
                  {isDone ? <CheckCircle2 className="h-4 w-4" /> : <Circle className="h-4 w-4" />}
                  <span>{step}</span>
                </div>
              </li>
            );
          })}
        </ol>

        {lastError && (
          <div className="chip-error mt-4 rounded-xl px-3 py-3 text-sm">
            <div className="flex items-start gap-2">
              <TriangleAlert className="mt-0.5 h-4 w-4 shrink-0" />
              <p className="whitespace-pre-wrap">{lastError}</p>
            </div>
          </div>
        )}
      </section>

      <section className="reveal-up mt-6 grid gap-6 lg:grid-cols-[1.5fr_1fr]">
        <div className="rounded-2xl p-5 surface-card sm:p-6">
          <h2 className="font-display text-2xl font-semibold text-[var(--text-primary)]">Video Output</h2>
          <div className="mt-4 overflow-hidden rounded-xl border border-[var(--border-soft)] bg-black/10">
            <ReactPlayer
              url={
                translatedVideoUrl ||
                (videoId ? `https://www.youtube.com/watch?v=${videoId}` : undefined)
              }
              controls
              width="100%"
            />
          </div>
        </div>

        <aside className="rounded-2xl p-5 surface-card sm:p-6">
          <h3 className="font-display text-xl font-semibold text-[var(--text-primary)]">
            Transcript Viewer
          </h3>
          <p className="mt-1 text-sm text-[var(--text-muted)]">
            Toggle between source and translated transcript.
          </p>

          <div className="mt-4 grid grid-cols-2 gap-2 rounded-lg border border-[var(--border-soft)] bg-white/70 p-1">
            <button
              className={`rounded-md px-3 py-2 text-sm transition ${
                transcriptTab === "original"
                  ? "bg-[var(--accent-brand)] text-white"
                  : "text-[var(--text-primary)] hover:bg-white"
              }`}
              onClick={() => setTranscriptTab("original")}
              type="button"
            >
              Original
            </button>
            <button
              className={`rounded-md px-3 py-2 text-sm transition ${
                transcriptTab === "translated"
                  ? "bg-[var(--accent-brand)] text-white"
                  : "text-[var(--text-primary)] hover:bg-white"
              }`}
              onClick={() => setTranscriptTab("translated")}
              type="button"
            >
              {selectedLanguageLabel}
            </button>
          </div>

          <div className="mt-4 h-[360px] overflow-auto rounded-lg border border-[var(--border-soft)] bg-white/65 p-4 text-sm leading-6 text-[var(--text-primary)]">
            {transcriptTab === "original" ? (
              translationMeta.originalTranscript ? (
                <p className="whitespace-pre-wrap">{translationMeta.originalTranscript}</p>
              ) : (
                <p className="text-[var(--text-muted)]">
                  Original transcript will appear after translation completes.
                </p>
              )
            ) : translationMeta.translatedTranscript ? (
              <p className="whitespace-pre-wrap">{translationMeta.translatedTranscript}</p>
            ) : (
              <p className="text-[var(--text-muted)]">
                Translated transcript will appear after translation completes.
              </p>
            )}
          </div>
        </aside>
      </section>
    </main>
  );
}
