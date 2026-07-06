import calendar

import plotly.graph_objects as go


# ---------------------------------
# Vremenske oznake - dinamicki iz duljine podataka
# ---------------------------------

def _time_labels(n_slots, include_endpoint=False):
    """Vraća listu vremenskih oznaka "HH:MM" za n_slots vremenskih
    koraka unutar 24 sata. Ako je include_endpoint=True, doda i
    zavrsni label (npr. "24:00") - koristi se za SOC koji ima
    n_slots + 1 tocaka."""

    steps_per_hour = max(1, n_slots // 24)
    step_minutes = 60 // steps_per_hour

    labels = [
        f"{(i // steps_per_hour):02d}:{(i % steps_per_hour) * step_minutes:02d}"
        for i in range(n_slots)
    ]

    if include_endpoint:
        labels.append(f"{24:02d}:00")

    return labels


def _tick_config(labels, target_ticks=12):
    """Konfiguracija x-osi za bar plotove s velikim brojem kategorija -
    prikazuje samo svaki k-ti label da izbjegne pretrpanost."""

    step = max(1, len(labels) // target_ticks)

    return dict(
        tickmode="array",
        tickvals=labels[::step],
        ticktext=labels[::step]
    )


# ---------------------------------
# SOC
# ---------------------------------

def plot_soc_pv(soc):

    x = _time_labels(len(soc) - 1, include_endpoint=True)

    fig = go.Figure()

    fig.add_trace(

        go.Scatter(

            x=x,
            y=soc,

            mode="lines+markers",

            name="SOC",

            line=dict(width=3),

            marker=dict(size=4),

            hovertemplate=
            "<b>Vrijeme:</b> %{x}<br>"
            "<b>SOC:</b> %{y:.3f}<extra></extra>"

        )

    )

    fig.add_hline(
        y=0.2,
        line_dash="dash",
        annotation_text="SOC min"
    )

    fig.add_hline(
        y=0.9,
        line_dash="dash",
        annotation_text="SOC max"
    )

    fig.update_layout(

        title="Stanje napunjenosti baterije (SOC) - PV + baterija",

        xaxis_title="Vrijeme",

        yaxis_title="SOC",

        yaxis_range=[0,1],

        xaxis=_tick_config(x),

        template="plotly_white",

        hovermode="x unified"

    )

    return fig


def plot_soc_grid(soc):

    x = _time_labels(len(soc) - 1, include_endpoint=True)

    fig = go.Figure()

    fig.add_trace(

        go.Scatter(

            x=x,
            y=soc,

            mode="lines+markers",

            name="SOC",

            line=dict(width=3),

            marker=dict(size=4),

            hovertemplate=
            "<b>Vrijeme:</b> %{x}<br>"
            "<b>SOC:</b> %{y:.3f}<extra></extra>"

        )

    )

    fig.add_hline(
        y=0.2,
        line_dash="dash",
        annotation_text="SOC min"
    )

    fig.add_hline(
        y=0.9,
        line_dash="dash",
        annotation_text="SOC max"
    )

    fig.update_layout(

        title="Stanje napunjenosti baterije (SOC) - baterija spojena na mrežu",

        xaxis_title="Vrijeme",

        yaxis_title="SOC",

        yaxis_range=[0,1],

        xaxis=_tick_config(x),

        template="plotly_white",

        hovermode="x unified"

    )

    return fig


# ---------------------------------
# PV
# ---------------------------------

def plot_pv(pv):

    x = _time_labels(len(pv))

    fig = go.Figure()

    fig.add_trace(

        go.Bar(

            x=x,

            y=pv,

            name="PV",

            hovertemplate=
            "<b>Vrijeme:</b> %{x}<br>"
            "<b>PV:</b> %{y:.3f} kW<extra></extra>"

        )

    )

    fig.update_layout(

        title="Proizvodnja fotonaponske elektrane",

        xaxis_title="Vrijeme",

        yaxis_title="Snaga [kW]",

        xaxis=_tick_config(x),

        template="plotly_white",

        hovermode="x unified"

    )

    return fig


# ---------------------------------
# Cijene
# ---------------------------------

def plot_prices(prices):

    x = _time_labels(len(prices))

    fig = go.Figure()

    fig.add_trace(

        go.Scatter(

            x=x,

            y=prices,

            mode="lines",

            line=dict(width=2, shape="hv"),

            name="Cijena",

            hovertemplate=
            "<b>Vrijeme:</b> %{x}<br>"
            "<b>Cijena:</b> %{y:.2f} €/MWh<extra></extra>"

        )

    )

    fig.update_layout(

        title="Cijene električne energije",

        xaxis_title="Vrijeme",

        yaxis_title="€/MWh",

        xaxis=_tick_config(x),

        template="plotly_white",

        hovermode="x unified"

    )

    return fig


# ---------------------------------
# Punjenje / pražnjenje
# ---------------------------------

def plot_power_pv(charge, discharge):

    x = _time_labels(len(charge))

    fig = go.Figure()

    fig.add_trace(

        go.Bar(

            x=x,

            y=charge,

            name="Punjenje",

            marker_color="green",

            hovertemplate=
            "<b>Vrijeme:</b> %{x}<br>"
            "<b>Punjenje:</b> %{y:.3f} kW<extra></extra>"

        )

    )

    fig.add_trace(

        go.Bar(

            x=x,

            y=[-v for v in discharge],

            customdata=discharge,

            name="Pražnjenje",

            marker_color="red",

            hovertemplate=
            "<b>Vrijeme:</b> %{x}<br>"
            "<b>Pražnjenje:</b> %{customdata:.3f} kW<extra></extra>"

        )

    )

    fig.update_layout(

        title="Punjenje iz fotonaponske elektrane i pražnjenje baterije",

        xaxis_title="Vrijeme",

        yaxis_title="Snaga [kW]",

        xaxis=_tick_config(x),

        barmode="relative",

        template="plotly_white",

        hovermode="x unified"

    )

    return fig


def plot_power_grid(charge, discharge):

    x = _time_labels(len(charge))

    fig = go.Figure()

    fig.add_trace(

        go.Bar(

            x=x,

            y=charge,

            name="Punjenje",

            marker_color="green",

            hovertemplate=
            "<b>Vrijeme:</b> %{x}<br>"
            "<b>Punjenje:</b> %{y:.3f} kW<extra></extra>"

        )

    )

    fig.add_trace(

        go.Bar(

            x=x,

            y=[-v for v in discharge],

            customdata=discharge,

            name="Pražnjenje",

            marker_color="red",

            hovertemplate=
            "<b>Vrijeme:</b> %{x}<br>"
            "<b>Pražnjenje:</b> %{customdata:.3f} kW<extra></extra>"

        )

    )

    fig.update_layout(

        title="Punjenje iz mreže i pražnjenje baterije",

        xaxis_title="Vrijeme",

        yaxis_title="Snaga [kW]",

        xaxis=_tick_config(x),

        barmode="relative",

        template="plotly_white",

        hovermode="x unified"

    )

    return fig


# ---------------------------------
# Troškovi
# ---------------------------------

def plot_costs(charge_costs, discharge_benefits):

    x = _time_labels(len(charge_costs))

    fig = go.Figure()

    fig.add_trace(

        go.Bar(

            x=x,

            y=[-v for v in charge_costs],

            name="Trošak punjenja",

            marker_color="red",

            hovertemplate=
            "<b>Vrijeme:</b> %{x}<br>"
            "<b>Trošak:</b> %{customdata:.3f} €<extra></extra>",

            customdata=charge_costs

        )

    )

    fig.add_trace(

        go.Bar(

            x=x,

            y=discharge_benefits,

            name="Korist pražnjenja",

            marker_color="green",

            hovertemplate=
            "<b>Vrijeme:</b> %{x}<br>"
            "<b>Korist:</b> %{y:.3f} €<extra></extra>"

        )

    )

    fig.update_layout(

        title="Satni troškovi i koristi rada baterije",

        xaxis_title="Vrijeme",

        yaxis_title="€",

        xaxis=_tick_config(x),

        barmode="relative",

        template="plotly_white",

        hovermode="x unified"

    )

    return fig


def plot_costs_pv(values):

    x = _time_labels(len(values))

    fig = go.Figure()

    fig.add_trace(

        go.Bar(

            x=x,

            y=[max(0.0, v) for v in values],

            marker_color="green",

            name="Ušteda u odnosu na baseline",

            hovertemplate=
            "<b>Vrijeme:</b> %{x}<br>"
            "<b>Ušteda:</b> %{y:.3f} €<extra></extra>"

        )

    )

    fig.add_trace(

        go.Bar(

            x=x,

            y=[min(0.0, v) for v in values],

            marker_color="red",

            name="Dodatni trošak (degradacija)",

            hovertemplate=
            "<b>Vrijeme:</b> %{x}<br>"
            "<b>Iznos:</b> %{y:.3f} €<extra></extra>"

        )

    )

    fig.update_layout(

        title="Ušteda po vremenskom koraku u odnosu na baseline (bez baterije)",

        xaxis_title="Vrijeme",

        yaxis_title="€",

        xaxis=_tick_config(x),

        template="plotly_white",

        barmode="relative",

        hovermode="x unified"

    )

    return fig


# ---------------------------------
# Energetski balans (PV + baterija + potrošnja)
# ---------------------------------

def plot_energy_balance(
    pv_to_load,
    discharge,
    grid_imp,
    load
):

    x = _time_labels(len(load))

    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            x=x,
            y=pv_to_load,
            name="PV → potrošnja",
            marker_color="#f6c343",
            hovertemplate=
            "<b>Vrijeme:</b> %{x}<br>"
            "<b>Iz PV-a:</b> %{y:.3f} kW<extra></extra>"
        )
    )

    fig.add_trace(
        go.Bar(
            x=x,
            y=discharge,
            name="Baterija → potrošnja",
            marker_color="#4caf50",
            hovertemplate=
            "<b>Vrijeme:</b> %{x}<br>"
            "<b>Iz baterije:</b> %{y:.3f} kW<extra></extra>"
        )
    )

    fig.add_trace(
        go.Bar(
            x=x,
            y=grid_imp,
            name="Mreža → potrošnja",
            marker_color="#e57373",
            hovertemplate=
            "<b>Vrijeme:</b> %{x}<br>"
            "<b>Iz mreže:</b> %{y:.3f} kW<extra></extra>"
        )
    )

    fig.add_trace(
        go.Scatter(
            x=x,
            y=load,
            mode="lines",
            name="Ukupna potrošnja",
            line=dict(width=3, color="#333"),
            hovertemplate=
            "<b>Vrijeme:</b> %{x}<br>"
            "<b>Potrošnja:</b> %{y:.3f} kW<extra></extra>"
        )
    )

    fig.update_layout(
        title="Pokrivenost potrošnje - PV, baterija, mreža",
        xaxis_title="Vrijeme",
        yaxis_title="Snaga [kW]",
        xaxis=_tick_config(x),
        barmode="stack",
        template="plotly_white",
        hovermode="x unified"
    )

    return fig


