# WNBA Prop Engine — The Odds API Clean Rebuild

This build avoids the mixed Underdog feed.

## Setup

Railway env var:
ODDS_API_KEY=your_key_here

Streamlit Cloud secret:
ODDS_API_KEY = "your_key_here"

## Main file
app.py

## Features
- Real WNBA lines only through sport key basketball_wnba
- Event-odds player props
- Full player cards
- EV / probability / Kelly
- Before/after saves
- Grading + learning
- CLV tracking
- Projection CSV upload
- NBA leak blocker


## v1.1

Your API key was added as the default fallback inside `app.py`.

Railway/Streamlit secrets can still override it with:

```text
ODDS_API_KEY=c9f5eadbe263f64c3fd17df20a4f1f3b
```


## v1.2 MLB protection layers added

Added MLB-style protection pieces:
- Market Confidence Score
- Overall Rating
- Volatility Rating
- Steam / line-movement signal
- Protection Tag
- Stronger sorting by rating


## v1.3 Manual Line Adjuster

Added:
- Manual line overrides by player/market/book
- Blank book applies override to all books for that player+market
- Projection remains unchanged
- Learning baseline remains unchanged
- Edge/Pick/EV/Rating use manual line when active
- Original sportsbook line remains visible as Book Line
