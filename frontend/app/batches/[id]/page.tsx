"use client";
import { useEffect, useState } from "react";
import Link from "next/link";

const STATUS_LABEL: Record<string, string> = {
  pending: "⏳ 排队中",
  ocr_running: "🔍 OCR中",
  llm_running: "🧠 抽取中",
  done: "✅ 完成",
  failed: "❌ 失败",
};

export default function Page({ params }: { params: { id: string } }) {
  const [data, setData] = useState<any>(null);

  async function load() {
    const r = await fetch(`/api/batches/${params.id}`);
    setData(await r.json());
  }

  useEffect(() => {
    load();
    const es = new EventSource(`/api/batches/${params.id}/stream`);
    es.onmessage = () => load();
    return () => es.close();
  }, [params.id]);

  async function retry(did: number) {
    await fetch(`/api/documents/${did}/retry`, { method: "POST" });
    load();
  }

  async function retryAllFailed() {
    const failed = data.documents.filter((d: any) => d.status === "failed");
    await Promise.all(
      failed.map((d: any) =>
        fetch(`/api/documents/${d.id}/retry`, { method: "POST" })
      )
    );
    load();
  }

  if (!data) return <p style={{ padding: 20 }}>加载中…</p>;

  const total = data.documents.length;
  const done = data.documents.filter((d: any) => d.status === "done").length;
  const failed = data.documents.filter((d: any) => d.status === "failed").length;
  const inProgress = total - done - failed;
  const pct = total ? Math.round((done / total) * 100) : 0;

  return (
    <main style={{ maxWidth: 1100, margin: "30px auto", padding: 20 }}>
      <Link href="/">← 返回</Link>
      <h2>{data.name}</h2>
      <div style={{ margin: "10px 0", color: "#555" }}>
        总数 {total} | 完成 {done} | 进行中 {inProgress} | 失败 {failed}
      </div>
      <div style={{ background: "#eee", height: 12, borderRadius: 6, overflow: "hidden" }}>
        <div
          style={{
            width: `${pct}%`,
            height: "100%",
            background: "#22c55e",
            transition: "width .3s",
          }}
        />
      </div>

      <div style={{ margin: "16px 0" }}>
        {failed > 0 && (
          <button onClick={retryAllFailed} style={{ marginRight: 8 }}>
            一键重试失败项 ({failed})
          </button>
        )}
        {done > 0 && (
          <Link href={`/batches/${data.id}/review`}>
            <button style={{ background: "#111", color: "#fff", border: 0 }}>
              进入表格审阅 →
            </button>
          </Link>
        )}
      </div>

      <table>
        <thead>
          <tr>
            <th>文件</th>
            <th style={{ width: 110 }}>状态</th>
            <th style={{ width: 70 }}>重试</th>
            <th>错误</th>
            <th style={{ width: 80 }}></th>
          </tr>
        </thead>
        <tbody>
          {data.documents.map((d: any) => (
            <tr key={d.id}>
              <td>{d.filename}</td>
              <td>{STATUS_LABEL[d.status] ?? d.status}</td>
              <td>{d.retry_count}</td>
              <td style={{ color: "#c00", fontSize: 12 }}>{d.error}</td>
              <td>
                {d.status === "failed" && (
                  <button onClick={() => retry(d.id)}>重试</button>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </main>
  );
}
