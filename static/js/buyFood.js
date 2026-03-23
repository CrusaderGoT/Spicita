"use strict";

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
    });
  });
}

// run location process before submission

const form = document.querySelector("form");

function getLocation() {
  if (navigator.geolocation) {
    // Geolocation is supported, proceed to request location
    navigator.geolocation.getCurrentPosition(setPositionToForm, showError);
  } else {
    // Geolocation is not supported
    alert("Geolocation is not supported by this browser.");
  }
}

function setPositionToForm(position) {
  const latitude = position.coords.latitude;
  const longitude = position.coords.longitude;

  const latitudeInput = document.getElementById("latitudeInput");
  const longitudeInput = document.getElementById("longitudeInput");

  latitudeInput.value = latitude;
  longitudeInput.value = longitude;

  form.submit();
}

function showError(error) {
  switch (error.code) {
    case error.PERMISSION_DENIED:
      alert("User denied the request for Geolocation.");
      break;
    case error.POSITION_UNAVAILABLE:
      alert("Location information is unavailable.");
      break;
    case error.TIMEOUT:
      alert("The request to get user location timed out.");
      break;
    case error.UNKNOWN_ERROR:
      alert("An unknown error occurred when getting location.");
      break;
  }
}

form.addEventListener("submit", function (event) {
  event.preventDefault(); // Stop the submission

  getLocation();
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
