# Modern Banking System

Bu proje, finansal teknolojiler (FinTech) prensiplerine uygun olarak geliştirilmiş tam donanımlı bir çekirdek bankacılık sistemidir. İçerisinde güvenli para transferleri, hesap yönetimi ve yönetici denetim logları (Audit) bulunur.

## 🚀 Projede Neler Var?

1. **Backend (Python / FastAPI):**
   * Kullanıcı yetkilendirme (JWT, BCrypt) ve Rol tabanlı erişim (Admin / Customer).
   * Çift kayıtlı muhasebe mantığına dayanan, değiştirilemez (Immutable) **Ledger (Defter)** yapısı. Para transferleri güvenli bir şekilde tek bir veritabanı "transaction" işlemi ile gerçekleştirilir.
   * `/docs` adresinde otomatik oluşturulan OpenAPI (Swagger) dokümantasyonu.

2. **Veritabanı (PostgreSQL):**
   * İlişkisel veritabanı bütünlüğü. Tüm veriler Docker volume içerisinde güvenle saklanır.

3. **Frontend (HTML / JS / TailwindCSS):**
   * `index.html`: Kullanıcı giriş ekranı.
   * `dashboard.html`: Kullanıcıların bakiyelerini gördüğü ve para transferi yapabildiği ekran.
   * `admin.html`: Tüm sistemdeki finansal hareketlerin kronolojik olarak izlendiği Denetim (Audit) paneli.

4. **DevOps / Altyapı:**
   * Tüm sistemi veritabanıyla birlikte tek tuşla ayağa kaldıran `docker-compose.yml`.
   * GitHub Actions için hazırlanmış CI (Continuous Integration) boru hattı yapılandırması (`.github/workflows`).

## 🛠️ Nasıl Çalıştırılır?

Bu projeyi bilgisayarınızda çalıştırmak için yalnızca **Docker** (ve Docker Compose) yüklü olması yeterlidir.

1. Terminali veya Komut İstemcisi'ni açın ve proje klasörünün içindeki `infra` dizinine gidin:
   ```bash
   cd infra
   ```

2. Docker ile tüm sistemi inşa edip ayağa kaldırın:
   ```bash
   docker compose up -d --build
   ```
   *(İlk kurulumda Python kütüphaneleri ve Postgres imajı indirileceği için biraz sürebilir.)*

3. Sistem hazır olduğunda test verilerini yüklemek için şu komutu çalıştırın:
   ```bash
   docker compose exec backend python seed.py
   ```

## 🌐 Sisteme Erişim

Kurulum bittikten sonra tarayıcınızdan aşağıdaki linklere gidebilirsiniz:

*   **Frontend (Arayüz):** Arayüzü kullanmak için herhangi bir sunucuya gerek yoktur. Doğrudan bilgisayarınızdaki `frontend/index.html` dosyasına çift tıklayarak tarayıcıda açın.
    *   *Test Müşterisi:* Kullanıcı adı: `johndoe` | Şifre: `pass1234`
    *   *Sistem Yöneticisi (Admin):* Kullanıcı adı: `admin` | Şifre: `admin123`
*   **API Dokümantasyonu (Backend):** `http://localhost:8000/docs`

## 📁 Klasör Yapısı

*   `/backend`: FastAPI kodları, veritabanı modelleri ve API rotaları.
*   `/frontend`: Web arayüzü dosyaları.
*   `/infra`: Docker Compose ve container ayarları.
*   `/docs`: Mimari şemalar, güvenlik notları ve API dışa aktarımları.
