// ── Toast ──────────────────────────────────────────────────
function showToast(msg, duration = 3000) {
  const toast = document.getElementById('toast');
  toast.textContent = msg;
  toast.classList.add('show');
  setTimeout(() => toast.classList.remove('show'), duration);
}

// ── CSRF helper (for fetch calls not tied to a rendered form) ──
function getCookie(name) {
  const match = document.cookie.match('(^|;)\\s*' + name + '\\s*=\\s*([^;]+)');
  return match ? decodeURIComponent(match[2]) : '';
}

// ── AJAX Add to Cart ───────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.add-form').forEach(form => {
    form.addEventListener('submit', async e => {
      e.preventDefault();
      const productName = form.dataset.product;
      const btn = form.querySelector('button[type="submit"]');
      btn.disabled = true;
      btn.textContent = 'Adding…';
      try {
        const res = await fetch(form.action, {
          method: 'POST',
          body: new FormData(form),
          headers: { 'X-Requested-With': 'XMLHttpRequest' }
        });
        const data = await res.json();
        document.querySelectorAll('#cart-count').forEach(el => el.textContent = data.cart_count);
        showToast(`✓ ${productName} added to cart`);
      } catch {
        showToast('Something went wrong. Please try again.');
      } finally {
        btn.disabled = false;
        btn.textContent = 'Add to Cart';
      }
    });
  });
});

// ── Sort dropdown ──────────────────────────────────────────
function sortProducts(value) {
  const url = new URL(window.location);
  if (value) url.searchParams.set('sort', value);
  else url.searchParams.delete('sort');
  window.location = url.toString();
}

// ── Auto-dismiss messages ──────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.message').forEach(msg => {
    setTimeout(() => msg.style.display = 'none', 5000);
  });
});

// ── Mobile hamburger menu ──────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  const btn = document.getElementById('hamburger');
  const links = document.getElementById('nav-links');
  if (!btn || !links) return;
  btn.addEventListener('click', () => {
    const open = links.classList.toggle('open');
    btn.classList.toggle('open', open);
    btn.setAttribute('aria-expanded', open);
  });
  // Close menu when a plain link inside it is clicked
  links.querySelectorAll(':scope > a').forEach(a => {
    a.addEventListener('click', () => {
      links.classList.remove('open');
      btn.classList.remove('open');
      btn.setAttribute('aria-expanded', false);
    });
  });
});

// ── Dropdown menus (Categories, Profile) — click to toggle, closes on outside click ──
document.addEventListener('DOMContentLoaded', () => {
  const dropdowns = document.querySelectorAll('.nav-dropdown');
  dropdowns.forEach(dropdown => {
    const label = dropdown.querySelector('.nav-dropdown-label');
    if (!label) return;
    label.addEventListener('click', e => {
      e.preventDefault();
      const isOpen = dropdown.classList.contains('open');
      dropdowns.forEach(d => d.classList.remove('open'));
      dropdown.classList.toggle('open', !isOpen);
    });
  });
  document.addEventListener('click', e => {
    if (!e.target.closest('.nav-dropdown')) {
      dropdowns.forEach(d => d.classList.remove('open'));
    }
  });
});

// ── Wishlist heart — AJAX toggle, live badge count, instant visual state ──
document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.wishlist-heart').forEach(btn => {
    btn.addEventListener('click', async e => {
      e.preventDefault();
      e.stopPropagation();
      const url = btn.dataset.toggleUrl;
      if (!url) return;
      btn.disabled = true;
      try {
        const res = await fetch(url, {
          method: 'POST',
          headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': getCookie('csrftoken'),
          },
        });
        if (res.status === 401) {
          const data = await res.json();
          window.location = `${data.login_url}?next=${encodeURIComponent(window.location.pathname)}`;
          return;
        }
        const data = await res.json();
        btn.classList.toggle('active', data.in_wishlist);
        btn.setAttribute('aria-pressed', data.in_wishlist);
        btn.classList.remove('pop');
        void btn.offsetWidth; // restart animation
        btn.classList.add('pop');
        document.querySelectorAll('#wishlist-count').forEach(el => el.textContent = data.wishlist_count);
        showToast(data.in_wishlist ? `Added to Wishlist ❤️` : 'Removed from Wishlist');

        // On the wishlist page itself, removing an item should drop its card
        const wishlistGrid = document.getElementById('wishlist-grid');
        if (!data.in_wishlist && wishlistGrid && wishlistGrid.contains(btn)) {
          const card = btn.closest('.product-card');
          if (card) {
            card.style.transition = 'opacity .25s, transform .25s';
            card.style.opacity = '0';
            card.style.transform = 'scale(.95)';
            setTimeout(() => {
              card.remove();
              if (!wishlistGrid.querySelector('.product-card')) {
                const tpl = document.getElementById('wishlist-empty-template');
                if (tpl) wishlistGrid.replaceWith(tpl.content.cloneNode(true));
              }
            }, 250);
          }
        }
      } catch {
        showToast('Something went wrong. Please try again.');
      } finally {
        btn.disabled = false;
      }
    });
  });
});

