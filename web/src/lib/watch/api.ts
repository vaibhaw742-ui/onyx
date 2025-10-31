// Client-side API helper for watch features
// Uses relative URLs that work through Next.js API routes

// =====================================================
// WATCH ITEMS API
// =====================================================

export interface WatchItem {
  id: number;
  user_id: string;
  url: string;
  added_date: string;
  last_checked: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface WatchItemCreate {
  url: string;
}

export interface WatchItemUpdate {
  url?: string;
  is_active?: boolean;
}

export interface WatchItemsResponse {
  watch_items: WatchItem[];
  total: number;
}

export async function createWatchItem(
  data: WatchItemCreate
): Promise<WatchItem> {
  const response = await fetch("/api/watch", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    throw new Error(`Failed to create watch item: ${response.statusText}`);
  }

  return response.json();
}

export async function getWatchItems(
  includeInactive: boolean = false
): Promise<WatchItemsResponse> {
  const params = new URLSearchParams();
  if (includeInactive) {
    params.append("include_inactive", "true");
  }

  const response = await fetch(
    `/api/watch?${params.toString()}`,
    {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
    }
  );

  if (!response.ok) {
    throw new Error(`Failed to fetch watch items: ${response.statusText}`);
  }

  return response.json();
}

export async function updateWatchItem(
  watchId: number,
  data: WatchItemUpdate
): Promise<WatchItem> {
  const response = await fetch(`/api/watch/${watchId}`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    throw new Error(`Failed to update watch item: ${response.statusText}`);
  }

  return response.json();
}

export async function deleteWatchItem(watchId: number): Promise<void> {
  const response = await fetch(`/api/watch/${watchId}`, {
    method: "DELETE",
    headers: {
      "Content-Type": "application/json",
    },
  });

  if (!response.ok) {
    throw new Error(`Failed to delete watch item: ${response.statusText}`);
  }
}

// =====================================================
// WATCH SOURCES API
// =====================================================

export interface WatchSource {
  id: string;
  watch_id: number;
  title: string | null;
  link: string;
  published_date: string | null;
  summary: string | null;
  content: string | null;
  is_new: boolean;
  detected_at: string;
  created_at: string;
}

export interface WatchSourcesResponse {
  sources: WatchSource[];
  total: number;
  new_count: number;
}

export async function getWatchSources(
  onlyNew: boolean = false
): Promise<WatchSourcesResponse> {
  const params = new URLSearchParams();
  if (onlyNew) {
    params.append("only_new", "true");
  }

  const response = await fetch(
    `/api/watch/sources?${params.toString()}`,
    {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
    }
  );

  if (!response.ok) {
    throw new Error(`Failed to fetch watch sources: ${response.statusText}`);
  }

  return response.json();
}

export async function markWatchSourceAsRead(
  sourceId: string
): Promise<WatchSource> {
  const response = await fetch(
    `/api/watch/sources/${sourceId}/read`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
    }
  );

  if (!response.ok) {
    throw new Error(
      `Failed to mark watch source as read: ${response.statusText}`
    );
  }

  return response.json();
}

export async function deleteWatchSource(sourceId: string): Promise<void> {
  const response = await fetch(
    `/api/watch/sources/${sourceId}`,
    {
      method: "DELETE",
      headers: {
        "Content-Type": "application/json",
      },
    }
  );

  if (!response.ok) {
    throw new Error(`Failed to delete watch source: ${response.statusText}`);
  }
}

// =====================================================
// ADDED SOURCES API
// =====================================================

export interface AddedSource {
  id: string;
  user_id: string;
  title: string | null;
  link: string;
  published_date: string | null;
  summary: string | null;
  content: string | null;
  is_new: boolean;
  created_at: string;
}

export interface AddedSourceCreate {
  link: string;
  title?: string;
  published_date?: string;
  summary?: string;
  content?: string;
}

export interface AddedSourceUpdate {
  title?: string;
  link?: string;
  published_date?: string;
  summary?: string;
  content?: string;
  is_new?: boolean;
}

export interface AddedSourcesResponse {
  sources: AddedSource[];
  total: number;
  new_count: number;
}

export async function createAddedSource(
  data: AddedSourceCreate
): Promise<AddedSource> {
  const response = await fetch("/api/watch/added-sources", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    throw new Error(`Failed to create added source: ${response.statusText}`);
  }

  return response.json();
}

export async function getAddedSources(
  onlyNew: boolean = false
): Promise<AddedSourcesResponse> {
  const params = new URLSearchParams();
  if (onlyNew) {
    params.append("only_new", "true");
  }

  const response = await fetch(
    `/api/watch/added-sources?${params.toString()}`,
    {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
    }
  );

  if (!response.ok) {
    throw new Error(`Failed to fetch added sources: ${response.statusText}`);
  }

  return response.json();
}

export async function updateAddedSource(
  sourceId: string,
  data: AddedSourceUpdate
): Promise<AddedSource> {
  const response = await fetch(
    `/api/watch/added-sources/${sourceId}`,
    {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
      },
    body: JSON.stringify(data),
    }
  );

  if (!response.ok) {
    throw new Error(`Failed to update added source: ${response.statusText}`);
  }

  return response.json();
}

export async function markAddedSourceAsRead(
  sourceId: string
): Promise<AddedSource> {
  const response = await fetch(
    `/api/watch/added-sources/${sourceId}/read`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
    }
  );

  if (!response.ok) {
    throw new Error(
      `Failed to mark added source as read: ${response.statusText}`
    );
  }

  return response.json();
}

export async function deleteAddedSource(sourceId: string): Promise<void> {
  const response = await fetch(
    `/api/watch/added-sources/${sourceId}`,
    {
      method: "DELETE",
      headers: {
        "Content-Type": "application/json",
      },
    }
  );

  if (!response.ok) {
    throw new Error(`Failed to delete added source: ${response.statusText}`);
  }
}
