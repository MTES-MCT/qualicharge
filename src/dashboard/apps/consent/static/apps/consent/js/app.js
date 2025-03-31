const PdlCheckboxesName = "status";

/**
 * check/uncheck all checkbox in consent form
 */
document.getElementById("toggle-all")
  .addEventListener("change", function() {
    const checkboxes = document.getElementsByName(PdlCheckboxesName);
    checkboxes.forEach(checkbox => checkbox.checked = this.checked);
    updateCheckedCount();
});


/**
 * Handle state changes for PDL checkboxes
 */
const individualCheckboxes = document.getElementsByName(PdlCheckboxesName);
individualCheckboxes.forEach(checkbox => {
  checkbox.addEventListener("change", function() {
    updateCheckedCount();
  });
});


/**
 * Updates the displayed count of checked PDLs checkboxes
 * to reflect the total number of checked checkboxes.
 */
function updateCheckedCount() {
  const checkboxes = document.getElementsByName(PdlCheckboxesName);
  const checkedCount = Array.from(checkboxes).filter(checkbox => checkbox.checked).length;

  document.getElementById("checked-count").textContent = checkedCount;
}


/**
 * keyboard navigation management for the manage form and more specifically
 * for the PDLs table.
 *
 * If the PDLs table is focused:
 * - On pressing the "Escape" key: the focus moves to the next element after the table.
 *
 * From the next element of PDLs table:
 * - If the "Tab" and "Shift" keys are pressed simultaneously: the focus moves back to
 *   the "Toggle All" checkbox of the PDLs table.
 *
 */
document.addEventListener("keydown", function (event) {
  const scrollableArea = document.querySelector(".fr-table__content");
  const activeElement = document.activeElement;

  //  PDLs table is focused and Escape key
  if (scrollableArea && scrollableArea.contains(activeElement)) {
    if (event.key === "Escape") {
      const nextFocus = document.getElementById("focus-after-consents");
      if (nextFocus) nextFocus.focus();
    }
  }

  // Next element of PDLs table and Tab+Shift keys
  if (activeElement.id === "focus-after-consents") {
    if (event.key === "Tab" && event.shiftKey) {
      event.preventDefault();
      const previousFocus = document.getElementById("toggle-all");
      if (previousFocus) previousFocus.focus();
    }
  }

});


/**
 * Activate the form submit button only if the user has viewed all PDLs.
 *
 * 2 possibilities to activate the buttons:
 * - there are only few PDLs, and the table is fully visible without scrolling.
 * - the user scrolled (or navigated using the keyboard) to view all the PDLs in the table.
 */
document.addEventListener("DOMContentLoaded", function () {
  const scrollableTable = document.querySelector(".fr-table__content");
  const validateButton = document.getElementById("btn-validate");
  const validateAlert = document.getElementById("alert-validate");

  // Checks if the table is scrollable
  function checkScrollable() {
    const isScrollable = scrollableTable.scrollHeight > scrollableTable.clientHeight;
    if (!isScrollable) {
      validateButton.disabled = false;
      validateAlert.style.display = "none";
    }
    return isScrollable;
  }

  const hasScroll = checkScrollable();

  // Add the scrolling listener only if the table is scrollable
  if (hasScroll) {
    scrollableTable.addEventListener("scroll", function () {
      const isScrolledToEnd =
        scrollableTable.scrollHeight - scrollableTable.scrollTop === scrollableTable.clientHeight;

      if (isScrolledToEnd) {
        validateButton.disabled = false;
        validateAlert.style.display = "none";
      }
    });
  }
});

