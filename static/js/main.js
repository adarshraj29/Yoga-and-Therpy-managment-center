// main.js — Minimal JavaScript for Yoga Therapy Center

document.documentElement.classList.add('js');

// ── Flash toasts: success disappears quickly, errors stay longer ───────────
document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('.alert-dismissible').forEach(function (alert) {
        var slow = alert.classList.contains('alert-danger') || alert.classList.contains('alert-warning');
        setTimeout(function () { bootstrap.Alert.getOrCreateInstance(alert).close(); }, slow ? 8000 : 4500);
    });
});

// ── Friendly confirm dialog for [data-confirm] buttons ─────────────────────
(function () {
    var modalEl, modal, pending;
    function build() {
        modalEl = document.createElement('div');
        modalEl.className = 'modal fade confirm-modal';
        modalEl.tabIndex = -1;
        modalEl.innerHTML =
            '<div class="modal-dialog modal-dialog-centered modal-sm"><div class="modal-content">' +
            '<div class="modal-body text-center p-4"><div class="confirm-icon"><i class="bi bi-exclamation-triangle"></i></div>' +
            '<h5 class="mb-1">Are you sure?</h5><p class="text-muted mb-4" id="confirmText"></p>' +
            '<div class="d-flex gap-2 justify-content-center">' +
            '<button type="button" class="btn btn-light px-4" data-bs-dismiss="modal">Keep it</button>' +
            '<button type="button" class="btn btn-danger px-4" id="confirmYes">Yes, continue</button></div></div></div></div>';
        document.body.appendChild(modalEl);
        modal = new bootstrap.Modal(modalEl);
        modalEl.querySelector('#confirmYes').addEventListener('click', function () {
            var el = pending; modal.hide();
            el.dataset.confirmed = '1';
            if (el.form) { el.form.requestSubmit(el); } else if (el.href) { window.location = el.href; }
        });
    }
    document.addEventListener('click', function (e) {
        var el = e.target.closest('[data-confirm]');
        if (!el || el.dataset.confirmed) return;
        e.preventDefault(); e.stopPropagation();
        if (!modalEl) build();
        pending = el;
        modalEl.querySelector('#confirmText').textContent = el.getAttribute('data-confirm') || 'This action cannot be undone.';
        modal.show();
    }, true);
})();

// ── Tables: responsive labels, scroll wrapper, search box ──────────────────
document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('table.table-yoga').forEach(function (table) {
        var heads = Array.prototype.map.call(table.querySelectorAll('thead th'), function (th) { return th.textContent.trim(); });
        var rows  = table.querySelectorAll('tbody tr');
        rows.forEach(function (tr) {
            Array.prototype.forEach.call(tr.children, function (td, i) {
                if (td.tagName === 'TD' && !td.hasAttribute('colspan') && heads[i]) td.setAttribute('data-label', heads[i]);
            });
        });
        table.classList.add('table-stack');
        var wrap = table.parentElement;
        if (!wrap.classList.contains('table-responsive')) {
            wrap = document.createElement('div'); wrap.className = 'table-responsive';
            table.parentNode.insertBefore(wrap, table); wrap.appendChild(table);
        }
        if (rows.length >= 6) {               // long lists get a live search box
            var tools = document.createElement('div'); tools.className = 'table-tools';
            tools.innerHTML = '<input type="search" class="form-control form-control-sm table-search" placeholder="Search this list...">';
            wrap.parentNode.insertBefore(tools, wrap);
            tools.firstChild.addEventListener('input', function (e) {
                var q = e.target.value.toLowerCase();
                rows.forEach(function (tr) { tr.style.display = tr.textContent.toLowerCase().indexOf(q) > -1 ? '' : 'none'; });
            });
        }
    });
});

