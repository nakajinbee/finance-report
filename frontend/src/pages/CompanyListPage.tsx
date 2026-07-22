import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { getCompanies, type Company } from "../api/client";
import { Button } from "../components/Button";
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
      <h1 className="text-xl font-semibold">企業一覧</h1>

      <input
        type="text"
        value={keyword}
        onChange={(e) => setKeyword(e.target.value)}
        placeholder="企業名・証券コードで検索..."
        className="w-full rounded border border-gray-300 px-3 py-2 outline-none focus:border-brand focus:ring-2 focus:ring-brand/20"
      />

      <p className="text-sm text-gray-500">
        {companies.length}件中 {filteredCompanies.length}件表示
      </p>

      {filteredCompanies.length === 0 ? (
        <p>&quot;{keyword}&quot; に一致する企業が見つかりませんでした</p>
      ) : (
        <ul className="grid grid-cols-1 gap-3 xl:grid-cols-2">
          {filteredCompanies.map((company) => (
            <li key={company.code}>
              <button
                type="button"
                onClick={() => navigate(`/companies/${company.code}`)}
                className="w-full rounded-lg border border-gray-200 bg-white p-4 text-left shadow-sm hover:bg-gray-50"
              >
                <p className="font-medium">{company.name}</p>
                <p className="text-sm text-gray-500">
                  {company.code} ｜ {company.sector ?? "業種不明"} ｜{" "}
                  {company.accounting_standard ?? "データ未取得"}
                </p>
              </button>
            </li>
          ))}
        </ul>
      )}

      <Button variant="secondary" onClick={() => navigate("/download")}>
        データを追加取得する
      </Button>
    </div>
  );
}
