/**
 * check/uncheck all checkbox in consent form
 */
document.getElementById("toggle-all")
  .addEventListener("change", function() {
    const checkboxes = document.getElementsByName("status");
    checkboxes.forEach(checkbox => checkbox.checked = this.checked);
});
