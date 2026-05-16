# Page 01 — Login / Authentication

**Route:** `/login`  
**Access:** All Roles  
**Purpose:** Authenticate users, manage sessions, and route to appropriate dashboard based on role.

---

## Page Content & Layout

### Components on Page

| Component | Type | Description |
|-----------|------|-------------|
| `LoginForm` | Form | Email + Password inputs with validation |
| `InstitutionLogo` | Image | Dynamic institution branding from config |
| `DeviceStatusBadge` | Badge | Shows Raspberry Pi online/offline status |
| `ForgotPasswordLink` | Link | Triggers password reset flow |
| `SessionExpiredAlert` | Alert | Displayed when redirected due to expired token |
| `LoginErrorToast` | Toast | Shows auth error messages |
| `LoadingSpinner` | Spinner | Shown during auth request |
| `RememberMeCheckbox` | Checkbox | Persist session across browser restarts |

### Buttons & Interactive Elements

| Element | ID | Action |
|---------|----|--------|
| Sign In Button | `btn-sign-in` | Submit credentials, authenticate |
| Forgot Password Link | `link-forgot-password` | Navigate to password reset |
| Remember Me Checkbox | `chk-remember-me` | Toggle session persistence |
| Show/Hide Password | `btn-toggle-password` | Toggle password visibility |

---

## Class Diagram

```mermaid
classDiagram
    direction TB

    class LoginPage {
        +String email
        +String password
        +Boolean rememberMe
        +Boolean isLoading
        +String errorMessage
        +handleSubmit()
        +handleForgotPassword()
        +togglePasswordVisibility()
    }

    class LoginForm {
        +String email
        +String password
        +Boolean showPassword
        +Boolean isValid
        +validate()
        +submit()
        +reset()
    }

    class AuthStore {
        +User currentUser
        +String accessToken
        +String refreshToken
        +Boolean isAuthenticated
        +String[] roles
        +login(email, password)
        +logout()
        +refreshSession()
        +checkAuth()
    }

    class AuthApiClient {
        +login(credentials) TokenPair
        +logout() void
        +refreshToken(refreshToken) TokenPair
        +getCurrentUser() User
        +forgotPassword(email) void
        +resetPassword(token, newPassword) void
    }

    class AuthRouter {
        +POST /api/v1/auth/login
        +POST /api/v1/auth/logout
        +POST /api/v1/auth/refresh
        +GET /api/v1/auth/me
        +POST /api/v1/auth/forgot-password
        +POST /api/v1/auth/reset-password
    }

    class AuthService {
        -UserRepository userRepo
        -TokenService tokenService
        -EmailService emailService
        +authenticate(email, password) TokenPair
        +validateToken(token) User
        +refreshToken(refreshToken) TokenPair
        +revokeToken(token) void
        +requestPasswordReset(email) void
        +resetPassword(token, newPassword) void
    }

    class TokenService {
        -String secretKey
        -int accessTokenExpiry
        -int refreshTokenExpiry
        +createAccessToken(userId, roles) String
        +createRefreshToken(userId) String
        +verifyToken(token) TokenPayload
        +revokeToken(token) void
    }

    class LoginSchema {
        +String email
        +String password
        +Boolean remember_me
        +validate_email()
        +validate_password()
    }

    class TokenResponseSchema {
        +String access_token
        +String refresh_token
        +String token_type
        +int expires_in
        +UserSchema user
    }

    class UserModel {
        +UUID id
        +String email
        +String password_hash
        +String name
        +String role
        +Boolean is_active
        +DateTime last_login
        +DateTime created_at
    }

    LoginPage --> LoginForm : contains
    LoginPage --> AuthStore : uses
    LoginForm --> AuthStore : calls login()
    AuthStore --> AuthApiClient : calls API
    AuthApiClient --> AuthRouter : HTTP requests
    AuthRouter --> AuthService : delegates
    AuthService --> TokenService : creates/verifies tokens
    AuthService --> UserModel : queries
    AuthRouter --> LoginSchema : validates input
    AuthRouter --> TokenResponseSchema : returns response
```

---

