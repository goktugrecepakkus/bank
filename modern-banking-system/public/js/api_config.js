// Akıllı API Konfigürasyonu
// Web'de çalışırken (browser) otomatik olarak kendi hostunu kullanır.
// Mobile App'de (Android/Capacitor) çalışırken Vercel sunucusuna bağlanır.

let API_BASE_URL = ""; // Varsayılan: Boş (yani relative path)

if (window.location.protocol === 'file:' || window.location.hostname === '') {
    // Eğer protokol 'file:' ise bu yüksek ihtimalle bir mobil uygulamadır.
    API_BASE_URL = "https://bank-murex-delta.vercel.app";
}

window.API_BASE_URL = API_BASE_URL;
console.log("[Rykard Config] API Base URL set to:", window.API_BASE_URL || "Local/Relative");
