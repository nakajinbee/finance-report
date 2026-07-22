import { Fragment } from "react";
import type { FinancialRecord, RatioRecord } from "../api/client";
import { formatYenForDisplay } from "../lib/formatCurrency";
import { formatByRatioFormat } from "../lib/formatRatio";
import { getComponentValue, getRatioValue, type RatioMetricDefinition } from "../lib/ratioCategories";

type RatioCategoryTableProps = {
  financialRecords: FinancialRecord[];
  ratioRecords: RatioRecord[];
  definitions: RatioMetricDefinition[];
  activeKeys: Set<string>;
};

export function RatioCategoryTable({ financialRecords, ratioRecords, definitions, activeKeys }: RatioCategoryTableProps) {
  const ratioByPeriod = new Map(ratioRecords.map((record) => [record.period_end, record]));
  const financialByPeriod = new Map(financialRecords.map((record) => [record.period_end, record]));
  // 選択中の指標のみ表示する（グラフの選択状態と一致させる、ユーザー要望）
  const activeDefinitions = definitions.filter((metric) => activeKeys.has(metric.key));
  // 同じ生の金額が複数の指標で使われても、カテゴリ内で最初に登場した指標の直前にだけ表示する
  const shownComponentKeys = new Set<string>();

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
          {activeDefinitions.map((metric) => {
            const newComponents = (metric.components ?? []).filter((component) => {
              if (shownComponentKeys.has(component.key)) {
                return false;
              }
              shownComponentKeys.add(component.key);
              return true;
            });

            return (
              <Fragment key={metric.key}>
                <tr>
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
                {newComponents.map((component) => (
                  <tr key={component.key} className="text-gray-500">
                    <td className="border border-gray-200 px-3 py-2 pl-6">{component.label}</td>
                    {financialRecords.map((record) => {
                      const financial = financialByPeriod.get(record.period_end);
                      const ratio = ratioByPeriod.get(record.period_end);
                      const value = getComponentValue(financial, ratio, component);
                      return (
                        <td key={record.period_end} className="border border-gray-200 px-3 py-2 text-right">
                          {formatYenForDisplay(value)}
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </Fragment>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
