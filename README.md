# ShopDjango — Full-Stack E-Commerce Store

A production-ready e-commerce application built with **Django 4.2**, vanilla **HTML/CSS/JS**, and **SQLite** (dev) / **PostgreSQL** (prod).

---

## Features

| Area | What's included |
|---|---|
| **Products** | Category browsing, search, sort (price/newest), sale badges, stock tracking |
| **Cart** | Session-based cart, AJAX add-to-cart, quantity controls, free-shipping threshold |
| **Checkout** | Shipping form, order summary, stock decrement on purchase |
| **Orders** | Order confirmation, full order history, per-order detail view, status tracking |
| **Auth** | Register, Login, Logout, Profile update, Change password, **Forgot password** flow |
| **Admin** | Products, Categories, Orders with inline items, editable status/paid, totals |
| **UI/UX** | Responsive design, mobile hamburger menu, toast notifications, pagination |

---

## Project Structure

```
shopdjango/
├── ecommerce/          # Django project settings & root URLs
├── store/              # Products & categories (models, views, admin)
├── cart/               # Session-based cart (Cart class, context processor)
├── orders/             # Checkout, order history, order detail
├── accounts/           # Auth — register, login, profile, password reset
├── templates/          # All HTML templates
│   ├── base.html
│   ├── store/
│   ├── cart/
│   ├── orders/
│   └── accounts/
├── static/
│   ├── css/main.css
│   └── js/main.js
├── manage.py
├── requirements.txt
└── .env.example
```

---

## Quick Start

### 1. Clone & set up a virtual environment

```bash
git clone <repo-url>
cd shopdjango
python -m venv venv
# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

```bash
cp .env.example .env
# Edit .env — at minimum change SECRET_KEY for any non-local use
```

### 4. Apply migrations

```bash
python manage.py migrate
```

### 5. Create a superuser (for admin access)

```bash
python manage.py createsuperuser
```

### 6. Run the development server

```bash
python manage.py runserver
```

| URL | Page |
|---|---|
| `http://127.0.0.1:8000/` | Shop homepage |
| `http://127.0.0.1:8000/admin/` | Django admin panel |
| `http://127.0.0.1:8000/accounts/register/` | Register |
| `http://127.0.0.1:8000/cart/` | Shopping cart |
| `http://127.0.0.1:8000/orders/create/` | Checkout |

---

## Adding Sample Data

Log into `/admin/` with your superuser and add:

1. **Categories** — e.g. Electronics, Clothing, Books
2. **Products** — assign a category, set price, upload an image, tick **Available**
3. Tick **Featured** on a few products to show them on the homepage hero

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.11+, Django 4.2 |
| Frontend | HTML5, CSS3 (custom, no framework), Vanilla JS |
| Database | SQLite (dev), PostgreSQL (prod via psycopg2) |
| Auth | Django built-in auth + password reset flow |
| Images | Pillow |
| Config | python-decouple (.env) |
| Payments | Stripe-ready (add keys to .env) |

---

## Deploying to Production

1. Set `DEBUG=False` and a strong `SECRET_KEY` in `.env`
2. Add your domain to `ALLOWED_HOSTS`
3. Uncomment `psycopg2-binary` in `requirements.txt` and update `DATABASES` in `settings.py`
4. Add Stripe keys to `.env` (`STRIPE_PUBLIC_KEY`, `STRIPE_SECRET_KEY`)
5. Run `python manage.py collectstatic`
6. Serve with **Gunicorn + Nginx**, or deploy to **Railway / Render / Fly.io**

---

## Pages

| Route | Description |
|---|---|
| `/` | Homepage with hero + featured products |
| `/category/<slug>/` | Filter by category |
| `/product/<slug>/` | Product detail with quantity picker |
| `/cart/` | Cart with live shipping calculation |
| `/orders/create/` | Checkout form |
| `/orders/my-orders/` | Order history (login required) |
| `/orders/<id>/` | Order detail & tracking |
| `/accounts/register/` | Register |
| `/accounts/login/` | Login (with "Forgot password?" link) |
| `/accounts/profile/` | Profile + recent orders |
| `/accounts/password-reset/` | Forgot password flow |
| `/admin/` | Django admin |

---

## Screenshots

> Add screenshots here after running the project locally.

- Homepage hero
- Product listing with search & filter
- Product detail page
- Shopping cart
- Checkout form
- Order confirmation
- My Orders / Order detail
- Admin panel

---

## License

MIT
