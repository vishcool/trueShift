# Authentication Bypass for Development

## Overview

I've set up a temporary authentication bypass so you can work on functionality without dealing with Firebase authentication.

## Changes Made

### 1. Added `BYPASS_AUTH` Feature Flag

**File**: `apps/backend/app/core/config.py`
- Added `bypass_auth: bool = False` to the Settings class

**File**: `apps/backend/.env`
- Set `BYPASS_AUTH=true` to enable the bypass

### 2. Modified Authentication Logic

**File**: `apps/backend/app/core/security.py`
- Updated `verify_firebase_token()` to check the `bypass_auth` flag
- When enabled, it immediately returns a dev user without checking the token:
  ```python
  {
      "uid": "dev-user-001",
      "email": "dev@trueshift.local",
      "dev_mode": True
  }
  ```

## How to Use

### Option 1: Using the Test Script

I've created a test script that demonstrates all the auth endpoints:

```bash
# Make sure your backend is running in debug mode (F5 in VS Code)
# Then run:
python test_auth_bypass.py
```

This will test:
- ✅ Health check
- ✅ User registration
- ✅ Get current user
- ✅ Update profile

### Option 2: Using curl

```bash
# Register a user (or get existing)
curl -X POST http://127.0.0.1:8000/api/v1/auth/register \
  -H "Authorization: Bearer dummy-token" \
  -H "Content-Type: application/json" \
  -d '{"display_name": "Test User", "email": "test@example.com"}'

# Get current user
curl http://127.0.0.1:8000/api/v1/auth/me \
  -H "Authorization: Bearer dummy-token"

# Update profile
curl -X PUT http://127.0.0.1:8000/api/v1/auth/me \
  -H "Authorization: Bearer dummy-token" \
  -H "Content-Type: application/json" \
  -d '{
    "display_name": "Updated Name",
    "fitness_goals": ["strength", "endurance"],
    "equipment": ["dumbbells"],
    "fitness_level": "intermediate"
  }'
```

### Option 3: Using Postman

1. Import the existing Postman collection: `apps/backend/TrueShift_API.postman_collection.json`
2. For any authenticated endpoint, add header:
   - **Key**: `Authorization`
   - **Value**: `Bearer dummy-token` (can be any value, it will be ignored)

## Dev User Details

When `BYPASS_AUTH=true`, all authenticated requests will use this dev user:
- **User ID**: `dev-user-001`
- **Email**: `dev@trueshift.local`
- **Firebase UID**: `dev-user-001`

The first time you call `/auth/register`, it will create this user in your database.

## Important Notes

⚠️ **Security Warning**: This bypass is for development only!
- Make sure `BYPASS_AUTH=false` (or remove it) in production
- The bypass only works when the flag is explicitly set to `true`

## Disabling the Bypass

When you're ready to test with real Firebase authentication:

1. Edit `apps/backend/.env`
2. Change `BYPASS_AUTH=true` to `BYPASS_AUTH=false` (or remove the line)
3. Restart your debug session

## Testing Other Endpoints

Now that auth is bypassed, you can test any protected endpoint by simply including:
```
Authorization: Bearer any-value-here
```

The token value doesn't matter - it will always authenticate as `dev-user-001`.
