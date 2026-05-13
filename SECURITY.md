# Security Policy

## Supported Versions

The following versions of Floe are currently supported with security updates:

| Version | Supported |
| ------- | --------- |
| 0.2.x   | ✅        |
| < 0.2   | ❌        |

## Reporting a Vulnerability

Floe handles financial data (transactions, budgets, Google Sheets access). If you discover a security vulnerability, please report it privately so we can address it before disclosure.

### How to Report

**Use GitHub Private Vulnerability Reporting:**

→ https://github.com/NugrahaPancaWibisana/floe/security/advisories

This is the preferred method. It creates a private advisory where we can discuss the issue confidentially.

### What to Include

- A clear description of the vulnerability
- Steps to reproduce (proof of concept is helpful)
- Affected version(s)
- Potential impact
- Any suggested fix (optional)

### Response Time

You should receive an initial response within **48 hours**. We will keep you informed as the fix progresses.

### Disclosure Process

1. Report is submitted via private vulnerability reporting
2. We acknowledge receipt within 48 hours
3. We investigate and develop a fix
4. A security advisory is published when the fix is released
5. You are credited for the discovery (unless you prefer to remain anonymous)

## Scope

### In Scope

- The Floe bot source code (`src/` directory)
- Python dependencies (direct and transitive)
- Configuration and environment variable handling
- Build and deployment scripts (`Dockerfile`, `Procfile`, CI configs)

### Out of Scope

- Third-party services (Telegram API, Google Gemini API, Google Sheets API)
- User Google accounts or Google Cloud projects
- The Telegram messaging platform itself
- Physical security or social engineering attacks

## Responsible Disclosure

We ask that you:

- Do not publicize the vulnerability before a fix is released
- Do not exploit the vulnerability beyond what is necessary to demonstrate it
- Follow our [Code of Conduct](CODE_OF_CONDUCT.md) during all interactions
