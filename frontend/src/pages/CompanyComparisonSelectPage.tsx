import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { getCompanies, type Company } from "../api/client";
import { Button } from "../components/Button";
import { ErrorMessage } from "../components/ErrorMessage";
import { ALL_SECTORS, useCompanyFilter, type SortOrder } from "../lib/useCompanyFilter";

type LoadState = "loading" | "loaded" | "error";

// SCR-005 比較企業選択画面（サイクル15新規）。SCR-002と同じ検索・絞り込みUXを流用するが、
// カードのクリックは詳細画面への遷移ではなく比較対象への選択・解除として扱う。
export function CompanyComparisonSelectPage() {
  const navigate = useNavigate();
  const [companies, setCompanies] = useState<Company[]>([]);
  const [loadState, setLoadState] = useState<LoadState>("loading");
  const [selected, setSelected] = useState<Company[]>([]);
  const {
    keyword,
    setKeyword,
    sector,
    setSector,
    sortOrder,
    setSortOrder,
    sectorOptions,
    hasFilter,
    filteredCompanies,
  } = useCompanyFilter(companies);

  useEffect(() => {
    let cancelled = false;
    getCompanies().then((result) => {
      if (cancelled) {
        return;
      }
      if (result.ok) {
        setCompanies(result.data);
        setLoadState("loaded");
      } else {
        setLoadState("error");
      }
    });
    return () => {
      cancelled = true;
    };
  }, []);

  function toggleSelection(company: Company) {
    setSelected((current) => {
      if (current.some((c) => c.code === company.code)) {
        return current.filter((c) => c.code !== company.code);
      }
      return [...current, company];
    });
  }

  function removeSelection(code: string) {
    setSelected((current) => current.filter((c) => c.code !== code));
  }

  function goToCompare() {
    const codes = selected.map((c) => c.code).join(",");
    navigate(`/compare/result?codes=${encodeURIComponent(codes)}`);
  }

  if (loadState === "loading") {
    return <div className="flex justify-center py-16 text-gray-500">読み込み中...</div>;
  }

  if (loadState === "error") {
    return (
      <div className="mx-auto max-w-2xl p-8">
        <ErrorMessage message="データの取得に失敗しました。しばらくしてから再度お試しください。" />
      </div>
    );
  }

  if (companies.length === 0) {
    return (
      <div className="mx-auto max-w-2xl space-y-4 p-8">
        <p>データがありません。まずデータを取得してください。</p>
        <Button variant="secondary" onClick={() => navigate("/download")}>
          データを取得する
        </Button>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-2xl space-y-4 p-8">
      <h1 className="text-xl font-semibold">比較する企業を選ぶ</h1>

      <input
        type="text"
        value={keyword}
        onChange={(e) => setKeyword(e.target.value)}
        placeholder="企業名・証券コードで検索..."
        className="w-full rounded border border-gray-300 px-3 py-2 outline-none focus:border-brand focus:ring-2 focus:ring-brand/20"
      />

      <div className="flex gap-3">
        <select
          value={sector}
          onChange={(e) => setSector(e.target.value)}
          className="rounded border border-gray-300 px-3 py-2 outline-none focus:border-brand focus:ring-2 focus:ring-brand/20"
        >
          <option value={ALL_SECTORS}>業種：すべて</option>
          {sectorOptions.map((option) => (
            <option key={option} value={option}>
              {option}
            </option>
          ))}
        </select>

        <select
          value={sortOrder}
          onChange={(e) => setSortOrder(e.target.value as SortOrder)}
          className="rounded border border-gray-300 px-3 py-2 outline-none focus:border-brand focus:ring-2 focus:ring-brand/20"
        >
          <option value="code_asc">並び順：証券コード昇順</option>
          <option value="code_desc">並び順：証券コード降順</option>
          <option value="name_asc">並び順：企業名昇順</option>
          <option value="name_desc">並び順：企業名降順</option>
        </select>
      </div>

      {selected.length > 0 && (
        <div className="space-y-2 rounded-lg border border-gray-200 bg-gray-50 p-4">
          <p className="text-sm font-medium text-gray-900">選択中の企業（{selected.length}）</p>
          <ul className="space-y-1">
            {selected.map((company) => (
              <li key={company.code} className="flex items-center justify-between text-sm">
                <span>
                  {company.name}（{company.code}）
                </span>
                <button
                  type="button"
                  onClick={() => removeSelection(company.code)}
                  className="text-gray-400 hover:text-gray-600"
                  aria-label={`${company.name}を選択から外す`}
                >
                  ×
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}

      <Button variant="primary" disabled={selected.length === 0} onClick={goToCompare}>
        比較する
      </Button>

      {!hasFilter ? (
        <p className="text-sm text-gray-500">
          企業名・証券コードで検索するか、業種を選択してください
        </p>
      ) : filteredCompanies.length === 0 ? (
        <p>&quot;{keyword}&quot; に一致する企業が見つかりませんでした</p>
      ) : (
        <ul className="grid grid-cols-1 gap-3 xl:grid-cols-2">
          {filteredCompanies.map((company) => {
            const isSelected = selected.some((c) => c.code === company.code);
            return (
              <li key={company.code}>
                <button
                  type="button"
                  onClick={() => toggleSelection(company)}
                  className={`w-full rounded-lg border p-4 text-left shadow-sm ${
                    isSelected
                      ? "border-brand bg-brand-tint"
                      : "border-gray-200 bg-white hover:bg-gray-50"
                  }`}
                >
                  <p className="font-medium">
                    {isSelected ? "✓ " : "+ "}
                    {company.name}
                    {isSelected && "（選択済み）"}
                  </p>
                  <p className="text-sm text-gray-500">
                    {company.code} ｜ {company.sector ?? "業種不明"} ｜{" "}
                    {company.accounting_standard ?? "データ未取得"}
                  </p>
                </button>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
