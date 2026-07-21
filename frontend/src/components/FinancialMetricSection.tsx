import { useState } from "react";
import type { FinancialRecord } from "../api/client";
import { FinancialChart } from "./FinancialChart";
import { MetricSelector } from "./MetricSelector";
import type { MetricDefinition, MetricKey } from "../lib/metrics";

type FinancialMetricSectionProps = {
  title: string;
  records: FinancialRecord[];
  definitions: MetricDefinition[];
};

export function FinancialMetricSection({ title, records, definitions }: FinancialMetricSectionProps) {
  const [activeMetrics, setActiveMetrics] = useState<Set<MetricKey>>(
    () => new Set(definitions.map((d) => d.key)),
  );

  function toggleMetric(key: MetricKey) {
    setActiveMetrics((current) => {
      const next = new Set(current);
      if (next.has(key)) {
        next.delete(key);
      } else {
        next.add(key);
      }
      return next;
    });
  }

  const hasAnyValue = records.some((record) => definitions.some((metric) => record[metric.key] !== null));

  return (
    <div className="space-y-2">
      <h2 className="font-medium">{title}</h2>
      <MetricSelector definitions={definitions} activeMetrics={activeMetrics} onToggle={toggleMetric} />
      {activeMetrics.size === 0 ? (
        <p className="text-gray-500">指標を1つ以上選択してください</p>
      ) : !hasAnyValue ? (
        <p className="text-gray-500">表示できるデータがありません</p>
      ) : (
        <FinancialChart records={records} definitions={definitions} activeMetrics={activeMetrics} />
      )}
    </div>
  );
}
