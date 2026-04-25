import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { clearAccessToken, getAccessToken, setAccessToken } from "../../../services/storage/tokenStorage";
import { getCurrentUser, login } from "../api/identityApi";
import type { LoginRequest } from "../types/auth";

export const currentUserQueryKey = ["identity", "me"] as const;

export function useLogin() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: LoginRequest) => login(payload),
    onSuccess: (response) => {
      setAccessToken(response.access_token);
      queryClient.setQueryData(currentUserQueryKey, response.user);
    },
  });
}

export function useCurrentUser() {
  return useQuery({
    queryKey: currentUserQueryKey,
    queryFn: getCurrentUser,
    enabled: Boolean(getAccessToken()),
    retry: false,
  });
}

export function useLogout() {
  const queryClient = useQueryClient();

  return () => {
    clearAccessToken();
    queryClient.removeQueries({ queryKey: currentUserQueryKey });
  };
}
