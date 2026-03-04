"use client";

import { useState } from "react";
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
import { Loader2 } from "lucide-react";

export default function Home() {
  const [youtubeUrl, setYoutubeUrl] = useState("");
  const [videoId, setVideoId] = useState("");
  const [targetLanguage, setTargetLanguage] = useState("en");
  const [translatedVideoUrl, setTranslatedVideoUrl] = useState("");
  const [translationStatus, setTranslationStatus] = useState("");
  const [forceRegenerate, setForceRegenerate] = useState(false);
  const [loading, setLoading] = useState(false);

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

  // Extract Video ID from YouTube URL
  const extractVideoId = (url: string) => {
    const match = url.match(
      /(?:youtu\.be\/|youtube\.com\/(?:.*v=|.*\/|.*vi\/|.*watch\?v=))([^&?\/]+)/
    );
    return match ? match[1] : "";
  };

  // Handle URL Input Change
  const handleUrlChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setYoutubeUrl(event.target.value);
    const id = extractVideoId(event.target.value);
    setVideoId(id);
  };

  // Handle Translation Request
  const handleTranslate = async () => {
    if (!videoId) return alert("Please enter a valid YouTube URL");
    setLoading(true);

    try {
      setTranslationStatus("");
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
      setTranslationStatus(data?.cache_hit ? "Using cached translation" : "Generated fresh translation");
    } catch (error) {
      let message =
        error instanceof Error ? error.message : "Error fetching translated video.";
      if (message === "Failed to fetch") {
        message = `Failed to fetch from ${SERVER_ADDRESS}/translate. Verify backend is running and reachable on this exact URL.`;
      }
      alert(message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto p-6 space-y-4">
      <h1 className="text-2xl font-bold">YouTube Video Translator - v1</h1>

      {/* YouTube URL Input */}
      <Input
        placeholder="Enter YouTube URL..."
        value={youtubeUrl}
        onChange={handleUrlChange}
      />

      {/* Show YouTube Video Player */}
      {videoId && (
        <div className="mt-4">
          <ReactPlayer
            url={`https://www.youtube.com/watch?v=${videoId}`}
            controls
            width="100%"
          />
        </div>
      )}

      {/* Language Selection Dropdown */}
      <Select onValueChange={setTargetLanguage} value={targetLanguage}>
        <SelectTrigger className="w-full">
          <SelectValue placeholder="Select Language" />
        </SelectTrigger>
        <SelectContent>
          {languages.map((lang) => (
            <SelectItem key={lang.code} value={lang.code}>
              {lang.label}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      <label className="flex items-center gap-2 text-sm">
        <input
          type="checkbox"
          checked={forceRegenerate}
          onChange={(event) => setForceRegenerate(event.target.checked)}
        />
        Force regenerate (ignore cached output)
      </label>

      {/* Translate Button */}
      <Button onClick={handleTranslate} disabled={loading}>
        {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : "Translate"}
      </Button>

      {!loading && translationStatus && (
        <p className="text-sm text-muted-foreground">{translationStatus}</p>
      )}

      {/* Show Translated Video */}
      {!loading && translatedVideoUrl && (
        <div className="mt-6">
          <h2 className="text-lg font-semibold">Translated Video</h2>
          <ReactPlayer url={translatedVideoUrl} controls width="100%" />
        </div>
      )}
    </div>
  );
}
