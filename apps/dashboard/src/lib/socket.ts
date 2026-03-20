import { io, type Socket } from "socket.io-client";

const BASE_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

const socketOptions = {
  autoConnect: false,
  transports: ["websocket", "polling"],
  reconnection: true,
  reconnectionAttempts: 10,
  reconnectionDelay: 1000,
} as any;

export const socket: Socket = io(BASE_URL, socketOptions);
export const pipelineSocket: Socket = socket;
export const agentSocket: Socket = socket;

export function connectSockets(token?: string): void {
  if (token) {
    socket.auth = { token };
  }

  if (!socket.connected) {
    socket.connect();
  }
}

export function disconnectSockets(): void {
  if (socket.connected) {
    socket.disconnect();
  }
}
