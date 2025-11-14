# Proof of Concept: NiceGUI to Vue.js Migration

## Purpose

This document outlines a 1-week proof of concept (POC) to validate the technical approach for migrating SahaBot2 from NiceGUI to a Vue.js frontend with FastAPI backend.

---

## POC Goals

### Success Criteria
1. ✅ **Authentication works** - Users can log in via Discord OAuth2
2. ✅ **User profile page functional** - Display and edit user information
3. ✅ **Real-time updates work** - WebSocket connection shows live updates
4. ✅ **Multi-tenant security validated** - Organization isolation verified
5. ✅ **Development workflow established** - Hot reload, build process confirmed
6. ✅ **Performance acceptable** - Load times <2s, smooth interactions

### Out of Scope for POC
- ❌ Complete UI design
- ❌ All pages migrated
- ❌ Comprehensive test coverage
- ❌ Production deployment
- ❌ Mobile optimization (test on desktop only)

---

## POC Timeline (5 days)

### Day 1: Project Setup & Authentication
**Goal**: Working Vue.js app with Discord OAuth2 login

**Tasks**:
1. Initialize Vue.js project with Vite + TypeScript (2 hours)
   ```bash
   npm create vite@latest sahabot2-frontend -- --template vue-ts
   cd sahabot2-frontend
   npm install
   npm install vue-router pinia axios
   ```

2. Configure Vue Router and Pinia (1 hour)
   - Set up basic routing
   - Create store structure
   - Configure Axios instance

3. Backend: Adapt OAuth2 for SPA (3 hours)
   - Create JWT token endpoint
   - Implement token refresh logic
   - Update CORS settings
   - Add `/api/auth/login` and `/api/auth/callback` endpoints

4. Frontend: Implement login flow (2 hours)
   - Create login page
   - Handle OAuth2 redirect
   - Store tokens securely
   - Create auth service

**Deliverables**:
- Working login flow
- Token storage and refresh
- Protected routes

---

### Day 2: User Profile Page
**Goal**: Complete user profile page with CRUD operations

**Tasks**:
1. Backend: User profile endpoints (2 hours)
   - `GET /api/users/me` - Already exists ✅
   - `PATCH /api/users/me` - Update user profile (add if missing)
   - `GET /api/users/me/settings` - Get user settings
   - `PATCH /api/users/me/settings` - Update user settings

2. Frontend: Base layout components (3 hours)
   - Header with user menu
   - Sidebar navigation
   - Footer
   - Base page container

3. Frontend: User profile page (3 hours)
   - Display user information
   - Avatar display
   - Permission badge
   - Editable fields (username, settings)
   - Save functionality

**Deliverables**:
- Functional user profile page
- Base layout working
- CRUD operations validated

---

### Day 3: Real-Time Updates (WebSocket)
**Goal**: Working WebSocket connection with live updates

**Tasks**:
1. Backend: WebSocket endpoint (3 hours)
   ```python
   # websocket.py
   from fastapi import WebSocket, WebSocketDisconnect
   from typing import Dict
   
   class ConnectionManager:
       def __init__(self):
           self.active_connections: Dict[int, WebSocket] = {}
       
       async def connect(self, user_id: int, websocket: WebSocket):
           await websocket.accept()
           self.active_connections[user_id] = websocket
       
       async def disconnect(self, user_id: int):
           if user_id in self.active_connections:
               del self.active_connections[user_id]
       
       async def send_to_user(self, user_id: int, message: dict):
           if user_id in self.active_connections:
               await self.active_connections[user_id].send_json(message)
   
   manager = ConnectionManager()
   
   @app.websocket("/ws/events")
   async def websocket_endpoint(websocket: WebSocket, token: str):
       # Validate token and get user
       user = await validate_token(token)
       if not user:
           await websocket.close(code=4001)
           return
       
       await manager.connect(user.id, websocket)
       try:
           while True:
               # Keep connection alive
               data = await websocket.receive_text()
               if data == "ping":
                   await websocket.send_text("pong")
       except WebSocketDisconnect:
           await manager.disconnect(user.id)
   ```

