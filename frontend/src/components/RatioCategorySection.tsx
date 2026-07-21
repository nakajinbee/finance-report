import { useState } from "react";
import type { FinancialRecord, RatioRecord } from "../api/client";
import { getRatioValue, type RatioKey, type RatioMetricDefinition } from "../lib/ratioCategories";
import { RatioCategoryChart } from "./RatioCategoryChart";
import { RatioCategoryTable } from "./RatioCategoryTable";
import { RatioToggle } from "./RatioToggle";

type RatioCategorySectionProps = {
  title: string;
  financialRecords: FinancialRecord[];
  ratioRecords: RatioRecord[];
  definitions: RatioMetricDefinition[];
};

export function RatioCategorySection({ title, financialRecords, ratioRecords, definitions }: RatioCategorySectionProps) {
  const [activeKeys, setActiveKeys] = useState<Set<RatioKey>>(() => new Set(definitions.map((d) => d.key)));

  function toggle(key: RatioKey) {
    setActiveKeys((current) => {
      const next = new Set(current);
      if (next.has(key)) {
        next.delete(key);
      } else {
        next.add(key);
      }
      return next;
    });
  }

  const hasAnyValue = ratioRecords.some((record) => definitions.some((metric) => getRatioValue(record, metric.key) !== null));

  return (
    <div className="space-y-2">
      <h3 className="font-medium">{title}</h3>
      <RatioToggle definitions={definitions} activeKeys={activeKeys} onToggle={toggle} />
      {activeKeys.size === 0 ? (
        <p className="text-gray-500">指標を1つ以上選択してください</p>
      ) : !hasAnyValue ? (
        <p className="text-gray-500">表示できるデータがありません</p>
      ) : (
        <RatioCategoryChart records={ratioRecords} definitions={definitions} activeKeys={activeKeys} />
      )}
      <RatioCategoryTable financialRecords={financialRecords} ratioRecords={ratioRecords} definitions={definitions} />
    </div>
  );
}
