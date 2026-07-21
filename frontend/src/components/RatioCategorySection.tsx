import { useMemo, useState } from "react";
import type { FinancialRecord, RatioRecord } from "../api/client";
import {
  buildCategoryChartEntries,
  type RatioMetricDefinition,
} from "../lib/ratioCategories";
import { Panel } from "./Panel";
import { RatioCategoryChart } from "./RatioCategoryChart";
import { RatioCategoryTable } from "./RatioCategoryTable";
import { RatioToggle } from "./RatioToggle";

type RatioCategorySectionProps = {
  title: string;
  financialRecords: FinancialRecord[];
  ratioRecords: RatioRecord[];
  definitions: RatioMetricDefinition[];
};

export function RatioCategorySection({
  title,
  financialRecords,
  ratioRecords,
  definitions,
}: RatioCategorySectionProps) {
  const entries = useMemo(
    () => buildCategoryChartEntries(definitions),
    [definitions],
  );

  // 初期表示は指標本体（ROE等）のみ選択状態にし、内訳（純利益・自己資本等）は非選択にする
  // （ユーザー要望、2026-07-22。内訳は見たい人だけトグルで表示する）
  const [activeKeys, setActiveKeys] = useState<Set<string>>(
    () =>
      new Set(
        entries.filter((entry) => !entry.isComponent).map((entry) => entry.key),
      ),
  );

  function toggle(key: string) {
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

  const hasAnyValue = entries.some((entry) =>
    ratioRecords.some((ratio) => {
      const financial = financialRecords.find(
        (r) => r.period_end === ratio.period_end,
      );
      return entry.getChartValue(financial, ratio) !== null;
    }),
  );

  return (
    <Panel className="space-y-2">
      <h3 className="font-medium">{title}</h3>
      <RatioToggle
        entries={entries}
        activeKeys={activeKeys}
        onToggle={toggle}
      />
      {activeKeys.size === 0 ? (
        <p className="text-gray-500">指標を1つ以上選択してください</p>
      ) : !hasAnyValue ? (
        <p className="text-gray-500">表示できるデータがありません</p>
      ) : (
        <RatioCategoryChart
          financialRecords={financialRecords}
          ratioRecords={ratioRecords}
          entries={entries}
          activeKeys={activeKeys}
        />
      )}
      <RatioCategoryTable
        financialRecords={financialRecords}
        ratioRecords={ratioRecords}
        definitions={definitions}
      />
    </Panel>
  );
}
