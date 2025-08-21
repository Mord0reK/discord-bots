# Discord Bots - Kolekcja Botów Discord

Ten repozytorium zawiera kolekcję botów Discord napisanych w języku Python, każdy z których oferuje różne funkcjonalności.

## 📁 Struktura Projektu

```
discord-bots/
├── GCP Minecraft Bot/          # Bot do zarządzania serwerem Minecraft z integracją GCP
│   ├── main.py                 # Główny kod bota
│   ├── README.md              # Dokumentacja bota
│   └── requirements.txt       # Zależności Python
├── Radyjko-DC/                # Bot radiowy z odtwarzaniem muzyki
│   ├── main.py                # Główny kod bota
│   ├── README.md              # Dokumentacja bota
│   ├── requirements.txt       # Zależności Python
│   └── stacje.txt            # Lista dostępnych stacji radiowych
├── .gitignore                 # Pliki ignorowane przez Git
└── README.md                  # Ten plik - dokumentacja główna
```

## 🤖 Dostępne Boty

### 1. GCP Minecraft Bot

**Lokalizacja:** `GCP Minecraft Bot/`

**Opis:** Bot Discord umożliwiający sprawdzanie statusu serwera Minecraft oraz zarządzanie maszynami wirtualnymi w Google Cloud Platform.

**Główne funkcjonalności:**
- 🔍 Sprawdzanie statusu serwera Minecraft (`/status`)
- 👥 Wyświetlanie liczby graczy online i ich listy
- 📊 Informacje o wersji serwera i pingu
- ☁️ Uruchamianie maszyn wirtualnych GCP (`/start`)
- 🛑 Zatrzymywanie maszyn wirtualnych GCP (`/stop`)
- 🔄 Automatyczne sprawdzanie statusu co minutę

**Kluczowe zależności:**
- `discord.py` >= 2.0.0
- `mcstatus` >= 9.0.0
- `google.cloud.compute_v1`

### 2. Radyjko-DC

**Lokalizacja:** `Radyjko-DC/`

**Opis:** Zaawansowany bot radiowy i muzyczny dla Discord, umożliwiający odtwarzanie stacji radiowych oraz treści z YouTube.

**Główne funkcjonalności:**
- 🔊 Łączenie się z kanałami głosowymi
- 📻 Odtwarzanie stacji radiowych (`/play`)
- 🎵 Odtwarzanie utworów i playlist z YouTube (`/yt`)
- 📋 Wyświetlanie dostępnych stacji (`/stacje`)
- 🔉 Kontrola głośności (`/volume`)
- ℹ️ Informacje o aktualnie odtwarzanych utworach (`/terazgrane`)
- 📝 Zarządzanie kolejką muzyki (`/kolejka`)
- ⏭️ Pomijanie utworów (`/skip`)
- 📈 Statystyki wydajności bota (`/performance`)
- 🚪 Automatyczne rozłączanie gdy bot zostaje sam

**Kluczowe zależności:**
- `discord.py` == 2.4.0
- `yt-dlp` == 2025.1.26
- `ffmpeg` == 1.4
- `requests` == 2.32.3
- `psutil` == 6.1.1

**Pliki konfiguracyjne:**
- `stacje.txt` - Lista dostępnych stacji radiowych z ID, nazwami i URL-ami

## 🚀 Instalacja i Uruchomienie

### Wymagania systemowe
- Python 3.8 lub nowszy
- FFmpeg (dla Radyjko-DC)
- Konto Discord Developer z tokenem bota
- (Opcjonalnie) Konto Google Cloud Platform dla GCP Minecraft Bot

### Kroki instalacji

1. **Sklonuj repozytorium:**
   ```bash
   git clone https://github.com/Mord0reK/discord-bots.git
   cd discord-bots
   ```

2. **Wybierz bot i przejdź do jego folderu:**
   ```bash
   # Dla GCP Minecraft Bot
   cd "GCP Minecraft Bot"
   
   # LUB dla Radyjko-DC
   cd "Radyjko-DC"
   ```

3. **Zainstaluj zależności:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Skonfiguruj zmienne środowiskowe:**
   - Utwórz odpowiednie zmienne środowiskowe z tokenem Discord
   - Dla GCP Minecraft Bot: skonfiguruj również dane GCP
   - Szczegółowe instrukcje znajdziesz w README.md każdego bota

5. **Uruchom bota:**
   ```bash
   python main.py
   ```

## 📖 Dokumentacja

Każdy bot posiada własną szczegółową dokumentację w pliku `README.md` w swoim folderze:

- [`GCP Minecraft Bot/README.md`](GCP%20Minecraft%20Bot/README.md) - Kompletna dokumentacja bota Minecraft
- [`Radyjko-DC/README.md`](Radyjko-DC/README.md) - Kompletna dokumentacja bota radiowego

## 🛠️ Rozwój i Współpraca

### Struktura kodu
- Każdy bot jest niezależnym projektem z własnymi zależnościami
- Kod wykorzystuje bibliotekę `discord.py` w wersji 2.x
- Implementowane są slash commands dla lepszej integracji z Discord

### Dodawanie nowych botów
1. Utwórz nowy folder z nazwą bota
2. Dodaj `main.py`, `README.md` i `requirements.txt`
3. Zaktualizuj ten główny README.md
4. Przetestuj funkcjonalność przed commit

## 📝 Licencja

Projekty zawarte w tym repozytorium są dostępne na warunkach określonych przez właściciela repozytorium.

## 🤝 Kontakt

W przypadku pytań lub problemów, prosimy o kontakt przez Issues na GitHub.

---

*Ostatnia aktualizacja: 2025*