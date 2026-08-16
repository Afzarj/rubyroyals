document.addEventListener('DOMContentLoaded', function(){
  const repayment = document.getElementById('repayment');
  const detailsBlock = document.getElementById('repayment-details-block');
  const detailsSelect = document.getElementById('repayment_details');
  const scheduleDiv = document.getElementById('repayment-schedule');
  const form = document.getElementById('pledgeForm');

  console.log('[pledge] DOM ready. Elements:', {
    repayment: !!repayment,
    detailsBlock: !!detailsBlock,
    detailsSelect: !!detailsSelect,
    scheduleDiv: !!scheduleDiv,
    form: !!form
  });

  function showHideRepayment() {
    if (!repayment || !detailsBlock) return;
    const val = (repayment.value || '').toString().trim();
    console.log('[pledge] repayment changed ->', val);
    if (val === 'Full' || val === 'Partial') {
      detailsBlock.style.display = 'block';
    } else {
      detailsBlock.style.display = 'none';
      if (detailsSelect) detailsSelect.value = '';
      clearSchedule();
    }
  }

  function clearSchedule() {
    if (!scheduleDiv) return;
    while (scheduleDiv.firstChild) scheduleDiv.removeChild(scheduleDiv.firstChild);
    console.log('[pledge] cleared schedule');
  }

  function buildSchedule(n) {
    if (!scheduleDiv) return;
    clearSchedule();
    n = parseInt(n) || 0;
    console.log('[pledge] buildSchedule n=', n);
    for (let i = 1; i <= n; i++) {
      const row = document.createElement('div');
      row.className = 'row g-2 align-items-center mt-2';

      const colAmt = document.createElement('div');
      colAmt.className = 'col-6';
      const amtInput = document.createElement('input');
      amtInput.name = `repay_amount_${i}`;
      amtInput.type = 'number';
      amtInput.step = '0.01';
      amtInput.className = 'form-control';
      amtInput.placeholder = `Amount ${i}`;
      amtInput.required = true;
      colAmt.appendChild(amtInput);

      const colDate = document.createElement('div');
      colDate.className = 'col-6';
      const dateInput = document.createElement('input');
      dateInput.name = `repay_date_${i}`;
      dateInput.type = 'date';
      dateInput.className = 'form-control';
      dateInput.required = true;
      colDate.appendChild(dateInput);

      row.appendChild(colAmt);
      row.appendChild(colDate);
      scheduleDiv.appendChild(row);
    }
  }

  // Attach listeners safely
  if (repayment) repayment.addEventListener('change', showHideRepayment);
  if (detailsSelect) detailsSelect.addEventListener('change', function(){
    const v = (this.value || '').toString().trim();
    buildSchedule(v);
  });

  // Fallback debug helpers
  window.__pledge_debug = {
    show: () => { if (detailsBlock) detailsBlock.style.display = 'block'; },
    hide: () => { if (detailsBlock) detailsBlock.style.display = 'none'; clearSchedule(); },
    build: (n) => buildSchedule(n)
  };

  // initialize repayment section
  showHideRepayment();

  // -------------------------------
  // Tamil keyboard integration
  // -------------------------------
  // Tamil keyboard popup integration
const toggleTamil = document.getElementById('toggleTamilKeyboard');
const openTamilBtn = document.getElementById('openTamilKeyboard');
let activeInput = null;

// Track focused input/textarea
document.querySelectorAll('input, textarea').forEach(el => {
  el.addEventListener('focus', () => { activeInput = el; });
  el.addEventListener('blur', () => { activeInput = null; });
});

// Show/hide the "Open Keyboard" button
if (toggleTamil && openTamilBtn) {
  toggleTamil.addEventListener('change', function(){
    openTamilBtn.style.display = this.checked ? 'inline-block' : 'none';
  });
}

// Handle Tamil key clicks inside modal
document.querySelectorAll('.tamil-key').forEach(btn => {
  btn.addEventListener('click', function(){
    if (activeInput) {
      const char = this.textContent;
      const start = activeInput.selectionStart;
      const end = activeInput.selectionEnd;
      const value = activeInput.value;
      activeInput.value = value.slice(0, start) + char + value.slice(end);
      activeInput.selectionStart = activeInput.selectionEnd = start + char.length;
      activeInput.focus();
    }
  });
});

});
