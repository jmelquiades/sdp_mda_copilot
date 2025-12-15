import axios, { AxiosInstance } from "axios";

const baseURL =
  import.meta.env.VITE_API_BASE ??
  (typeof window !== "undefined" ? window.location.origin : "http://localhost:8000");

const client: AxiosInstance = axios.create({
  baseURL,
  headers: { "Content-Type": "application/json" }
});

export interface UserInfo {
  user_upn: string;
  display_name?: string;
  technician_id_sdp?: string;
}

export interface Ticket {
  id: string;
  display_id: string;
  subject: string;
  status: string;
  priority: string;
  service_code?: string;
  service_name?: string;
  last_user_contact_at?: string | null;
  hours_since_last_user_contact?: number | null;
  communication_sla_hours?: number | null;
  is_silent?: boolean;
  experience_review_requested?: boolean;
}

export interface TicketDetail extends Ticket {
  description?: string;
  requester?: {
    name?: string;
    email_id?: string;
    phone?: string;
  };
  site?: string;
  group?: string;
  technician_id?: number | null;
  created_time?: string | null;
  sla?: {
    name?: string;
    id?: string;
  } | null;
}

export interface HistoryEvent {
  event_id: number | string;
  type: string;
  author_name?: string;
  author_type?: string;
  visibility?: string;
  timestamp: string;
  text: string;
}

export interface IaSuggestionResponse {
  suggested_message: string;
}

let authToken: string | null = null;

export const setAuthToken = (token: string | null) => {
  authToken = token;
  if (token) {
    client.defaults.headers.common.Authorization = `Bearer ${token}`;
  } else {
    delete client.defaults.headers.common.Authorization;
  }
};

export async function loginWithUpn(upn: string): Promise<UserInfo> {
  const { data } = await client.get<UserInfo>("/api/me", {
    headers: { Authorization: `Bearer ${upn}` }
  });
  return data;
}

export async function fetchTickets(): Promise<Ticket[]> {
  const { data } = await client.get<{ tickets: Ticket[] }>("/api/tickets");
  return data.tickets;
}

export async function fetchTicketDetail(id: string): Promise<TicketDetail> {
  const { data } = await client.get<TicketDetail>(`/api/tickets/${id}`);
  return data;
}

export async function fetchTicketHistory(id: string): Promise<HistoryEvent[]> {
  const { data } = await client.get<{ events: HistoryEvent[] }>(`/api/tickets/${id}/history`);
  return data.events;
}

export async function generateIaReply(params: {
  ticketId: string;
  messageType: string;
  draft: string;
  close_status?: string;
}): Promise<IaSuggestionResponse> {
  const { data } = await client.post<IaSuggestionResponse>(`/api/tickets/${params.ticketId}/ia`, {
    message_type: params.messageType,
    draft: params.draft,
    close_status: params.close_status
  });
  return data;
}

export async function interpretConversation(ticketId: string): Promise<{ suggestion: string }> {
  const { data } = await client.post<{ suggestion: string }>(
    `/api/ia/interpret_conversation`,
    { ticket_id: ticketId }
  );
  return data;
}

export async function sendReply(ticketId: string, payload: { message: string }) {
  const { data } = await client.post(`/api/tickets/${ticketId}/send_reply`, payload);
  return data;
}

export async function validateReviewToken(token: string) {
  const { data } = await client.get<{ valid: boolean; ticket_id?: string }>(
    `/api/experience/review/validate`,
    { params: { token } }
  );
  return data;
}

export async function submitReview(payload: { token: string; reason: string; comment?: string }) {
  const { data } = await client.post(`/api/experience/review/submit`, payload);
  return data;
}

export default client;
