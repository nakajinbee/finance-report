import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { getDownloadStatus, startDownload, type DownloadStatus } from "../api/client";
import { ErrorMessage } from "../components/ErrorMessage";

const POLL_INTERVAL_MS = 1000;

const LOG_STATUS_ICON: Record<string, string> = {
  done: "✓",
  in_progress: "⏳",
  error: "✗",
  pending: "・",
};

export function DownloadPage() {
  const navigate = useNavigate();
  const [isDownloading, setIsDownloading] = useState(false);
  const [status, setStatus] = useState<DownloadStatus | null>(null);
  const [conflictError, setConflictError] = useState<string | null>(null);
  const pollTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    return () => {
      if (pollTimerRef.current) {
        clearInterval(pollTimerRef.current);
      }
    };
  }, []);

  function pollStatus() {
    pollTimerRef.current = setInterval(async () => {
      const result = await getDownloadStatus();
      if (!result.ok) {
        return;
      }
      setStatus(result.data);
      if (result.data.status === "done" || result.data.status === "error") {
        setIsDownloading(false);
        if (pollTimerRef.current) {
          clearInterval(pollTimerRef.current);
          pollTimerRef.current = null;
        }
      }
    }, POLL_INTERVAL_MS);
  }

  async function handleDownloadClick() {
    setConflictError(null);
    setIsDownloading(true);
    const result = await startDownload();
    if (!result.ok) {
      // 409: すでにダウンロードが進行中。実行中のジョブがあるのでポーリングは継続する
      setConflictError(result.error.message);
    }
    pollStatus();
  }

  const hasAtLeastOneSuccess = status?.logs.some((log) => log.status === "done") ?? false;
  const showCompanyListLink = status?.status === "done" && hasAtLeastOneSuccess;
  const showAllFailedMessage = status?.status === "error";

  return (
    <div className="mx-auto max-w-xl space-y-6 p-8">
      <h1 className="text-xl font-semibold">データ取得</h1>

      <div className="space-y-1 text-gray-700">
        <p>対象企業：リクルートホールディングス</p>
        <p>取得期間：直近5期分</p>
      </div>

      <button
        type="button"
        onClick={handleDownloadClick}
        disabled={isDownloading}
        className="rounded bg-blue-600 px-4 py-2 text-white disabled:bg-gray-300"
      >
        データを取得する
      </button>

      {conflictError && <ErrorMessage message={conflictError} />}

      {status && status.logs.length > 0 && (
        <div className="space-y-1 border-t pt-4">
          <p className="font-medium">取得ログ：</p>
          <ul className="space-y-1">
            {status.logs.map((log) => (
              <li key={log.fiscal_year}>
                {LOG_STATUS_ICON[log.status]} {log.fiscal_year} {log.message}
              </li>
            ))}
          </ul>
        </div>
      )}

      {showAllFailedMessage && (
        <ErrorMessage message="データの取得に失敗しました。再度お試しください。" />
      )}

      {showCompanyListLink && (
        <button
          type="button"
          onClick={() => navigate("/companies")}
          className="rounded border border-gray-300 px-4 py-2"
        >
          企業一覧へ
        </button>
      )}
    </div>
  );
}
