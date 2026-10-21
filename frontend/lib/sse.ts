export interface SSEEvent {
  event: string;
  data: unknown;
}

export async function streamPost(
  url: string,
  body: object,
  onEvent: (event: SSEEvent) => void,
  onError?: (error: Error) => void,
  onComplete?: () => void,
  signal?: AbortSignal
): Promise<void> {
  console.log("[SSE] Connecting to:", url);
  try {
    const response = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
      signal,
    });

    console.log("[SSE] Response status:", response.status);

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    const reader = response.body?.getReader();
    if (!reader) throw new Error("No response body");

    const decoder = new TextDecoder();
    let buffer = "";
    // Persist across chunks so event names aren't lost at chunk boundaries
    let currentEvent = "message";
    let currentData = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      const text = decoder.decode(value, { stream: true });
      console.log("[SSE] Chunk received, length:", text.length);
      buffer += text;

      const lines = buffer.split("\n");
      buffer = lines.pop() || "";

      for (const line of lines) {
        if (line.startsWith("event: ")) {
          currentEvent = line.slice(7).trim();
        } else if (line.startsWith("data: ")) {
          currentData = line.slice(6);
        } else if (line === "" && currentData) {
          try {
            const parsed = JSON.parse(currentData);
            console.log("[SSE] Event:", currentEvent, parsed);
            onEvent({ event: currentEvent, data: parsed });
          } catch {
            console.warn("[SSE] Failed to parse SSE data:", currentData);
          }
          currentEvent = "message";
          currentData = "";
        }
      }
    }

    console.log("[SSE] Stream complete");
    onComplete?.();
  } catch (error) {
    // Don't report abort errors as failures
    if (error instanceof DOMException && error.name === "AbortError") {
      console.log("[SSE] Stream aborted");
      return;
    }
    onError?.(error as Error);
  }
}
