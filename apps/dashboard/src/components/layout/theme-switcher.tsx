import { LaptopMinimal, MoonStar, Palette, SunMedium } from "lucide-react";
import { cn } from "@/lib/utils";
import { useUiStore } from "@/stores/ui-store";
import { THEMES, type ThemeMode } from "@/theme/themes";

const MODE_OPTIONS: Array<{
  value: ThemeMode;
  label: string;
  icon: typeof SunMedium;
}> = [
  { value: "light", label: "Light", icon: SunMedium },
  { value: "dark", label: "Dark", icon: MoonStar },
  { value: "system", label: "System", icon: LaptopMinimal },
];

export function ThemeSwitcher(): React.JSX.Element {
  const theme = useUiStore((state) => state.theme);
  const themeId = useUiStore((state) => state.themeId);
  const setTheme = useUiStore((state) => state.setTheme);
  const setThemeId = useUiStore((state) => state.setThemeId);

  return (
    <div className="flex items-center gap-2">
      <label htmlFor="theme-id" className="sr-only">
        Theme family
      </label>
      <div className="relative hidden sm:block">
        <Palette className="pointer-events-none absolute left-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-muted-foreground" />
        <select
          id="theme-id"
          value={themeId}
          onChange={(event) => setThemeId(event.target.value as (typeof THEMES)[number]["id"])}
          className="h-10 rounded-full border border-border bg-panel pl-9 pr-8 text-sm text-foreground shadow-[var(--theme-shadow-panel)] outline-none transition focus:border-border-strong focus:ring-4 focus:ring-ring/50"
        >
          {THEMES.map((themeOption) => (
            <option key={themeOption.id} value={themeOption.id}>
              {themeOption.label}
            </option>
          ))}
        </select>
      </div>

      <div className="flex items-center gap-1 rounded-full border border-border bg-panel px-1 py-1 shadow-[var(--theme-shadow-panel)] backdrop-blur-xl">
        {MODE_OPTIONS.map(({ value, label, icon: Icon }) => {
          const active = theme === value;

          return (
            <button
              key={value}
              type="button"
              onClick={() => setTheme(value)}
              className={cn(
                "flex h-8 w-8 items-center justify-center rounded-full text-muted-foreground transition-all hover:text-foreground",
                active && "bg-accent text-accent-foreground shadow-[var(--theme-shadow-floating)]",
              )}
              aria-label={`Use ${label.toLowerCase()} mode`}
              title={label}
            >
              <Icon className="h-4 w-4" />
            </button>
          );
        })}
      </div>
    </div>
  );
}