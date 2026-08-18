// Generate ornament fields dynamically
function generateOrnaments() {
    const num = parseInt(document.getElementById("numOrnaments").value);
    const container = document.getElementById("ornamentsContainer");
    container.innerHTML = "";

    for (let i = 0; i < num; i++) {
        container.innerHTML += `
            <div class="ornament-block">
                <label>Ornament ${i+1} 
                    <select name="Ornament${i+1}" required>
                        <option>Chain</option><option>Necklace</option>
                        <option>Bangles</option><option>Ring</option>
                        <option>Stud</option><option>Ear Ring</option>
                        <option>Haram</option>
                    </select>
                </label>
                <label>Number of Ornaments* 
                    <select name="NumOrnament${i+1}" required>
                        <option>1</option><option>2</option><option>3</option>
                        <option>4</option><option>5</option>
                    </select>
                </label>
                <label>Grams 
                <input type="number" name="Grams${i+1}" step="0.01" min="0"
                        class="form-control" required oninput="updateTotals()">
                </label>

            </div>
        `;
    }
    updateTotals();
}

// Update totals for grams and balance jewellery
function updateTotals() {
    const gramInputs = document.querySelectorAll("[name^='Grams']");
    let total = 0;
    gramInputs.forEach(input => {
        const val = parseFloat(input.value) || 0;
        total += val;
    });
    document.getElementById("TotalGrams").value = total.toFixed(2);

    const returnVal = parseFloat(document.querySelector("[name='ReturnJewellery']").value) || 0;
    document.getElementById("BalanceJewellery").value = (total - returnVal).toFixed(2);
}


// Toggle repayment details
function toggleRepaymentDetails() {
    const repayment = document.getElementById("repayment").value;
    const container = document.getElementById("repaymentContainer");
    container.innerHTML = "";

    if (repayment === "Full" || repayment === "Partial") {
        container.innerHTML = `
            <label class="form-label">Repayment Details
                <select id="repaymentDetails" name="RepaymentDetails" class="form-select" required onchange="generateRepaymentFields()">
                    ${Array.from({length: 10}, (_, i) => `<option value="${i}">${i}</option>`).join("")}
                </select>
            </label>
            <div id="repaymentFields"></div>
        `;
    }
}

// Generate repayment amount/date fields
function generateRepaymentFields() {
    const num = parseInt(document.getElementById("repaymentDetails").value);
    const container = document.getElementById("repaymentFields");
    container.innerHTML = "";

    for (let i = 0; i < num; i++) {
        container.innerHTML += `
            <div class="repayment-block">
                <label>Amount ${i+1} 
                    <input type="number" name="RepayAmount${i+1}" required>
                </label>
                <label>Date ${i+1} 
                    <input type="date" name="RepayDate${i+1}" required>
                </label>
            </div>
        `;
    }
}

// Validation: prevent spaces in numeric fields
document.addEventListener("DOMContentLoaded", () => {
    const ornamentsEl = document.getElementById("numOrnaments");
    if (ornamentsEl && parseInt(ornamentsEl.value, 10) > 0) {
        generateOrnaments();
    }

    const repaymentEl = document.getElementById("repayment");
    if (repaymentEl && repaymentEl.value) {
        toggleRepaymentDetails();
    }

    const numericSelectors = [
        "Age", "AadharNumber", "BillNo", "HCClaimFormNumber",
        "TotalAmounts", "TotalGrams", "ReturnJewellery", "BalanceJewellery"
    ];

    numericSelectors.forEach(name => {
        const el = document.querySelector(`[name='${name}']`);
        if (el) {
            el.addEventListener("input", () => {
                if (/\s/.test(el.value)) {
                    el.value = el.value.replace(/\s/g, "");
                    alert(`Spaces are not allowed in ${name}`);
                }
            });
        }
    });

    // Keep balance updated when Return Jewellery changes
    const returnEl = document.querySelector("[name='ReturnJewellery']");
    if (returnEl) {
        returnEl.addEventListener("input", updateTotals);
    }
});
