/**
 * YES 2026 - Official Registration Portal
 * 3-Step Wizard Flow, Reference UI Cards, & Animated Processing Loader
 * VTU's Visvesvaraya Research and Innovation Foundation (VRIF), Belagavi
 */

let currentCategory = 'participant';
let currentStep = 1;

document.addEventListener('DOMContentLoaded', () => {
  initCategorySwitcher();
  initFormInputListeners();
  initWizardNavigation();
  updateLiveBadgePreview();
  updateTicketPricingSummary();
});

// ===================================================================
// 1. CATEGORY SWITCHER & TICKET PRICING SUMMARY
// ===================================================================
function initCategorySwitcher() {
  const tabs = document.querySelectorAll('.cat-tab');
  tabs.forEach(tab => {
    tab.addEventListener('click', () => {
      const cat = tab.getAttribute('data-category');
      switchCategory(cat);
    });
  });

  // Check URL params for category
  const urlParams = new URLSearchParams(window.location.search);
  const catParam = urlParams.get('category');
  if (catParam && ['participant', 'delegate', 'faculty', 'vip'].includes(catParam.toLowerCase())) {
    const resolvedCat = catParam.toLowerCase() === 'vip' ? 'faculty' : catParam.toLowerCase();
    switchCategory(resolvedCat);
  }
}

function switchCategory(cat) {
  currentCategory = cat;
  const tabs = document.querySelectorAll('.cat-tab');
  tabs.forEach(t => {
    t.classList.remove('active-participant', 'active-delegate', 'active-faculty', 'active-vip');
    if (t.getAttribute('data-category') === cat) {
      t.classList.add(`active-${cat}`);
    }
  });

  // Show/hide category customized fields
  document.querySelectorAll('.cat-fields-section').forEach(sec => {
    if (sec.getAttribute('data-cat') === cat) {
      sec.style.display = 'contents';
    } else {
      sec.style.display = 'none';
    }
  });

  // Update card header badge or title if present
  const pill = document.getElementById('form-cat-pill');
  if (pill) {
    pill.textContent = cat.toUpperCase() + ' PASS';
    pill.className = `form-badge-pill pill-cat-${cat}`;
  }

  updateTicketPricingSummary();
  updateLiveBadgePreview();
}

function updateTicketPricingSummary() {
  const displayTicket = document.getElementById('display_ticket_type');
  const feeLabel = document.getElementById('ticket-fee-label');
  const feeVal = document.getElementById('ticket-fee-val');
  const feeSub = document.getElementById('ticket-fee-sub');

  if (!displayTicket || !feeVal) return;

  if (currentCategory === 'delegate') {
    displayTicket.value = 'Delegate Pass - ₹1,000 + Applicable Taxes';
    feeLabel.textContent = 'Amount (incl. GST):';
    feeVal.textContent = '₹1,180';
    feeVal.style.color = '#0284c7';
    feeSub.textContent = '1 delegate × ₹1,000 | Base: ₹1,000 + GST (18%): ₹180. Includes B2B Matchmaking Suite and Industry Roundtables.';
  } else if (currentCategory === 'faculty') {
    displayTicket.value = 'Faculty & Academic Pass - Institutional Conclave & Mentorship';
    feeLabel.textContent = 'Institutional Pass Access:';
    feeVal.textContent = 'Complimentary';
    feeVal.style.color = '#7c3aed';
    feeSub.textContent = 'Authorized for professors, deans, and research scholars from VTU affiliated colleges & partner universities.';
  } else {
    displayTicket.value = 'Participant Pass - Complimentary Academic / Innovator Access';
    feeLabel.textContent = 'Pass Access Fee:';
    feeVal.textContent = '₹0 (Free Access)';
    feeVal.style.color = '#ea580c';
    feeSub.textContent = 'Includes entry to technical hackathons, prototype showcase exhibits, TBI open sessions, and digital pass.';
  }
}

