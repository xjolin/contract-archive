"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";

export default function Home() {
  const [files, setFiles] = useState<File[]>([]);
  const [name, setName] = useState("");
  const [busy, setBusy] = useState(false);
  const [batches, setBatches] = useState<any[]>([]);
  const router = useRouter();

  async function loadBatches() {
    try {
      const r = await fetch("/api/batches");
      setBatches(await r.json());
    } catch {}
  }

  useEffect(() => {
    loadBatches();
  }, []);

  async function deleteBatch(id: number, name: string) {
    if (!confirm(`确认删除批次 "${name}" 及其全部记录？此操作不可恢复。`)) return;
    await fetch(`/api/batches/${id}`, { method: "DELETE" });
    loadBatches();
  }

  async function submit() {
    if (!name || files.length === 0) return;
    setBusy(true);
    const fd = new FormData();
    fd.append("name", name);
    files.forEach(f => fd.append("files", f));
    const res = await fetch("/api/batches", { method: "POST", body: fd });
    const { batch_id } = await res.json();
    router.push(`/batches/${batch_id}`);
  }

  return (
    <main style={{ maxWidth: 900, margin: "40px auto", padding: 20 }}>
      <h1>合同归档系统</h1>

      <section style={{ border: "1px solid #ddd", padding: 16, borderRadius: 6 }}>
        <h3>新建批次</h3>
        <input
          style={{ width: "100%", padding: 8, marginBottom: 12 }}
          placeholder="批次名称，如 2026年5月归档"
          value={name}
          onChange={e => setName(e.target.value)}
        />
        <input
          type="file"
          multiple
          accept="application/pdf"
          onChange={e => setFiles(Array.from(e.target.files ?? []))}
        />
        {files.length > 0 && (
          <ul style={{ fontSize: 13, color: "#555" }}>
            {files.map(f => <li key={f.name}>{f.name}</li>)}
          </ul>
        )}
        <button
          disabled={busy}
          onClick={submit}
          style={{ background: "#111", color: "#fff", border: 0, marginTop: 12 }}
        >
          {busy ? "提交中…" : "开始解析"}
        </button>
      </section>

      <section style={{ marginTop: 30 }}>
        <h3>历史批次</h3>
        {batches.length === 0 && <p style={{ color: "#888" }}>暂无</p>}
        <ul>
          {batches.map(b => (
            <li key={b.id} style={{ margin: "6px 0" }}>
              <Link href={`/batches/${b.id}`}>
                #{b.id} - {b.name}
              </Link>{" "}
              <span style={{ color: "#888", fontSize: 12 }}>
                {b.documents.length} 份 / {b.created_at?.slice(0, 16)}
              </span>{" "}
              <button
                onClick={() => deleteBatch(b.id, b.name)}
                style={{
                  marginLeft: 8,
                  fontSize: 12,
                  color: "#c00",
                  background: "none",
                  border: "1px solid #c00",
                  padding: "2px 8px",
                }}
              >
                删除
              </button>
            </li>
          ))}
        </ul>
      </section>
    </main>
  );
}
