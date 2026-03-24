"use strict";

document.addEventListener("DOMContentLoaded", function () {
  // ======================
  // SHARED HELPERS
  // ======================

  /**
   * Safely extracts a numeric price from an element.
   * Prefers `data-price` attribute (recommended for future-proofing),
   * falls back to parsing textContent.
   */
  const parsePrice = (element) => {
    if (!element) return 0;
    const raw = element.dataset.price ?? element.textContent;
    const cleaned = raw.replace(/[^0-9.]/g, "");
    const price = parseFloat(cleaned);
    return isNaN(price) ? 0 : price;
  };

  /**
   * Formats a number as Nigerian Naira with proper thousands separator.
   */
  const formatNaira = (amount) => `₦${amount.toLocaleString("en-NG")}`;

  // ======================
  // 1. MAIN DISH QUANTITY & PRICE UPDATER
  // ======================

  const inputRange = document.getElementById("dishAmtRange");
  const inputRangeDisplay = document.getElementById("dishRangeDisplay");
  const dishAmtPrice = document.getElementById("dishAmtPrice");
  const dishAmtPriceDisplay = document.getElementById("dishAmtPriceDisplay");

  if (inputRange && inputRangeDisplay) {
    const updateDishDisplay = () => {
      const amount = inputRange.value;
      inputRangeDisplay.textContent = amount;

      if (dishAmtPrice && dishAmtPriceDisplay) {
        const basePrice = parsePrice(dishAmtPrice);
        const multiplier = parseInt(amount, 10) || 1; // range.value is always numeric
        const newPrice = basePrice * multiplier;

        dishAmtPriceDisplay.textContent = formatNaira(newPrice);
      }
    };

    inputRange.addEventListener("input", updateDishDisplay);
    // Initial render
    updateDishDisplay();
  } else {
    console.warn("Main dish range elements not found");
  }

  // ======================
  // 2. EXTRA CARDS (checkbox + range + price sync)
  // ======================

  function initExtraCard(card) {
    const checkbox = card.querySelector('input[type="checkbox"]');
    const range = card.querySelector('input[type="range"]');
    const display = card.querySelector('[id^="extraRangeDisplay-"]');
    const unitPriceEl = card.querySelector('[id^="extraAmtPrice-"]');
    const priceDisplay = card.querySelector('[id^="extraAmtPriceDisplay-"]');
    const amountBody = card.querySelector('[id^="extraAmtBody-"]');

    if (!checkbox || !range || !display || !priceDisplay) return;

    const updateExtraPrice = () => {
      const amount = parseInt(range.value, 10) || 1;
      display.textContent = amount;

      const unitPrice = parsePrice(unitPriceEl);
      priceDisplay.textContent = formatNaira(unitPrice * amount);
    };

    // Range listener
    range.addEventListener("input", updateExtraPrice);

    // Checkbox toggles card style, enables range, shows/hides amount controls
    checkbox.addEventListener("change", () => {
      const isChecked = checkbox.checked;

      card.classList.toggle("bg-success", isChecked);
      card.classList.toggle("shadow", isChecked);

      range.disabled = !isChecked;
      amountBody.style.display = isChecked ? "block" : "none";

      // Reset to default quantity when unchecked (standard UX)
      if (!isChecked) range.value = "1";

      updateExtraPrice();
    });

    // ======================
    // INITIAL STATE (FIXED BUG)
    // ======================
    // Previously this always hid the amountBody regardless of checkbox state
    range.disabled = !checkbox.checked;
    amountBody.style.display = checkbox.checked ? "block" : "none";
    updateExtraPrice(); // sync display immediately
  }

  // Initialize every extra card
  document.querySelectorAll('[id^="selectExtra-"]').forEach((checkbox) => {
    const card = checkbox.closest(".card");
    if (card) initExtraCard(card);
  });

  // ======================
  // 3. CONFIRM ORDER MODAL – POPULATE ITEMS LIST
  // ======================

  function createOrderItem(name, amount) {
    const li = document.createElement("li");
    li.className = "list-group-item d-flex justify-content-between align-items-center";

    const nameSpan = document.createElement("span");
    nameSpan.textContent = name;

    const amountSpan = document.createElement("small");
    amountSpan.className = "text-muted";
    amountSpan.textContent = `× ${amount}`;

    li.appendChild(nameSpan);
    li.appendChild(amountSpan);
    return li;
  }

  const continueToOrderBtn = document.getElementById("continueToOrder");

  if (continueToOrderBtn) {
    continueToOrderBtn.addEventListener("click", () => {
      const orderedItemList = document.getElementById("itemsList");
      const mainDishName = document.getElementById("dishName");
      const extraCheckboxes = document.querySelectorAll('[id^="selectExtra-"]');

      if (!orderedItemList || !mainDishName) return;

      // Clear previous list
      orderedItemList.replaceChildren();

      // Main dish
      orderedItemList.appendChild(
        createOrderItem(mainDishName.textContent.trim(), inputRange?.value || "1")
      );

      // Selected extras only
      extraCheckboxes.forEach((cb) => {
        if (!cb.checked) return;

        const card = cb.closest(".card");
        if (!card) return;

        const extraNameEl = card.querySelector('[id^="extraName-"]');
        const extraRange = card.querySelector('input[type="range"]');

        if (extraNameEl && extraRange) {
          orderedItemList.appendChild(
            createOrderItem(extraNameEl.textContent.trim(), extraRange.value)
          );
        }
      });
    });
  }

  // ======================
  // 4. FORM SUBMISSION WITH GEOLOCATION
  // ======================

  const form = document.querySelector("form");

  if (form) {
    const getLocation = () =>
      new Promise((resolve, reject) => {
        if (!navigator.geolocation) {
          reject(new Error("Geolocation not supported"));
          return;
        }
        navigator.geolocation.getCurrentPosition(
          resolve,
          reject,
          { timeout: 10000, enableHighAccuracy: true } // improved UX
        );
      });

    form.addEventListener("submit", async function (event) {
      event.preventDefault();

      try {
        const position = await getLocation();

        document.getElementById("latitudeInput").value = position.coords.latitude;
        document.getElementById("longitudeInput").value = position.coords.longitude;

        form.submit(); // re-submit with coordinates
      } catch (error) {
        const messages = {
          1: "Location permission was denied. Delivery address cannot be verified.",
          2: "Location information is unavailable.",
          3: "Location request timed out.",
        };
        alert(messages[error.code] ?? "Unable to get your location. Please try again.");
      }
    });
  }

  // ======================
  // 5. ONLINE/OFFLINE STATUS (DISABLE SUBMIT WHEN OFFLINE)
  // ======================

  const continueOrderBtn = document.getElementById("continueOrderBtn");
  const statusBanner = document.getElementById("onlineStatus");

  const updateOnlineStatus = () => {
    const isOnline = navigator.onLine;

    if (continueOrderBtn) {
      continueOrderBtn.disabled = !isOnline;
      continueOrderBtn.setAttribute("aria-disabled", String(!isOnline));
    }

    if (statusBanner) {
      statusBanner.classList.toggle("d-none", isOnline);
      statusBanner.classList.toggle("d-flex", !isOnline);
    }
  };

  window.addEventListener("online", updateOnlineStatus);
  window.addEventListener("offline", updateOnlineStatus);

  // Initial state
  updateOnlineStatus();
});