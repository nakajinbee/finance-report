import { formatByRatioFormat } from "../../lib/formatRatio";
import type { ComparisonRatioDatum, ComparisonRatioMetric } from "./ComparisonRatioChart";

type ComparisonRatioTableProps = {
  data: ComparisonRatioDatum[];
  metrics: ComparisonRatioMetric[];
  onCompanyClick: (code: string) => void;
};

export function ComparisonRatioTable({ data, metrics, onCompanyClick }: ComparisonRatioTableProps) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="bg-gray-50">
            <th className="border-b border-gray-200 px-3 py-2 text-left">指標</th>
            {data.map((datum) => (
              <th key={datum.code} className="border-b border-gray-200 px-3 py-2 text-right">
                <button
                  type="button"
                  onClick={() => onCompanyClick(datum.code)}
                  className="text-brand hover:text-brand-dark"
                >
                  {datum.name}
                </button>
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {metrics.map((metric) => (
            <tr key={metric.key}>
              <td className="border-b border-gray-200 px-3 py-2">{metric.label}</td>
              {data.map((datum) => (
                <td key={datum.code} className="border-b border-gray-200 px-3 py-2 text-right tabular-nums">
                  {formatByRatioFormat((datum[metric.key] ?? null) as number | null, metric.format)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
