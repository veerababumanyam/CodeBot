import { create } from "zustand";
import { socket } from "@/lib/socket";
import type { Socket } from "socket.io-client";

interface SocketState {
  socket: Socket;
  isConnected: boolean;
  setConnected: (connected: boolean) => void;
}

export const useSocketStore = create<SocketState>((set) => ({
  socket: socket,
  isConnected: socket.connected,
  setConnected: (connected) => set({ isConnected: connected }),
}));

// Setup connection listeners
socket.on("connect", () => {
  useSocketStore.getState().setConnected(true);
});

socket.on("disconnect", () => {
  useSocketStore.getState().setConnected(false);
});
