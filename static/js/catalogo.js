const state = { products: [], cart: new Map(), config: {} };
const money = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" });

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>'"]/g, (char) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;",
  })[char]);
}

function toast(message) {
  const el = document.getElementById("catalog-toast");
  el.textContent = message;
  el.classList.add("show");
  window.setTimeout(() => el.classList.remove("show"), 2500);
}

async function getJson(url) {
  const response = await fetch(url);
  if (!response.ok) throw new Error("Não foi possível carregar o catálogo.");
  return response.json();
}

function renderProducts() {
  const grid = document.getElementById("product-grid");
  if (!state.products.length) {
    grid.innerHTML = '<div class="empty-catalog">Nenhum produto disponível com esses filtros.</div>';
    return;
  }
  grid.innerHTML = state.products.map((product) => `
    <article class="product-card">
      <div class="product-visual">${escapeHtml(product.category)}</div>
      <div class="product-body">
        <h2>${escapeHtml(product.name)}</h2>
        <p class="product-meta">Disponível: ${Number(product.available).toLocaleString("pt-BR")} ${escapeHtml(product.unit)}</p>
        ${product.expiry_date ? `<p class="product-meta">Validade: ${new Date(`${product.expiry_date}T12:00:00`).toLocaleDateString("pt-BR")}</p>` : ""}
        <div class="product-price">${money.format(product.price)} <small>/ ${escapeHtml(product.unit)}</small></div>
        <div class="add-row">
          <input type="number" min="0.01" max="${product.available}" step="0.01" value="1" data-qty="${escapeHtml(product.sku)}" aria-label="Quantidade de ${escapeHtml(product.name)}">
          <button type="button" data-add="${escapeHtml(product.sku)}">Adicionar</button>
        </div>
      </div>
    </article>
  `).join("");
  grid.querySelectorAll("[data-add]").forEach((button) => button.addEventListener("click", () => addToCart(button.dataset.add)));
}

function addToCart(sku) {
  const product = state.products.find((item) => item.sku === sku);
  const input = document.querySelector(`[data-qty="${CSS.escape(sku)}"]`);
  const quantity = Number(input?.value || 0);
  if (!product || quantity <= 0 || quantity > product.available) return toast("Confira a quantidade disponível.");
  const previous = state.cart.get(sku)?.quantity || 0;
  if (previous + quantity > product.available) return toast("A quantidade supera o estoque disponível.");
  state.cart.set(sku, { product, quantity: previous + quantity });
  renderCart();
  toast("Produto adicionado à cesta.");
}

function renderCart() {
  const items = [...state.cart.values()];
  document.getElementById("cart-count").textContent = String(items.length);
  document.getElementById("cart-items").innerHTML = items.length ? items.map(({ product, quantity }) => `
    <div class="cart-item">
      <div><strong>${escapeHtml(product.name)}</strong><p>${quantity.toLocaleString("pt-BR")} ${escapeHtml(product.unit)} × ${money.format(product.price)}</p></div>
      <button type="button" class="remove-item" data-remove="${escapeHtml(product.sku)}">Remover</button>
    </div>
  `).join("") : '<p class="product-meta">Sua cesta está vazia.</p>';
  document.querySelectorAll("[data-remove]").forEach((button) => button.addEventListener("click", () => {
    state.cart.delete(button.dataset.remove);
    renderCart();
  }));
  const total = items.reduce((sum, item) => sum + item.quantity * item.product.price, 0);
  document.getElementById("cart-total").textContent = money.format(total);
}

function toggleCart(open) {
  document.getElementById("cart-drawer").classList.toggle("open", open);
  document.getElementById("cart-drawer").setAttribute("aria-hidden", String(!open));
  document.getElementById("drawer-backdrop").hidden = !open;
}

function checkout() {
  const items = [...state.cart.values()];
  if (!items.length) return toast("Adicione produtos antes de enviar o pedido.");
  const total = items.reduce((sum, item) => sum + item.quantity * item.product.price, 0);
  const lines = items.map(({ product, quantity }) => `- ${product.name}: ${quantity} ${product.unit} (${money.format(quantity * product.price)})`);
  const message = [`Olá! Quero fazer um pedido na ${state.config.farm_name}:`, "", ...lines, "", `Total estimado: ${money.format(total)}`, "", "Podemos combinar retirada ou entrega?"].join("\n");
  const phone = String(state.config.whatsapp || "").replace(/\D/g, "");
  if (phone) {
    window.open(`https://wa.me/${phone}?text=${encodeURIComponent(message)}`, "_blank", "noopener");
  } else {
    navigator.clipboard.writeText(message).then(() => toast("Resumo copiado. Configure AGRO_WHATSAPP para envio direto."));
  }
}

async function loadProducts() {
  const query = document.getElementById("catalog-search").value.trim();
  const category = document.getElementById("catalog-category").value;
  const params = new URLSearchParams();
  if (query) params.set("q", query);
  if (category) params.set("category", category);
  state.products = await getJson(`/api/catalog/products?${params}`);
  renderProducts();
}

async function boot() {
  [state.config, state.products] = await Promise.all([getJson("/api/catalog/config"), getJson("/api/catalog/products")]);
  document.getElementById("farm-name").textContent = state.config.farm_name;
  const pix = document.getElementById("pix-info");
  if (state.config.pix_key) { pix.textContent = `Chave Pix: ${state.config.pix_key}`; pix.hidden = false; }
  renderProducts();
  renderCart();
  document.getElementById("catalog-search").addEventListener("input", () => window.setTimeout(loadProducts, 180));
  document.getElementById("catalog-category").addEventListener("change", loadProducts);
  document.getElementById("open-cart").addEventListener("click", () => toggleCart(true));
  document.getElementById("close-cart").addEventListener("click", () => toggleCart(false));
  document.getElementById("drawer-backdrop").addEventListener("click", () => toggleCart(false));
  document.getElementById("checkout").addEventListener("click", checkout);
}

boot().catch((error) => {
  document.getElementById("product-grid").innerHTML = `<div class="empty-catalog">${escapeHtml(error.message)}</div>`;
});