## State Diagram

```mermaid
stateDiagram-v2
    [*] --> Idle

    Idle --> Validating : User clicks Sign In
    Idle --> TypingEmail : User types email
    Idle --> TypingPassword : User types password

    TypingEmail --> Idle : Field blur
    TypingPassword --> Idle : Field blur

    Validating --> ValidationFailed : Invalid inputs
    Validating --> Authenticating : Inputs valid

    ValidationFailed --> Idle : User corrects fields

    Authenticating --> AuthSuccess : 200 OK + tokens
    Authenticating --> AuthFailed : 401 Invalid credentials
    Authenticating --> AccountLocked : 403 Account locked
    Authenticating --> ServerError : 500 Server error
    Authenticating --> NetworkError : No connectivity

    AuthFailed --> Idle : User retries
    AccountLocked --> Idle : User contacts admin
    ServerError --> Idle : User retries
    NetworkError --> Idle : Connection restored

    AuthSuccess --> StoringTokens : Save JWT tokens
    StoringTokens --> FetchingProfile : GET /auth/me
    FetchingProfile --> Redirecting : Profile loaded

    Redirecting --> DashboardPage : Role = Admin
    Redirecting --> MonitoringPage : Role = Staff Operator

    DashboardPage --> [*]
    MonitoringPage --> [*]

    state Authenticating {
        [*] --> SendingRequest
        SendingRequest --> WaitingResponse
        WaitingResponse --> ProcessingResponse
        ProcessingResponse --> [*]
    }
```

---

## Feature-Action-Controller Map

| # | Feature | User Action | Frontend Controller | API Endpoint | Backend Service | Reaction / Side Effect |
|---|---------|-------------|-------------------|--------------|-----------------|----------------------|
| 1 | **Email Input** | Types email address | `LoginForm.validate()` | — | — | Real-time validation, red border on invalid |
| 2 | **Password Input** | Types password | `LoginForm.validate()` | — | — | Minimum length check, strength indicator |
| 3 | **Toggle Password** | Clicks eye icon | `LoginPage.togglePasswordVisibility()` | — | — | Input type switches text ↔ password |
| 4 | **Remember Me** | Checks/unchecks box | `LoginPage.rememberMe` toggle | — | — | Controls localStorage vs sessionStorage for tokens |
| 5 | **Sign In** | Clicks Sign In button | `AuthStore.login()` | `POST /api/v1/auth/login` | `AuthService.authenticate()` | Validates credentials → returns JWT pair → stores tokens → redirects to dashboard |
| 6 | **Login Failure** | Submits wrong credentials | `AuthStore.login()` error handler | `POST /api/v1/auth/login` → 401 | `AuthService.authenticate()` raises | Toast error "Invalid email or password", increment failed attempt counter |
| 7 | **Account Lockout** | Too many failed attempts | `AuthStore.login()` error handler | `POST /api/v1/auth/login` → 403 | `AuthService.authenticate()` checks lockout | Display "Account locked. Contact admin.", log audit event |
| 8 | **Forgot Password** | Clicks "Forgot Password" | `LoginPage.handleForgotPassword()` | `POST /api/v1/auth/forgot-password` | `AuthService.requestPasswordReset()` | Sends reset email with token link |
| 9 | **Session Expired** | Redirected from protected page | `AuthStore.checkAuth()` | `POST /api/v1/auth/refresh` → 401 | `TokenService.verifyToken()` fails | Show "Session expired, please login again" alert |
| 10 | **Auto-Refresh Token** | Token nearing expiry | `AuthStore.refreshSession()` (auto) | `POST /api/v1/auth/refresh` | `AuthService.refreshToken()` | Silent token refresh, no user interruption |
| 11 | **Role-Based Redirect** | After successful login | SvelteKit `load()` function | `GET /api/v1/auth/me` | `AuthService.validateToken()` | Super/Inst Admin → `/dashboard`, Staff → `/dashboard/monitoring` |
| 12 | **Audit Logging** | Every login attempt | — (server-side) | — | `AuditService.log()` | Records IP, timestamp, success/failure, user agent |

---