2. Frontend: WebSocket service (2 hours)
   ```typescript
   // websocketService.ts
   class WebSocketService {
     private ws: WebSocket | null = null;
     private reconnectAttempts = 0;
     private maxReconnectAttempts = 5;
     
     connect(token: string) {
       const wsUrl = `ws://localhost:8080/ws/events?token=${token}`;
       this.ws = new WebSocket(wsUrl);
       
       this.ws.onopen = () => {
         console.log('WebSocket connected');
         this.reconnectAttempts = 0;
         this.startHeartbeat();
       };
       
       this.ws.onmessage = (event) => {
         const data = JSON.parse(event.data);
         this.handleMessage(data);
       };
       
       this.ws.onclose = () => {
         console.log('WebSocket disconnected');
         this.reconnect(token);
       };
     }
     
     private handleMessage(data: any) {
       // Emit event to components
       window.dispatchEvent(new CustomEvent('ws-message', { detail: data }));
     }
     
     private startHeartbeat() {
       setInterval(() => {
         if (this.ws?.readyState === WebSocket.OPEN) {
           this.ws.send('ping');
         }
       }, 30000);
     }
     
     send(message: any) {
       if (this.ws?.readyState === WebSocket.OPEN) {
         this.ws.send(JSON.stringify(message));
       }
     }
   }
   
   export const wsService = new WebSocketService();
   ```

3. Frontend: Live notification demo (3 hours)
   - Display notification count in header
   - Show toast when notification arrives
   - Update notification list in real-time

**Deliverables**:
- Working WebSocket connection
- Real-time notification demo
- Reconnection logic

---

### Day 4: Organization List & Multi-Tenant Security
**Goal**: Validate multi-tenant architecture and organization switching

**Tasks**:
1. Backend: Organization endpoints (2 hours)
   - `GET /api/organizations/my` - List user's organizations (add if missing)
   - `GET /api/organizations/{id}` - Already exists ✅
   - Verify all endpoints filter by organization

2. Frontend: Organization selector (3 hours)
   - Organization list page
   - Organization card component
   - Organization context (Pinia store)
   - Organization switcher in header

3. Security validation (3 hours)
   - Test cross-tenant data access
   - Verify API validates organization membership
   - Test with multiple users and organizations
   - Document any security issues found

**Deliverables**:
- Organization list and switcher
- Multi-tenant security validated
- Security test report

---

### Day 5: Polish & Demo Preparation
**Goal**: Prepare POC demo and document findings

**Tasks**:
1. UI polish (2 hours)
   - Add loading states
   - Add error handling
   - Improve transitions
   - Basic styling

2. Performance testing (2 hours)
   - Measure load times
   - Check bundle size
   - Test WebSocket latency
   - Profile render performance

3. Documentation (3 hours)
   - Architecture diagram
   - Setup instructions
   - API documentation
   - Findings report
   - Demo video (optional)

4. Demo preparation (1 hour)
   - Prepare demo script
   - Set up demo data
   - Test demo flow

**Deliverables**:
- Polished POC
- Documentation
- Demo ready
- Findings report

---

## Technical Stack for POC

### Frontend
```json
{
  "dependencies": {
    "vue": "^3.3.0",
    "vue-router": "^4.2.0",
    "pinia": "^2.1.0",
    "axios": "^1.5.0",
    "typescript": "^5.2.0"
  },
  "devDependencies": {
    "@vitejs/plugin-vue": "^4.4.0",
    "vite": "^4.5.0"
  }
}
```

### Backend (minimal additions)
```python
# requirements for POC
fastapi[all]  # Already installed
python-jose[cryptography]  # For JWT
passlib[bcrypt]  # For token hashing
websockets  # For WebSocket support (included in fastapi[all])
```

---

## POC Project Structure

```
sahabot2/
├── backend/                 # Existing FastAPI backend
│   ├── main.py             # Add WebSocket endpoint
│   ├── api/
│   │   └── routes/
│   │       ├── auth.py     # NEW: JWT auth endpoints
│   │       └── websocket.py # NEW: WebSocket handler
│   └── ...
│
└── frontend-poc/           # NEW: Vue.js frontend
    ├── public/
    ├── src/
    │   ├── main.ts
    │   ├── App.vue
    │   ├── router/
    │   │   └── index.ts    # Route definitions
    │   ├── stores/
    │   │   ├── auth.ts     # Auth state
    │   │   └── org.ts      # Organization context
    │   ├── services/
    │   │   ├── api.ts      # Axios instance
    │   │   ├── auth.ts     # Auth service
    │   │   └── websocket.ts # WebSocket service
    │   ├── views/
    │   │   ├── Login.vue
    │   │   ├── Profile.vue
    │   │   └── Organizations.vue
    │   ├── components/
    │   │   ├── AppHeader.vue
    │   │   ├── AppSidebar.vue
    │   │   ├── AppFooter.vue
    │   │   └── BaseLayout.vue
    │   └── assets/
    │       └── styles.css
    ├── package.json
    ├── vite.config.ts
    └── tsconfig.json