// ===================================================================
// 2. LIVE BADGE PREVIEW GENERATOR
// ===================================================================
function initFormInputListeners() {
  const inputs = [
    'full_name', 'organization', 'designation', 'track_or_industry',
    'faculty_title', 'faculty_dept', 'faculty_role', 'faculty_college_code',
    'faculty_engagement', 'faculty_specialization', 'vip_honorific'
  ];
  inputs.forEach(id => {
    const el = document.getElementById(id);
    if (el) {
      el.addEventListener('input', () => {
        el.classList.remove('has-error');
        const errMsg = document.getElementById(`err-${id}`);
        if (errMsg) errMsg.style.display = 'none';
        updateLiveBadgePreview();
      });
      el.addEventListener('change', () => {
        el.classList.remove('has-error');
        const errMsg = document.getElementById(`err-${id}`);
        if (errMsg) errMsg.style.display = 'none';
        updateLiveBadgePreview();
      });
    }
  });
}

function getInitials(name) {
  if (typeof BadgeManager !== 'undefined' && BadgeManager && typeof BadgeManager.getInitials === 'function') {
    return BadgeManager.getInitials(name);
  }
  if (!name || name === 'Attendee Name') return 'YES';
  return name
    .split(' ')
    .filter(p => p.length > 0)
    .slice(0, 2)
    .map(p => p[0].toUpperCase())
    .join('');
}

function updateLiveBadgePreview() {
  let name = document.getElementById('full_name')?.value?.trim() || 'Attendee Name';
  const org = document.getElementById('organization')?.value?.trim() || 'Organization / Institution';
  let role = document.getElementById('designation')?.value?.trim();
  
  if (currentCategory === 'faculty' || currentCategory === 'vip') {
    const honorific = document.getElementById('faculty_title')?.value || document.getElementById('vip_honorific')?.value || 'Prof.';
    const facRole = document.getElementById('faculty_role')?.value;
    if (!role) role = facRole ? `${honorific} ${facRole}` : `${honorific} / Academic Mentor`;
  } else if (currentCategory === 'delegate') {
    if (!role) role = 'Corporate Delegate';
  } else {
    if (!role) role = 'Attendee';
  }

  // Update Preview Elements across badges
  const badges = document.querySelectorAll('.preview-badge-card');
  badges.forEach(badge => {
    badge.className = `preview-badge-card badge-${currentCategory}`;
  });

  const names = document.querySelectorAll('.preview-name');
  names.forEach(n => { n.textContent = name; });

  const roles = document.querySelectorAll('.preview-role');
  roles.forEach(r => { r.textContent = role; });

  const orgs = document.querySelectorAll('.preview-org');
  orgs.forEach(o => { o.textContent = org; });

  const initials = document.querySelectorAll('.badge-photo-placeholder span, #preview-initials');
  initials.forEach(i => { i.textContent = getInitials(name); });

  const catBanners = document.querySelectorAll('.badge-cat-banner');
  catBanners.forEach(b => {
    if (currentCategory === 'faculty' || currentCategory === 'vip') {
      b.textContent = 'FACULTY & RESEARCH PASS';
      b.style.background = 'linear-gradient(90deg, #6d28d9, #7c3aed)';
      b.style.color = '#fff';
    } else if (currentCategory === 'delegate') {
      b.textContent = 'OFFICIAL DELEGATE';
      b.style.background = 'linear-gradient(90deg, #0369a1, #0284c7)';
      b.style.color = '#fff';
    } else {
      b.textContent = 'PARTICIPANT PASS';
      b.style.background = 'linear-gradient(90deg, #c2410c, #ea580c)';
      b.style.color = '#fff';
    }
  });
}

// ===================================================================
// 3. WIZARD STEPPER NAVIGATION & VALIDATION
// ===================================================================
function initWizardNavigation() {
  // Step 1 -> Step 2 Button
  const btnToStep2 = document.getElementById('btn-to-step-2');
  if (btnToStep2) {
    btnToStep2.addEventListener('click', () => {
      if (validateStep1()) {
        populateReviewSummary();
        goToStep(2);
      }
    });
  }

  // Step 2 -> Step 1 (Back to Edit)
  const btnBackTo1 = document.getElementById('btn-back-to-step-1');
  if (btnBackTo1) {
    btnBackTo1.addEventListener('click', () => {
      goToStep(1);
    });
  }

  // Step 2 -> Submit (Confirm & Complete Registration)
  const btnConfirm = document.getElementById('btn-confirm-registration');
  if (btnConfirm) {
    btnConfirm.addEventListener('click', () => {
      const termsCheck = document.getElementById('review-terms');
      if (termsCheck && !termsCheck.checked) {
        alert('Please accept the declaration checkbox to complete registration.');
        return;
      }
      processRegistration();
    });
  }

  // Step 3 -> Register Another Attendee
  const btnRegisterAnother = document.getElementById('btn-register-another');
  if (btnRegisterAnother) {
    btnRegisterAnother.addEventListener('click', () => {
      const form = document.getElementById('registration-form');
      if (form) form.reset();
      updateLiveBadgePreview();
      updateTicketPricingSummary();
      goToStep(1);
    });
  }
}

