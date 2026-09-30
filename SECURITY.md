# Security Policy

## Reporting a vulnerability

Please do not open a public issue for security problems.
Use GitHub's private reporting: **Security tab, then Report a vulnerability**.

Include what you found, how to reproduce it, and the impact you expect.
You will get an acknowledgement within 7 days.

## Scope

This is a portfolio and learning project. Do not put real supplier, customer,
or personal data into it. All bundled datasets are synthetic.

## Practices in this repository

- Secrets are never committed. gitleaks runs in pre-commit and CI, and GitHub push protection is on.
- Dependencies are locked (`uv.lock`) and monitored by Dependabot.
- Changes reach `main` only through pull requests with passing CI.
