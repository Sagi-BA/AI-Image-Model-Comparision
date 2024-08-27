function reloadPage() {
  window.sessionStorage.setItem("clear_uploader", "true");
  window.location.reload();
}

window.addEventListener("load", function () {
  if (window.sessionStorage.getItem("clear_uploader") === "true") {
    window.sessionStorage.removeItem("clear_uploader");
    const fileInput =
      window.parent.document.querySelector('input[type="file"]');
    if (fileInput) {
      fileInput.value = "";
      const event = new Event("change", { bubbles: true });
      fileInput.dispatchEvent(event);
    }
  }
});
