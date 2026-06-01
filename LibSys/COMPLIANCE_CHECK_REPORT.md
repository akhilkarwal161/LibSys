# COMPLIANCE CHECK REPORT

## 1. Executive Summary
This report evaluates the LibSys application against industry compliance frameworks, including the CIS Docker Benchmarks, GDPR/PCI-DSS Secret Protections, Python PEP 8 style guides, and Django production deployment checklists. Non-compliance findings are cataloged with actionable remediation paths.

---

## 2. Compliance Framework Audit Matrix

| Compliance Standard | Status | Finding / Non-Compliance |
| :--- | :--- | :--- |
| **GDPR / PCI-DSS Secret Protection** | ❌ NON-COMPLIANT | Plain-text MySQL root database credentials found hardcoded in `Dockerfile` line 43. |
| **CIS Docker Benchmark (Least Privilege)** | ❌ NON-COMPLIANT | Container runs implicitly under `root` user permissions (lacks `USER` non-root specification). |
| **Django Security Check** | ⚠️ Partial | Allowed Hosts and CSRF trusted origins configured as wildcards in production environment presets. |
| **PEP 8 Standards** |  COMPLIANT | Standard Python naming conventions (except for legacy model attributes `Bid` and `Issue_No` which are PascalCase instead of snake_case). |
| **Permissive Dependency Licenses** |  COMPLIANT | All requirements (Django, DRF, etc.) utilize highly permissive licenses (MIT, BSD, Apache-2.0). No copyleft GPL-style licensing detected. |

---

## 3. Detailed Compliance Deficiencies & Remediations

### A. Docker Non-Root Execution Deficit (CIS Benchmark 4.1)
*   **Deficit:** The Dockerfile does not define a dedicated user. The container starts and runs Gunicorn with full `root` operating privileges. In the event of a container breakout, the host system is fully exploitable.
*   **Remediation:** Declare a non-root system user inside the Dockerfile:
    ```dockerfile
    RUN groupadd -r appgroup && useradd -r -g appgroup appuser
    WORKDIR /app
    ...
    USER appuser
    ```

### B. Insecure Hardcoded Secrets (GDPR/PCI-DSS Section 3)
*   **Deficit:** Storing database connection credentials (`Mahesh@2018`) in code files violates data privacy standards, exposing the internal backend database to unauthorized extraction.
*   **Remediation:** Remove plain-text lines. Utilize Secret Manager parameters mapped to env variables dynamically at the container startup lifecycle.

### C. PascalCase Attribute Legacy Schemas (PEP 8 Compliance)
*   **Deficit:** Attributes `Bid` and `Issue_No` violate snake_case column guidelines of Python PEP 8 and Django model design patterns.
*   **Remediation:** Plan migrations to normalize naming fields to `bid` and `issue_no` in future schema versions.

---

## 4. Audit Limitations
*   **Licensing Tree:** This compliance check did not perform an automated licensing recursive tree audit of transitive dependencies (sub-dependencies). Dynamic package compliance should be verified using automated auditing tools like `license-checker` or `safety`.
