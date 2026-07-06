# BESS Optimization

Battery Energy Storage System (BESS) optimization using Mixed-Integer Linear Programming (MILP), photovoltaic (PV) generation forecasting, Open-Meteo weather forecasts and ENTSO-E day-ahead electricity prices.

The project includes an interactive Streamlit application for analyzing battery operation under different operating scenarios and comparing MILP optimization with a heuristic control strategy.

---

## Features

- Two operating scenarios:
  - **PV + Battery**
  - **Grid-connected Battery**
- MILP-based battery optimization
- Heuristic battery control algorithm
- Automatic retrieval of day-ahead electricity prices (ENTSO-E)
- Automatic retrieval of solar radiation forecast (Open-Meteo)
- Photovoltaic power estimation
- Battery degradation cost modelling
- Battery State of Charge (SOC) simulation
- Interactive Streamlit dashboard
- Mathematical model documentation
- CSV and Excel export of optimization results

---

## Mathematical model

The battery scheduling problem is formulated as a Mixed-Integer Linear Programming (MILP) optimization problem.

The optimization minimizes the operating cost while considering:

- electricity market prices,
- battery degradation cost,
- battery charging and discharging efficiencies,
- State of Charge (SOC) limits,
- charging/discharging power limits,
- battery capacity,
- final SOC constraint,
- complementarity constraint using binary decision variables.

As a reference method, the application also includes a heuristic control algorithm based on predefined charging and discharging rules.

---

## Project structure

```text
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
│   ├── battery.py
│   └── pv_model.py
│
├── optimization/
│   ├── milp.py
│   ├── objective_function.py
│   ├── objective_function_pv.py
│   ├── costs.py
│   ├── costs_pv.py
│   └── economic_effect.py
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

Clone the repository:

```bash
git clone https://github.com/YOUR_USERNAME/BESS_optimization.git
```

Install the required dependencies:

```bash
pip install -r requirements.txt
```

Run the application:

```bash
streamlit run gui/app.py
```

---

## Technologies

- Python
- Streamlit
- PuLP
- CBC Solver
- Plotly
- Pandas
- OpenPyXL
- Open-Meteo API
- ENTSO-E Transparency Platform

---

## Data sources

- **Open-Meteo API** – hourly solar radiation forecast
- **ENTSO-E Transparency Platform** – day-ahead electricity market prices

---

## Application overview

The application allows users to:

- configure battery and PV system parameters,
- select the operating scenario,
- compare MILP optimization with a heuristic approach,
- analyse charging/discharging schedules,
- monitor battery SOC,
- evaluate hourly operating costs and economic benefits,
- export optimization results.

---

## Author

**Antonija Kežić**

Bachelor Thesis

Faculty of Electrical Engineering, Mechanical Engineering and Naval Architecture (FESB)

University of Split
