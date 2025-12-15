import { useMemo, useState } from "react";
import { Ticket } from "../api/client";

interface Props {
  tickets: Ticket[];
  selectedId: string | null;
  onSelect: (id: string) => void;
  loading?: boolean;
}

export default function TicketList({ tickets, selectedId, onSelect, loading }: Props) {
  const [search, setSearch] = useState("");
  const [priority, setPriority] = useState<string>("todos");

  const filtered = useMemo(() => {
    return tickets.filter((t) => {
      const matchesSearch =
        t.subject.toLowerCase().includes(search.toLowerCase()) ||
        t.display_id.toLowerCase().includes(search.toLowerCase());
      const matchesPriority = priority === "todos" || t.priority === priority;
      return matchesSearch && matchesPriority;
    });
  }, [tickets, search, priority]);

  return (
    <div className="ticket-list">
      <div className="filters">
        <input
          type="text"
          placeholder="Buscar..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <select value={priority} onChange={(e) => setPriority(e.target.value)}>
          <option value="todos">Todas</option>
          <option value="Alta">Alta</option>
          <option value="Media">Media</option>
          <option value="Baja">Baja</option>
        </select>
      </div>
      {loading && <div className="muted small">Cargando...</div>}
      <div className="list">
        {filtered.map((t) => (
          <button
            key={t.id}
            className={`list-item ${selectedId === t.id ? "active" : ""}`}
            onClick={() => onSelect(t.id)}
          >
            <div className="list-title">
              <span className="muted small">INC-{t.display_id}</span>
              <span className="badge">{t.priority}</span>
            </div>
            <div className="list-subject">{t.subject}</div>
            <div className="list-meta">
              <span className="muted small">{t.status}</span>
              {t.service_name && <span className="muted small">{t.service_name}</span>}
            </div>
          </button>
        ))}
        {!filtered.length && <div className="muted small">Sin tickets</div>}
      </div>
    </div>
  );
}
