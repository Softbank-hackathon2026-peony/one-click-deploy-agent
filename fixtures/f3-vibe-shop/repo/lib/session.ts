const sessions = new Map<string, { userId: string }>();

export function getSession(id: string) {
  return sessions.get(id);
}

export function setSession(id: string, userId: string) {
  sessions.set(id, { userId });
}
