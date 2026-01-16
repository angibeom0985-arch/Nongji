document.addEventListener('DOMContentLoaded', () => {
    // === Logic Constants ===
    // Simplified estimation factors based on research.
    // Factor: Monthly Payment (KRW) per 100 Million KRW Land Value
    // Based on ~600k for 75yo/100M, ~300k for 65yo/100M (Estimation)
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
        max: { life: 750000, term5: 2500000, term10: 1500000, term15: 1200000 } // Cap for >80
    };

    // === UI Elements ===
    const landValueInput = document.getElementById('landValue');
    const actualEvalDisplay = document.getElementById('actualEvalAmount');
    const spouseToggle = document.getElementById('spouseToggle');
    const spouseDobGroup = document.getElementById('spouseDobGroup');
    const form = document.getElementById('pensionForm');
    const resultsSection = document.getElementById('resultsSection');

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

    // === Calculation ===
    form.addEventListener('submit', (e) => {
        e.preventDefault();

        // 1. Get Inputs
        const dob = new Date(document.getElementById('ownerDob').value);
        const landValue = updateActualValue();
        const hasSpouse = spouseToggle.checked;
        const spouseDob = hasSpouse ? new Date(document.getElementById('spouseDob').value) : null;

        // 2. Validate Age (Simple Year diff)
        const today = new Date();
        const age = today.getFullYear() - dob.getFullYear();

        if (age < 60) {
            alert('농지연금 가입은 만 60세 이상부터 가능합니다.');
            return;
        }
        
        // 3. Determine Factor
        // Use spouse age for calculation if spouse is younger and survivor option selected (simplified logic: check younger)
        let calcAge = age;
        if (hasSpouse && spouseDob) {
            const spouseAge = today.getFullYear() - spouseDob.getFullYear();
            if (spouseAge < calcAge) {
                // Usually survivor pension reduces amount, here simplified by taking younger age if signifiant
                // or just apply a reduction factor. Let's just use a flat reduction for 'Survivor' logic simplicity
            }
        }

        // Clamp age to 80 for factors (or use lookup)
        let factorKey = calcAge;
        if (calcAge > 80) factorKey = 80;
        if (calcAge < 60) factorKey = 60; // Should not happen due to check above but for safety
        
        let factors = AGE_FACTORS[factorKey] || AGE_FACTORS[80];

        // 4. Calculate
        // Payout = (LandValue / 100,000,000) * Factor
        const unitValue = landValue / 100000000;
        
        let lifeAmount = Math.floor(factors.life * unitValue);
        let term5Amount = Math.floor(factors.term5 * unitValue);
        let term10Amount = Math.floor(factors.term10 * unitValue);
        let term15Amount = Math.floor(factors.term15 * unitValue);

        // Apply max cap (3 million KRW)
        const MAX_PAYOUT = 3000000;
        if (lifeAmount > MAX_PAYOUT) lifeAmount = MAX_PAYOUT;
        if (term5Amount > MAX_PAYOUT) term5Amount = MAX_PAYOUT;
        if (term10Amount > MAX_PAYOUT) term10Amount = MAX_PAYOUT;
        if (term15Amount > MAX_PAYOUT) term15Amount = MAX_PAYOUT;
        
        // Survivor Penalty (Simplified: -20% if spouse included for simple estimation vs complicated actuarial)
        // Note: Actual logic is complex. This is an estimation tool.
        if (hasSpouse) {
            lifeAmount = Math.floor(lifeAmount * 0.85); // 15% reduction for survivor coverage estimation
        }

        // 5. Update UI
        document.getElementById('resAge').textContent = `만 ${age}세`;
        document.getElementById('resEvalAmount').textContent = `${landValue.toLocaleString()}원`;

        animateValue('valLifetime', lifeAmount);
        animateValue('valTerm5', term5Amount);
        animateValue('valTerm10', term10Amount);
        animateValue('valTerm15', term15Amount);

        // Show Results
        resultsSection.classList.remove('hidden');
        resultsSection.scrollIntoView({ behavior: 'smooth' });
    });

    function animateValue(id, value) {
        const el = document.getElementById(id);
        const duration = 1000;
        const start = 0;
        let startTimestamp = null;

        const step = (timestamp) => {
            if (!startTimestamp) startTimestamp = timestamp;
            const progress = Math.min((timestamp - startTimestamp) / duration, 1);
            const current = Math.floor(progress * (value - start) + start);
            el.textContent = current.toLocaleString();
            if (progress < 1) {
                window.requestAnimationFrame(step);
            }
        };
        window.requestAnimationFrame(step);
    }
});