```

---

## Key Code Samples

### 1. Auth Store (Pinia)
```typescript
// stores/auth.ts
import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import { authService } from '@/services/auth';

export const useAuthStore = defineStore('auth', () => {
  const user = ref(null);
  const accessToken = ref(localStorage.getItem('access_token'));
  const refreshToken = ref(localStorage.getItem('refresh_token'));

  const isAuthenticated = computed(() => !!accessToken.value);

  async function login(code: string) {
    const response = await authService.exchangeCode(code);
    accessToken.value = response.access_token;
    refreshToken.value = response.refresh_token;
    localStorage.setItem('access_token', response.access_token);
    localStorage.setItem('refresh_token', response.refresh_token);
    await fetchUser();
  }

  async function fetchUser() {
    const response = await authService.getMe();
    user.value = response;
  }

  async function refresh() {
    const response = await authService.refreshToken(refreshToken.value);
    accessToken.value = response.access_token;
    localStorage.setItem('access_token', response.access_token);
  }

  function logout() {
    user.value = null;
    accessToken.value = null;
    refreshToken.value = null;
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
  }

  return {
    user,
    accessToken,
    isAuthenticated,
    login,
    fetchUser,
    refresh,
    logout,
  };
});
```

### 2. API Client with Interceptors
```typescript
// services/api.ts
import axios from 'axios';
import { useAuthStore } from '@/stores/auth';

