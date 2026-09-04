# Hamro Sports - Updates & Image Management Guide

## ✅ What's Been Added

### 1. **35+ New Sport Items** 
Organized across 6 categories:

- **Football / Soccer** (4 items): Soccer balls, cleats, training cones, shin guards
- **Basketball** (4 items): Basketballs, shoes, backboards, socks
- **Tennis & Racket Sports** (4 items): Rackets, balls, badminton gear, squash equipment
- **Running & Fitness** (5 items): Running shoes, yoga mats, dumbbells, water bottles, jump ropes
- **Outdoor & Hiking** (5 items): Backpacks, tents, boots, sleeping bags, camping stoves
- **Sports Apparel & Accessories** (6 items): T-shirts, shorts, smartwatches, caps, gym bags, gloves

### 2. **Dynamic Hero Carousel** 
5 new attractive hero slides with:
- Compelling titles and subtexts
- Call-to-action buttons linking to specific sections
- Professional layout and styling
- Easy sorting and management

## 🖼️ Image Management

### Adding/Replacing Images

**Option 1: Through Django Admin** (Easiest)
1. Go to `http://localhost:8000/admin/`
2. Navigate to "Hero Slides" or "Items"
3. Click on any item to edit
4. Upload a new image using the image field
5. Click Save

**Option 2: Fetch real photos automatically (recommended)**

Every item and hero slide currently ships with a clean, generated
placeholder graphic — that's just a stand-in built inside this sandboxed
environment, which has no general internet access. To pull in real,
free-to-use product photos, run this on your own machine or server:

1. Get a free API key at https://www.pexels.com/api/ (instant signup, no
   payment info needed). Pexels photos are free for commercial use and
   don't require attribution.
2. Add it to your `.env` file:
   ```
   PEXELS_API_KEY=your-key-here
   ```
3. Run:
   ```bash
   python manage.py fetch_real_images
   ```
   This downloads one real, relevant photo per item and hero slide (e.g.
   "soccer ball", "hiking backpack", "tennis racket") and saves it
   straight into each record.

   Useful flags:
   - `python manage.py fetch_real_images --only-missing` — only fill in
     images that are still blank, leave everything else untouched.
   - `python manage.py fetch_real_images --item wilson-pro-staff-97` —
     re-fetch just one product.

The search terms used for each item are generic and descriptive (not
brand names), so you get real, relevant stock photos rather than
guessing at specific product shots. You can always override any single
image afterward through Django Admin (Option 1).

### SSL certificate errors

If `fetch_real_images` fails with something like:
```
[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: certificate has expired
```
this is almost always **your computer**, not Pexels — Pexels' certificate
is valid. Two common causes, in order of likelihood:

1. **Your system clock/date is wrong.** SSL certificate checks compare
   against your machine's current date; if it's off, valid certificates
   look "expired." Check your system date and time, fix it if it's wrong,
   and re-run the command.
2. **Your OS's CA certificate bundle is outdated.** The command already
   uses the `certifi` package (a self-contained, regularly-updated CA
   bundle) instead of your OS trust store when it's installed, which
   fixes this for most people automatically — just make sure you've run
   `pip install -r requirements.txt` so `certifi` is actually installed.
   - On macOS with python.org installers, you may also need to run
     `/Applications/Python 3.x/Install Certificates.command`.
   - On corporate/school networks, a proxy or firewall sometimes
     intercepts HTTPS with its own certificate — try a different network
     if the above doesn't fix it.

### Image Specifications

**Image Specifications:**
- **Hero Slides**: 1200x400px recommended (landscape)
- **Product Images**: 400x400px recommended (square)
- **Format**: JPG or PNG
- **Quality**: High quality, 100-200KB each

### Manual Image Upload

1. Find or create your image file
2. Save it with a descriptive name (e.g., `nike-soccer-ball.jpg`)
3. Go to Django Admin → Item/HeroSlide
4. Click the image field and upload
5. Save the entry

## 📊 Database Stats

