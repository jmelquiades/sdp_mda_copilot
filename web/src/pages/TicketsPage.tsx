import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  fetchTicketDetail,
  fetchTicketHistory,
  fetchTickets,
  generateIaReply,
  interpretConversation,
  sendReply,
  Ticket,
  TicketDetail,
  HistoryEvent
} from "../api/client";
import { useAuth } from "../context/AuthContext";
import TicketList from "../components/TicketList";

type MessageType = "primera_respuesta" | "actualizacion" | "cierre";

export default function TicketsPage() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [messageType, setMessageType] = useState<MessageType>("cierre");
  const [draft, setDraft] = useState("");
  const [suggested, setSuggested] = useState("");
  const [closeStatus, setCloseStatus] = useState<string | undefined>("Cerrado");
  const [replyMessage, setReplyMessage] = useState("");

  const ticketsQuery = useQuery<Ticket[]>({
    queryKey: ["tickets"],
    queryFn: fetchTickets
  });

  useEffect(() => {
    if (!selectedId && ticketsQuery.data?.length) {
      setSelectedId(ticketsQuery.data[0].id);
    }
  }, [ticketsQuery.data, selectedId]);

  const detailQuery = useQuery<TicketDetail>({
    queryKey: ["ticket-detail", selectedId],
    queryFn: () => fetchTicketDetail(selectedId || ""),
    enabled: Boolean(selectedId)
  });

  const historyQuery = useQuery<HistoryEvent[]>({
    queryKey: ["ticket-history", selectedId],
    queryFn: () => fetchTicketHistory(selectedId || ""),
    enabled: Boolean(selectedId)
  });

  const iaMutation = useMutation({
    mutationFn: () =>
      generateIaReply({
        ticketId: selectedId || "",
        messageType,
        draft,
        close_status: messageType === "cierre" ? closeStatus : undefined
      }),
    onSuccess: (data) => {
      setSuggested(data.suggested_message);
      setReplyMessage(data.suggested_message);
    }
  });

  const interpretMutation = useMutation({
    mutationFn: () => interpretConversation(selectedId || ""),
    onSuccess: (data) => {
      setSuggested(data.suggestion);
      setReplyMessage(data.suggestion);
    }
  });

  const sendReplyMutation = useMutation({
    mutationFn: () => sendReply(selectedId || "", { message: replyMessage }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["tickets"] });
      alert("Respuesta enviada al usuario.");
    }
  });

  const current = detailQuery.data;
  const slaDanger =
    current?.hours_since_last_user_contact != null &&
    current.communication_sla_hours != null &&
    current.hours_since_last_user_contact > current.communication_sla_hours;

  const statusBadge = useMemo(() => {
    if (!current) return null;
    const status = current.status?.toLowerCase();
    const className =
      status === "cerrado"
        ? "badge success"
        : status?.includes("pend") || status?.includes("hold")
        ? "badge warning"
      : "badge info";
    return <span className={className}>{current.status}</span>;
  }, [current]);

  const toPlainText = (value?: string) => {
    if (!value) return "";
    // Simplify HTML coming from SDP to readable plain text
    if (value.includes("<")) {
      const parser = new DOMParser();
      const doc = parser.parseFromString(value, "text/html");
      return doc.body.textContent || value;
    }
    return value;
  };

  const descriptionText = useMemo(() => toPlainText(current?.description), [current]);

  return (
    <div className="page layout">
      <header className="topbar">
        <div>
          <strong>Criteria ServiceDesk Copilot</strong>
          <span className="muted"> · Panel del técnico</span>
        </div>
        <div className="topbar-actions">
          {user && <span className="muted">Sesión: {user.display_name || user.user_upn}</span>}
          <button onClick={() => navigate("/experience/review")}>Token review</button>
          <button className="ghost" onClick={logout}>
            Salir
          </button>
        </div>
      </header>

      <div className="layout-grid">
        <aside className="panel">
          <div className="panel-header">
            <h2>Tickets</h2>
            <span className="muted small">Mis asignados</span>
          </div>
          <TicketList
            tickets={ticketsQuery.data || []}
            selectedId={selectedId}
            onSelect={setSelectedId}
            loading={ticketsQuery.isLoading}
          />
        </aside>

        <main className="panel main">
          {current ? (
            <div className="ticket-grid">
              <div className="card stretch">
                <div className="card-header">
                  <div>
                    <div className="muted small">INC-{current.display_id}</div>
                    <h2>{current.subject}</h2>
                  </div>
                  <div className="tags">
                    {statusBadge}
                    <span className="badge">{current.priority}</span>
                    {current.is_silent && <span className="badge danger">Silencio</span>}
                    {current.experience_review_requested && (
                      <span className="badge outline">Review</span>
                    )}
                  </div>
                </div>
                <div className="two-col">
                  <div className="stack">
                    <span className="muted small">Solicitante</span>
                    <strong>{current.requester?.name || "N/D"}</strong>
                    <span className="muted">{current.requester?.email_id}</span>
                    <span className="muted">{current.created_time || "sin fecha"}</span>
                  </div>
                  <div className="stack">
                    <span className="muted small">Servicio</span>
                    <strong>{current.service_name || current.service_code || "N/D"}</strong>
                    <span className="muted small">
                      SLA: {current.sla?.name || "N/A"} · objetivo{" "}
                      {current.communication_sla_hours ?? "-"}h
                    </span>
                    {slaDanger && <span className="badge danger">Riesgo de SLA</span>}
                  </div>
                </div>
                <div className="description">
                  <span className="muted small">Descripción</span>
                  <pre className="description-content">
                    {descriptionText || "Sin descripción"}
                  </pre>
                </div>
              </div>

              <div className="card stretch">
                <div className="card-header">
                  <h3>Conversación IA</h3>
                </div>
                <div className="form-grid">
                  <label className="stack">
                    <span>Tipo de mensaje</span>
                    <div className="pill-group">
                      {(["primera_respuesta", "actualizacion", "cierre"] as MessageType[]).map(
                        (t) => (
                          <button
                            key={t}
                            type="button"
                            className={messageType === t ? "pill active" : "pill"}
                            onClick={() => setMessageType(t)}
                          >
                            {t.replace("_", " ")}
                          </button>
                        )
                      )}
                    </div>
                  </label>
                  {messageType === "cierre" && (
                    <label className="stack">
                      <span>Cambiar estado al enviar</span>
                      <select
                        value={closeStatus}
                        onChange={(e) => setCloseStatus(e.target.value || undefined)}
                      >
                        <option value="Cerrado">Cerrado</option>
                        <option value="Resuelto">Resuelto</option>
                        <option value="">No cambiar</option>
                      </select>
                    </label>
                  )}
                  <label className="stack full">
                    <span>Intención de mensaje</span>
                    <textarea
                      rows={3}
                      placeholder="Notas para guiar a la IA"
                      value={draft}
                      onChange={(e) => setDraft(e.target.value)}
                    />
                  </label>
                  <div className="actions">
                    <button
                      type="button"
                      className="ghost"
                      onClick={() => interpretMutation.mutate()}
                      disabled={!selectedId || interpretMutation.isPending}
                    >
                      Interpretar conversación
                    </button>
                    <button
                      type="button"
                      className="primary"
                      onClick={() => iaMutation.mutate()}
                      disabled={!selectedId || iaMutation.isPending}
                    >
                      Generar con IA
                    </button>
                  </div>
                  <label className="stack full">
                    <span>Mensaje sugerido</span>
                    <textarea
                      rows={6}
                      value={replyMessage || suggested}
                      onChange={(e) => setReplyMessage(e.target.value)}
                      placeholder="Aquí verás la respuesta sugerida"
                    />
                  </label>
                  <div className="actions">
                    <button
                      type="button"
                      className="primary"
                      onClick={() => sendReplyMutation.mutate()}
                      disabled={!replyMessage || sendReplyMutation.isPending}
                    >
                      Enviar al usuario
                    </button>
                  </div>
                </div>
              </div>

              <div className="card stretch">
                <div className="card-header">
                  <h3>Historial</h3>
                  <span className="muted small">{historyQuery.data?.length || 0} eventos</span>
                </div>
                <div className="timeline">
                  {historyQuery.isLoading && <div className="muted">Cargando...</div>}
                  {historyQuery.data?.map((ev) => (
                    <div key={ev.event_id} className="timeline-item">
                  <div className="timeline-meta">
                    <span className="muted small">{ev.timestamp}</span>
                    <span className="badge outline">{ev.visibility || ev.type}</span>
                  </div>
                  <div className="timeline-body">
                    <strong>{ev.author_name || "N/D"}</strong>
                    <p className="timeline-text">{toPlainText(ev.text)}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
            </div>
          ) : (
            <div className="muted">Selecciona un ticket para ver el detalle.</div>
          )}
        </main>
      </div>
    </div>
  );
}
