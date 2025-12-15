import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState
} from "react";
import { loginWithUpn, setAuthToken, UserInfo } from "../api/client";

interface AuthContextType {
  user: UserInfo | null;
  token: string | null;
  login: (upn: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider = ({ children }: { children: React.ReactNode }) => {
  const [user, setUser] = useState<UserInfo | null>(null);
  const [token, setToken] = useState<string | null>(() => localStorage.getItem("copilot_token"));

  useEffect(() => {
    setAuthToken(token);
  }, [token]);

  const login = useCallback(async (upn: string) => {
    const profile = await loginWithUpn(upn.trim());
    setUser(profile);
    setToken(upn.trim());
    localStorage.setItem("copilot_token", upn.trim());
  }, []);

  const logout = useCallback(() => {
    setUser(null);
    setToken(null);
    localStorage.removeItem("copilot_token");
    setAuthToken(null);
  }, []);

  const value = useMemo(
    () => ({
      user,
      token,
      login,
      logout
    }),
    [user, token, login, logout]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = (): AuthContextType => {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside AuthProvider");
  return ctx;
};
