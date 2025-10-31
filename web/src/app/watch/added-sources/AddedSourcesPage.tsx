"use client";

import { useState, useEffect } from "react";
import {
  createAddedSource,
  getAddedSources,
  updateAddedSource,
  markAddedSourceAsRead,
  deleteAddedSource,
  type AddedSource,
} from "@/lib/watch/api";
import Text from "@/refresh-components/texts/Text";

export function AddedSourcesPage() {
  const [sources, setSources] = useState<AddedSource[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [onlyNew, setOnlyNew] = useState(false);
  const [newCount, setNewCount] = useState(0);

  // Form state
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState({
    link: "",
    title: "",
    summary: "",
    content: "",
  });

  const fetchSources = async () => {
    try {
      setLoading(true);
      const response = await getAddedSources(onlyNew);
      setSources(response.sources);
      setNewCount(response.new_count);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load added sources");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSources();
  }, [onlyNew]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!formData.link.trim()) {
      setError("Please enter a link");
      return;
    }

    if (!formData.link.startsWith("http://") && !formData.link.startsWith("https://")) {
      setError("Link must start with http:// or https://");
      return;
    }

    try {
      setLoading(true);
      await createAddedSource({
        link: formData.link,
        title: formData.title || undefined,
        summary: formData.summary || undefined,
        content: formData.content || undefined,
      });
      setFormData({ link: "", title: "", summary: "", content: "" });
      setShowForm(false);
      await fetchSources();
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to add source");
    } finally {
      setLoading(false);
    }
  };

  const handleMarkAsRead = async (sourceId: string) => {
    try {
      await markAddedSourceAsRead(sourceId);
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
      await deleteAddedSource(sourceId);
      await fetchSources();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete source");
    }
  };

  return (
    <div className="flex flex-col h-screen w-full overflow-hidden">
      <div className="flex-none border-b border-border p-6">
        <div className="flex items-center justify-between mb-2">
          <h1 className="text-3xl font-bold">Add Sources</h1>
          <button
            onClick={() => setShowForm(!showForm)}
            className="px-4 py-2 bg-accent text-inverted rounded-lg hover:bg-accent-hover font-medium"
          >
            {showForm ? "Cancel" : "Add Source"}
          </button>
        </div>
        <div className="flex items-center justify-between">
          <Text className="text-text-secondary">
            Manually added sources and content
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
          {/* Add source form */}
          {showForm && (
            <form onSubmit={handleSubmit} className="mb-8 p-6 border border-border rounded-lg bg-background-tint-01">
              <h3 className="text-lg font-semibold mb-4">Add New Source</h3>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium mb-2">
                    Link <span className="text-error">*</span>
                  </label>
                  <input
                    type="text"
                    value={formData.link}
                    onChange={(e) =>
                      setFormData({ ...formData, link: e.target.value })
                    }
                    placeholder="https://example.com/article"
                    className="w-full px-4 py-2 border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-accent"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">
                    Title
                  </label>
                  <input
                    type="text"
                    value={formData.title}
                    onChange={(e) =>
                      setFormData({ ...formData, title: e.target.value })
                    }
                    placeholder="Article title"
                    className="w-full px-4 py-2 border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-accent"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">
                    Summary
                  </label>
                  <textarea
                    value={formData.summary}
                    onChange={(e) =>
                      setFormData({ ...formData, summary: e.target.value })
                    }
                    placeholder="Brief summary of the content"
                    rows={3}
                    className="w-full px-4 py-2 border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-accent"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">
                    Content
                  </label>
                  <textarea
                    value={formData.content}
                    onChange={(e) =>
                      setFormData({ ...formData, content: e.target.value })
                    }
                    placeholder="Full content or notes"
                    rows={6}
                    className="w-full px-4 py-2 border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-accent"
                  />
                </div>

                <div className="flex gap-3">
                  <button
                    type="submit"
                    disabled={loading}
                    className="px-6 py-2 bg-accent text-inverted rounded-lg hover:bg-accent-hover disabled:opacity-50 disabled:cursor-not-allowed font-medium"
                  >
                    {loading ? "Adding..." : "Add Source"}
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      setShowForm(false);
                      setFormData({ link: "", title: "", summary: "", content: "" });
                    }}
                    className="px-6 py-2 border border-border rounded-lg hover:bg-background-tint-02"
                  >
                    Cancel
                  </button>
                </div>
              </div>

              {error && (
                <div className="mt-4 p-3 bg-error/10 text-error rounded-lg text-sm">
                  {error}
                </div>
              )}
            </form>
          )}

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

          {error && !showForm && (
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
                  : "No sources added yet. Click 'Add Source' to get started!"}
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
                      Added: {new Date(source.created_at).toLocaleString()}
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
