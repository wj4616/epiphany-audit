# Build Plan — User Dashboard v2

## Phases

### Phase A — Auth Foundation
- [ ] Set up OAuth2 flow with PKCE
- [ ] Token refresh middleware
- [ ] Session store (Redis)
**Checkpoint A:** `curl /auth/me` returns 200 with valid token.

### Phase B — Dashboard UI Shell
- [ ] Layout shell with sidebar navigation
- [ ] Dark/light theme toggle
- [ ] Responsive grid (mobile-first)
**Checkpoint B:** Lighthouse score ≥90 on mobile.

### Phase C — Data Pipeline
- [ ] WebSocket connection for real-time updates
- [ ] REST fallback when WS unavailable
**Checkpoint C:** Dashboard updates within 2s of backend event.
