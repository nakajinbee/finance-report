import type { CashFlowRecord, FinancialRecord } from "../api/client";
import { formatYenForDisplay } from "../lib/formatCurrency";

type CashFlowTableProps = {
  financialRecords: FinancialRecord[];
  cashFlowRecords: CashFlowRecord[];
};

const ROWS: { key: keyof Pick<CashFlowRecord, "operating_cash_flow" | "investing_cash_flow" | "financing_cash_flow">; label: string }[] = [
  { key: "operating_cash_flow", label: "営業CF" },
  { key: "investing_cash_flow", label: "投資CF" },
  { key: "financing_cash_flow", label: "財務CF" },
];

export function CashFlowTable({ financialRecords, cashFlowRecords }: CashFlowTableProps) {
  const cashFlowByPeriod = new Map(cashFlowRecords.map((record) => [record.period_end, record]));

  return (
    <div className="space-y-2">
      <h2 className="font-medium">キャッシュフロー計算書</h2>
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
                  const cashFlow = cashFlowByPeriod.get(record.period_end);
                  const value = cashFlow ? cashFlow[row.key] : null;
                  return (
                    <td key={record.period_end} className="border border-gray-200 px-3 py-2 text-right">
                      {formatYenForDisplay(value)}
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
