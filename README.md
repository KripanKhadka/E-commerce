# Hamro Sports — Django Sports E-commerce

A clean, Bootstrap-based sports store built with Django.

## Included
- Responsive storefront with Bootstrap 5
- Hero slider managed from Django admin
- Product catalog, categories, search and featured products
- Product detail pages
- Login/register
- Cart with quantity controls
- Coupons
- Checkout and delivery address
- Order tracking and customer messages
- Refund requests
- Django admin for products, slides, orders, payments, coupons and refunds
- eSewa ePay v2 payment flow
- Server-side payment verification
- Stock management
- Environment-based secrets

## Customer accounts
- Registration collects username, name, email and Nepal mobile number.
- Checkout/cart actions require login.
- Customers get an account dashboard with profile editing and order history.
- Django's built-in password hashing and authentication are used.

## Quick start — Windows / VS Code terminal

```bat
cd sportshop
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Open:
- Store: http://127.0.0.1:8000/
- Admin: http://127.0.0.1:8000/admin/

## Product photos

Items and hero slides ship with clean placeholder graphics. To swap them
for real product photos, get a free key at https://www.pexels.com/api/,
add `PEXELS_API_KEY=...` to `.env`, then run:
```bash
python manage.py fetch_real_images
```
See `IMAGES_AND_ITEMS_GUIDE.md` for details and options.

## Payment setup

### eSewa
1. Use the test values already in `.env.example` for development — they are eSewa's public RC (test) merchant credentials, not real money.
2. Keep `ESEWA_ENV=test` while developing. On the eSewa test page, log in with eSewa's official test account: eSewa ID `9806800001` (also `...002`–`...005`), password `Nepal@123`, MPIN `1122`, and confirm with the token `123456`. Using any other login will get the transaction cancelled.
3. For production, register as an eSewa merchant, replace `ESEWA_PRODUCT_CODE` and `ESEWA_SECRET_KEY` with the values eSewa gives your registered merchant account (tied to your bank/receiving account), and set `ESEWA_ENV=production`.

See `PAYMENT_SETUP_GUIDE.md` for the full walkthrough and troubleshooting.

Do not commit `.env` or live merchant keys.

## Notes

Payment gateways need a reachable return URL for real end-to-end testing. For localhost development, the browser can return to your local server, but external gateway testing may require a public HTTPS tunnel depending on the gateway/account configuration.

This project deliberately does not mark an order as paid merely because the browser returned from a payment page. It verifies the transaction with the gateway first.
