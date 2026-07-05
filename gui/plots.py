import plotly.graph_objects as go

# ---------------------------------
# Oznake vremena
# ---------------------------------

hours = [f"{i:02d}:00" for i in range(24)]
hours_soc = [f"{i:02d}:00" for i in range(25)]


# ---------------------------------
# SOC
# ---------------------------------

def plot_soc(soc):

    fig = go.Figure()

    fig.add_trace(

        go.Scatter(

            x=hours_soc,
            y=soc,

            mode="lines+markers",

            name="SOC",

            line=dict(width=3),

            marker=dict(size=7),

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

        title="Stanje napunjenosti baterije (SOC)",

        xaxis_title="Vrijeme",

        yaxis_title="SOC",

        yaxis_range=[0,1],

        template="plotly_white",

        hovermode="x unified"

    )

    return fig


# ---------------------------------
# PV
# ---------------------------------

def plot_pv(pv):

    fig = go.Figure()

    fig.add_trace(

        go.Bar(

            x=hours,

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

        template="plotly_white",

        hovermode="x unified"

    )

    return fig


# ---------------------------------
# Cijene
# ---------------------------------

def plot_prices(prices):

    fig = go.Figure()

    fig.add_trace(

        go.Scatter(

            x=hours,

            y=prices,

            mode="lines+markers",

            line=dict(width=3),

            marker=dict(size=7),

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

        template="plotly_white",

        hovermode="x unified"

    )

    return fig


# ---------------------------------
# Punjenje / pražnjenje
# ---------------------------------

def plot_power(charge, discharge):

    fig = go.Figure()

    fig.add_trace(

        go.Bar(

            x=hours,

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

            x=hours,

            y=[-x for x in discharge],

            customdata=discharge,

            name="Pražnjenje",

            marker_color="red",

            hovertemplate=
            "<b>Vrijeme:</b> %{x}<br>"
            "<b>Pražnjenje:</b> %{customdata:.3f} kW<extra></extra>"

        )

    )

    fig.update_layout(

        title="Punjenje i pražnjenje baterije",

        xaxis_title="Vrijeme",

        yaxis_title="Snaga [kW]",

        barmode="relative",

        template="plotly_white",

        hovermode="x unified"

    )

    return fig


# ---------------------------------
# Troškovi
# ---------------------------------

def plot_costs(costs):

    fig = go.Figure()

    colors = [

        "green" if x < 0 else "red"

        for x in costs

    ]

    fig.add_trace(

        go.Bar(

            x=hours,

            y=costs,

            marker_color=colors,

            name="Trošak",

            hovertemplate=
            "<b>Vrijeme:</b> %{x}<br>"
            "<b>Trošak:</b> %{y:.3f} €<extra></extra>"

        )

    )

    fig.update_layout(

        title="Satni troškovi",

        xaxis_title="Vrijeme",

        yaxis_title="€",

        template="plotly_white",

        hovermode="x unified"

    )

    return fig