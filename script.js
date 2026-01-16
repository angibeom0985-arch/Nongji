document.addEventListener('DOMContentLoaded', () => {
    // === Logic Constants ===
    const AGE_FACTORS = {
        60: { life: 230000, term5: 1600000, term10: 850000, term15: 600000 },
        61: { life: 245000, term5: 1630000, term10: 870000, term15: 620000 },
        62: { life: 260000, term5: 1660000, term10: 890000, term15: 640000 },
        63: { life: 275000, term5: 1690000, term10: 910000, term15: 660000 },
        64: { life: 290000, term5: 1720000, term10: 930000, term15: 680000 },
        65: { life: 305000, term5: 1750000, term10: 950000, term15: 700000 },
        66: { life: 322000, term5: 1780000, term10: 975000, term15: 720000 },
        67: { life: 340000, term5: 1810000, term10: 1000000, term15: 740000 },
        68: { life: 358000, term5: 1840000, term10: 1025000, term15: 760000 },
        69: { life: 377000, term5: 1870000, term10: 1050000, term15: 780000 },
        70: { life: 397000, term5: 1900000, term10: 1075000, term15: 800000 },
        71: { life: 418000, term5: 1930000, term10: 1100000, term15: 820000 },
        72: { life: 440000, term5: 1960000, term10: 1125000, term15: 840000 },
        73: { life: 463000, term5: 1990000, term10: 1150000, term15: 860000 },
        74: { life: 487000, term5: 2020000, term10: 1175000, term15: 880000 },
        75: { life: 512000, term5: 2050000, term10: 1200000, term15: 900000 },
        76: { life: 538000, term5: 2080000, term10: 1225000, term15: 920000 },
        77: { life: 565000, term5: 2110000, term10: 1250000, term15: 940000 },
        78: { life: 593000, term5: 2140000, term10: 1275000, term15: 960000 },
        79: { life: 622000, term5: 2170000, term10: 1300000, term15: 980000 },
        80: { life: 652000, term5: 2200000, term10: 1325000, term15: 1000000 },
        max: { life: 750000, term5: 2500000, term10: 1500000, term15: 1200000 }
    };

    // === UI Elements ===
    const landValueInput = document.getElementById('landValue');
    const actualEvalDisplay = document.getElementById('actualEvalAmount');
    const spouseToggle = document.getElementById('spouseToggle');
    const spouseDobGroup = document.getElementById('spouseDobGroup');
    const calcBtn = document.getElementById('calcBtn');

    // Bottom Sheet Elements
    const resultSheet = document.getElementById('resultSheet');
    const sheetOverlay = document.getElementById('sheetOverlay');
    const closeSheetBtn = document.getElementById('closeSheetBtn');

    // Exit Modal Elements
    const exitModal = document.getElementById('exitModal');
    const stayBtn = document.getElementById('stayBtn');
    const exitBtn = document.getElementById('exitBtn');

    // === Currency Formatting ===
    landValueInput.addEventListener('input', (e) => {
        let value = e.target.value.replace(/[^0-9]/g, '');
        if (value) {
            e.target.value = parseInt(value, 10).toLocaleString();
            updateActualValue();
        } else {
            e.target.value = '';
            actualEvalDisplay.textContent = '0';
        }
    });

    // === Toggle Spouse Input ===
    spouseToggle.addEventListener('change', (e) => {
        if (e.target.checked) {
            spouseDobGroup.classList.remove('hidden');
            document.getElementById('spouseDob').required = true;
        } else {
            spouseDobGroup.classList.add('hidden');
            document.getElementById('spouseDob').required = false;
        }
    });

    // === Radio Change ===
    document.querySelectorAll('input[name="evalMethod"]').forEach(radio => {
        radio.addEventListener('change', updateActualValue);
    });

    function updateActualValue() {
        const rawValue = parseInt(landValueInput.value.replace(/,/g, '') || 0, 10);
        const method = document.querySelector('input[name="evalMethod"]:checked').value;
        const ratio = method === 'public' ? 1.0 : 0.9;
        const mkValue = Math.floor(rawValue * ratio);
        actualEvalDisplay.textContent = mkValue.toLocaleString();
        return mkValue;
    }

    // === Open/Close Sheet ===
    function openSheet() {
        resultSheet.classList.add('active');
        document.body.style.overflow = 'hidden';
    }

    function closeSheet() {
        resultSheet.classList.remove('active');
        document.body.style.overflow = '';
    }

    sheetOverlay.addEventListener('click', closeSheet);
    closeSheetBtn.addEventListener('click', closeSheet);

    // === Calculation Trigger ===
    calcBtn.addEventListener('click', () => {
        if (!document.getElementById('ownerDob').value) {
            alert('생년월일을 입력해주세요.');
            return;
        }
        if (!landValueInput.value) {
            alert('농지 가격을 입력해주세요.');
            return;
        }
        if (spouseToggle.checked && !document.getElementById('spouseDob').value) {
            alert('배우자 생년월일을 입력해주세요.');
            return;
        }

        calculateAndShow();
    });

    function calculateAndShow() {
        const dob = new Date(document.getElementById('ownerDob').value);
        const landValue = updateActualValue();
        const hasSpouse = spouseToggle.checked;

        const today = new Date();
        const age = today.getFullYear() - dob.getFullYear();

        if (age < 60) {
            alert('농지연금 가입은 만 60세 이상부터 가능합니다.');
            return;
        }

        // Calculate Logic
        let calcAge = age;
        if (calcAge > 80) calcAge = 80;
        if (!AGE_FACTORS[calcAge]) calcAge = 80;

        let factors = AGE_FACTORS[calcAge];
        const unitValue = landValue / 100000000;

        let lifeAmount = Math.floor(factors.life * unitValue);
        let term5Amount = Math.floor(factors.term5 * unitValue);
        let term10Amount = Math.floor(factors.term10 * unitValue);
        let term15Amount = Math.floor(factors.term15 * unitValue);

        const MAX_PAYOUT = 3000000;
        if (lifeAmount > MAX_PAYOUT) lifeAmount = MAX_PAYOUT;
        if (term5Amount > MAX_PAYOUT) term5Amount = MAX_PAYOUT;
        if (term10Amount > MAX_PAYOUT) term10Amount = MAX_PAYOUT;
        if (term15Amount > MAX_PAYOUT) term15Amount = MAX_PAYOUT;

        if (hasSpouse) {
            lifeAmount = Math.floor(lifeAmount * 0.85);
        }

        // Update UI
        document.getElementById('resAge').textContent = `${age}`;
        document.getElementById('resEvalAmount').textContent = `${(landValue / 100000000).toFixed(1)}억`;
        document.getElementById('valLifetime').textContent = lifeAmount.toLocaleString();
        document.getElementById('valTerm5').textContent = term5Amount.toLocaleString();
        document.getElementById('valTerm10').textContent = term10Amount.toLocaleString();
        document.getElementById('valTerm15').textContent = term15Amount.toLocaleString();

        openSheet();
    }

    // === Exit Logic (History API) ===
    // Initialize History
    if (window.history && window.history.pushState) {
        window.history.pushState({ page: 'home' }, '', '');

        window.addEventListener('popstate', (event) => {
            // Check if result sheet is open, close it first
            if (resultSheet.classList.contains('active')) {
                closeSheet();
                // Push history back again so we are still in "app" state
                window.history.pushState({ page: 'home' }, '', '');
            } else {
                // Determine if we should show exit modal
                // If modal is already visible?
                if (exitModal.classList.contains('visible')) {
                    // If modal visible and back pressed again -> actually exit or just keep showing?
                    // Typically 'stay' means close modal.
                    // For now, let's keep showing modal or assume this popstate is for exit
                    // But to block exit, we must push state again.
                    window.history.pushState({ page: 'modal' }, '', '');
                } else {
                    // Show Exit Modal
                    showExitModal();
                    // Push state to override the "back" action effectively
                    window.history.pushState({ page: 'modal' }, '', '');
                }
            }
        });
    }

    function showExitModal() {
        exitModal.classList.remove('hidden');
        // Small delay to allow display flex to apply before opacity transition
        requestAnimationFrame(() => {
            exitModal.classList.add('visible');
        });
    }

    function hideExitModal() {
        exitModal.classList.remove('visible');
        setTimeout(() => {
            exitModal.classList.add('hidden');
        }, 200);
    }

    stayBtn.addEventListener('click', () => {
        hideExitModal();
        // Ensure we have history state
        // window.history.pushState({ page: 'home' }, '', ''); // Might be redundant if popstate logic handles it
    });

    exitBtn.addEventListener('click', () => {
        // Try clear history and close
        // In WebView, window.close() might need interface injection
        window.close();
        // If webview interface exists
        if (window.Android) {
            window.Android.closeApp();
        } else if (window.webkit && window.webkit.messageHandlers && window.webkit.messageHandlers.closeApp) {
            window.webkit.messageHandlers.closeApp.postMessage('');
        }
    });
});
