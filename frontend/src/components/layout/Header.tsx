import { Link } from "react-router-dom";

export function Header() {
  return (
    <header className="bg-brand-dark">
      <div className="mx-auto flex max-w-5xl items-center justify-between px-8 py-4">
        <Link to="/companies" className="text-lg font-semibold text-white">
          企業会計情報
        </Link>
        <Link
          to="/companies"
          className="text-sm text-brand-light hover:text-white"
        >
          企業一覧
        </Link>
      </div>
    </header>
  );
}
