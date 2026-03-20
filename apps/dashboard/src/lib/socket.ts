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
export const pipelineSocket: Socket = io(`${BASE_URL}/pipeline`, socketOptions);
export const agentSocket: Socket = io(`${BASE_URL}/agents`, socketOptions);

export function connectSockets(token?: string): void {
  if (token) {
    socket.auth = { token };
    pipelineSocket.auth = { token };
    agentSocket.auth = { token };
  }
  socket.connect();
  pipelineSocket.connect();
  agentSocket.connect();
}

export function disconnectSockets(): void {
  socket.disconnect();
  pipelineSocket.disconnect();
  agentSocket.disconnect();
}
