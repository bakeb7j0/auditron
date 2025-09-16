# Security & Privacy

- **SSH keys:** store only paths in DB; keep keys outside DB and passphrase‑protected.
- **At‑rest protection:** prefer encrypted USB (LUKS). Consider SQLCipher if DB encryption is required.
- **Least privilege:** if `sudo` is needed, restrict it to read‑only commands via sudoers (NOPASSWD for specific binaries).
- **Content capture:** size caps and allow‑list globs (e.g., allow `/etc/*.conf`, deny secrets). Never capture credential stores (`/etc/shadow`, private keys).
- **Timestamps:** normalize to UTC to avoid TZ confusion across hosts.
- **Logging:** avoid secrets in logs; truncate excessive stderr/stdout.
