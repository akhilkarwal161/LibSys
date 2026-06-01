# SECURITY AUDIT REPORT

## 1. Executive Summary
This report performs a Maestro-style security assessment of the LibSys Django application, analyzing Trust Boundaries, Secret Handling, Authentication/Authorization, and Exploitation risks. Unsafe API exposures and credential leakage are addressed with CVSS-aligned severity rankings.

---

## 2. Trust Boundaries & Data Flows
```
[Unauthenticated Client] ---> [REST API Endpoints (Home/api/)] ---> [Write/Read Book Data]
                                                                          | (Bypass Access Control)
                                                                          v
[Internal Application]  ---> [Production Database (Cloud SQL)] <--- [Exposed Plaintext Secrets]
```

---

## 3. Vulnerability Classification & Analysis

### A. API Authorization Bypass (OWASP A01:2021-Broken Access Control)
*   **Severity:** **HIGH (CVSS: 8.1 - CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:N)**
*   **File Reference:** [Home/api/views.py](file:///F:/REpo/LibSys/LibSys/Home/api/views.py)
*   **Vulnerability Details:** The REST API controllers `BookCreate`, `BookList`, `IssuedCreate`, and `IssuedList` do not specify `permission_classes`. Consequently, anonymous clients can modify database records, creating new catalog entries or manipulating checkouts without login tokens.
*   **Remediation:** Apply global DRF settings or individual class permissions:
    ```python
    permission_classes = [IsAuthenticated]
    ```

### B. Leakage of Production Database Connection Secret
*   **Severity:** **CRITICAL (CVSS: 9.8 - CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:H/A:H)**
*   **File Reference:** [Dockerfile:L43](file:///F:/REpo/LibSys/Dockerfile#L43)
*   **Vulnerability Details:** Plain-text credentials for the production MySQL database (`DATABASE_URL=mysql://root:Mahesh@2018@34.38.41.15:3306/libsys_db`) are hardcoded directly in the deployment Dockerfile.
*   **Remediation:** Remove plain-text connection strings. Source values dynamically from GCP Secret Manager during run-time deployment.

### C. Insecure Configuration Wildcards (OWASP A05:2021-Security Misconfiguration)
*   **Severity:** **MEDIUM (CVSS: 6.5 - CVSS:3.1/AV:N/AC:L/PR:N/UI:R/S:U/C:L/I:H/A:N)**
*   **File Reference:** [Dockerfile:L38-L39](file:///F:/REpo/LibSys/Dockerfile#L38-L39)
*   **Vulnerability Details:** `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS` are configured as wildcards (`*`). This permits Host Header Injection attacks, web cache poisoning, and CSRF protection bypasses.
*   **Remediation:** Replace wildcards with exact deployment hostnames:
    ```env
    ALLOWED_HOSTS=libsys.akhilkarwal.com
    CSRF_TRUSTED_ORIGINS=https://libsys.akhilkarwal.com
    ```

---

## 4. Prioritized Remediation Timeline
1.  **Phase 1 (Immediate):** Apply REST API `IsAuthenticated` access controls.
2.  **Phase 2 (Immediate):** Clean plains-text credentials from Dockerfile.
3.  **Phase 3 (Next Deploy):** Secure Allowed Hosts and CSRF trusted origin lists.
