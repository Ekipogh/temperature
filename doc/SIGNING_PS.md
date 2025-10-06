# Signing and Running PowerShell Scripts Across Machines

This guide explains how to **sign PowerShell scripts on one machine** and **execute them safely on another** by using code-signing certificates.

---

## 1. Why Sign PowerShell Scripts?

PowerShell’s execution policy prevents malicious or tampered scripts from running. Signing provides:

* **Authenticity** — verifies the script author.
* **Integrity** — ensures the script has not been altered.
* **Trust** — only scripts signed by trusted certificates will run.

---

## 2. Prerequisites

* Two Windows machines:

  * **Signer Machine** → creates a certificate and signs scripts.
  * **Execution Machine** → runs the signed scripts.
* Administrator rights on both machines.
* PowerShell 5.1 or later (Windows) or PowerShell 7+.

---

## 3. Generate a Code Signing Certificate

### Option A: Self-Signed Certificate (test/lab use)

On the **signer machine**:

```powershell
# Create a new self-signed code signing certificate
$cert = New-SelfSignedCertificate `
    -Type CodeSigningCert `
    -Subject "CN=MyCodeSigningCert" `
    -CertStoreLocation Cert:\CurrentUser\My

# Export certificate with private key (keep secure)
Export-PfxCertificate -Cert $cert `
    -FilePath "C:\Keys\MyCodeSigningCert.pfx" `
    -Password (Read-Host -AsSecureString)

# Export public certificate (to trust on other machines)
Export-Certificate -Cert $cert `
    -FilePath "C:\Keys\MyCodeSigningCert.cer"
```

* **.pfx** → contains the private key (used for signing). Keep safe.
* **.cer** → public key (used for trust). Share with other machines.

### Option B: Enterprise/CA Certificate

If using Active Directory Certificate Services (AD CS) or a purchased certificate, request a **Code Signing** certificate instead.

---

## 4. Sign the PowerShell Script

On the **signer machine**:

```powershell
# Import your PFX with private key
$cert = Import-PfxCertificate `
    -FilePath "C:\Keys\MyCodeSigningCert.pfx" `
    -CertStoreLocation Cert:\CurrentUser\My `
    -Password (Read-Host -AsSecureString)

# Sign the script
Set-AuthenticodeSignature `
    -FilePath "C:\Scripts\script.ps1" `
    -Certificate $cert
```

Verify:

```powershell
Get-AuthenticodeSignature "C:\Scripts\script.ps1"
```

Should show **Status: Valid**.

---

## 5. Trust the Certificate on the Execution Machine

Copy **MyCodeSigningCert.cer** to the execution machine.

On the **execution machine**:

```powershell
# Trust the certificate (Root + Trusted Publisher)
Import-Certificate -FilePath "C:\Keys\MyCodeSigningCert.cer" `
    -CertStoreLocation Cert:\LocalMachine\Root

Import-Certificate -FilePath "C:\Keys\MyCodeSigningCert.cer" `
    -CertStoreLocation Cert:\LocalMachine\TrustedPublisher
```

This step resolves the `UnknownError` issue.

---

## 6. Configure Execution Policy

On the **execution machine**:

```powershell
Set-ExecutionPolicy AllSigned -Scope LocalMachine
```

* **AllSigned** → all scripts must be signed.
* **RemoteSigned** → local scripts can run unsigned, remote ones must be signed.

---

## 7. Run the Signed Script

```powershell
.\script.ps1
```

If the script and certificate are valid, it runs without prompts.
If the script was edited after signing, you’ll need to re-sign it.

---

## 8. Troubleshooting

* **UnknownError**
  → Import the `.cer` into `Root` and `TrustedPublisher` stores.

* **Script edited after signing**
  → Re-sign the script.

* **Certificate missing private key**
  → Ensure `.pfx` with private key was imported.

* **Certificate expired**
  → Renew/reissue and re-sign scripts.

* **Add timestamp to signatures (optional)**

  ```powershell
  Set-AuthenticodeSignature `
      -FilePath "C:\Scripts\script.ps1" `
      -Certificate $cert `
      -TimestampServer "http://timestamp.digicert.com"
  ```

---

✅ **Summary**

1. Create/export certificate on signer machine.
2. Sign scripts using `.pfx`.
3. Import `.cer` on execution machine into trusted stores.
4. Set execution policy.
5. Run scripts with verified trust.

---