const api = axios.create({
  baseURL: 'http://localhost:8080/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor: Add token to all requests
api.interceptors.request.use(
  (config) => {
    const authStore = useAuthStore();
    if (authStore.accessToken) {
      config.headers.Authorization = `Bearer ${authStore.accessToken}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor: Handle token expiration
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // If 401 and not already retrying, try to refresh token
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      const authStore = useAuthStore();
      
      try {
        await authStore.refresh();
        // Retry original request with new token
        originalRequest.headers.Authorization = `Bearer ${authStore.accessToken}`;
        return api(originalRequest);
      } catch (refreshError) {
        // Refresh failed, logout user
        authStore.logout();
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);

export default api;
```

### 3. Protected Route Guard
```typescript
// router/index.ts
import { createRouter, createWebHistory } from 'vue-router';
import { useAuthStore } from '@/stores/auth';

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'Login',
      component: () => import('@/views/Login.vue'),
    },
    {
      path: '/profile',
      name: 'Profile',
      component: () => import('@/views/Profile.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/organizations',
      name: 'Organizations',
      component: () => import('@/views/Organizations.vue'),
      meta: { requiresAuth: true },
    },
  ],
});

router.beforeEach((to, from, next) => {
  const authStore = useAuthStore();
  
  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    next({ name: 'Login' });
  } else {
    next();
  }
});

export default router;
```

---

## Expected Challenges & Solutions

### Challenge 1: Discord OAuth2 Redirect
**Problem**: OAuth2 callback URL needs to handle SPA routing

**Solution**:
1. Backend endpoint `/api/auth/callback` handles OAuth2 exchange
2. Backend returns HTML page that posts message to opener window
3. Frontend listens for message and completes login
4. Alternative: Backend redirects to frontend with token in URL fragment

### Challenge 2: Token Storage Security
**Problem**: Where to store JWT tokens securely?

**Solution Options**:
1. **localStorage** (easier, less secure)
   - Vulnerable to XSS
   - Simple implementation
   - Good for POC

2. **httpOnly cookies** (more secure, recommended)
   - Protected from XSS
   - Requires backend changes
   - Better for production

**POC Decision**: Use localStorage for simplicity, document security implications

### Challenge 3: WebSocket Authentication
**Problem**: How to authenticate WebSocket connections?

**Solution**:
- Pass token as query parameter: `/ws/events?token=<access_token>`
- Backend validates token on connection
- Close connection if token invalid or expired
- Frontend handles reconnection with fresh token

### Challenge 4: Organization Context Switching
**Problem**: How to handle organization switching without page reload?

**Solution**:
- Store current organization in Pinia store
- Watch for organization changes
- Refetch data when organization changes
- Update API requests to include organization context

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| OAuth2 flow breaks | Low | High | Test thoroughly, have fallback |
| WebSocket unreliable | Medium | Medium | Implement reconnection, fallback to polling |
| Performance issues | Low | Medium | Lazy loading, code splitting |
| CORS problems | Medium | Low | Configure properly from start |
| Token refresh fails | Medium | Medium | Clear error handling, automatic logout |
| Build process slow | Low | Low | Vite is fast, optimize if needed |

---

## Success Metrics

### Performance
- Initial load: <2s
- Route transition: <200ms
- API response: <500ms
- WebSocket latency: <100ms

### Code Quality
- TypeScript strict mode enabled
- No `any` types (except external libraries)
- ESLint configured and passing
- Clean console (no errors/warnings)

### Functionality
- 100% of POC features working
- No blocking bugs
- Error handling in place
- Loading states visible

---

## Demo Script

### 1. Project Setup (2 min)
- Show project structure
- Explain technology choices
- Show package.json

### 2. Authentication (3 min)
- Navigate to login page
- Click "Login with Discord"
- Show OAuth2 flow
- Show authenticated state
- Show token in localStorage

### 3. User Profile (2 min)
- Navigate to profile page
- Show user information
- Edit a field
- Save changes
- Show success notification

### 4. Real-Time Updates (3 min)
- Open WebSocket DevTools
- Show connection established
- Trigger test notification from backend
- Show notification appear in UI
- Show notification count update

### 5. Multi-Tenant Security (2 min)
- Navigate to organizations page
- Show user's organizations
- Select an organization
- Show organization context in header
- Explain security validation

### 6. Performance Demo (2 min)
- Show Network DevTools
- Show bundle size
- Show load time
- Show API requests

### 7. Q&A (5 min)
- Discuss findings
- Address concerns
- Next steps

---

## Post-POC Decisions

After completing the POC, decide on:

### 1. Framework Choice
- ✅ Proceed with Vue.js
- ⬜ Try React alternative
- ⬜ Stay with NiceGUI

### 2. UI Library
- ⬜ Vuetify 3 (Material Design)
- ⬜ PrimeVue (Enterprise)
- ⬜ Quasar (Mobile-ready)
- ⬜ Custom (Full control)

### 3. State Management
- ✅ Pinia (already tested)
- ⬜ Vuex
- ⬜ No state management

### 4. Build Strategy
- ⬜ Big bang migration
- ✅ Incremental migration (recommended)
- ⬜ Hybrid approach

### 5. Timeline
- ⬜ Proceed with full migration (8-12 weeks)
- ⬜ Delay migration
- ⬜ Abandon migration

---

## Deliverables Checklist

- [ ] Working Vue.js + FastAPI application
- [ ] Discord OAuth2 login flow
- [ ] User profile page (view & edit)
- [ ] WebSocket connection with live updates
- [ ] Organization list and selector
- [ ] Multi-tenant security validation report
- [ ] Performance benchmark results
- [ ] Architecture documentation
- [ ] Setup instructions (README)
- [ ] Findings report with recommendations
- [ ] Demo video (optional)
- [ ] Decision document for next steps

---

## Next Steps After POC

### If POC Succeeds
1. Review findings with stakeholders
2. Make go/no-go decision on full migration
3. If go: Begin Phase 1 (API completion) from main estimation
4. Set up CI/CD pipeline for frontend
5. Establish frontend coding standards

### If POC Reveals Issues
1. Document specific problems encountered
2. Evaluate alternatives (different framework, hybrid approach)
3. Consider staying with NiceGUI
4. Reassess requirements and constraints

---

## Budget

### Time Investment
- **Developer time**: 5 days (1 developer)
- **Review time**: 2-3 hours (stakeholders)
- **Total**: ~45 hours

### Cost
- **Development**: ~$4,000-6,000 (at $100-150/hr)
- **Infrastructure**: $0 (local development)
- **Tools**: $0 (all open source)

### ROI
If POC validates approach:
- **Saves**: 1-2 weeks of uncertainty in full migration
- **Reduces risk**: ~30% (validates critical technical assumptions)
- **Value**: $10,000-15,000 in avoided rework

---

## Conclusion

This 5-day POC will validate the core technical assumptions for migrating from NiceGUI to Vue.js:

✅ **Authentication works** - Discord OAuth2 with JWT tokens  
✅ **Real-time updates work** - WebSocket connection  
✅ **Multi-tenant security preserved** - Organization isolation  
✅ **Development workflow smooth** - Hot reload, TypeScript  
✅ **Performance acceptable** - Fast load times  

Upon successful completion, we'll have:
- High confidence in technical approach
- Working code samples as foundation
- Clear understanding of challenges
- Data-driven decision on full migration

**Recommendation**: Execute this POC before committing to full 8-12 week migration.

---

**Document Version**: 1.0  
**Date**: November 14, 2024  
**Author**: GitHub Copilot Coding Agent  
**Status**: Ready for Execution
