import { Link } from "react-router-dom";

export function Header() {
  return (
    <header className="border-b border-gray-200 bg-white">
      <div className="mx-auto flex max-w-5xl items-center justify-between px-8 py-4">
        <Link to="/companies" className="text-lg font-semibold text-gray-900">
          企業会計情報
        </Link>
        <Link to="/companies" className="text-sm text-gray-500 hover:text-brand">
          企業一覧
        </Link>
      </div>
    </header>
  );
}
