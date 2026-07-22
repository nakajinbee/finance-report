import type { FinancialRecord } from "../api/client";
import { formatYenForDisplay } from "../lib/formatCurrency";
import { getMetricValue, type MetricDefinition, type MetricKey } from "../lib/metrics";

type FinancialMetricTableProps = {
  records: FinancialRecord[];
  definitions: MetricDefinition[];
  activeMetrics: Set<MetricKey>;
};

export function FinancialMetricTable({ records, definitions, activeMetrics }: FinancialMetricTableProps) {
  const activeDefinitions = definitions.filter((metric) => activeMetrics.has(metric.key));
  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-max border-collapse text-sm">
        <thead>
          <tr>
            <th className="border border-gray-200 px-3 py-2 text-left"></th>
            {records.map((record) => (
              <th key={record.period_end} className="border border-gray-200 px-3 py-2 text-right font-medium">
                {record.fiscal_year}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {activeDefinitions.map((metric) => (
            <tr key={metric.key}>
              <td className="border border-gray-200 px-3 py-2 font-medium">{metric.label}</td>
              {records.map((record) => (
                <td key={record.period_end} className="border border-gray-200 px-3 py-2 text-right">
                  {formatYenForDisplay(getMetricValue(record, metric.key))}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
