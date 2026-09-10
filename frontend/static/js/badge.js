/**
 * NEXUS 2026 - Category-Specific ID Card (Lanyard Badge) Generator & Print
 */

const BadgeManager = {
  getInitials(name) {
    if (!name) return "YES";
    const parts = name.trim().split(" ");
    if (parts.length === 1) return parts[0].substring(0, 2).toUpperCase();
    return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
  },

  getCategoryConfig(category) {
    const cat = (category || "participant").toLowerCase();
    if (cat === "faculty" || cat === "vip") {
      return {
        className: "badge-faculty",
        title: "FACULTY & RESEARCH PASS",
        roleDefault: "Professor / Academic Mentor",
        ribbonText: "ACADEMIC CONCLAVE • R&D SESSIONS",
        badgeBorder: "#7c3aed"
      };
    } else if (cat === "delegate") {
      return {
        className: "badge-delegate",
        title: "OFFICIAL DELEGATE",
        roleDefault: "Corporate / Industry Executive",
        ribbonText: "B2B SUITES • NETWORKING DINNER",
        badgeBorder: "#0284c7"
      };
    } else {
      return {
        className: "badge-participant",
        title: "PARTICIPANT / INNOVATOR",
        roleDefault: "Summit Innovator",
        ribbonText: "TOP 20 SHOWCASE • TBI SESSIONS",
        badgeBorder: "#ff5722"
      };
    }
  },

  createBadgeHTML(attendee) {
    const config = this.getCategoryConfig(attendee.category);
    const initials = this.getInitials(attendee.full_name);
    const qrSrc = attendee.qr_base64 
      ? `data:image/png;base64,${attendee.qr_base64}` 
      : `/api/registration/${attendee.registration_id}/qr.png`;

    return `
      <div class="lanyard-badge ${config.className}" id="printable-badge-card">
        <!-- Punch hole for lanyard clip -->
        <div class="badge-punch-hole"></div>

        <!-- Top summit branding -->
        <div class="badge-top-bar">
          <div style="display: flex; align-items: center; justify-content: center; gap: 8px; margin-bottom: 4px;">
            <img src="/static/img/VRIF%20LOGO.png" alt="VRIF" style="height: 22px; background: white; padding: 2px 4px; border-radius: 4px; object-fit: contain;">
            <img src="/static/img/Young%20Entrepreneur%20SuMmit%20(9).png" alt="YES Mascot" style="height: 22px; object-fit: contain;">
          </div>
          <div class="badge-event-title">YES 2026</div>
          <div class="badge-event-subtitle">YOUNG ENTREPRENEURS SUMMIT • VTU VRIF</div>
        </div>

        <!-- Category Banner Stripe -->
        <div class="badge-category-stripe">${config.title}</div>

        <!-- Main Body -->
        <div class="badge-body">
          <div class="badge-avatar-ring">
            <div class="badge-avatar-inner">${initials}</div>
          </div>

          <div class="badge-name">${attendee.full_name || 'Attendee Name'}</div>
          <div class="badge-title">${attendee.designation || config.roleDefault}</div>
          <div class="badge-org">${attendee.organization || 'Organization'}</div>

          <div class="badge-qr-container">
            <img src="${qrSrc}" alt="Badge QR Code" />
          </div>

          <div class="badge-reg-code">${attendee.registration_id || 'YES26-0000'}</div>
        </div>

        <!-- Bottom bar & venue info -->
        <div class="badge-bottom-bar">
          <span>SEPT 27-28, 2026</span>
          <span>${config.ribbonText}</span>
          <span>VTU BELAGAVI</span>
        </div>
      </div>
    `;
  },

  async openModal(attendeeOrId) {
    if (!attendeeOrId) {
      if (window.currentScannedAttendee) attendeeOrId = window.currentScannedAttendee;
      else return;
    }

    let attendee = attendeeOrId;
    if (typeof attendeeOrId === 'string') {
      if (window.currentScannedAttendee && window.currentScannedAttendee.registration_id === attendeeOrId) {
        attendee = window.currentScannedAttendee;
      } else {
        try {
          const resp = await fetch(`/api/registration/${attendeeOrId}`);
          const res = await resp.json();
          if (res.success && res.attendee) {
            attendee = res.attendee;
          } else {
            attendee = { registration_id: attendeeOrId, full_name: 'Registered Attendee', category: 'participant' };
          }
        } catch (e) {
          attendee = { registration_id: attendeeOrId, full_name: 'Registered Attendee', category: 'participant' };
        }
      }
    }

    let modal = document.getElementById('badge-modal');
    if (!modal) {
      modal = document.createElement('div');
      modal.id = 'badge-modal';
      modal.className = 'modal-overlay';
      modal.innerHTML = `
        <div class="badge-modal-content">
          <button class="modal-close-btn" onclick="BadgeManager.closeModal()">&times;</button>
          
          <div style="margin-bottom: 12px; text-align: left;">
            <span style="font-size: 11px; font-weight: 800; color: var(--primary); text-transform: uppercase; letter-spacing: 0.5px;">Official Lanyard Credential</span>
            <h3 style="font-size: 20px; font-weight: 800; margin-top: 2px;">Printable Attendee ID Badge</h3>
          </div>

          <div id="badge-modal-render-target"></div>

          <div class="badge-actions-bar ticket-actions" style="margin-top: 20px; display: flex; gap: 10px; justify-content: center; flex-wrap: wrap;">
            <button class="btn btn-primary" onclick="BadgeManager.printBadge()" style="display: inline-flex; align-items: center; gap: 8px;">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M6 9V2h12v7M6 18H4a2 2 0 01-2-2v-5a2 2 0 012-2h16a2 2 0 012 2v5a2 2 0 01-2 2h-2"/><path d="M6 14h12v8H6z"/></svg>
              Print Lanyard Badge
            </button>
            <a id="badge-modal-pdf-link" href="#" target="_blank" class="btn btn-outline-cyan" style="display: inline-flex; align-items: center; gap: 8px;">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="12" y1="18" x2="12" y2="12"/><line x1="9" y1="15" x2="15" y2="15"/></svg>
              Printable PDF Pass
            </a>
            <button class="btn btn-secondary" onclick="BadgeManager.closeModal()">Close</button>
          </div>
        </div>
      `;
      document.body.appendChild(modal);

      modal.addEventListener('click', (e) => {
        if (e.target === modal) BadgeManager.closeModal();
      });

      document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') BadgeManager.closeModal();
      });
    }

    const target = document.getElementById('badge-modal-render-target');
    if (target) target.innerHTML = this.createBadgeHTML(attendee);

    const pdfLink = document.getElementById('badge-modal-pdf-link');
    if (pdfLink && attendee.registration_id) {
      pdfLink.href = `/api/registration/${attendee.registration_id}/pdf`;
      pdfLink.title = 'Open printable PDF format in new window';
    }

    modal.classList.add('active');
  },

  closeModal() {
    const modal = document.getElementById('badge-modal');
    if (modal) modal.classList.remove('active');
  },

  printBadge() {
    window.print();
  }
};

window.BadgeManager = BadgeManager;
