import { FormEvent, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { submitReview, validateReviewToken } from "../api/client";
import { useQuery } from "@tanstack/react-query";

export default function ExperienceReviewPage() {
  const [params] = useSearchParams();
  const token = params.get("token") || "";
  const [reason, setReason] = useState("Conforme");
  const [comment, setComment] = useState("");

  const validation = useQuery({
    queryKey: ["review-token", token],
    queryFn: () => validateReviewToken(token),
    enabled: Boolean(token)
  });

  const valid = validation.data?.valid;
  const ticketId = validation.data?.ticket_id;
  const disabled = !valid;

  const title = useMemo(() => {
    if (validation.isLoading) return "Validando enlace...";
    if (!valid) return "Enlace inválido o vencido";
    return `Feedback de atención (Ticket ${ticketId})`;
  }, [validation.isLoading, valid, ticketId]);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!token) return;
    await submitReview({ token, reason, comment });
    alert("¡Gracias por compartir tu experiencia!");
  };

  return (
    <div className="page auth-page">
      <div className="card auth-card">
        <h1>{title}</h1>
        {validation.isError && (
          <div className="error-box">No pudimos validar el enlace. Intenta de nuevo.</div>
        )}
        <form className="stack" onSubmit={handleSubmit}>
          <label className="stack">
            <span>Califica la experiencia</span>
            <select value={reason} onChange={(e) => setReason(e.target.value)} disabled={disabled}>
              <option value="Conforme">Conforme</option>
              <option value="No conforme">No conforme</option>
              <option value="Regular">Regular</option>
            </select>
          </label>
          <label className="stack">
            <span>Comentarios</span>
            <textarea
              rows={4}
              value={comment}
              onChange={(e) => setComment(e.target.value)}
              placeholder="¿Qué podríamos mejorar?"
              disabled={disabled}
            />
          </label>
          <button type="submit" className="primary" disabled={disabled}>
            Enviar
          </button>
        </form>
      </div>
    </div>
  );
}
