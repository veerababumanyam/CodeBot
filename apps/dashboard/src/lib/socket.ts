import { io, type Socket } from "socket.io-client";

const BASE_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export const pipelineSocket: Socket = io(`${BASE_URL}/pipeline`, {
  autoConnect: false,
  transports: ["websocket", "polling"],
  reconnection: true,
  reconnectionAttempts: 10,
  reconnectionDelay: 1000,
});

export const agentSocket: Socket = io(`${BASE_URL}/agents`, {
  autoConnect: false,
  transports: ["websocket", "polling"],
  reconnection: true,
  reconnectionAttempts: 10,
  reconnectionDelay: 1000,
});

export function connectSockets(token?: string): void {
  if (token) {
    pipelineSocket.auth = { token };
    agentSocket.auth = { token };
  }
  pipelineSocket.connect();
  agentSocket.connect();
}

export function disconnectSockets(): void {
  pipelineSocket.disconnect();
  agentSocket.disconnect();
}
