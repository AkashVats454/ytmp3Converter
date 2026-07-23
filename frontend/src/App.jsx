import React, { useEffect, useMemo, useState } from 'react';

const API_BASE = '/api/v1';

function App() {
  const [url, setUrl] = useState('');
  const [retentionMinutes, setRetentionMinutes] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState(null);
  const [deleting, setDeleting] = useState(false);
  const [countdown, setCountdown] = useState('');

  const urlIsFilled = url.trim().length > 0;
  const canConvert = urlIsFilled && retentionMinutes !== '';

  useEffect(() => {
    if (!result?.auto_delete_after_minutes) {
      setCountdown('');
      return undefined;
    }

    const expiresAt = Date.now() + Number(result.auto_delete_after_minutes) * 60 * 1000;
    const tick = () => {
      const remainingMs = expiresAt - Date.now();
      if (remainingMs <= 0) {
        setCountdown('Auto-delete in 00:00');
        return;
      }

      const totalSeconds = Math.max(0, Math.floor(remainingMs / 1000));
      const minutes = String(Math.floor(totalSeconds / 60)).padStart(2, '0');
      const seconds = String(totalSeconds % 60).padStart(2, '0');
      setCountdown(`Auto-delete in ${minutes}:${seconds}`);
    };

    tick();
    const intervalId = window.setInterval(tick, 1000);
    return () => window.clearInterval(intervalId);
  }, [result]);

  const downloadHref = useMemo(() => {
    if (!result?.download_url) return '';
    return result.download_url.startsWith('http')
      ? result.download_url
      : `${API_BASE}/download/${encodeURIComponent(result.file_name)}`;
  }, [result]);

  async function handleConvert(e) {
    e.preventDefault();
    setLoading(true);
    setError('');
    setResult(null);

    try {
      const response = await fetch(`${API_BASE}/convert`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url, retention_minutes: Number(retentionMinutes) }),
      });

      const payload = await response.json();

      if (!response.ok) {
        throw new Error(payload.detail || 'Unable to convert this YouTube URL');
      }

      setResult(payload);
      setCountdown('');
    } catch (err) {
      setError(err.message || 'Something went wrong');
    } finally {
      setLoading(false);
    }
  }

  async function handleDelete() {
    if (!result?.file_name) return;

    setDeleting(true);
    try {
      const response = await fetch(`${API_BASE}/download/${encodeURIComponent(result.file_name)}`, {
        method: 'DELETE',
      });

      const payload = await response.json();
      if (!response.ok) {
        throw new Error(payload.detail || 'Unable to delete the file');
      }

      setResult(null);
      setError('');
      setUrl('');
      setRetentionMinutes('');
      setCountdown('');
    } catch (err) {
      setError(err.message || 'Unable to delete the file');
    } finally {
      setDeleting(false);
    }
  }

  return (
    <div className="app-shell">
      <div className="card">
        <div className="brand-row">
          <span className="brand-badge">YTMp3Downloader</span>
          <h1 className="title">Download MP3 from YouTube</h1>
          <p className="subtitle">Convert a supported YouTube link into an MP3 file and save it in seconds.</p>
        </div>

        <div className="info-panel">
          <h2>About</h2>
          <p>
            This app lets you paste a YouTube URL, convert the audio to MP3, and download the result from the browser.
            After the file is downloaded, you can confirm the download completed and remove the local copy from the server.
          </p>
        </div>

        <div className="steps-panel">
          <h3>How it works</h3>
          <ol>
            <li>Enter a YouTube video URL.</li>
            <li>Click <strong>Convert to MP3</strong>.</li>
            <li>Use the download link to save the file.</li>
            <li>Click <strong>Confirm download completed</strong> to delete the local copy.</li>
          </ol>
        </div>

        <form onSubmit={handleConvert} className="convert-form">
          <label htmlFor="youtubeUrl">YouTube URL</label>
          <input
            id="youtubeUrl"
            type="url"
            placeholder="https://youtu.be/..."
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            required
          />

          <label htmlFor="retentionMinutes">Auto-delete after</label>
          <select
            id="retentionMinutes"
            value={retentionMinutes}
            onChange={(e) => setRetentionMinutes(e.target.value)}
            disabled={!urlIsFilled}
          >
            <option value="">Choose 1–5 minutes</option>
            <option value="1">1 minute</option>
            <option value="2">2 minutes</option>
            <option value="3">3 minutes</option>
            <option value="4">4 minutes</option>
            <option value="5">5 minutes</option>
          </select>

          <button type="submit" disabled={loading || !canConvert}>
            {loading ? 'Converting...' : 'Convert to MP3'}
          </button>
        </form>

        {error && <div className="message error">{error}</div>}

        {result && (
          <div className="result-box">
            <div className="result-row">
              <strong>File:</strong>
              <span>{result.file_name}</span>
            </div>
            <div className="result-row">
              <strong>Auto-delete:</strong>
              <span>{result.auto_delete_after_minutes} minute(s) if not confirmed</span>
            </div>
            {countdown && <div className="countdown-box">{countdown}</div>}
            <div className="result-actions">
              <a
                className="download-link"
                href={downloadHref}
                download={result.file_name}
                rel="noopener noreferrer"
              >
                Download MP3
              </a>
              <button className="ghost-button" onClick={handleDelete} disabled={deleting}>
                {deleting ? 'Deleting...' : 'Confirm download completed'}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