function goToStep(step) {
  currentStep = step;

  // 1. Update Stepper Node Classes
  const stepNodes = [
    document.getElementById('step-node-1'),
    document.getElementById('step-node-2'),
    document.getElementById('step-node-3')
  ];
  const stepConnectors = [
    document.getElementById('step-conn-1'),
    document.getElementById('step-conn-2')
  ];

  stepNodes.forEach((node, idx) => {
    if (!node) return;
    const nodeNum = idx + 1;
    node.classList.remove('active', 'completed');
    if (nodeNum < step) {
      node.classList.add('completed');
    } else if (nodeNum === step) {
      node.classList.add('active');
    }
  });

  if (stepConnectors[0]) {
    stepConnectors[0].classList.toggle('completed', step >= 2);
  }
  if (stepConnectors[1]) {
    stepConnectors[1].classList.toggle('completed', step >= 3);
  }

  // 2. Show/Hide Step Containers
  const view1 = document.getElementById('step-1-view');
  const view2 = document.getElementById('step-2-view');
  const view3 = document.getElementById('step-3-view');

  if (view1) view1.style.display = (step === 1) ? 'block' : 'none';
  if (view2) view2.style.display = (step === 2) ? 'block' : 'none';
  if (view3) view3.style.display = (step === 3) ? 'block' : 'none';

  // 3. Move Live Badge into Step 2 preview target if in Step 2
  if (step === 2) {
    const origBadge = document.getElementById('live-preview-badge');
    const step2Placeholder = document.getElementById('step-2-badge-placeholder');
    if (origBadge && step2Placeholder) {
      step2Placeholder.innerHTML = '';
      step2Placeholder.appendChild(origBadge);
    }
  } else if (step === 1) {
    const origBadge = document.getElementById('live-preview-badge');
    const step1BadgeCol = document.querySelector('#step-1-view .badge-preview-column');
    if (origBadge && step1BadgeCol && !step1BadgeCol.contains(origBadge)) {
      step1BadgeCol.appendChild(origBadge);
    }
  }

  // Scroll up to wizard card smoothly
  const wizardCard = document.querySelector('.reg-wizard-card');
  if (wizardCard) {
    wizardCard.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }
}

function validateStep1() {
  const form = document.getElementById('registration-form');
  if (!form) return false;

  let isValid = true;
  let firstErrorElem = null;

  const requiredFields = [
    { id: 'full_name', errId: 'err-full_name' },
    { id: 'email', errId: 'err-email' },
    { id: 'phone', errId: 'err-phone' },
    { id: 'organization', errId: 'err-organization' }
  ];

  requiredFields.forEach(f => {
    const el = document.getElementById(f.id);
    const errEl = document.getElementById(f.errId);
    if (!el) return;

    const val = (el.value || '').trim();
    if (!val || (f.id === 'email' && !val.includes('@'))) {
      el.classList.add('has-error');
      if (errEl) errEl.style.display = 'block';
      isValid = false;
      if (!firstErrorElem) firstErrorElem = el;
    } else {
      el.classList.remove('has-error');
      if (errEl) errEl.style.display = 'none';
    }
  });

  if (!isValid && firstErrorElem) {
    firstErrorElem.focus();
    firstErrorElem.scrollIntoView({ behavior: 'smooth', block: 'center' });
  }

  return isValid;
}

