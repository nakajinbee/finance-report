import { useState } from "react";
import type { Company } from "../api/client";
import { normalizeForSearch } from "./kana";

export type SortOrder = "code_asc" | "code_desc" | "name_asc" | "name_desc";
export const ALL_SECTORS = "すべて";

/** SCR-002・SCR-005共通の検索・業種絞り込み・並び順ロジック（サイクル14・15） */
export function useCompanyFilter(companies: Company[]) {
  const [keyword, setKeyword] = useState("");
  const [sector, setSector] = useState(ALL_SECTORS);
  const [sortOrder, setSortOrder] = useState<SortOrder>("code_asc");

  const sectorOptions = Array.from(
    new Set(
      companies
        .map((company) => company.sector)
        .filter((value): value is string => value !== null),
    ),
  ).sort((a, b) => a.localeCompare(b, "ja"));

  const hasFilter = keyword.trim() !== "" || sector !== ALL_SECTORS;

  const normalizedKeyword = normalizeForSearch(keyword);
  const filteredCompanies = companies
    .filter(
      (company) =>
        normalizeForSearch(company.name).includes(normalizedKeyword) ||
        normalizeForSearch(company.code).includes(normalizedKeyword),
    )
    .filter((company) => sector === ALL_SECTORS || company.sector === sector)
    .sort((a, b) => {
      if (sortOrder === "code_desc") {
        return b.code.localeCompare(a.code);
      }
      if (sortOrder === "name_asc") {
        return a.name.localeCompare(b.name, "ja");
      }
      if (sortOrder === "name_desc") {
        return b.name.localeCompare(a.name, "ja");
      }
      return a.code.localeCompare(b.code);
    });

  return {
    keyword,
    setKeyword,
    sector,
    setSector,
    sortOrder,
    setSortOrder,
    sectorOptions,
    hasFilter,
    filteredCompanies,
  };
}
