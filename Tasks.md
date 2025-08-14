## **1. Core Setup (Easiest)**

* [ ] **Set up Django project** with apps: `users`, `hospitals`, `medications`, `prescriptions`.
* [ ] Configure **PostgreSQL** (Render-friendly).
* [ ] Install and configure **Django tenant-aware utilities** (our `TenantAwareManager`).
* [ ] Configure **custom user model** (`User` with doctor/patient flags, hospital FK).
* [ ] Add **gender** and **age** to `User` model (removing duplicates from doctor/patient).
* [ ] Implement **`TimestampMixin`** for created/updated tracking.

---

## **2. Multi-Tenant & Admin Integration**

* [ ] Finalize **`TenantAwareManager`** with combined Fix 1 + Fix 2 (hospital context + permission logic).
* [ ] Create **User Admin** with inline `Doctor` & `Patient` profiles.
* [ ] Allow **creating Doctor & Patient from their own admin pages** (auto-create linked User).
* [ ] Add `HospitalAdmin` with proper filters/search.

---

## **3. Medication & Prescription Logic**

* [ ] **Redesign `Prescription` & `PrescriptionSchedule`**:

  * Store dosage frequency (interval in hours or times per day).
  * Calculate **next dose** dynamically in Django (no background worker).
  * Handle start/end dates and missed doses.
* [ ] Add `hospital` FK to `Medication`, `Prescription`, `PrescriptionSchedule` (tenant separation).
* [ ] Implement clean method to **ensure doctor and patient belong to the same hospital**.
* [ ] Add **validation** for overlapping prescriptions.

---

## **4. On-Demand Scheduling (No Worker)**

* [ ] Create **service function** to compute:

  * Next dose time
  * Remaining doses
  * Late/missed doses
* [ ] Expose **“Check next dose”** button in the admin or a patient portal page.
* [ ] Make API endpoint for “next dose” so front-end can poll manually (instead of async tasks).

---

## **5. API Layer**

* [ ] Install **Django REST Framework**.
* [ ] Build endpoints:

  * Login & signup (hospital-bound)
  * Get user profile
  * List medications
  * Create prescription
  * Get next dose
  * Mark dose as taken
* [ ] Implement **DRF permissions** for doctors, patients, hospital admins.

---

## **6. UI & Patient Portal**

* [ ] Create minimal web UI (Django templates or small React app):

  * Doctor dashboard → manage patients & prescriptions
  * Patient dashboard → view prescriptions, next dose, and mark taken
* [ ] Add **filters** for today’s doses.

---

## **7. Deployment (Render)**

* [ ] Prepare **Procfile** (`web: gunicorn medimind.wsgi`).
* [ ] Configure environment variables in Render.
* [ ] Add **static files handling** (`whitenoise`).
* [ ] Run migrations on Render.
* [ ] Test multi-tenant restrictions on live site.

---

## **8. Final Enhancements (Hardest)**

* [ ] Implement **audit logging** for all prescription changes.
* [ ] Add **export** (CSV/PDF) for prescriptions.
* [ ] Add **basic notifications** (email-based instead of worker).
* [ ] Optimize queries for tenant filtering under concurrency.

