import type { FinancialRecord, RatioRecord } from "../api/client";
import { formatNumberForDisplay, formatPercentForDisplay, formatTurnoverForDisplay } from "../lib/formatRatio";

type RatioSectionProps = {
  financialRecords: FinancialRecord[];
  ratioRecords: RatioRecord[];
};

type RatioKey = Exclude<keyof RatioRecord, "fiscal_year" | "period_end">;

const ROWS: { key: RatioKey; label: string; format: (value: number | null) => string }[] = [
  { key: "roe", label: "ROE（自己資本利益率）", format: formatPercentForDisplay },
  { key: "equity_ratio", label: "自己資本比率", format: formatPercentForDisplay },
  { key: "eps", label: "EPS（1株当たり当期純利益）", format: formatNumberForDisplay },
  { key: "per", label: "PER（株価収益率）", format: formatNumberForDisplay },
  { key: "payout_ratio", label: "配当性向", format: formatPercentForDisplay },
  { key: "roa", label: "ROA（総資産利益率）", format: formatPercentForDisplay },
  { key: "total_asset_turnover", label: "総資産回転率", format: formatTurnoverForDisplay },
  { key: "operating_margin", label: "売上高営業利益率", format: formatPercentForDisplay },
  { key: "net_margin", label: "売上高純利益率", format: formatPercentForDisplay },
  { key: "current_ratio", label: "流動比率", format: formatPercentForDisplay },
  { key: "fixed_ratio", label: "固定比率", format: formatPercentForDisplay },
  { key: "inventory_turnover", label: "棚卸資産回転率", format: formatTurnoverForDisplay },
];

export function RatioSection({ financialRecords, ratioRecords }: RatioSectionProps) {
  const ratioByPeriod = new Map(ratioRecords.map((record) => [record.period_end, record]));

  return (
    <div className="space-y-2">
      <h2 className="font-medium">財務分析指標</h2>
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
            {ROWS.map((row) => (
              <tr key={row.key}>
                <td className="border border-gray-200 px-3 py-2 font-medium">{row.label}</td>
                {financialRecords.map((record) => {
                  const ratio = ratioByPeriod.get(record.period_end);
                  const value = ratio ? ratio[row.key] : null;
                  return (
                    <td key={record.period_end} className="border border-gray-200 px-3 py-2 text-right">
                      {row.format(value)}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
