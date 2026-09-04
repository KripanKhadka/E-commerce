document.addEventListener("DOMContentLoaded", function () {
  document.querySelectorAll(".product-image-wrap img, .cart-thumb img, .detail-image img").forEach(function (img) {
    img.addEventListener("error", function () { this.closest(".product-image-wrap, .cart-thumb, .detail-image")?.classList.add("image-missing"); });
  });
});
