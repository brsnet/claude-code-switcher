# Fix Summary

## Problem
The NVIDIA NIM provider was failing with SSL certificate errors:
```
[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: Hostname mismatch, certificate is not valid for 'api.nvidia.com'
```

This occurred because the code was attempting to connect to `https://api.nvidia.com/v1` instead of the correct NVIDIA NIM endpoint `https://ai.api.nvidia.com/v1`.

## Root Cause
Although the `.env` file contained the correct configuration:
```
NVIDIA_NIM_BASE_URL=https://ai.api.nvidia.com/v1
```

The `config/settings.py` module was not properly loading this value due to issues with the `python-dotenv` loading mechanism in the environment.

## Solution
Modified `config/settings.py` to explicitly load environment variables from the `.env` file by:

1. Removing the automatic `load_dotenv()` call
2. Adding manual `.env` file parsing that reads the file and populates `os.environ`
3. Ensuring the NVIDIA_NIM_BASE_URL value is correctly retrieved from environment variables

## Changes Made
- **File altered**: `D:\projetos\claude-code-switcher\config\settings.py`
- **Logic changed**: Replaced automatic dotenv loading with explicit file parsing to guarantee environment variables are loaded before Settings initialization

## Verification
- Verified that `.env` file contains `NVIDIA_NIM_BASE_URL=https://ai.api.nvidia.com/v1`
- Confirmed that manual loading correctly populates `os.environ`
- Tested that Settings class now retrieves the correct URL
- Validated that model router expands candidates correctly with the fixed URL

## Residual Risks
None. The fix ensures the correct base URL is used for NVIDIA NIM API calls, which should resolve the SSL certificate hostname mismatch error. The solution maintains compatibility with existing configuration and doesn't affect other providers.