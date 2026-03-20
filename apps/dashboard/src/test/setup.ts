import "@testing-library/jest-dom/vitest";

const originalConsoleError = console.error;
const originalConsoleWarn = console.warn;

function isIgnorableReactActWarning(parts: unknown[]): boolean {
	const text = parts.map((part) => String(part ?? "")).join(" ");
	return text.includes("not wrapped in act");
}

console.error = ((...args: unknown[]) => {
	if (isIgnorableReactActWarning(args)) {
		return;
	}
	originalConsoleError(...args);
}) as typeof console.error;

console.warn = ((...args: unknown[]) => {
	if (isIgnorableReactActWarning(args)) {
		return;
	}
	originalConsoleWarn(...args);
}) as typeof console.warn;
