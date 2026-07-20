import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { getCompanies, type Company } from "../api/client";
import { ErrorMessage } from "../components/ErrorMessage";
import { normalizeForSearch } from "../lib/kana";

type LoadState = "loading" | "loaded" | "error";

export function CompanyListPage() {
  const navigate = useNavigate();
  const [companies, setCompanies] = useState<Company[]>([]);
  const [loadState, setLoadState] = useState<LoadState>("loading");
  const [keyword, setKeyword] = useState("");

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

  const normalizedKeyword = normalizeForSearch(keyword);
  const filteredCompanies = companies
    .filter(
      (company) =>
        normalizeForSearch(company.name).includes(normalizedKeyword) ||
        normalizeForSearch(company.code).includes(normalizedKeyword),
    )
    .sort((a, b) => a.code.localeCompare(b.code));

  if (loadState === "loading") {
    return <p className="p-8">読み込み中...</p>;
  }

  if (loadState === "error") {
    return (
      <div className="p-8">
        <ErrorMessage message="データの取得に失敗しました。しばらくしてから再度お試しください。" />
      </div>
    );
  }

  if (companies.length === 0) {
    return (
      <div className="mx-auto max-w-xl space-y-4 p-8">
        <p>データがありません。まずデータを取得してください。</p>
        <button
          type="button"
          onClick={() => navigate("/download")}
          className="rounded border border-gray-300 px-4 py-2"
        >
          データを取得する
        </button>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-xl space-y-4 p-8">
      <h1 className="text-xl font-semibold">企業一覧</h1>

      <input
        type="text"
        value={keyword}
        onChange={(e) => setKeyword(e.target.value)}
        placeholder="企業名・証券コードで検索..."
        className="w-full rounded border border-gray-300 px-3 py-2"
      />

      <p className="text-sm text-gray-500">
        {companies.length}件中 {filteredCompanies.length}件表示
      </p>

      {filteredCompanies.length === 0 ? (
        <p>&quot;{keyword}&quot; に一致する企業が見つかりませんでした</p>
      ) : (
        <ul className="space-y-2">
          {filteredCompanies.map((company) => (
            <li key={company.code}>
              <button
                type="button"
                onClick={() => navigate(`/companies/${company.code}`)}
                className="w-full rounded border border-gray-200 px-4 py-3 text-left hover:bg-gray-50"
              >
                <p className="font-medium">{company.name}</p>
                <p className="text-sm text-gray-500">
                  {company.code} ｜ {company.sector ?? "業種不明"} ｜ {company.accounting_standard}
                </p>
              </button>
            </li>
          ))}
        </ul>
      )}

      <button
        type="button"
        onClick={() => navigate("/download")}
        className="rounded border border-gray-300 px-4 py-2"
      >
        データを追加取得する
      </button>
    </div>
  );
}