// ── Submit buttons show a spinner and block double-clicks ──────────────────
document.addEventListener('submit', function (e) {
    var form = e.target;
    if (form.dataset.submitted) { e.preventDefault(); return; }
    var btn = form.querySelector('button[type=submit]');
    if (!btn || !form.checkValidity()) return;
    form.dataset.submitted = '1'; btn.classList.add('is-loading');
});
window.addEventListener('pageshow', function () {       // back button restores a usable form
    document.querySelectorAll('form[data-submitted]').forEach(function (f) {
        delete f.dataset.submitted;
        var b = f.querySelector('.is-loading'); if (b) b.classList.remove('is-loading');
    });
});

// ── Count-up numbers on dashboards + scroll reveal for cards ───────────────
document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('.stat-number').forEach(function (el) {
        var target = parseInt(el.textContent.trim(), 10);
        if (!/^\d+$/.test(el.textContent.trim()) || target > 100000) return;
        var start = null;
        function tick(ts) { start = start || ts; var p = Math.min((ts - start) / 700, 1); el.textContent = Math.round(target * p); if (p < 1) requestAnimationFrame(tick); }
        requestAnimationFrame(tick);
    });
    var cards = document.querySelectorAll('.feature-card, .class-card, .asana-card, .how-step');
    if ('IntersectionObserver' in window) {
        var io = new IntersectionObserver(function (entries) {
            entries.forEach(function (en) { if (en.isIntersecting) { en.target.classList.add('in'); io.unobserve(en.target); } });
        }, { threshold: 0.12 });
        cards.forEach(function (c, i) { c.classList.add('reveal'); c.style.transitionDelay = (i % 4) * 70 + 'ms'; io.observe(c); });
    }
    // One-click demo logins (login page)
    document.querySelectorAll('[data-demo-email]').forEach(function (b) {
        b.addEventListener('click', function () {
            document.getElementById('email').value = b.dataset.demoEmail;
            document.getElementById('password').value = b.dataset.demoPass;
            document.getElementById('loginForm').requestSubmit();
        });
    });
});

// ── BMI Calculator Live Feedback ─────────────────────────────────────────────
(function () {
    const weightInput = document.getElementById('bmi-weight');
    const heightInput = document.getElementById('bmi-height');
    const liveResult  = document.getElementById('bmi-live');

    if (!weightInput || !heightInput || !liveResult) return;

    function updateLiveBMI() {
        const w = parseFloat(weightInput.value);
        const h = parseFloat(heightInput.value) / 100;
        if (w > 0 && h > 0) {
            const bmi = (w / (h * h)).toFixed(1);
            let cat = '', color = '';
            if      (bmi < 18.5) { cat = 'Underweight'; color = '#0dcaf0'; }
            else if (bmi < 25.0) { cat = 'Normal';      color = '#198754'; }
            else if (bmi < 30.0) { cat = 'Overweight';  color = '#fd7e14'; }
            else                  { cat = 'Obese';        color = '#dc3545'; }

            liveResult.innerHTML =
                `BMI: <strong style="color:${color}">${bmi}</strong>
                 &nbsp;|&nbsp;
                 <span style="color:${color}">${cat}</span>`;
        } else {
            liveResult.innerHTML = '';
        }
    }

    weightInput.addEventListener('input', updateLiveBMI);
    heightInput.addEventListener('input', updateLiveBMI);
})();

// ── Feedback booking_type toggle ─────────────────────────────────────────────
(function () {
    const typeSelect  = document.getElementById('booking_type');
    const classGroup  = document.getElementById('class-group');
    const therapyGroup = document.getElementById('therapy-group');

    if (!typeSelect) return;

    function toggleGroups() {
        if (typeSelect.value === 'class') {
            if (classGroup)   classGroup.style.display   = 'block';
            if (therapyGroup) therapyGroup.style.display = 'none';
        } else {
            if (classGroup)   classGroup.style.display   = 'none';
            if (therapyGroup) therapyGroup.style.display = 'block';
        }
    }

    typeSelect.addEventListener('change', toggleGroups);
    toggleGroups(); // run on load
})();