// ===================================================================
// 4. STEP 2: REVIEW SUMMARY GENERATOR
// ===================================================================
function populateReviewSummary() {
  const form = document.getElementById('registration-form');
  if (!form) return;

  const formData = new FormData(form);
  const target = document.getElementById('review-content-target');
  if (!target) return;

  const fullName = (formData.get('full_name') || '').trim();
  const email = (formData.get('email') || '').trim();
  const phone = (formData.get('phone') || '').trim();
  const org = (formData.get('organization') || '').trim();
  const role = (formData.get('designation') || 'Attendee').trim();
  const orgType = (formData.get('org_type') || 'Academic Institution').trim();
  const track = (formData.get('track_or_industry') || 'Artificial Intelligence & AGI').trim();

  let catLabel = 'Participant Pass';
  let catColor = '#ea580c';
  if (currentCategory === 'delegate') {
    catLabel = 'Official Corporate Delegate';
    catColor = '#0284c7';
  } else if (currentCategory === 'faculty') {
    catLabel = 'Faculty / Academic Pass';
    catColor = '#7c3aed';
  }

  let catSpecificHTML = '';
  if (currentCategory === 'participant') {
    catSpecificHTML = `
      <div class="review-section-heading">Participant Credentials & Swag</div>
      <div class="review-grid">
        <div class="review-item">
          <div class="review-item-lbl">Swag T-Shirt Size</div>
          <div class="review-item-val">${formData.get('tshirt_size') || 'M'}</div>
        </div>
        <div class="review-item">
          <div class="review-item-lbl">Portfolio / GitHub</div>
          <div class="review-item-val">${formData.get('portfolio_url') || 'Not provided'}</div>
        </div>
        <div class="review-item" style="grid-column: span 2;">
          <div class="review-item-lbl">Technical Interests</div>
          <div class="review-item-val">${formData.get('interests') || 'Autonomous AI & Frontier Systems'}</div>
        </div>
      </div>
    `;
  } else if (currentCategory === 'delegate') {
    catSpecificHTML = `
      <div class="review-section-heading">Corporate & Executive Networking</div>
      <div class="review-grid">
        <div class="review-item">
          <div class="review-item-lbl">B2B Matchmaking</div>
          <div class="review-item-val">${formData.get('b2b_networking') || 'Yes'}</div>
        </div>
        <div class="review-item">
          <div class="review-item-lbl">Company GSTIN / Tax ID</div>
          <div class="review-item-val">${formData.get('tax_id') || 'Not specified'}</div>
        </div>
      </div>
    `;
  } else if (currentCategory === 'faculty') {
    catSpecificHTML = `
      <div class="review-section-heading">Academic & Conclave Credentials</div>
      <div class="review-grid">
        <div class="review-item">
          <div class="review-item-lbl">Title & Position</div>
          <div class="review-item-val">${formData.get('faculty_title') || 'Prof.'} ${formData.get('faculty_role') || 'Professor'}</div>
        </div>
        <div class="review-item">
          <div class="review-item-lbl">Academic Department</div>
          <div class="review-item-val">${formData.get('faculty_dept') || 'Engineering & Technology'}</div>
        </div>
        <div class="review-item">
          <div class="review-item-lbl">VTU College / Faculty Code</div>
          <div class="review-item-val">${formData.get('faculty_college_code') || 'VTU Belagavi'}</div>
        </div>
        <div class="review-item">
          <div class="review-item-lbl">Conclave Engagement</div>
          <div class="review-item-val">${formData.get('faculty_engagement') || 'Startup Mentor'}</div>
        </div>
        <div class="review-item" style="grid-column: span 2;">
          <div class="review-item-lbl">Research Specialization</div>
          <div class="review-item-val">${formData.get('faculty_specialization') || 'Artificial Intelligence & Deep Tech'}</div>
        </div>
      </div>
    `;
  }

  target.innerHTML = `
    <div class="review-section-heading">Ticket & Summit Pathway</div>
    <div class="review-grid">
      <div class="review-item">
        <div class="review-item-lbl">Registration Category</div>
        <div class="review-item-val" style="color: ${catColor}; font-weight: 800;">${catLabel}</div>
      </div>
      <div class="review-item">
        <div class="review-item-lbl">Primary Summit Track</div>
        <div class="review-item-val">${track}</div>
      </div>
    </div>

    <div class="review-section-heading">Attendee Details</div>
    <div class="review-grid">
      <div class="review-item">
        <div class="review-item-lbl">Full Legal Name</div>
        <div class="review-item-val">${fullName}</div>
      </div>
      <div class="review-item">
        <div class="review-item-lbl">Email Address</div>
        <div class="review-item-val">${email}</div>
      </div>
      <div class="review-item">
        <div class="review-item-lbl">Phone Number</div>
        <div class="review-item-val">${phone}</div>
      </div>
      <div class="review-item">
        <div class="review-item-lbl">Organization / College</div>
        <div class="review-item-val">${org}</div>
      </div>
      <div class="review-item">
        <div class="review-item-lbl">Designation / Role</div>
        <div class="review-item-val">${role}</div>
      </div>
      <div class="review-item">
        <div class="review-item-lbl">Organisation Type</div>
        <div class="review-item-val">${orgType}</div>
      </div>
    </div>

    ${catSpecificHTML}
  `;
}

