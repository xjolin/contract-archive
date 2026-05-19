"use client";
import { useEffect, useMemo, useState } from "react";
import Link from "next/link";

const FIELDS: [string, string][] = [
  ["合同类型", "合同类型"],
  ["项目序号", "项目序号"],
  ["合同名称", "合同名称"],
  ["合作方", "合作方"],
  ["甲方公司", "甲方公司"],
  ["乙方公司", "乙方公司"],
  ["合同年度", "合同年度"],
  ["项目编号", "项目编号"],
  ["合同金额", "合同金额"],
  ["合同币种", "合同币种"],
  ["合同期限", "合同期限"],
  ["违约金额/比例", "违约金额/比例"],
  ["审计条款", "审计条款"],
];

export default function Review({ params }: { params: { id: string } }) {
  const [data, setData] = useState<any>(null);
  const [dirty, setDirty] = useState<Record<number, any>>({});
  const [saving, setSaving] = useState(false);

  async function load() {
    const r = await fetch(`/api/batches/${params.id}`);
    setData(await r.json());
  }

  useEffect(() => {
    load();
  }, [params.id]);

  useEffect(() => {
    if (Object.keys(dirty).length === 0) return;
    const handler = (e: BeforeUnloadEvent) => {
      e.preventDefault();
      e.returnValue = "";
    };
    window.addEventListener("beforeunload", handler);
    return () => window.removeEventListener("beforeunload", handler);
  }, [dirty]);

  const rows = useMemo(
    () => (data?.documents ?? []).filter((d: any) => d.status === "done"),
    [data]
  );

  function setCell(docId: number, key: string, val: string) {
    setDirty(prev => {
      const base = prev[docId] ?? rows.find((r: any) => r.id === docId)?.extracted_json ?? {};
      return { ...prev, [docId]: { ...base, [key]: val } };
    });
  }

  async function save() {
    setSaving(true);
    await Promise.all(
      Object.entries(dirty).map(([id, body]) =>
        fetch(`/api/documents/${id}`, {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ extracted_json: body }),
        })
      )
    );
    setDirty({});
    await load();
    setSaving(false);
  }

  if (!data) return <p style={{ padding: 20 }}>加载中…</p>;

  return (
    <main style={{ maxWidth: 1500, margin: "20px auto", padding: 20 }}>
      <Link href={`/batches/${params.id}`}>← 返回批次</Link>
      <h2>表格审阅 - {data.name}</h2>
      <div style={{ margin: "10px 0", color: "#555" }}>
        共 {rows.length} 份成功记录，未保存修改 {Object.keys(dirty).length} 行
      </div>
      <div style={{ marginBottom: 12 }}>
        <button onClick={save} disabled={!Object.keys(dirty).length || saving}>
          {saving ? "保存中…" : "保存修改"}
        </button>{" "}
        <a href={`/api/batches/${params.id}/export.xlsx`}>
          <button>导出 Excel</button>
        </a>
      </div>
      <div style={{ overflow: "auto", border: "1px solid #ddd" }}>
        <table>
          <thead>
            <tr>
              {FIELDS.map(([k, l]) => (
                <th key={k} style={{ minWidth: 140 }}>{l}</th>
              ))}
              <th style={{ minWidth: 110 }}>归档时间</th>
              <th style={{ minWidth: 200 }}>文件名</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((d: any) => {
              const cur = dirty[d.id] ?? d.extracted_json ?? {};
              return (
                <tr key={d.id}>
                  {FIELDS.map(([k]) => {
                    const edited = dirty[d.id]?.[k] !== undefined;
                    return (
                      <td key={k} style={{ padding: 0 }}>
                        <input
                          value={cur[k] ?? ""}
                          onChange={e => setCell(d.id, k, e.target.value)}
                          style={{
                            border: "none",
                            width: "100%",
                            padding: "6px 10px",
                            outline: "none",
                            background: edited ? "#fff7cc" : "transparent",
                          }}
                        />
                      </td>
                    );
                  })}
                  <td>{(data.created_at ?? "").slice(0, 10)}</td>
                  <td>{d.filename}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </main>
  );
}