```
Total Items: 35
Total Hero Slides: 8

Items by Category:
- Football/Soccer: 4
- Basketball: 4
- Tennis & Racket: 4
- Running & Fitness: 5
- Outdoor & Hiking: 5
- Sports Apparel: 6

Featured Items: 12 (marked for homepage display)
Sale Items (Discount): 11
New Items: 12
```

## 🎨 Featured Items

These 12 items are marked as "featured" and will display on the homepage:
1. Professional Soccer Ball
2. Soccer Cleats Premium
3. Pro Basketball
4. Basketball Shoes High Top
5. Professional Tennis Racket
6. Running Shoes Pro
7. Hiking Backpack 50L
8. Camping Tent 2 Person
9. Sports T-Shirt Pro
10. Sports Watch Smartband
11. Gym Bag Duffel
12. (Add more by marking items as featured in admin)

## 💰 Pricing & Discounts

**Sale Structure:**
- Regular items: Full price only
- Sale items (11): Have discount_price set (10-45% off)
- Examples:
  - Soccer Cleats: 8999 → 6999 NPR
  - Running Shoes: 7999 → 5999 NPR
  - Hiking Backpack: 8500 → 6999 NPR

**Adjust Prices:**
1. Go to Admin → Items
2. Click on the item
3. Update "Price" and/or "Discount Price"
4. Save

## 🔧 Managing Items

### Edit Item Details
Admin Panel Fields:
- **Title**: Product name
- **Slug**: URL-friendly identifier (auto-generated)
- **Brand**: Manufacturer (Nike, Adidas, etc.)
- **Description**: Detailed product info
- **Category**: Sport type
- **Price**: Regular price
- **Discount Price**: Sale price (leave blank if no discount)
- **Stock**: Quantity available
- **Active**: Show/hide from store
- **Featured**: Highlight on homepage
- **Label**: Mark as "New" (P), "Trending" (S), or "Sale" (D)
- **Image**: Product photo

### Bulk Actions in Admin
- Click checkboxes next to items
- Use "Action" dropdown to:
  - Mark as featured/inactive
  - Change stock levels
  - Update labels

## 📱 Homepage Display

The homepage automatically displays:
1. **Hero Carousel** - Top banner with your hero slides (rotates every 5 seconds)
2. **Category Cards** - 6 category shortcuts
3. **Featured Items** - Top 8 items marked as featured
4. **Full Product Grid** - Organized by category with search

## 🚀 Quick Start Checklist

- [x] Added 35+ sport items across 6 categories
- [x] Created 5 hero slides for carousel
- [x] Downloaded sample images for most items
- [x] Enhanced admin interface
- [ ] Upload your own high-quality images
- [ ] Adjust pricing for your market
- [ ] Test homepage carousel on different devices
- [ ] Configure payment gateway (eSewa)

## 📝 Next Steps

1. **Add Your Own Images**: 
   - Replace sample images with high-quality product photos
   - Use consistent lighting and angles
   - Include product details clearly

2. **Customize Hero Slides**:
   - Update titles and descriptions
   - Add your business messaging
   - Link to specific promotions

3. **Review Product Details**:
   - Verify all descriptions
   - Update stock levels as needed
   - Adjust pricing for your market

4. **Test the Website**:
   - View homepage at `http://localhost:8000/`
   - Test category filters
   - Try product search
   - Check cart and checkout

## 🎯 Admin Tips

**Useful Admin Filters:**
- Filter by Category
- Filter by Featured status
- Filter by Active/Inactive
- Filter by Label (New/Trending/Sale)
- Filter by Brand
- Search by Title or Description

**Bulk Editing:**
- Inline edit Stock and Featured status
- Use admin actions for bulk changes
- Export/Import via Django admin

## 📞 Support

If you need to:
- Add more items: Admin → Items → Add Item
- Update hero slides: Admin → Hero Slides → Edit
- Change images: Click on item → Upload new image
- Manage pricing: Edit item → Update price fields

---

**Your store is now ready with a full product catalog and professional hero carousel!**