// ===================================================================
// 5. REGISTRATION SUBMISSION & ANIMATED LOADER OVERLAY
// ===================================================================
async function processRegistration() {
  const form = document.getElementById('registration-form');
  if (!form) return;

  const overlay = document.getElementById('processing-loader-overlay');
  const statusMsg = document.getElementById('processing-status-text');

  // 1. Show Animated Processing Loader
  if (overlay) {
    overlay.classList.add('active');
  }

  // Pulsing dynamic status updates during issuance
  let statusIdx = 0;
  const statusUpdates = [
    'Encrypting attendee credentials and creating summit record...',
    'Generating camera-optimized high-contrast QR pass card...',
    'Compiling official vector print-ready PDF badge...',
    'Finalizing official registration ID and dispatching confirmation...'
  ];

  if (statusMsg) {
    statusMsg.textContent = statusUpdates[0];
  }

  const statusInterval = setInterval(() => {
    statusIdx = (statusIdx + 1) % statusUpdates.length;
    if (statusMsg) statusMsg.textContent = statusUpdates[statusIdx];
  }, 1100);

  // Gather Form Data
  const formData = new FormData(form);
  const data = {
    category: currentCategory || 'participant',
    full_name: (formData.get('full_name') || '').trim(),
    email: (formData.get('email') || '').trim(),
    phone: (formData.get('phone') || '').trim(),
    organization: (formData.get('organization') || '').trim(),
    designation: (formData.get('designation') || '').trim(),
    track_or_industry: (formData.get('track_or_industry') || 'General').trim(),
    custom_fields: {}
  };

  if (currentCategory === 'participant') {
    data.custom_fields = {
      tshirt_size: formData.get('tshirt_size') || 'M',
      portfolio_url: formData.get('portfolio_url') || '',
      interests: formData.get('interests') || ''
    };
  } else if (currentCategory === 'delegate') {
    data.custom_fields = {
      b2b_networking: formData.get('b2b_networking') || 'Yes',
      tax_id: formData.get('tax_id') || ''
    };
  } else if (currentCategory === 'faculty' || currentCategory === 'vip') {
    data.custom_fields = {
      title: formData.get('faculty_title') || formData.get('vip_honorific') || 'Prof.',
      academic_role: formData.get('faculty_role') || 'Professor & HOD',
      department: formData.get('faculty_dept') || '',
      college_code: formData.get('faculty_college_code') || '',
      engagement_role: formData.get('faculty_engagement') || 'Startup Mentor / Pitch Evaluator',
      specialization: formData.get('faculty_specialization') || ''
    };
  }

  try {
    const resp = await fetch('/api/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });

    let result;
    try {
      result = await resp.json();
    } catch (jsonErr) {
      throw new Error(`Server returned HTTP ${resp.status}`);
    }

    clearInterval(statusInterval);

    if (result.success && result.attendee) {
      // Small graceful pause so user sees finalization
      await new Promise(r => setTimeout(r, 600));

      if (overlay) overlay.classList.remove('active');

      fireConfetti();
      populateStep3Confirmation(result);
      goToStep(3);
    } else {
      if (overlay) overlay.classList.remove('active');

      if (result.error_type === 'DUPLICATE_EMAIL') {
        const activeForm = document.querySelector(`.registration-form[data-category="${currentCategory}"]`);
        const emailInput = activeForm ? activeForm.querySelector('input[type="email"]') : null;
        if (emailInput) {
          emailInput.style.borderColor = '#ef4444';
          emailInput.style.boxShadow = '0 0 0 3px rgba(239, 68, 68, 0.25)';
          emailInput.focus();
        }
      }
      alert(result.error || 'Failed to complete registration. Please check your details.');
    }
  } catch (err) {
    clearInterval(statusInterval);
    if (overlay) overlay.classList.remove('active');
    console.error('[Registration Error]', err);
    alert('Registration network notice: ' + err.message);
  }
}

// ===================================================================
// 6. STEP 3: CONFIRMATION VIEW POPULATION
// ===================================================================
function populateStep3Confirmation(data) {
  const attendee = data.attendee;
  if (!attendee) return;

  const regId = attendee.registration_id;

  const setElText = (id, txt) => {
    const el = document.getElementById(id);
    if (el) el.textContent = txt;
  };

  setElText('step3-reg-id', regId);
  setElText('step3-attendee-name', attendee.full_name);
  setElText('step3-attendee-org', attendee.organization);
  setElText('step3-attendee-email', attendee.email);

  // Category pill
  const catPill = document.getElementById('step3-attendee-cat');
  if (catPill) {
    catPill.textContent = (attendee.category || 'PARTICIPANT').toUpperCase() + ' PASS';
    catPill.className = `pill-cat pill-cat-${attendee.category || 'participant'}`;
  }

  // QR Code image
  const qrImg = document.getElementById('step3-qr-img');
  if (qrImg) {
    if (regId) {
      qrImg.src = `/api/registration/${encodeURIComponent(regId)}/qr.png?v=${Date.now()}`;
    } else if (data.qr_code_base64) {
      qrImg.src = data.qr_code_base64;
    }
  }

  // Dedicated QR Pass PNG Download
  const dlQrPass = document.getElementById('step3-dl-qr-pass');
  if (dlQrPass && regId) {
    dlQrPass.href = `/api/registration/${encodeURIComponent(regId)}/qr-pass.png`;
    dlQrPass.download = `YES2026_QR_Pass_${regId}.png`;
  }

  // Official PDF Badge Download
  const dlPdf = document.getElementById('step3-dl-pdf');
  if (dlPdf && regId) {
    dlPdf.href = `/api/registration/${encodeURIComponent(regId)}/pdf`;
    dlPdf.download = `YES2026_Badge_${regId}.pdf`;
  }
}

// ===================================================================
// 7. CONFETTI CELEBRATION
// ===================================================================
function fireConfetti() {
  try {
    const colors = ['#ea580c', '#0284c7', '#7c3aed', '#16a34a', '#f59e0b'];
    const container = document.body;

    for (let i = 0; i < 40; i++) {
      const el = document.createElement('div');
      el.className = 'confetti-piece';
      el.style.position = 'fixed';
      el.style.width = Math.floor(Math.random() * 8 + 6) + 'px';
      el.style.height = Math.floor(Math.random() * 12 + 8) + 'px';
      el.style.backgroundColor = colors[Math.floor(Math.random() * colors.length)];
      el.style.left = Math.random() * 100 + 'vw';
      el.style.top = '-20px';
      el.style.borderRadius = '2px';
      el.style.zIndex = '99999';
      el.style.opacity = '1';
      el.style.transform = `rotate(${Math.random() * 360}deg)`;
      el.style.transition = `all ${Math.random() * 2 + 2}s cubic-bezier(0.25, 1, 0.5, 1)`;

      container.appendChild(el);

      setTimeout(() => {
        el.style.top = '105vh';
        el.style.transform = `rotate(${Math.random() * 720}deg) translateX(${Math.random() * 80 - 40}px)`;
        el.style.opacity = '0';
      }, 50);

      setTimeout(() => {
        if (el.parentNode) el.parentNode.removeChild(el);
      }, 3500);
    }
  } catch (e) {
    // Non-essential visual decoration
  }
}
