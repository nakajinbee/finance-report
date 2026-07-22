import type { MetricDefinition, MetricKey } from "../lib/metrics";

type MetricSelectorProps = {
  definitions: MetricDefinition[];
  activeMetrics: Set<MetricKey>;
  onToggle: (key: MetricKey) => void;
};

export function MetricSelector({ definitions, activeMetrics, onToggle }: MetricSelectorProps) {
  return (
    <div className="flex flex-wrap gap-2">
      {definitions.map((metric) => {
        const isActive = activeMetrics.has(metric.key);
        return (
          <button
            key={metric.key}
            type="button"
            onClick={() => onToggle(metric.key)}
            className={`flex items-center gap-2 rounded border px-3 py-1.5 text-sm ${
              isActive ? "border-brand bg-brand-tint text-gray-900" : "border-gray-200 text-gray-400"
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
