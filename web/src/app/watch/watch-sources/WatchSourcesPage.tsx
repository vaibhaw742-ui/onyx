"use client";

import { useState, useEffect } from "react";
import {
  getWatchSources,
  markWatchSourceAsRead,
  deleteWatchSource,
  type WatchSource,
} from "@/lib/watch/api";
import Text from "@/refresh-components/texts/Text";

export function WatchSourcesPage() {
  const [sources, setSources] = useState<WatchSource[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [onlyNew, setOnlyNew] = useState(false);
  const [newCount, setNewCount] = useState(0);

  const fetchSources = async () => {
    try {
      setLoading(true);
      const response = await getWatchSources(onlyNew);
      setSources(response.sources);
      setNewCount(response.new_count);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load watch sources");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSources();
  }, [onlyNew]);

  const handleMarkAsRead = async (sourceId: string) => {
    try {
      await markWatchSourceAsRead(sourceId);
      await fetchSources();
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to mark source as read"
      );
    }
  };

  const handleDelete = async (sourceId: string) => {
    if (!confirm("Are you sure you want to delete this source?")) {
      return;
    }

    try {
      await deleteWatchSource(sourceId);
      await fetchSources();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete source");
    }
  };

  return (
    <div className="flex flex-col h-screen w-full overflow-hidden">
      <div className="flex-none border-b border-border p-6">
        <h1 className="text-3xl font-bold mb-2">Watch Sources</h1>
        <div className="flex items-center justify-between">
          <Text className="text-text-secondary">
            Content detected from your watched URLs
          </Text>
          {newCount > 0 && (
            <span className="px-3 py-1 bg-accent text-inverted rounded-full text-sm font-medium">
              {newCount} new
            </span>
          )}
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-6">
        <div className="max-w-4xl mx-auto">
          {/* Filter controls */}
          <div className="mb-6 flex items-center gap-4">
            <button
              onClick={() => setOnlyNew(false)}
              className={`px-4 py-2 rounded-lg font-medium ${
                !onlyNew
                  ? "bg-accent text-inverted"
                  : "bg-background-tint-02 text-text-secondary hover:bg-background-tint-03"
              }`}
            >
              All Sources
            </button>
            <button
              onClick={() => setOnlyNew(true)}
              className={`px-4 py-2 rounded-lg font-medium ${
                onlyNew
                  ? "bg-accent text-inverted"
                  : "bg-background-tint-02 text-text-secondary hover:bg-background-tint-03"
              }`}
            >
              New Only ({newCount})
            </button>
          </div>

          {error && (
            <div className="mb-4 p-4 bg-error/10 text-error rounded-lg">
              {error}
            </div>
          )}

          {/* Sources list */}
          {loading && sources.length === 0 ? (
            <div className="text-center py-12">
              <Text className="text-text-secondary">Loading...</Text>
            </div>
          ) : sources.length === 0 ? (
            <div className="text-center py-12">
              <Text className="text-text-secondary">
                {onlyNew
                  ? "No new sources found."
                  : "No sources detected yet. Add some URLs to watch!"}
              </Text>
            </div>
          ) : (
            <div className="space-y-4">
              {sources.map((source) => (
                <div
                  key={source.id}
                  className={`border rounded-lg p-5 ${
                    source.is_new
                      ? "border-accent bg-accent/5"
                      : "border-border"
                  }`}
                >
                  <div className="flex items-start justify-between gap-4 mb-3">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        {source.is_new && (
                          <span className="px-2 py-1 text-xs bg-accent text-inverted rounded">
                            NEW
                          </span>
                        )}
                        <h3 className="font-semibold text-lg">
                          {source.title || "Untitled"}
                        </h3>
                      </div>
                      <a
                        href={source.link}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-accent hover:underline text-sm break-all"
                      >
                        {source.link}
                      </a>
                    </div>
                    <div className="flex gap-2">
                      {source.is_new && (
                        <button
                          onClick={() => handleMarkAsRead(source.id)}
                          className="px-3 py-1 text-sm bg-accent text-inverted rounded hover:bg-accent-hover"
                        >
                          Mark Read
                        </button>
                      )}
                      <button
                        onClick={() => handleDelete(source.id)}
                        className="px-3 py-1 text-sm border border-error text-error rounded hover:bg-error hover:text-inverted"
                      >
                        Delete
                      </button>
                    </div>
                  </div>

                  {source.summary && (
                    <div className="mb-3">
                      <Text className="text-sm text-text-secondary">
                        {source.summary}
                      </Text>
                    </div>
                  )}

                  {source.content && (
                    <div className="mb-3 p-3 bg-background-tint-02 rounded">
                      <Text className="text-sm whitespace-pre-wrap">
                        {source.content.substring(0, 300)}
                        {source.content.length > 300 && "..."}
                      </Text>
                    </div>
                  )}

                  <div className="flex items-center gap-4 text-xs text-text-secondary">
                    {source.published_date && (
                      <span>
                        Published:{" "}
                        {new Date(source.published_date).toLocaleDateString()}
                      </span>
                    )}
                    <span>
                      Detected:{" "}
                      {new Date(source.detected_at).toLocaleString()}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