// ── Quick View modal ────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  const modal = document.getElementById('quick-view-modal');
  if (!modal) return;
  const backdrop = document.getElementById('qv-backdrop');
  const closeBtn = document.getElementById('qv-close');
  const image = document.getElementById('qv-image');
  const category = document.getElementById('qv-category');
  const name = document.getElementById('qv-name');
  const price = document.getElementById('qv-price');
  const stock = document.getElementById('qv-stock');
  const viewDetails = document.getElementById('qv-view-details');
  const addToCartBtn = document.getElementById('qv-add-to-cart');
  let currentAddUrl = null;

  function openModal(btn) {
    image.src = btn.dataset.image || '';
    image.alt = btn.dataset.name || '';
    category.textContent = btn.dataset.category || '';
    name.textContent = btn.dataset.name || '';
    price.innerHTML = btn.dataset.onSale === '1'
      ? `<span class="price-new">$${btn.dataset.price}</span> <span class="price-old">$${btn.dataset.oldPrice}</span>`
      : `<span class="price-new">$${btn.dataset.price}</span>`;
    const stockNum = parseInt(btn.dataset.stock, 10);
    stock.textContent = stockNum > 5 ? `✅ In Stock (${stockNum} available)`
      : stockNum > 0 ? `⚠️ Only ${stockNum} left!` : '❌ Out of Stock';
    stock.classList.toggle('out', stockNum === 0);
    viewDetails.href = btn.dataset.url || '#';
    currentAddUrl = btn.dataset.addUrl;
    addToCartBtn.disabled = stockNum === 0;
    addToCartBtn.textContent = stockNum === 0 ? 'Out of Stock' : 'Add to Cart';
    modal.classList.add('open');
    modal.setAttribute('aria-hidden', 'false');
  }

  function closeModal() {
    modal.classList.remove('open');
    modal.setAttribute('aria-hidden', 'true');
  }

  document.querySelectorAll('.quick-view-btn').forEach(btn => {
    btn.addEventListener('click', () => openModal(btn));
  });
  backdrop.addEventListener('click', closeModal);
  closeBtn.addEventListener('click', closeModal);
  document.addEventListener('keydown', e => {
    if (e.key === 'Escape') closeModal();
  });

  addToCartBtn.addEventListener('click', async () => {
    if (!currentAddUrl) return;
    addToCartBtn.disabled = true;
    const originalText = addToCartBtn.textContent;
    addToCartBtn.textContent = 'Adding…';
    try {
      const body = new FormData();
      body.append('quantity', '1');
      body.append('csrfmiddlewaretoken', getCookie('csrftoken'));
      const res = await fetch(currentAddUrl, {
        method: 'POST',
        body,
        headers: { 'X-Requested-With': 'XMLHttpRequest' },
      });
      const data = await res.json();
      document.querySelectorAll('#cart-count').forEach(el => el.textContent = data.cart_count);
      showToast(`✓ ${name.textContent} added to cart`);
      closeModal();
    } catch {
      showToast('Something went wrong. Please try again.');
    } finally {
      addToCartBtn.disabled = false;
      addToCartBtn.textContent = originalText;
    }
  });
});

// ── Newsletter subscribe (footer) — AJAX with toast feedback ──
document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('newsletter-form');
  if (!form) return;
  form.addEventListener('submit', async e => {
    e.preventDefault();
    const btn = form.querySelector('button[type="submit"]');
    const input = form.querySelector('.newsletter-input');
    btn.disabled = true;
    try {
      const res = await fetch(form.action, {
        method: 'POST',
        body: new FormData(form),
        headers: { 'X-Requested-With': 'XMLHttpRequest' },
      });
      const data = await res.json();
      showToast(data.message);
      if (data.ok) input.value = '';
    } catch {
      showToast('Something went wrong. Please try again.');
    } finally {
      btn.disabled = false;
    }
  });
});

// ── Scroll reveal — subtle fade-in for homepage sections ──
document.addEventListener('DOMContentLoaded', () => {
  const targets = document.querySelectorAll('.reveal');
  if (!targets.length) return;
  if (!('IntersectionObserver' in window)) {
    targets.forEach(el => el.classList.add('visible'));
    return;
  }
  const observer = new IntersectionObserver(entries => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('visible');
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.1 });
  targets.forEach(el => observer.observe(el));
});
