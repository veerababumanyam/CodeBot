import { useEffect, useState } from "react";
import type * as Y from "yjs";
import type { WebsocketProvider } from "y-websocket";
import { createYjsProvider, destroyYjsProvider } from "@/lib/yjs-provider";

interface UseYjsResult {
  doc: Y.Doc | null;
  provider: WebsocketProvider | null;
  connected: boolean;
}

export function useYjs(docId: string | null): UseYjsResult {
  const [doc, setDoc] = useState<Y.Doc | null>(null);
  const [provider, setProvider] = useState<WebsocketProvider | null>(null);
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    if (!docId) {
      setDoc(null);
      setProvider(null);
      setConnected(false);
      return;
    }

    const result = createYjsProvider(docId);
    setDoc(result.doc);
    setProvider(result.provider);

    const onStatus = ({ status }: { status: string }) => {
      setConnected(status === "connected");
    };

    result.provider.on("status", onStatus);
    setConnected(result.provider.wsconnected);

    return () => {
      result.provider.off("status", onStatus);
      destroyYjsProvider(result.provider, result.doc);
      setDoc(null);
      setProvider(null);
      setConnected(false);
    };
  }, [docId]);

  return { doc, provider, connected };
}
