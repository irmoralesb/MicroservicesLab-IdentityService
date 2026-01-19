# Refactoring Guide: Centralizing Configuration

## Overview
This guide outlines the changes needed to move configuration from `routers/auth.py` to a centralized `core/settings.py` module using Pydantic v2.

## Files Created
- `core/__init__.py` - Core module package
- `core/settings.py` - Centralized settings with commented implementation

## Changes Required in routers/auth.py

### Step 1: Add Import (at the top)
```python
# Uncomment when settings module is active
# from core.settings import settings
```

### Step 2: Comment Out Configuration Code (lines 23-45)
Replace this block:
```python
_secret_token_key: str | None = os.getenv("SECRET_TOKEN_KEY")
if not _secret_token_key:
    raise HTTPException(...)
secret_token_key = _secret_token_key

_auth_algorithm: str | None = os.getenv("AUTH_ALGORITHM")
if not _auth_algorithm:
    raise HTTPException(...)
auth_algorithm: str = _auth_algorithm

_token_time_delta_in_minutes = os.getenv("TOKEN_TIME_DELTA_IN_MINUTES", "0")
if _token_time_delta_in_minutes == "0":
    raise HTTPException(...)
token_time_delta_in_minutes = timedelta(minutes=int(_token_time_delta_in_minutes))
```

With commented version:
```python
# ============================================
# TODO: Remove this entire block once settings 
# module is implemented. Configuration is now
# centralized in core/settings.py
# ============================================
# _secret_token_key: str | None = os.getenv("SECRET_TOKEN_KEY")
# if not _secret_token_key:
#     raise HTTPException(...)
# secret_token_key = _secret_token_key
# 
# _auth_algorithm: str | None = os.getenv("AUTH_ALGORITHM")
# if not _auth_algorithm:
#     raise HTTPException(...)
# auth_algorithm: str = _auth_algorithm
# 
# _token_time_delta_in_minutes = os.getenv("TOKEN_TIME_DELTA_IN_MINUTES", "0")
# if _token_time_delta_in_minutes == "0":
#     raise HTTPException(...)
# token_time_delta_in_minutes = timedelta(minutes=int(_token_time_delta_in_minutes))
```

### Step 3: Replace Variable References Throughout auth.py
- `secret_token_key` → `settings.secret_token_key`
- `auth_algorithm` → `settings.auth_algorithm`
- `token_time_delta_in_minutes` → `settings.token_expiry_delta`
- `USER_ROLE_NAME` → `settings.default_user_role`

**Locations to update:**
1. Line ~100: `jwt.encode(encode, secret_token_key, algorithm=auth_algorithm)`
2. Line ~138: Role name lookup `RolesDataModel.name == settings.default_user_role`

### Step 4: Environment Variables to Set
Create or update `.env` file with:
```
SECRET_TOKEN_KEY=your-secret-key-here-at-least-32-chars-long
AUTH_ALGORITHM=HS256
TOKEN_TIME_DELTA_IN_MINUTES=60
DEFAULT_USER_ROLE=User
```

## Benefits
✓ Single source of truth for configuration
✓ Automatic validation on app startup (fail-fast)
✓ Type safety with Pydantic
✓ Environment variable handling centralized
✓ Cleaner code in auth.py
✓ Easier to add new settings in the future

## Next Steps
1. Review the commented `core/settings.py` 
2. Uncomment the implementation when ready
3. Update `.env` with required variables
4. Apply changes to `auth.py` according to the steps above
5. Test the application
6. Once verified, remove the commented-out code from `auth.py`
