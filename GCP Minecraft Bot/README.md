# GCP-Bot - Discord Bot dla statusu serwera Minecraft

Bot Discord umożliwiający sprawdzenie statusu lokalnego serwera Minecraft.

## Funkcje

- Sprawdzanie statusu serwera Minecraft
- Wyświetlanie liczby graczy online
- Wyświetlanie listy aktywnych graczy
- Wyświetlanie informacji o wersji serwera i pingu

## Instalacja

1. Zainstaluj Python 3.8 lub nowszy
2. Sklonuj repozytorium
3. Zainstaluj wymagane zależności:
   ```
   pip install -r requirements.txt
   ```
4. Skonfiguruj plik `config.py` podając token bota Discord oraz adres i port serwera Minecraft
5. Uruchom bota:
   ```
   python main.py
   ```

## Użycie

Po dodaniu bota do serwera Discord, użyj komendy:

```
!status
```

Bot odpowie embedem zawierającym informacje o statusie serwera Minecraft.

## Wymagania

- Python 3.8+
- Discord.py
- mcstatus
- Działający serwer Minecraft (lokalnie lub na tej samej sieci co bot)
- Token bota Discord