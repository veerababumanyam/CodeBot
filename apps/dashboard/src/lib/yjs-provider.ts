import * as Y from "yjs";
import { WebsocketProvider } from "y-websocket";

export function createYjsProvider(
  docId: string,
  serverUrl?: string,
): { doc: Y.Doc; provider: WebsocketProvider } {
  const envUrl = (import.meta.env as Record<string, string | undefined>)["VITE_YJS_URL"];
  const url = serverUrl ?? envUrl ?? "ws://localhost:1234";
  const doc = new Y.Doc();
  const provider = new WebsocketProvider(url, docId, doc, { connect: true });
  return { doc, provider };
}

export function destroyYjsProvider(
  provider: WebsocketProvider,
  doc: Y.Doc,
): void {
  provider.disconnect();
  provider.destroy();
  doc.destroy();
}
