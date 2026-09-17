const OPERATOR_ID_KEY = "orderDesk.operatorId";
const OPERATOR_TOKEN_KEY = "orderDesk.operatorToken";

export type OperatorSession = {
  operatorId: string;
  operatorToken: string;
};

export function getOperatorSession(): OperatorSession | null {
  const operatorId = sessionStorage.getItem(OPERATOR_ID_KEY)?.trim() ?? "";
  const operatorToken = sessionStorage.getItem(OPERATOR_TOKEN_KEY)?.trim() ?? "";
  if (!operatorId || !operatorToken) {
    return null;
  }
  return { operatorId, operatorToken };
}

export function saveOperatorSession(session: OperatorSession): void {
  sessionStorage.setItem(OPERATOR_ID_KEY, session.operatorId.trim());
  sessionStorage.setItem(OPERATOR_TOKEN_KEY, session.operatorToken.trim());
}

export function clearOperatorSession(): void {
  sessionStorage.removeItem(OPERATOR_ID_KEY);
  sessionStorage.removeItem(OPERATOR_TOKEN_KEY);
}

export function operatorAuthHeaders(session: OperatorSession): Record<string, string> {
  return {
    Authorization: `Bearer ${session.operatorToken}`,
    "X-Operator-Id": session.operatorId,
  };
}
