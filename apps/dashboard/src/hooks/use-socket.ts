import { useEffect } from "react";
import { connectSockets, disconnectSockets } from "@/lib/socket";

export function useSocket(): void {
  useEffect(() => {
    connectSockets();
    return () => {
      disconnectSockets();
    };
  }, []);
}
