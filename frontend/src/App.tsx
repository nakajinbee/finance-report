import { useEffect, useState } from "react";
import { Navigate, Route, BrowserRouter as Router, Routes } from "react-router-dom";
import { getCompanies } from "./api/client";
import { CompanyDetailPage } from "./pages/CompanyDetailPage";
import { CompanyListPage } from "./pages/CompanyListPage";
import { DownloadPage } from "./pages/DownloadPage";

// 起動時：DBが空なら/downloadへ、データがあれば/companiesへリダイレクトする(SCR-001「初期遷移」)
function AppEntry() {
  const [destination, setDestination] = useState<"/download" | "/companies" | null>(null);

  useEffect(() => {
    getCompanies().then((result) => {
      setDestination(result.ok && result.data.length > 0 ? "/companies" : "/download");
    });
  }, []);

  if (destination === null) {
    return <p className="p-8">読み込み中...</p>;
  }
  return <Navigate to={destination} replace />;
}

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<AppEntry />} />
        <Route path="/download" element={<DownloadPage />} />
        <Route path="/companies" element={<CompanyListPage />} />
        <Route path="/companies/:code" element={<CompanyDetailPage />} />
      </Routes>
    </Router>
  );
}

export default App
