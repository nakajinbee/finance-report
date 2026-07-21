import type { FinancialRecord, RatioRecord } from "../api/client";
import { formatByRatioFormat } from "../lib/formatRatio";
import { getRatioValue, type RatioMetricDefinition } from "../lib/ratioCategories";

type RatioCategoryTableProps = {
  financialRecords: FinancialRecord[];
  ratioRecords: RatioRecord[];
  definitions: RatioMetricDefinition[];
};

export function RatioCategoryTable({ financialRecords, ratioRecords, definitions }: RatioCategoryTableProps) {
  const ratioByPeriod = new Map(ratioRecords.map((record) => [record.period_end, record]));

  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-max border-collapse text-sm">
        <thead>
          <tr>
            <th className="border border-gray-200 px-3 py-2 text-left"></th>
            {financialRecords.map((record) => (
              <th key={record.period_end} className="border border-gray-200 px-3 py-2 text-right font-medium">
                {record.fiscal_year}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {definitions.map((metric) => (
            <tr key={metric.key}>
              <td className="border border-gray-200 px-3 py-2 font-medium">{metric.label}</td>
              {financialRecords.map((record) => {
                const ratio = ratioByPeriod.get(record.period_end);
                const value = ratio ? getRatioValue(ratio, metric.key) : null;
                return (
                  <td key={record.period_end} className="border border-gray-200 px-3 py-2 text-right">
                    {formatByRatioFormat(value, metric.format)}
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
