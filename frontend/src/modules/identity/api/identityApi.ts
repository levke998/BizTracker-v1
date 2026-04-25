import { apiGet, apiPostJson } from "../../../services/api/client";
import type { CurrentUser, LoginRequest, LoginResponse } from "../types/auth";

export function login(payload: LoginRequest) {
  return apiPostJson<LoginRequest, LoginResponse>("auth/login", payload);
}

export function getCurrentUser() {
  return apiGet<CurrentUser>("me");
}
