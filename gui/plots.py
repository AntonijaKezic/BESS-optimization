import plotly.graph_objects as go
# ---------------------------------
# Oznake vremena
# ---------------------------------

hours = [f"{i:02d}:00" for i in range(24)]
hours_soc = [f"{i:02d}:00" for i in range(25)]


# ---------------------------------
# SOC
# ---------------------------------

def plot_soc_pv(soc):

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

        title="Stanje napunjenosti baterije (SOC) - PV + baterija",

        xaxis_title="Vrijeme",

        yaxis_title="SOC",

        yaxis_range=[0,1],

        template="plotly_white",

        hovermode="x unified"

    )

    return fig

def plot_soc_grid(soc):

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

        title="Stanje napunjenosti baterije (SOC) - baterija spojena na mrežu",

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

def plot_power_pv(charge, discharge):

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

        title="Punjenje iz fotonaponske elektrane i pražnjenje baterije",

        xaxis_title="Vrijeme",

        yaxis_title="Snaga [kW]",

        barmode="relative",

        template="plotly_white",

        hovermode="x unified"

    )

    return fig


def plot_power_grid(charge, discharge):

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

        title="Punjenje iz mreže i pražnjenje baterije",

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

def plot_costs(charge_costs, discharge_benefits):

    fig = go.Figure()

    fig.add_trace(

        go.Bar(

            x=hours,

            y=[-x for x in charge_costs],

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

            x=hours,

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

        barmode="relative",

        template="plotly_white",

        hovermode="x unified"

    )

    return fig
     
def plot_costs_pv(values):

    fig = go.Figure()

    fig.add_trace(

        go.Bar(

            x=hours,

            y=[abs(x) if x < 0 else 0 for x in values],

            marker_color="green",

            name="Procijenjena ušteda",

            hovertemplate=
            "<b>Vrijeme:</b> %{x}<br>"
            "<b>Ušteda:</b> %{y:.3f} €<extra></extra>"

        )

    )

    fig.update_layout(

        title="Satna procijenjena ušteda (PV + baterija)",

        xaxis_title="Sat",

        yaxis_title="€",

        template="plotly_white",
        
        hovermode="x unified"

    )

    return fig