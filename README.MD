<div align="center">
    <img src="logo.png" alt="crypto-pulse-logo" width=128/>
    <h1>CryptoPulse</h1>
</div>

<p align="center">
    <img src="https://img.shields.io/badge/Docker-2496ED?logo=docker&logoColor=white">
    <img src="https://img.shields.io/badge/Python-3776AB?logo=python&logoColor=white">
    <img src="https://img.shields.io/badge/Aiogram-2CA5E0?logo=telegram&logoColor=white">
    <img src="https://img.shields.io/badge/PostgreSQL-4169E1?logo=postgresql&logoColor=white">
</p>


## ⚡ CryptoPulse - SaaS Telegram Bot for Crypto Tracking

***CryptoPulse*** is a production-ready SaaS Telegram bot designed for real-time tracking of anomalous cryptocurrency market activity ("whale" trades, volume spikes, and price surges) featuring an integrated subscription billing engine.

<h2>🎯 MVP Goal</h2>
To provide crypto traders with instant Telegram alerts driven by direct exchange feeds, while showcasing a fully functional automated subscription model built on a scalable backend architecture.

##

## 🚀 Key Features
<ul>
    <li>Whale Tracking:</li>
    <ul>
        <li>Real-time WebSocket connection to the Bybit exchange API.</li>
        <li>Live trade filtering based on customizable volume thresholds.</li>
        <li>Dynamic Watchlist — full support for any spot and futures pairs listed on Bybit.</li>
    </ul>
    <li>User managment:</li>
    <ul>
        <li>Personal user dashboard right inside the bot interface.</li>
        <li>Alert fine-tuning: filtering by trading pairs, minimum USD volume, and notification types.</li>
    </ul>
</ul>

##

## Project setup

<h4>1. Clone github repository</h4>

```
git clone https://github.com/lithiumdev-c/cryptopulse
cd cryptopulse
```

<h4>2. Setup virtual environment inside project folder</h4>

```
python -m venv .venv
```
<p>Activate it</p>


```
# For Linux or MacOS
source .venv/bin/activate

# For Windows
.venv\Scripts\activate
```

<h4>3. Install Backend</h4>

```
pip install -r requirements.txt
```

<h4>4. Env setup</h4>```pip install -r requirements.txt
```
Create .env file and get telegram token from @BotFather
And fill this constants inside .env file!

```
    BOT_TOKEN = ""
    DATABASE_URL = ""
```

<h4>Docker</h4>

```
#if Windows

docker compose up -d

#if Linux

sudo docker compose up -d
```

##

## Launch

After project setup and installation run main.py

```
python main.py
```