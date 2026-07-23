import { Link } from "react-router-dom";

export function Header() {
  return (
    <header className="bg-brand">
      <div className="mx-auto flex max-w-5xl items-center justify-between px-8 py-4">
        <Link to="/companies" className="text-lg font-semibold text-white">
          企業会計情報
        </Link>
        <nav className="flex items-center gap-6">
          <Link to="/companies" className="text-sm text-brand-tint hover:text-white">
            企業一覧
          </Link>
          <Link to="/compare" className="text-sm text-brand-tint hover:text-white">
            企業比較
          </Link>
          <Link to="/ranking" className="text-sm text-brand-tint hover:text-white">
            ランキング
          </Link>
        </nav>
      </div>
    </header>
  );
}
