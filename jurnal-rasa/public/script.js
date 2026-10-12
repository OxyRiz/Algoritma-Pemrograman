// Ubah warna latar halaman sesuai mood yang dipilih
document.querySelectorAll('input[name="mood"]').forEach((radio) => {
  radio.addEventListener("change", () => {
    document.body.dataset.mood = radio.value;
  });
});

// Konfirmasi sebelum menghapus catatan
document.querySelectorAll("form[data-confirm]").forEach((form) => {
  form.addEventListener("submit", (event) => {
    if (!confirm(form.dataset.confirm)) event.preventDefault();
  });
});
