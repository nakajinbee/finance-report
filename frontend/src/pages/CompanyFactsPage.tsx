import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { getCompanyFacts, type FactRecord } from "../api/client";
import { ErrorMessage } from "../components/ErrorMessage";
import { Panel } from "../components/Panel";

type LoadState = "loading" | "loaded" | "error";

const SEARCH_DEBOUNCE_MS = 300;

const DOC_TYPE_LABELS: Record<string, string> = {
  "120": "年次",
  "160": "半期",
};

export function CompanyFactsPage() {
  const { code } = useParams<{ code: string }>();
  const navigate = useNavigate();

  const [loadState, setLoadState] = useState<LoadState>("loading");
  const [facts, setFacts] = useState<FactRecord[]>([]);
  const [availablePeriods, setAvailablePeriods] = useState<string[]>([]);
  const [elementIdFilter, setElementIdFilter] = useState("");
  const [periodFilter, setPeriodFilter] = useState("");

  // 初回ロード：絞り込みなしの全件から期間セレクタの選択肢を作る
  useEffect(() => {
    if (!code) {
      return;
    }
    let cancelled = false;
    getCompanyFacts(code).then((result) => {
      if (cancelled) {
        return;
      }
      if (result.ok) {
        setAvailablePeriods(
          Array.from(new Set(result.data.map((f) => f.period_end)))
            .sort()
            .reverse(),
        );
      }
    });
    return () => {
      cancelled = true;
    };
  }, [code]);

  // 絞り込み条件が変わるたびにサーバーへ問い合わせる
  useEffect(() => {
    if (!code) {
      return;
    }
    let cancelled = false;
    const timer = setTimeout(async () => {
      const result = await getCompanyFacts(
        code,
        elementIdFilter.trim() === "" ? undefined : elementIdFilter.trim(),
        periodFilter === "" ? undefined : periodFilter,
      );
      if (cancelled) {
        return;
      }
      if (result.ok) {
        setFacts(result.data);
        setLoadState("loaded");
      } else {
        setLoadState("error");
      }
    }, SEARCH_DEBOUNCE_MS);
    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
  }, [code, elementIdFilter, periodFilter]);

  if (loadState === "loading") {
    return (
      <div className="flex justify-center py-16 text-gray-500">
        読み込み中...
      </div>
    );
  }

  if (loadState === "error") {
    return (
      <div className="mx-auto max-w-2xl p-8">
        <ErrorMessage message="データの取得に失敗しました。しばらくしてから再度お試しください。" />
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-6xl space-y-4 p-8">
      <button
        type="button"
        onClick={() => navigate(`/companies/${code}`)}
        className="text-sm text-gray-500"
      >
        ← 企業詳細へ
      </button>

      <h1 className="text-xl font-semibold">保存済みデータ</h1>

      <Panel className="space-y-4">
        <div className="flex flex-wrap items-center gap-3">
          <input
            type="text"
            value={elementIdFilter}
            onChange={(e) => setElementIdFilter(e.target.value)}
            placeholder="要素IDで絞り込み..."
            className="min-w-64 rounded border border-gray-300 px-3 py-2 outline-none focus:border-brand focus:ring-2 focus:ring-brand/20"
          />
          <label className="flex items-center gap-2">
            期間：
            <select
              value={periodFilter}
              onChange={(e) => setPeriodFilter(e.target.value)}
              className="rounded border border-gray-300 px-2 py-1 outline-none focus:border-brand focus:ring-2 focus:ring-brand/20"
            >
              <option value="">すべて</option>
              {availablePeriods.map((period) => (
                <option key={period} value={period}>
                  {period}
                </option>
              ))}
            </select>
          </label>
        </div>

        {facts.length === 0 ? (
          <p className="text-gray-500">
            {elementIdFilter || periodFilter
              ? "条件に一致するデータが見つかりませんでした"
              : "データがありません"}
          </p>
        ) : (
          <>
            <p className="text-sm text-gray-500">{facts.length}件表示</p>
            <div className="overflow-x-auto rounded-md border border-gray-200">
              <table className="w-full min-w-max border-collapse text-sm">
                <thead>
                  <tr className="bg-gray-50">
                    <th className="border border-gray-200 px-3 py-2 text-left">
                      要素ID
                    </th>
                    <th className="border border-gray-200 px-3 py-2 text-left">
                      項目名
                    </th>
                    <th className="border border-gray-200 px-3 py-2 text-left">
                      書類種別
                    </th>
                    <th className="border border-gray-200 px-3 py-2 text-left">
                      期間
                    </th>
                    <th className="border border-gray-200 px-3 py-2 text-left">
                      連結個別
                    </th>
                    <th className="border border-gray-200 px-3 py-2 text-right">
                      値
                    </th>
                    <th className="border border-gray-200 px-3 py-2 text-left">
                      単位
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {facts.map((fact, i) => (
                    <tr
                      key={`${fact.element_id}-${fact.context_id}-${fact.period_end}-${i}`}
                    >
                      <td className="border border-gray-200 px-3 py-2 font-mono text-xs">
                        {fact.element_id}
                      </td>
                      <td className="border border-gray-200 px-3 py-2">
                        {fact.element_name ?? "-"}
                      </td>
                      <td className="border border-gray-200 px-3 py-2">
                        {DOC_TYPE_LABELS[fact.doc_type_code] ??
                          fact.doc_type_code}
                      </td>
                      <td className="border border-gray-200 px-3 py-2">
                        {fact.period_end}
                      </td>
                      <td className="border border-gray-200 px-3 py-2">
                        {fact.consolidated_or_individual ?? "-"}
                      </td>
                      <td className="border border-gray-200 px-3 py-2 text-right">
                        {fact.value.toLocaleString()}
                      </td>
                      <td className="border border-gray-200 px-3 py-2">
                        {fact.unit ?? "-"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        )}
      </Panel>
    </div>
  );
}
