import { useEffect, useState } from "react";
import type { WebsocketProvider } from "y-websocket";

interface CollabIndicatorProps {
  provider: WebsocketProvider | null;
}

const PEER_COLORS = [
  "bg-blue-500",
  "bg-green-500",
  "bg-purple-500",
  "bg-orange-500",
  "bg-pink-500",
  "bg-teal-500",
  "bg-indigo-500",
  "bg-yellow-500",
];

export function CollabIndicator({
  provider,
}: CollabIndicatorProps): React.JSX.Element {
  const [peerCount, setPeerCount] = useState(0);
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    if (!provider) {
      setPeerCount(0);
      setConnected(false);
      return;
    }

    const updatePeers = () => {
      const states = provider.awareness.getStates();
      // Subtract 1 for self
      setPeerCount(Math.max(0, states.size - 1));
    };

    const onStatus = ({ status }: { status: string }) => {
      setConnected(status === "connected");
    };

    provider.awareness.on("change", updatePeers);
    provider.on("status", onStatus);
    setConnected(provider.wsconnected);
    updatePeers();

    return () => {
      provider.awareness.off("change", updatePeers);
      provider.off("status", onStatus);
    };
  }, [provider]);

  if (!provider) {
    return <div />;
  }

  if (!connected) {
    return (
      <div className="flex items-center gap-1.5 text-xs text-red-500">
        <span className="inline-block h-2 w-2 rounded-full bg-red-500" />
        Disconnected
      </div>
    );
  }

  return (
    <div className="flex items-center gap-1.5">
      <div className="flex -space-x-1">
        {Array.from({ length: Math.min(peerCount, 8) }).map((_, i) => (
          <span
            key={`peer-${String(i)}`}
            className={`inline-block h-4 w-4 rounded-full border-2 border-white ${PEER_COLORS[i % PEER_COLORS.length]}`}
          />
        ))}
      </div>
      {peerCount > 0 && (
        <span className="text-xs text-gray-500">
          {String(peerCount)} peer{peerCount !== 1 ? "s" : ""}
        </span>
      )}
      <span className="inline-block h-2 w-2 rounded-full bg-green-500" />
    </div>
  );
}
