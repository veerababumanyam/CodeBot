import { Terminal } from "xterm";
import { FitAddon } from "@xterm/addon-fit";
import { WebLinksAddon } from "@xterm/addon-web-links";

export interface TerminalSession {
  id: string;
  terminal: Terminal;
  fitAddon: FitAddon;
}

export class TerminalManager {
  private sessions: Map<string, TerminalSession> = new Map();
  private maxSessions = 5;

  createSession(id: string): TerminalSession {
    if (this.sessions.size >= this.maxSessions) {
      throw new Error(
        `Maximum terminal sessions (${String(this.maxSessions)}) reached`,
      );
    }

    const existing = this.sessions.get(id);
    if (existing) {
      return existing;
    }

    const terminal = new Terminal({
      theme: {
        background: "#1e1e1e",
        foreground: "#d4d4d4",
        cursor: "#aeafad",
        selectionBackground: "#264f78",
      },
      fontSize: 14,
      fontFamily: "'Fira Code', 'Cascadia Code', Menlo, monospace",
      cursorBlink: true,
      scrollback: 5000,
    });

    const fitAddon = new FitAddon();
    const webLinksAddon = new WebLinksAddon();

    terminal.loadAddon(fitAddon);
    terminal.loadAddon(webLinksAddon);

    const session: TerminalSession = { id, terminal, fitAddon };
    this.sessions.set(id, session);

    return session;
  }

  getSession(id: string): TerminalSession | undefined {
    return this.sessions.get(id);
  }

  destroySession(id: string): void {
    const session = this.sessions.get(id);
    if (session) {
      session.terminal.dispose();
      this.sessions.delete(id);
    }
  }

  destroyAll(): void {
    for (const [id] of this.sessions) {
      this.destroySession(id);
    }
  }

  fit(id: string): void {
    const session = this.sessions.get(id);
    if (session) {
      session.fitAddon.fit();
    }
  }
}
