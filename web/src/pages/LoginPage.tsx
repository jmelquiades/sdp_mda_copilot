import { FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function LoginPage() {
  const [upn, setUpn] = useState("");
  const [error, setError] = useState<string | null>(null);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    try {
      await login(upn);
      navigate("/tickets");
    } catch (err) {
      console.error(err);
      setError("No pudimos validar tu usuario. Verifica el UPN/correo.");
    }
  };

  return (
    <div className="page auth-page">
      <div className="card auth-card">
        <h1>Criteria ServiceDesk Copilot</h1>
        <p className="muted">Ingresa tu UPN / correo corporativo para continuar.</p>
        <form onSubmit={handleSubmit} className="stack">
          <label className="stack">
            <span>UPN / correo</span>
            <input
              type="email"
              placeholder="mds_usuario@cliente.com"
              value={upn}
              onChange={(e) => setUpn(e.target.value)}
              required
            />
          </label>
          {error && <div className="error-box">{error}</div>}
          <button type="submit" className="primary">
            Entrar
          </button>
        </form>
      </div>
    </div>
  );
}
