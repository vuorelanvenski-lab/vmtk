# Leijona Catering Foodlist API (Hoikanhovi Kajaani)

FastAPI-pohjainen mikropalvelu, joka hakee Leijona Cateringin (Kajaani, Hoikanhovi) kuluvan viikon ruokalistat heidän JSON-rajapinnastaan. Palvelu tarjoaa varusmiesten ja henkilökunnan ruokalistat jäsennellyssä JSON-muodossa.

## Proxmox Docker -asennus

Palvelu on tarkoitettu ajettavaksi Docker-konttina Proxmox-ympäristössä (virtuaalikone tai LXC).

### 1. Ympäristön valmistelu

Asenna Docker ja Docker Compose, jos niitä ei ole vielä asennettu (Debian/Ubuntu):

```bash
sudo apt-get update && sudo apt-get upgrade -y
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo apt-get install docker-compose-plugin -y
sudo systemctl enable docker
sudo systemctl start docker
```

### 2. Projektin lataaminen ja käynnistys

Kloonaa repository ja käynnistä palvelu:

```bash
git clone https://gitlab.com/sinun-kayttajatunnus/foodlist-api.git
cd foodlist-api
sudo docker compose up -d --build
```

Palvelin käynnistyy porttiin 8000. Voit varmistaa kontin tilan komennolla:

```bash
sudo docker ps
```

Rajapinta on nyt saatavilla osoitteessa:
`http://<PALVELIMEN_IP>:8000/api/foodlist`

## Paikallinen kehitys

Jos haluat ajaa ohjelmaa ilman Dockeria:

1. Asenna Python 3.11+.
2. Asenna riippuvuudet: `pip install -r requirements.txt`
3. Käynnistä palvelin: `uvicorn app:app --reload --host 0.0.0.0 --port 8000`
4. Swagger UI -dokumentaatio löytyy osoitteesta: `http://localhost:8000/docs`

## API Dokumentaatio

### GET /api/foodlist

Palauttaa kuluvan viikon ruokalistat.

Esimerkkivastaus:
```json
{
  "data": {
    "week_start": "2026-04-27T00:00:00.000Z",
    "week_end": "2026-05-03T00:00:00.000Z",
    "conscript_menu": [
      {
        "date": "ma 27.4.2026",
        "meals": [
          {
            "meal_name": "Lounas",
            "dishes": [
              {
                "name": "Broileria currykastikkeessa",
                "diets": "L, G"
              }
            ]
          }
        ]
      }
    ],
    "staff_menu": []
  }
}
```
