import { FormEvent, useState } from "react";
import { api, saveToken } from "../services/api";
import type { User } from "../types";

type AuthDialogProps = {
  onClose: () => void;
  onAuthenticated: (user: User) => void;
};

export function AuthDialog({ onClose, onAuthenticated }: AuthDialogProps) {
  const [registering, setRegistering] = useState(false);
  const [email, setEmail] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      const response = registering
        ? await api.register(email, displayName, password)
        : await api.login(email, password);
      saveToken(response.access_token);
      onAuthenticated(response.user);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Не удалось выполнить вход.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="dialog-backdrop" role="presentation" onMouseDown={(event) => event.target === event.currentTarget && onClose()}>
      <section className="auth-dialog" role="dialog" aria-modal="true" aria-labelledby="auth-title">
        <button className="dialog-close" type="button" aria-label="Закрыть" onClick={onClose}>×</button>
        <span className="brand-mark dialog-mark">♫</span>
        <p className="eyebrow">ТВОЯ МУЗЫКА СОХРАНЯЕТСЯ ЗДЕСЬ</p>
        <h2 id="auth-title">{registering ? "Создать аккаунт" : "С возвращением"}</h2>
        <p className="dialog-copy">Войди, чтобы сохранять композиции и историю поиска.</p>
        <form className="auth-form" onSubmit={submit}>
          {registering && (
            <label>Имя
              <input value={displayName} onChange={(event) => setDisplayName(event.target.value)} minLength={2} maxLength={80} required />
            </label>
          )}
          <label>Email
            <input type="email" value={email} onChange={(event) => setEmail(event.target.value)} autoComplete="email" required />
          </label>
          <label>Пароль
            <input type="password" value={password} onChange={(event) => setPassword(event.target.value)} minLength={registering ? 8 : 1} maxLength={128} autoComplete={registering ? "new-password" : "current-password"} required />
          </label>
          {error && <p className="form-error">{error}</p>}
          <button className="primary-button auth-submit" type="submit" disabled={busy}>{busy ? "Подождите…" : registering ? "Зарегистрироваться" : "Войти"}</button>
        </form>
        <button className="text-button auth-switch" type="button" onClick={() => { setRegistering(!registering); setError(""); }}>
          {registering ? "Уже есть аккаунт? Войти" : "Впервые здесь? Создать аккаунт"}
        </button>
      </section>
    </div>
  );
}