# ---------------------------------
# Kalendarski heatmap dnevne dozracene energije
# ---------------------------------

_MONTH_NAMES_HR = [
    "", "Siječanj", "Veljača", "Ožujak", "Travanj", "Svibanj",
    "Lipanj", "Srpanj", "Kolovoz", "Rujan", "Listopad",
    "Studeni", "Prosinac"
]


def plot_month_heatmap(
    year,
    month,
    daily_kwh,
    clearsky_by_day
):
    """Kalendarski heatmap (tjedni x dani u tjednu) za odabrani
    mjesec. Boja svake ćelije odgovara postotku stvarne dnevne
    dozračene energije u odnosu na idealni vedri dan.

    Parametri
    ---------
    year, month : int
    daily_kwh : dict[int, float]
        {dan_u_mjesecu: stvarna dnevna energija [kWh/m²]}
    clearsky_by_day : dict[int, float]
        {dan_u_mjesecu: idealna clear-sky vrijednost [kWh/m²]}
    """

    cal = calendar.Calendar(firstweekday=0)  # ponedjeljak prvi
    weeks = cal.monthdayscalendar(year, month)

    z = []
    text = []
    hover = []

    for week in weeks:

        z_row = []
        t_row = []
        h_row = []

        for day in week:

            if day == 0:
                z_row.append(None)
                t_row.append("")
                h_row.append("")
                continue

            actual = daily_kwh.get(day)
            ideal = clearsky_by_day.get(day)

            if actual is None or ideal is None or ideal <= 0:
                z_row.append(None)
                t_row.append(f"<b>{day}</b><br><i>—</i>")
                h_row.append(
                    f"{day:02d}.{month:02d}.{year}.<br>"
                    f"nema podataka"
                )
                continue

            pct = 100.0 * actual / ideal
            pct_clamped = max(0.0, min(120.0, pct))
            z_row.append(pct_clamped)
            t_row.append(
                f"<b>{day}</b><br>{pct:.0f} %"
            )
            h_row.append(
                f"{day:02d}.{month:02d}.{year}.<br>"
                f"Dozračeno: {actual:.2f} kWh/m²<br>"
                f"Vedri dan: {ideal:.2f} kWh/m²<br>"
                f"<b>{pct:.0f} % idealnog</b>"
            )

        z.append(z_row)
        text.append(t_row)
        hover.append(h_row)

    fig = go.Figure(
        data=go.Heatmap(
            z=z,
            text=text,
            texttemplate="%{text}",
            textfont=dict(size=11),
            hovertext=hover,
            hovertemplate="%{hovertext}<extra></extra>",
            x=["Po", "Ut", "Sr", "Če", "Pe", "Su", "Ne"],
            y=[f"Tj. {i + 1}" for i in range(len(weeks))],
            zmin=0,
            zmax=100,
            colorscale=[
                [0.0, "#374151"],
                [0.3, "#78716c"],
                [0.55, "#ea580c"],
                [0.8, "#f59e0b"],
                [1.0, "#fbbf24"],
            ],
            showscale=True,
            colorbar=dict(
                title="% idealnog<br>vedrog dana",
                thickness=15,
                len=0.8
            ),
            xgap=2,
            ygap=2,
        )
    )

    fig.update_layout(
        title=dict(
            text=f"{_MONTH_NAMES_HR[month]} {year}",
            font=dict(size=13)
        ),
        yaxis_autorange="reversed",
        height=260,
        margin=dict(l=10, r=10, t=40, b=10),
        template="plotly_white",
        xaxis=dict(side="top", tickfont=dict(size=11)),
        yaxis=dict(showticklabels=False),
    )

    return fig
