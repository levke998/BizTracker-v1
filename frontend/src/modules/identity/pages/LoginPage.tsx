import { FormEvent, useEffect, useState } from "react";
import { Navigate, useLocation, useNavigate } from "react-router-dom";

import { Button } from "../../../shared/components/ui/Button";
import { getAccessToken } from "../../../services/storage/tokenStorage";
import { routes } from "../../../shared/constants/routes";
import { useLogin } from "../hooks/useLogin";

type LocationState = {
  from?: {
    pathname?: string;
  };
};

export function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const loginMutation = useLogin();
  const [email, setEmail] = useState("admin@biztracker.local");
  const [password, setPassword] = useState("");
  const [hasToken, setHasToken] = useState(Boolean(getAccessToken()));

  const from =
    (location.state as LocationState | null)?.from?.pathname ?? routes.dashboard;

  useEffect(() => {
    setHasToken(Boolean(getAccessToken()));
  }, []);

  if (hasToken) {
    return <Navigate replace to={from} />;
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    loginMutation.mutate(
      { email, password },
      {
        onSuccess: () => {
          navigate(from, { replace: true });
        },
      },
    );
  }

  return (
    <main className="login-page">
      <section className="login-panel">
        <div className="login-copy">
          <span className="page-eyebrow">BizTracker</span>
          <h1>Bejelentkezés</h1>
          <p>Üzleti iránytű a Gourmand és a Flow napi döntéseihez.</p>
        </div>

        <form className="login-form" onSubmit={handleSubmit}>
          <label className="field login-field">
            <span>E-mail</span>
            <input
              className="field-input"
              type="email"
              autoComplete="username"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              required
            />
          </label>

          <label className="field login-field">
            <span>Jelszó</span>
            <input
              className="field-input"
              type="password"
              autoComplete="current-password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              required
            />
          </label>

          {loginMutation.isError ? (
            <p className="form-error">{loginMutation.error.message}</p>
          ) : null}

          <Button type="submit" glow disabled={loginMutation.isPending}>
            {loginMutation.isPending ? "Bejelentkezés..." : "Belépés"}
          </Button>
        </form>
      </section>
    </main>
  );
}
