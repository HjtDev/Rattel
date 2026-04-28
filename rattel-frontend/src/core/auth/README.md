# Authentication Manager

A comprehensive JWT-based authentication system for the Rattel frontend.

## Features

- **JWT Token Management**: Automatic token storage, refresh, and expiration handling
- **User State Management**: Global user state with React hooks
- **Automatic Token Refresh**: Tokens are refreshed 1 minute before expiration
- **OTP Authentication**: Support for register/login with OTP verification
- **LocalStorage Persistence**: Auth state persists across page reloads
- **Axios Integration**: Automatic token attachment to API requests
- **401 Retry Logic**: Automatically refreshes token and retries failed requests

## Usage

### 1. Using the `useAuth` Hook (Recommended)

```tsx
"use client";

import { useAuth } from "@/src/core/hooks/useAuth";

export default function MyComponent() {
    const { user, isAuthenticated, isLoading, login, logout } = useAuth();

    if (isLoading) {
        return <div>Loading...</div>;
    }

    if (!isAuthenticated) {
        return <button onClick={() => login("username")}>Login</button>;
    }

    return (
        <div>
            <p>Welcome, {user?.name}!</p>
            <button onClick={logout}>Logout</button>
        </div>
    );
}
```

### 2. Authentication Flow

#### Register Flow
```tsx
const { register, verifyOTP } = useAuth();

// Step 1: Initiate registration (sends OTP)
const result = await register({
    username: "john_doe",
    name: "John Doe",
    phone: "09123456789",
    email: "john@example.com" // optional
});

if (result.success) {
    const identifier = result.identifier;
    
    // Step 2: Verify OTP code
    const verifyResult = await verifyOTP(identifier, "123456");
    
    if (verifyResult.success) {
        // User is now logged in, tokens are stored
        console.log("Registration successful!");
    }
}
```

#### Login Flow
```tsx
const { login, verifyOTP } = useAuth();

// Step 1: Initiate login (sends OTP)
const result = await login("username_or_phone");

if (result.success) {
    const identifier = result.identifier;
    
    // Step 2: Verify OTP code
    const verifyResult = await verifyOTP(identifier, "123456");
    
    if (verifyResult.success) {
        // User is now logged in
        console.log("Login successful!");
    }
}
```

### 3. Direct AuthManager Usage

For non-React contexts or advanced usage:

```typescript
import { authManager } from "@/src/core/auth/authManager";

// Check authentication
if (authManager.isAuthenticated()) {
    const user = authManager.getUser();
    console.log(user?.name);
}

// Get tokens
const accessToken = authManager.getAccessToken();
const refreshToken = authManager.getRefreshToken();

// Subscribe to auth changes
const unsubscribe = authManager.subscribe((user) => {
    console.log("Auth state changed:", user);
});

// Later: unsubscribe
unsubscribe();

// Manual token refresh
await authManager.refreshAccessToken();

// Update user data locally (after profile update)
authManager.updateUser({ name: "New Name" });

// Logout
authManager.logout();
```

### 4. Protected Routes

```tsx
"use client";

import { useAuth } from "@/src/core/hooks/useAuth";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

export default function ProtectedPage() {
    const { isAuthenticated, isLoading } = useAuth();
    const router = useRouter();

    useEffect(() => {
        if (!isLoading && !isAuthenticated) {
            router.push("/login");
        }
    }, [isAuthenticated, isLoading, router]);

    if (isLoading) {
        return <div>Loading...</div>;
    }

    if (!isAuthenticated) {
        return null;
    }

    return <div>Protected Content</div>;
}
```

### 5. Accessing User Profile & Settings

```tsx
const { user } = useAuth();

// Basic user info
console.log(user?.username);
console.log(user?.email);
console.log(user?.name);
console.log(user?.phone);
console.log(user?.profile_picture);
console.log(user?.score);

// Profile data (if loaded with full serializer)
console.log(user?.profile?.role); // 'student' | 'teacher'
console.log(user?.profile?.gender);
console.log(user?.profile?.city);

// Settings (if loaded with full serializer)
console.log(user?.settings?.profile_visible);
console.log(user?.settings?.email_on_payment);
```

## API Endpoints Used

- `POST /auth/register/` - Initiate registration
- `POST /auth/login/` - Initiate login
- `POST /auth/verify/` - Verify OTP code
- `POST /auth/refresh/` - Refresh access token
- `GET /users/info/` - Fetch current user info

## Token Storage

Tokens and user data are stored in `localStorage`:
- `access_token` - JWT access token
- `refresh_token` - JWT refresh token
- `user_data` - Serialized user object

## Automatic Features

1. **Token Refresh**: Access tokens are automatically refreshed 1 minute before expiration
2. **Request Retry**: Failed 401 requests automatically retry after token refresh
3. **Auto Logout**: User is logged out if token refresh fails
4. **State Persistence**: Auth state persists across page reloads
5. **Global State**: All components using `useAuth` receive the same user state

## Security Notes

- Tokens are stored in localStorage (consider httpOnly cookies for production)
- Refresh tokens are rotated if backend is configured for rotation
- Failed refresh attempts trigger automatic logout
- All API requests automatically include the Bearer token
