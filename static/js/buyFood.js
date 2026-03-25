"use strict";
document.addEventListener("DOMContentLoaded", function () {
  // interactivity for dish amount display
  const inputRange = document.getElementById("dishAmtRange");
  const inputRangeDisplay = document.getElementById("dishRangeDisplay");
  const dishAmtPrice = document.getElementById("dishAmtPrice");
  const dishAmtPriceDisplay = document.getElementById("dishAmtPriceDisplay");

  if (inputRange && inputRangeDisplay) {
    const updateDisplay = () => {
      const amount = inputRange.value;
      inputRangeDisplay.textContent = amount;

      if (dishAmtPrice) {
        try {
          // parse only the number/float values;
          const price = parseFloat(
            dishAmtPrice.textContent.replace(/[^0-9.]/g, "")
          );
          const multiplier = parseInt(inputRange.value.replace(/[^0-9.]/g, ""));

          const newPrice = price * multiplier;
          dishAmtPriceDisplay.textContent = `₦${newPrice.toLocaleString()}`; // locale str formats number properly, 1000 -> 1,000
        } catch (e) {
          console.warn("Failed to update new dish price");
        }
      }
    };
    inputRange.addEventListener("input", updateDisplay);
    updateDisplay();
  } else {
    console.warn("dishAmtRange or dishRangeDisplay element not found");
  }

  // extras cards interactivity
  function initExtraCard(card) {
    const checkbox = card.querySelector('input[type="checkbox"]');
    const range = card.querySelector('input[type="range"]');
    const display = card.querySelector('[id^="extraRangeDisplay-"]');
    const unitPrice = card.querySelector('[id^="extraAmtPrice-"]');
    const priceDisplay = card.querySelector('[id^="extraAmtPriceDisplay-"]');
    const amountBody = card.querySelector('[id^="extraAmtBody-"]');

    if (!checkbox || !range || !display || !unitPrice || !priceDisplay) return;

    const updatePrice = () => {
      const amount = parseInt(range.value, 10);
      display.textContent = amount;

      // Prefer data-price attribute; fall back to parsing text content
      const raw = unitPrice.dataset.price ?? unitPrice.textContent;
      const price = parseFloat(raw.replace(/[^0-9.]/g, ""));

      if (!isNaN(price)) {
        priceDisplay.textContent = `₦${(price * amount).toLocaleString()}`;
      } else {
        console.warn("Could not parse unit price for", card);
      }
    };

    range.addEventListener("input", updatePrice);

    checkbox.addEventListener("change", () => {
      card.classList.toggle("bg-success", checkbox.checked);
      card.classList.toggle("shadow", checkbox.checked);
      range.disabled = !checkbox.checked;
      amountBody.style.display = checkbox.checked ? "block" : "none";

      if (!checkbox.checked) range.value = 1;

      updatePrice(); // sync on both check and uncheck
    });

    // Initialise disabled state and body visibility
    range.disabled = !checkbox.checked;
    amountBody.style.display = checkbox.checked ? "none" : "none";
    updatePrice();
  }

  document.querySelectorAll('[id^="selectExtra-"]').forEach((checkbox) => {
    const card = checkbox.closest(".card");
    if (card) initExtraCard(card);
  });

  // confirm order modal UI/UX
  function createOrderItem(name, amount) {
    const li = document.createElement("li");
    li.className = "list-group-item";

    const span = document.createElement("span");
    span.textContent = name;

    const sub = document.createElement("sub");
    sub.textContent = ` x ${amount}`;

    li.appendChild(span);
    li.appendChild(sub);
    return li;
  }

  let expectedTotalPrice = 0;

  function addItemTotalPrice(price, range) {
    const itemPrice = price * range;

    if (!isNaN(itemPrice)) {
      expectedTotalPrice += itemPrice;
    }
  }

  const continueToOrderBtn = document.getElementById("continueToOrder");

  if (continueToOrderBtn) {
    continueToOrderBtn.addEventListener("click", function () {
      const orderedItemList = document.getElementById("itemsList");
      const mainOrder = document.getElementById("dishName");
      const extras = document.querySelectorAll('[id^="selectExtra-"]');

      if (!orderedItemList || !mainOrder) return;

      orderedItemList.replaceChildren();

      // Add main dish
      orderedItemList.appendChild(
        createOrderItem(mainOrder.textContent, inputRange.value)
      );

      // add main dish total price
      // parse only the number/float values;
      const dishPrice = parseFloat(
        dishAmtPrice.textContent.replace(/[^0-9.]/g, "")
      );
      const dishMultiplier = parseInt(inputRange.value.replace(/[^0-9.]/g, ""));

      if (dishPrice && dishMultiplier) {
        addItemTotalPrice(dishPrice, dishMultiplier);
      }

      // Add selected extras
      extras.forEach((checkbox) => {
        if (!checkbox.checked) return;

        const card = checkbox.closest(".card");
        const extraName = card.querySelector('[id^="extraName-"]');
        const extraRange = card.querySelector('input[type="range"]');

        if (extraName && extraRange) {
          orderedItemList.appendChild(
            createOrderItem(extraName.textContent, extraRange.value)
          );
        }

        // add extra item total price
        const extraAmtPrice = card.querySelector('[id^="extraAmtPrice-"]');
        // parse only the number/float values;
        const extraPrice = parseFloat(
          extraAmtPrice.textContent.replace(/[^0-9.]/g, "")
        );
        const extraMultiplier = parseInt(
          extraRange.value.replace(/[^0-9.]/g, "")
        );

        if (extraPrice && extraMultiplier) {
          addItemTotalPrice(extraPrice, extraMultiplier);
        }
      });

      if (expectedTotalPrice > 0) {
        const totalPriceDisplay = document.getElementById("totalPriceDisplay");
        totalPriceDisplay.className = "text-muted fw-bold small float-end";
        totalPriceDisplay.textContent = `Total - ₦${expectedTotalPrice.toLocaleString()}`;
        totalPriceDisplay.appendChild(p);
      }
    });
  }

  // run location process before submission
  const form = document.querySelector("form");

  function getLocation() {
    return new Promise((resolve, reject) => {
      if (!navigator.geolocation) {
        reject(new Error("Geolocation is not supported by this browser."));
        return;
      }
      navigator.geolocation.getCurrentPosition(resolve, reject);
    });
  }

  form.addEventListener("submit", async function (event) {
    event.preventDefault();

    try {
      const position = await getLocation();

      document.getElementById("latitudeInput").value = position.coords.latitude;
      document.getElementById("longitudeInput").value =
        position.coords.longitude;

      form.submit();
    } catch (error) {
      const messages = {
        1: "Location permission was denied.",
        2: "Location information is unavailable.",
        3: "Location request timed out.",
      };
      alert(
        messages[error.code] ?? "An unknown error occurred getting location."
      );
    }
  });

  // disable state management for offline
  const btn = document.getElementById("continueOrderBtn");
  const statusBanner = document.getElementById("onlineStatus");

  function updateOnlineStatus() {
    const isOnline = navigator.onLine;

    // Toggle button
    if (btn) {
      btn.disabled = !isOnline;
      btn.setAttribute("aria-disabled", String(!isOnline));
    }

    // Toggle alert banner
    if (statusBanner) {
      statusBanner.classList.toggle("d-none", isOnline);
      statusBanner.classList.toggle("d-flex", !isOnline);
    }
  }

  window.addEventListener("online", updateOnlineStatus);
  window.addEventListener("offline", updateOnlineStatus);

  // Run immediately so initial state is correct on page load
  updateOnlineStatus();
});
