# Payment Setup Guide — eSewa

This store now uses **eSewa only**. Khalti has been removed to keep the
checkout flow and deployment simpler.

## Why "payment unsuccessful or cancelled" happens in testing

It is almost never because there is "no receiver account" — eSewa's test
environment doesn't move real money at all, so no bank account is needed
during development. The message appears when:

1. **You didn't use eSewa's official test login on their payment page.**
   This is the #1 cause. The `.env.example` values (`ESEWA_PRODUCT_CODE=EPAYTEST`
   and the matching `ESEWA_SECRET_KEY`) are eSewa's own published sandbox
   merchant credentials — shared by every developer testing eSewa. They are
   **not** a receiving account and don't need to be. What you log in with
   *on eSewa's own page* is a separate, official test **customer** account:

   | Field | Value |
   |---|---|
   | eSewa ID | `9806800001` (or `...002`, `...003`, `...004`, `...005`) |
   | Password | `Nepal@123` |
   | MPIN | `1122` |
   | Confirmation token/OTP | `123456` |

   If you enter anything else (a real phone number, a made-up password),
   eSewa itself rejects/cancels the transaction and sends the browser back
   to the failure URL — which is exactly the "unsuccessful or cancelled"
   message you're seeing.

2. **The success/failure return URL isn't reachable.** The app builds this
   URL from the request you used to load the payment page. Always open the
   site the same way your users will (e.g. consistently via
   `http://127.0.0.1:8000`, not a mix of `127.0.0.1` and `localhost`), and
   if you deploy it publicly, make sure `DJANGO_ALLOWED_HOSTS` and `SITE_URL`
   in `.env` match the real domain.

## Going live (real money)

1. Register as a merchant at https://merchant.esewa.com.np and complete
   eSewa's verification (this is where you link your real receiving/bank
   account — you only need this step for production, not for testing).
2. eSewa will issue you a live `product_code` and `secret_key` tied to that
   merchant account.
3. In `.env`, set:
   ```
   ESEWA_ENV=production
   ESEWA_PRODUCT_CODE=<your live product code>
   ESEWA_SECRET_KEY=<your live secret key>
   ```
4. Set `DJANGO_DEBUG=False`, and set `DJANGO_ALLOWED_HOSTS` and `SITE_URL`
   to your real domain.

Never commit `.env` or real merchant keys to source control.

## How the flow works (for reference)

1. `payment` view creates a `Payment` record and calls `initiate_esewa`.
2. `initiate_esewa` builds a signed HMAC-SHA256 form (per eSewa's ePay v2
   spec) and auto-submits it to eSewa's hosted payment page.
3. eSewa redirects the customer's browser back to `esewa-success` or
   `esewa-failure` with a base64-encoded payload.
4. `esewa_success` re-verifies the signature and amount server-side before
   marking the order as paid — the app never trusts the redirect alone.
