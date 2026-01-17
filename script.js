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

    // === Theme Logic ===
    const themeToggle = document.getElementById('themeToggle');
    const savedTheme = localStorage.getItem('theme');

    // Default to Light if no save, or respect save
    if (savedTheme === 'dark') {
        document.body.classList.add('dark-mode');
    }

    themeToggle.addEventListener('click', () => {
        document.body.classList.toggle('dark-mode');
        const isDark = document.body.classList.contains('dark-mode');
        localStorage.setItem('theme', isDark ? 'dark' : 'light');
    });

    // === UI Elements ===
    const landValueInput = document.getElementById('amount');
    const actualEvalDisplay = document.getElementById('actualEvalAmount');
    // const spouseToggle = document.getElementById('spouseToggle'); // Removed? No, snippet didn't used it directly.
    const spouseDobGroup = document.getElementById('spouseDobGroup');
    const calcBtn = document.getElementById('calcBtn');

    // ... (Sheet/Modal elements unchanged) ...

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

    // === Spouse Succession Radio Logic ===
    const spouseRadios = document.querySelectorAll('input[name="successionYn"]'); // Name updated
    spouseRadios.forEach(radio => {
        radio.addEventListener('change', (e) => {
            updateRadioClasses();

            if (e.target.value === 'Y') {
                document.getElementById('birthday2').required = true;
            } else {
                document.getElementById('birthday2').required = false;
            }
        });
    });

    // ... (updateRadioClasses unchanged) ...

    function updateRadioClasses() {
        document.querySelectorAll('.radio-card input[type="radio"]').forEach(radio => {
            if (radio.checked) {
                radio.closest('.radio-card').classList.add('active');
            } else {
                radio.closest('.radio-card').classList.remove('active');
            }
        });
    }

    // Initialize radio classes on load
    updateRadioClasses();

    // Hook up Valuation Radios to also update classes
    document.querySelectorAll('input[name="flndEvlMth"]').forEach(radio => {
        radio.addEventListener('change', () => {
            updateActualValue();
            updateRadioClasses();
        });
    });

    // === Update Calculation Logic ===

    function updateActualValue() {
        const rawValue = landValueInput.value.replace(/,/g, '');
        if (!rawValue) return 0;

        const method = document.querySelector('input[name="flndEvlMth"]:checked').value;
        let multiplier = 1.0;
        if (method === 'R') { // R = Appraised (Confusion: Reference says P=100%, R=90%)
            // Check Reference Label: lblflndEvlMthR -> 감정가 (평가율 : 90%)
            multiplier = 0.9;
        }
        // P (Public) = 1.0

        const actual = Math.floor(parseInt(rawValue, 10) * multiplier);
        actualEvalDisplay.textContent = actual.toLocaleString();
        return actual;
    }

    // ... (Sheet Logic remains same) ...

    // === Calculation Trigger ===
    calcBtn.addEventListener('click', () => {
        if (!document.getElementById('birthday1').value) {
            alert('생년월일을 입력해주세요.');
            return;
        }
        if (!landValueInput.value) {
            alert('농지 가격을 입력해주세요.');
            return;
        }

        const isSpouseSuccession = document.querySelector('input[name="successionYn"]:checked').value === 'Y';
        if (isSpouseSuccession && !document.getElementById('birthday2').value) {
            alert('배우자 생년월일을 입력해주세요.');
            return;
        }

        calculateAndShow();
    });

    function calculateAndShow() {
        const dob = new Date(document.getElementById('birthday1').value);
        const landValue = updateActualValue();
        const isSpouseSuccession = document.querySelector('input[name="successionYn"]:checked').value === 'Y';

        const today = new Date();
        const age = today.getFullYear() - dob.getFullYear();

        if (age < 60) {
            alert('농지연금 가입은 만 60세 이상부터 가능합니다.');
            return;
        }

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

        if (isSpouseSuccession) {
            lifeAmount = Math.floor(lifeAmount * 0.85);
        }

        document.getElementById('resAge').textContent = `${age}`;
        document.getElementById('resEvalAmount').textContent = `${(landValue / 100000000).toFixed(1)}억`;
        document.getElementById('valLifetime').textContent = lifeAmount.toLocaleString();
        document.getElementById('valTerm5').textContent = term5Amount.toLocaleString();
        document.getElementById('valTerm10').textContent = term10Amount.toLocaleString();
        document.getElementById('valTerm15').textContent = term15Amount.toLocaleString();

        openSheet();
    }

    // === Exit Logic (History API) ===
    if (window.history && window.history.pushState) {
        window.history.pushState({ page: 'home' }, '', '');

        window.addEventListener('popstate', (event) => {
            if (resultSheet.classList.contains('active')) {
                closeSheet();
                window.history.pushState({ page: 'home' }, '', '');
            } else {
                if (exitModal.classList.contains('visible')) {
                    window.history.pushState({ page: 'modal' }, '', '');
                } else {
                    showExitModal();
                    window.history.pushState({ page: 'modal' }, '', '');
                }
            }
        });
    }

    function showExitModal() {
        exitModal.classList.remove('hidden');
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
    });

    exitBtn.addEventListener('click', () => {
        window.close();
        if (window.Android) {
            window.Android.closeApp();
        } else if (window.webkit && window.webkit.messageHandlers && window.webkit.messageHandlers.closeApp) {
            window.webkit.messageHandlers.closeApp.postMessage('');
        }
    });
});
