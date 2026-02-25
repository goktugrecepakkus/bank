# 🗺️ Proje Yol Haritası ve Veritabanı Planı

## 📅 3 Haftalık Uygulama Planı

### Hafta 1: Temel Mimari ve Çekirdek Bankacılık (Core APIs)
- [ ] Proje klasör yapısının (`backend`, `frontend`, `docs`) oluşturulması.
- [ ] Docker ve PostgreSQL altyapısının `docker-compose.yml` ile ayağa kaldırılması.
- [ ] Veritabanı tablolarının (Customer, Account, Ledger) oluşturulması.
- [ ] FastAPI uygulamasının başlatılması ve otomatik Swagger belgesinin test edilmesi.
- [ ] Müşteri oluşturma (Customer) ve Hesap Açma (Account) API'lerinin yazılması.
- [ ] **KRİTİK:** Çift girişli muhasebe mantığıyla çalışan Transfer (Ledger) API'sinin yazılması.

### Hafta 2: Güvenlik, Arayüz ve Entegrasyon (Security & UI)
- [ ] JWT tabanlı Kimlik Doğrulama (Login) ve Yetkilendirme (Admin/Customer rolleri) eklenmesi.
- [ ] API yetki kontrollerinin (Kimse başkasının hesabından para gönderemez) yapılması.
- [ ] Frontend tarafında HTML sayfalarının (Giriş, Pano, Transfer Formu) tasarlanması.
- [ ] Frontend sayfalarının JavaScript fetch() ile Backend API'lerine bağlanması.
- [ ] Tüm işlemlerin (kim, ne zaman, ne yaptı) loglanması (Audit Log).

### Hafta 3: Son Rötuşlar, Test ve Teslimat
- [ ] GitHub Actions ile basit bir CI (Otomatik Test/Linting) kurgusu yapılması.
- [ ] Hata yakalama mesajlarının (Örn: Yetersiz Bakiye) düzenlenmesi.
- [ ] Projenin uçtan uca (End-to-End) tek tıkla çalışabildiğinin test edilmesi.
- [ ] Sunum için ekran görüntülerinin ve hikayenin hazırlanması.

---

## 💾 Veritabanı Tablo Tasarımı (Core Banking Schema)

Ödevin en önemli kısmı **Veri Bütünlüğü** ve **Ledger (Kasa Defteri)** mantığıdır. Bu yüzden ilişkisel bir veritabanı (PostgreSQL) kullanıyoruz. İlk aşamada şu 3 temel tabloyu kuracağız:

### 1. `customers` Tablosu
Sisteme kayıt olan kullanıcıların bilgilerini tutar.
*   `id` (UUID veya Serial) - Primary Key
*   `username` (String) - Giriş adı
*   `password_hash` (String) - Şifreli parola
*   `role` (String) -> 'admin' veya 'customer'
*   `created_at` (Timestamp)

### 2. `accounts` Tablosu
Bir müşterinin birden fazla hesabı (Vadesiz, Vadeli vb.) olabilir. Bakiyeler burada durur ancak **buradaki bakiye doğrudan güncellenmez, Ledger'dan hesaplanır ya da Ledger'a kayıt atılmadan değiştirilmesine izin verilmez.**
*   `id` (UUID veya Serial) - Primary Key
*   `customer_id` (Foreign Key -> customers.id) - Hesabın sahibi
*   `account_type` (String) -> Örn: 'CHECKING' (Vadesiz)
*   `balance` (Decimal) -> Güncel Bakiye (Örn: 1500.50)
*   `status` (String) -> 'ACTIVE', 'BLOCKED'

### 3. `ledger` Tablosu (En Önemlisi! İptal Edilemez Defter)
Sistemdeki TEK GERÇEK KAYNAK (Single Source of Truth) burasıdır. Para asla yoktan var olmaz (Para yatırma -Deposit- hariç) ve kaybolmaz.
*   `transaction_id` (UUID) - Primary Key
*   `from_account_id` (Foreign Key / Nullable) -> Para nereden çıktı? (Eğer dışarıdan para yatırılıyorsa NULL veya 'SYSTEM' olur).
*   `to_account_id` (Foreign Key / Nullable) -> Para nereye girdi? (Para çekiliyorsa NULL veya 'CASH_OUT' olur).
*   `amount` (Decimal) -> Giden tutar.
*   `transaction_type` (String) -> 'DEPOSIT' (Yatırma), 'WITHDRAWAL' (Çekme), 'TRANSFER' (Havale).
*   `created_at` (Timestamp) -> İşlem zamanı (Silinemez ve güncellenemez - Append Only).

> **💡 Bankacılık Kuralı:** Eğer A firmasından B firmasına 100 ₺ gönderilecekse, sistem önce hesabın bakiyesini kontrol eder. Para yetiyorsa, `ledger` tablosuna bir satır eklenir: *"A'dan B'ye 100 ₺ Transfer edildi"*. Bu işlem başarılı olduktan sonra A'nın bakiyesi `-100`, B'nin bakiyesi `+100` güncellenir. Eğer Ledger'a yazılamazsa, bakiyeler de güncellenmez. İşlem geri alınmak istenirse, Ledger'dan satır silinmez, tam tersi bir kayıt daha atılır (B'den A'ya 100 ₺ İade).
