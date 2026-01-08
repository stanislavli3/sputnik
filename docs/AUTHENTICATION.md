# Authentication with Clerk

Sputnik uses [Clerk](https://clerk.com) for authentication and user management. This provides secure, production-ready authentication out of the box.

> **Note:** This project uses **React with Vite**, not Next.js. For Next.js integration, see [Clerk's Next.js documentation](https://clerk.com/docs/nextjs/getting-started/quickstart).

## Setup

### 1. Create a Clerk Account

1. Go to [https://clerk.com](https://clerk.com)
2. Sign up for a free account
3. Create a new application
4. Note your API keys from the dashboard

### 2. Configure Environment Variables

**Frontend (`frontend/.env` or `frontend/.env.local`):**
```bash
VITE_CLERK_PUBLISHABLE_KEY=pk_test_...
```

**Backend (`.env`):**
```bash
CLERK_SECRET_KEY=sk_test_...
ENABLE_AUTH=true  # Optional: set to false to disable auth in development
```

> **Important:** 
> - Never commit real keys to version control
> - Use `.env.local` for local development (already in `.gitignore`)
> - Use placeholders (`pk_test_...`, `sk_test_...`) in documentation

### 3. Install Dependencies

```bash
# Backend
pip install -e .

# Frontend
cd frontend && npm install
```

## Current Implementation (React/Vite)

### Frontend Structure

Our implementation uses the **latest Clerk React SDK** (`@clerk/clerk-react`):

```typescript
// App.tsx - Wraps app with ClerkProvider
import { ClerkProvider } from "@clerk/clerk-react";

<ClerkProvider publishableKey={clerkConfig.publishableKey}>
  <AppContent />
</ClerkProvider>
```

```typescript
// Route Protection
import { SignedIn, SignedOut, RedirectToSignIn } from "@clerk/clerk-react";

<SignedIn>{children}</SignedIn>
<SignedOut><RedirectToSignIn /></SignedOut>
```

### Key Components

- **`ClerkProvider`** - Wraps the app in `App.tsx`
- **`SignedIn`/`SignedOut`** - Conditional rendering based on auth state
- **`UserButton`** - User profile button component
- **`getToken()`** - Gets JWT token for API requests

## Usage

### Development Mode

If Clerk is not configured, the application runs in development mode without authentication. This is useful for local development.

To enable auth in development:
1. Set `VITE_CLERK_PUBLISHABLE_KEY` in `frontend/.env.local`
2. Set `CLERK_SECRET_KEY` in `.env`
3. Restart servers

### Production

In production, authentication is required. Ensure:
- `VITE_CLERK_PUBLISHABLE_KEY` is set in frontend build environment
- `CLERK_SECRET_KEY` is set in backend environment
- Environment variables are properly configured in your deployment platform

## How It Works

### Frontend

- Uses `@clerk/clerk-react` for React integration (latest SDK)
- Wraps the app with `ClerkProvider` in `App.tsx`
- Protects routes with `SignedIn`/`SignedOut` components
- Shows sign-in page for unauthenticated users
- Automatically includes JWT tokens in API requests

### Backend

- Verifies JWT tokens from Clerk
- Middleware protects API routes (`/api/*`)
- Public endpoints (`/`, `/health`, `/docs`) remain accessible
- User information is attached to `request.state.user`

## API Authentication

All API requests automatically include the Clerk session token via the `apiRequest` helper:

```typescript
import { apiRequest } from "@/lib/api";

// Token is automatically included
const response = await apiRequest("/api/v1/query", {
  method: "POST",
  body: JSON.stringify({ question: "..." }),
});
```

The Clerk React SDK automatically provides the token when configured.

## Customization

### Sign-In/Sign-Up Pages

Clerk provides hosted pages by default. To customize:

1. Go to Clerk Dashboard → Customization
2. Customize the appearance
3. Or use Clerk's component library for custom pages

### User Metadata

Access user information in backend routes:

```python
from fastapi import Request

@app.post("/api/v1/query")
async def execute_query(request: Request):
    user = request.state.user
    user_id = user.get("user_id")
    email = user.get("email")
    # ...
```

### Role-Based Access

To add role-based access control:

1. Configure roles in Clerk Dashboard
2. Check roles in backend middleware
3. Use `user.get("roles")` to check permissions

## Troubleshooting

### "Clerk not configured" error

- Check that `VITE_CLERK_PUBLISHABLE_KEY` is set in frontend
- Verify the key is correct (starts with `pk_test_` or `pk_live_`)
- Restart the frontend dev server

### Backend returns 401 Unauthorized

- Check that `CLERK_SECRET_KEY` is set in backend
- Verify the key is correct (starts with `sk_test_` or `sk_live_`)
- Check that frontend is sending the token (check browser network tab)

### Frontend shows sign-in page

- Check `VITE_CLERK_PUBLISHABLE_KEY` is set
- Verify the key is correct
- Clear browser cache and reload
- Check browser console for errors

## Security Notes

- **Never commit API keys** to version control
- Use environment variables for all secrets
- In production, use `pk_live_` and `sk_live_` keys
- Enable additional security features in Clerk Dashboard:
  - MFA (Multi-Factor Authentication)
  - Session management
  - Rate limiting
  - IP allowlisting

## React vs Next.js

This project uses **React with Vite**, not Next.js. Key differences:

| Feature | React/Vite (This Project) | Next.js |
|---------|---------------------------|---------|
| SDK Package | `@clerk/clerk-react` | `@clerk/nextjs` |
| Provider | `ClerkProvider` in `App.tsx` | `ClerkProvider` in `app/layout.tsx` |
| Middleware | N/A (client-side routing) | `clerkMiddleware()` in `middleware.ts` |
| Auth Check | `SignedIn`/`SignedOut` components | `auth()` from `@clerk/nextjs/server` |

## Resources

- [Clerk React Documentation](https://clerk.com/docs/references/react/overview)
- [Clerk Quickstart (React)](https://clerk.com/docs/quickstarts/react)
- [Clerk Python SDK](https://clerk.com/docs/references/backend-api/overview)
- [Clerk Dashboard](https://dashboard.clerk.com)
