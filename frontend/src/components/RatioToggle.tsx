type ToggleEntry = { key: string; label: string; color: string };

type RatioToggleProps = {
  entries: ToggleEntry[];
  activeKeys: Set<string>;
  onToggle: (key: string) => void;
};

export function RatioToggle({ entries, activeKeys, onToggle }: RatioToggleProps) {
  return (
    <div className="flex flex-wrap gap-2">
      {entries.map((entry) => {
        const isActive = activeKeys.has(entry.key);
        return (
          <button
            key={entry.key}
            type="button"
            onClick={() => onToggle(entry.key)}
            className={`flex items-center gap-2 rounded border px-3 py-1.5 text-sm ${
              isActive ? "border-gray-400 bg-gray-100" : "border-gray-200 text-gray-400"
            }`}
          >
            <span aria-hidden style={{ color: entry.color }}>
              ━
            </span>
            {entry.label}
          </button>
        );
      })}
    </div>
  );
}
