# BESS-optimization
Battery Energy Storage System optimization using MILP, PV forecasting, Open-Meteo and ENTSO-E day-ahead electricity prices.

# 🔋 BESS Optimization

A Streamlit application for optimizing the operation of a Battery Energy Storage System (BESS) coupled with a photovoltaic (PV) power plant.

The optimization is formulated as a Mixed-Integer Linear Programming (MILP) problem and uses:

- ☀️ Open-Meteo API for solar radiation forecast
- ⚡ ENTSO-E Transparency Platform for day-ahead electricity prices
- 🔋 Battery operation constraints
- 📈 Interactive visualization of optimization results

---

## Features

- Automatic retrieval of weather forecast
- Automatic retrieval of ENTSO-E day-ahead prices
- PV production estimation
- MILP battery optimization
- State of Charge (SOC) simulation
- Interactive Streamlit dashboard
- CSV and Excel export
- Mathematical model documentation

---

## Mathematical model

The optimization minimizes the total operating cost.

Subject to:

- Battery SOC dynamics
- SOC limits
- Charging/discharging power limits
- Battery capacity constraints
- Complementarity constraint

---

## Project structure

```
BESS_optimization/
│
├── api/
│   ├── entsoe_api.py
│   └── openmeteo_api.py
│
├── gui/
│   ├── app.py
│   └── plots.py
│
├── models/
│   └── pv_model.py
│
├── optimization/
│   ├── milp.py
│   ├── costs.py
│   └── objective_function.py
│
├── simulation/
│   └── runner.py
│
├── run_model.py
├── requirements.txt
└── README.md
```

---

## Installation

Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/BESS_optimization.git
```

Install dependencies

```bash
pip install -r requirements.txt
```

Run the application

```bash
streamlit run gui/app.py
```

---

## Technologies

- Python
- Streamlit
- PuLP
- Plotly
- Pandas
- Open-Meteo API
- ENTSO-E Transparency Platform

---

## Data sources

- Open-Meteo API
- ENTSO-E Transparency Platform

---

## Author

Antonija Kežić

Bachelor Thesis

Faculty of Electrical Engineering, Mechanical Engineering and Naval Architecture (FESB)

University of Split
