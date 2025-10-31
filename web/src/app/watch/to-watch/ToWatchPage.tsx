"use client";

import { useState, useEffect } from "react";
import {
  createWatchItem,
  getWatchItems,
  updateWatchItem,
  deleteWatchItem,
  type WatchItem,
} from "@/lib/watch/api";
import Text from "@/refresh-components/texts/Text";

export function ToWatchPage() {
  const [watchItems, setWatchItems] = useState<WatchItem[]>([]);
  const [newUrl, setNewUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [includeInactive, setIncludeInactive] = useState(false);

  const fetchWatchItems = async () => {
    try {
      setLoading(true);
      const response = await getWatchItems(includeInactive);
      setWatchItems(response.watch_items);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load watch items");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchWatchItems();
  }, [includeInactive]);

  const handleAddUrl = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!newUrl.trim()) {
      setError("Please enter a URL");
      return;
    }

    if (!newUrl.startsWith("http://") && !newUrl.startsWith("https://")) {
      setError("URL must start with http:// or https://");
      return;
    }

    try {
      setLoading(true);
      await createWatchItem({ url: newUrl });
      setNewUrl("");
      await fetchWatchItems();
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to add watch item");
    } finally {
      setLoading(false);
    }
  };

  const handleToggleActive = async (item: WatchItem) => {
    try {
      await updateWatchItem(item.id, { is_active: !item.is_active });
      await fetchWatchItems();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update watch item");
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm("Are you sure you want to delete this watch item?")) {
      return;
    }

    try {
      await deleteWatchItem(id);
      await fetchWatchItems();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete watch item");
    }
  };

  return (
    <div className="flex flex-col h-screen w-full overflow-hidden">
      <div className="flex-none border-b border-border p-6">
        <h1 className="text-3xl font-bold mb-2">To Watch</h1>
        <Text className="text-text-secondary">
          Add URLs to track and monitor for new content
        </Text>
      </div>

      <div className="flex-1 overflow-y-auto p-6">
        <div className="max-w-4xl mx-auto">
          {/* Add new watch item form */}
          <form onSubmit={handleAddUrl} className="mb-8">
            <div className="flex gap-3">
              <input
                type="text"
                value={newUrl}
                onChange={(e) => setNewUrl(e.target.value)}
                placeholder="Enter URL to watch (e.g., https://example.com/feed)"
                className="flex-1 px-4 py-2 border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-accent"
                disabled={loading}
              />
              <button
                type="submit"
                disabled={loading}
                className="px-6 py-2 bg-accent text-inverted rounded-lg hover:bg-accent-hover disabled:opacity-50 disabled:cursor-not-allowed font-medium"
              >
                {loading ? "Adding..." : "Add URL"}
              </button>
            </div>
            {error && (
              <div className="mt-2 text-sm text-error">{error}</div>
            )}
          </form>

          {/* Filter controls */}
          <div className="mb-4 flex items-center gap-2">
            <input
              type="checkbox"
              id="include-inactive"
              checked={includeInactive}
              onChange={(e) => setIncludeInactive(e.target.checked)}
              className="rounded"
            />
            <label htmlFor="include-inactive" className="text-sm">
              Include inactive items
            </label>
          </div>

          {/* Watch items list */}
          {loading && watchItems.length === 0 ? (
            <div className="text-center py-12">
              <Text className="text-text-secondary">Loading...</Text>
            </div>
          ) : watchItems.length === 0 ? (
            <div className="text-center py-12">
              <Text className="text-text-secondary">
                No watch items yet. Add a URL above to get started.
              </Text>
            </div>
          ) : (
            <div className="space-y-4">
              {watchItems.map((item) => (
                <div
                  key={item.id}
                  className={`border border-border rounded-lg p-4 ${
                    !item.is_active ? "opacity-50" : ""
                  }`}
                >
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-2">
                        <a
                          href={item.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-accent hover:underline font-medium truncate"
                        >
                          {item.url}
                        </a>
                        {!item.is_active && (
                          <span className="px-2 py-1 text-xs bg-background-tint-02 rounded">
                            Inactive
                          </span>
                        )}
                      </div>
                      <div className="text-sm text-text-secondary space-y-1">
                        <div>
                          Added: {new Date(item.added_date).toLocaleDateString()}
                        </div>
                        {item.last_checked && (
                          <div>
                            Last checked:{" "}
                            {new Date(item.last_checked).toLocaleString()}
                          </div>
                        )}
                      </div>
                    </div>
                    <div className="flex gap-2">
                      <button
                        onClick={() => handleToggleActive(item)}
                        className="px-3 py-1 text-sm border border-border rounded hover:bg-background-tint-02"
                      >
                        {item.is_active ? "Deactivate" : "Activate"}
                      </button>
                      <button
                        onClick={() => handleDelete(item.id)}
                        className="px-3 py-1 text-sm border border-error text-error rounded hover:bg-error hover:text-inverted"
                      >
                        Delete
                      </button>
                    </div>
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
