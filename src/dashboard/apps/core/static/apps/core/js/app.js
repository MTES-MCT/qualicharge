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
      const previousFocus = document.getElementById("focus-before-consents");
      if (previousFocus) previousFocus.focus();
    }
  }

});
