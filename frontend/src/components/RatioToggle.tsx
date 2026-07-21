import type { RatioKey, RatioMetricDefinition } from "../lib/ratioCategories";

type RatioToggleProps = {
  definitions: RatioMetricDefinition[];
  activeKeys: Set<RatioKey>;
  onToggle: (key: RatioKey) => void;
};

export function RatioToggle({ definitions, activeKeys, onToggle }: RatioToggleProps) {
  return (
    <div className="flex flex-wrap gap-2">
      {definitions.map((metric) => {
        const isActive = activeKeys.has(metric.key);
        return (
          <button
            key={metric.key}
            type="button"
            onClick={() => onToggle(metric.key)}
            className={`flex items-center gap-2 rounded border px-3 py-1.5 text-sm ${
              isActive ? "border-gray-400 bg-gray-100" : "border-gray-200 text-gray-400"
            }`}
          >
            <span aria-hidden style={{ color: metric.color }}>
              ━
            </span>
            {metric.label}
          </button>
        );
      })}
    </div>
  );
}
