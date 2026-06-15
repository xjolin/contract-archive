"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";

type Stats = {
  this_week_usage: number;
  this_week_docs: number;
  weekly: { week: string; count: number }[];
};

export default function Home() {
  const [files, setFiles] = useState<File[]>([]);
  const [name, setName] = useState("");
  const [busy, setBusy] = useState(false);
  const [batches, setBatches] = useState<any[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);
  const [showBoard, setShowBoard] = useState(false);
  const router = useRouter();

  async function loadBatches() {
    try {
      const r = await fetch("/api/batches");
      setBatches(await r.json());
    } catch {}
  }

  async function loadStats() {
    try {
      const r = await fetch("/api/stats");
      setStats(await r.json());
    } catch {}
  }

  useEffect(() => {
    loadBatches();
    loadStats();
  }, []);

  async function deleteBatch(id: number, name: string) {
    if (!confirm(`确认删除批次 "${name}" 及其全部记录？此操作不可恢复。`)) return;
    await fetch(`/api/batches/${id}`, { method: "DELETE" });
    loadBatches();
    loadStats();
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
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          marginBottom: 20,
        }}
      >
        <h1 style={{ margin: 0, fontSize: 26 }}>合同归档系统</h1>
        <button onClick={() => setShowBoard(s => !s)}>
          📊 {showBoard ? "收起看板" : "数据看板"}
        </button>
      </div>

      {/* 顶部本周指标 */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "1fr 1fr",
          gap: 16,
          marginBottom: 20,
        }}
      >
        <StatCard
          label="本周使用次数"
          value={stats?.this_week_usage ?? "—"}
          hint="本周新建的批次数"
          accent="#2563eb"
        />
        <StatCard
          label="本周处理数量"
          value={stats?.this_week_docs ?? "—"}
          hint="本周已完成处理的文件数"
          accent="#22c55e"
        />
      </div>

      {/* 数据看板 */}
      {showBoard && <WeeklyBoard weekly={stats?.weekly ?? []} />}

      <section style={card}>
        <h3 style={cardTitle}>新建批次</h3>
        <input
          style={input}
          placeholder="批次名称，如 2026年5月归档"
          value={name}
          onChange={e => setName(e.target.value)}
        />
        <input
          type="file"
          multiple
          accept="application/pdf"
          onChange={e => {
            const selected = Array.from(e.target.files ?? []);
            if (selected.length > 20) {
              alert(`一次最多上传 20 份，你选择了 ${selected.length} 份，请分批上传。`);
              e.target.value = "";
              setFiles([]);
              return;
            }
            setFiles(selected);
          }}
        />
        {files.length > 0 && (
          <ul style={{ fontSize: 13, color: "var(--muted)", marginBottom: 0 }}>
            {files.map(f => <li key={f.name}>{f.name}</li>)}
          </ul>
        )}
        <div>
          <button
            className="btn-primary"
            disabled={busy || !name || files.length === 0}
            onClick={submit}
            style={{ marginTop: 14 }}
          >
            {busy ? "提交中…" : "开始解析"}
          </button>
        </div>
      </section>

      <section style={{ ...card, marginTop: 20 }}>
        <h3 style={cardTitle}>历史批次</h3>
        {batches.length === 0 && <p style={{ color: "var(--muted)" }}>暂无</p>}
        <ul style={{ listStyle: "none", padding: 0, margin: 0 }}>
          {batches.map(b => (
            <li
              key={b.id}
              style={{
                display: "flex",
                alignItems: "center",
                gap: 10,
                padding: "10px 0",
                borderBottom: "1px solid var(--border)",
              }}
            >
              <Link href={`/batches/${b.id}`} style={{ fontWeight: 500 }}>
                #{b.id} · {b.name}
              </Link>
              <span style={{ color: "var(--muted)", fontSize: 12 }}>
                {b.documents.length} 份 · {b.created_at?.slice(0, 16).replace("T", " ")}
              </span>
              <button
                onClick={() => deleteBatch(b.id, b.name)}
                style={{
                  marginLeft: "auto",
                  fontSize: 12,
                  color: "var(--danger)",
                  borderColor: "var(--danger)",
                  padding: "4px 10px",
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

function StatCard({
  label,
  value,
  hint,
  accent,
}: {
  label: string;
  value: number | string;
  hint: string;
  accent: string;
}) {
  return (
    <div style={{ ...card, padding: 18, borderTop: `3px solid ${accent}` }}>
      <div style={{ color: "var(--muted)", fontSize: 13 }}>{label}</div>
      <div style={{ fontSize: 34, fontWeight: 700, lineHeight: 1.2, marginTop: 4 }}>
        {value}
      </div>
      <div style={{ color: "var(--muted)", fontSize: 12, marginTop: 2 }}>{hint}</div>
    </div>
  );
}

function WeeklyBoard({ weekly }: { weekly: { week: string; count: number }[] }) {
  const max = Math.max(1, ...weekly.map(w => w.count));
  const total = weekly.reduce((s, w) => s + w.count, 0);
  return (
    <section style={{ ...card, marginBottom: 20 }}>
      <div
        style={{
          display: "flex",
          alignItems: "baseline",
          justifyContent: "space-between",
          marginBottom: 14,
        }}
      >
        <h3 style={{ ...cardTitle, marginBottom: 0 }}>每周处理文件数</h3>
        <span style={{ color: "var(--muted)", fontSize: 12 }}>
          近 {weekly.length} 周 · 合计 {total} 份（已忽略 test 批次）
        </span>
      </div>
      {weekly.length === 0 ? (
        <p style={{ color: "var(--muted)" }}>暂无数据</p>
      ) : (
        <div
          style={{
            display: "flex",
            alignItems: "flex-end",
            gap: 8,
            height: 160,
            paddingTop: 18,
          }}
        >
          {weekly.map(w => (
            <div
              key={w.week}
              style={{
                flex: 1,
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                height: "100%",
                justifyContent: "flex-end",
              }}
              title={`${w.week} 当周：${w.count} 份`}
            >
              <div style={{ fontSize: 11, color: "var(--muted)", marginBottom: 4 }}>
                {w.count}
              </div>
              <div
                style={{
                  width: "100%",
                  maxWidth: 36,
                  height: `${(w.count / max) * 100}%`,
                  minHeight: w.count > 0 ? 4 : 0,
                  background: "linear-gradient(180deg, #3b82f6, #2563eb)",
                  borderRadius: "4px 4px 0 0",
                  transition: "height .3s",
                }}
              />
              <div style={{ fontSize: 10, color: "var(--muted)", marginTop: 6 }}>
                {w.week.slice(5)}
              </div>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}

const card: React.CSSProperties = {
  background: "var(--card)",
  border: "1px solid var(--border)",
  borderRadius: 12,
  padding: 20,
  boxShadow: "0 1px 3px rgba(0,0,0,0.04)",
};

const cardTitle: React.CSSProperties = {
  margin: "0 0 14px",
  fontSize: 16,
};

const input: React.CSSProperties = {
  width: "100%",
  padding: "10px 12px",
  marginBottom: 12,
  border: "1px solid var(--border)",
  borderRadius: 8,
  fontSize: 14,
};
